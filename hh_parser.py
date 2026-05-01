"""
Асинхронный парсер вакансий с hh.ru.
Извлекает структурированный JSON-LD (schema.org/JobPosting) из HTML страницы вакансии.
Не требует авторизации. Работает без доступа к API.

Поддерживаемые форматы ссылок:
  https://hh.ru/vacancy/123456789
  https://spb.hh.ru/vacancy/123456789
  https://hh.ru/vacancy/123456789?hhtmFrom=...
"""

import re
import ssl
import html
import json
import logging
import certifi
import aiohttp

logger = logging.getLogger(__name__)

_VACANCY_URL = "https://hh.ru/vacancy/{vacancy_id}"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_VACANCY_ID_RE = re.compile(r"hh\.ru/vacancy/(\d+)", re.IGNORECASE)
_HTML_TAGS_RE = re.compile(r"<[^>]+>")
# schema.org JobPosting живёт в <script type="application/ld+json">
_JSONLD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


class HHParseError(Exception):
    pass


def extract_vacancy_id(url: str) -> str | None:
    """Вытаскивает числовой ID вакансии из URL. Возвращает None если не hh.ru-ссылка."""
    m = _VACANCY_ID_RE.search(url)
    return m.group(1) if m else None


def _strip_html(text: str) -> str:
    """Убирает HTML-теги и декодирует HTML-entities."""
    text = _HTML_TAGS_RE.sub(" ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_jsonld(page_html: str) -> dict | None:
    """Ищет JobPosting JSON-LD в HTML страницы."""
    for match in _JSONLD_RE.finditer(page_html):
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict) and data.get("@type") == "JobPosting":
                return data
            # Иногда JSON-LD — это список
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        return item
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def _format_vacancy(data: dict) -> str:
    """Собирает читаемый текст вакансии из JSON-LD JobPosting."""
    parts: list[str] = []

    # Название и работодатель
    title = data.get("title", "")
    employer = (data.get("hiringOrganization") or {}).get("name", "")
    location = (data.get("jobLocation") or {}).get("address", {})
    city = location.get("addressLocality", "") if isinstance(location, dict) else ""

    if title:
        header = title
        if employer:
            header += f" — {employer}"
        if city:
            header += f" ({city})"
        parts.append(header)

    # Зарплата
    salary_data = data.get("baseSalary") or data.get("estimatedSalary")
    if isinstance(salary_data, dict):
        value = salary_data.get("value", {})
        if isinstance(value, dict):
            lo = value.get("minValue")
            hi = value.get("maxValue")
            currency = salary_data.get("currency", "")
            if lo and hi:
                parts.append(f"Зарплата: {lo}–{hi} {currency}")
            elif lo:
                parts.append(f"Зарплата: от {lo} {currency}")
            elif hi:
                parts.append(f"Зарплата: до {hi} {currency}")

    # Описание (HTML → текст)
    description_html = data.get("description", "")
    if description_html:
        parts.append(_strip_html(description_html))

    return "\n\n".join(parts)


def _make_ssl_connector() -> aiohttp.TCPConnector:
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    return aiohttp.TCPConnector(ssl=ssl_ctx)


async def fetch_vacancy(url: str) -> str:
    """
    Основная функция. Принимает URL вакансии hh.ru, возвращает чистый текст.
    Бросает HHParseError если что-то пошло не так.
    """
    vacancy_id = extract_vacancy_id(url)
    if not vacancy_id:
        raise HHParseError(
            "Не удалось определить ID вакансии. "
            "Убедись что ссылка вида https://hh.ru/vacancy/XXXXXXXX"
        )

    page_url = _VACANCY_URL.format(vacancy_id=vacancy_id)
    logger.info("HH parser: загружаю страницу %s", page_url)

    async with aiohttp.ClientSession(
        headers=_HEADERS,
        connector=_make_ssl_connector(),
    ) as session:
        async with session.get(
            page_url,
            timeout=aiohttp.ClientTimeout(total=15),
            allow_redirects=True,
        ) as resp:
            if resp.status == 404:
                raise HHParseError(
                    "Вакансия не найдена. "
                    "Возможно, она удалена или скрыта работодателем."
                )
            if resp.status != 200:
                raise HHParseError(
                    f"hh.ru вернул ошибку {resp.status}. Попробуй позже."
                )
            page_html = await resp.text()

    data = _extract_jsonld(page_html)
    if not data:
        raise HHParseError(
            "Не удалось извлечь данные вакансии со страницы. "
            "Возможно, hh.ru изменил структуру страницы. "
            "Скопируй текст вакансии вручную."
        )

    text = _format_vacancy(data)
    if not text:
        raise HHParseError("Не удалось извлечь текст вакансии.")

    logger.info("HH parser: извлечено %d символов", len(text))
    return text

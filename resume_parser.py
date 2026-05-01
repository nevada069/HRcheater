"""
Асинхронный парсер резюме по ссылке.

Поддерживает:
  1. hh.ru/resume/...  — структурированный парсинг страницы резюме
  2. Любая публичная ссылка — извлечение текста из HTML (fallback)

Ограничения:
  - LinkedIn требует авторизацию — не поддерживается
  - hh.ru резюме должно быть публичным (настройка видимости в профиле)
"""

import re
import ssl
import html
import json
import logging
import certifi
import aiohttp

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# hh.ru/resume/abc123def456...  (хэш из букв и цифр, от 24 символов)
_HH_RESUME_RE = re.compile(r"hh\.ru/resume/([a-f0-9]{24,})", re.IGNORECASE)
_HTML_TAGS_RE = re.compile(r"<[^>]+>")
_JSONLD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)
# Теги которые вносят шум при generic-парсинге
_NOISE_TAGS_RE = re.compile(
    r"<(script|style|noscript|nav|footer|header|aside|iframe|svg)[^>]*>.*?</\1>",
    re.DOTALL | re.IGNORECASE,
)
# Простая эвристика: ссылка начинается с http/https
_URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)


class ResumeParseError(Exception):
    pass


def is_url(text: str) -> bool:
    """Быстрая проверка: строка похожа на URL?"""
    return bool(_URL_RE.match(text.strip()))


def is_hh_resume_url(url: str) -> bool:
    return bool(_HH_RESUME_RE.search(url))


def _make_ssl_connector() -> aiohttp.TCPConnector:
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    return aiohttp.TCPConnector(ssl=ssl_ctx)


def _strip_html(raw: str) -> str:
    raw = html.unescape(raw)
    raw = _HTML_TAGS_RE.sub(" ", raw)
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


# ── hh.ru resume parser ───────────────────────────────────────────────────────

def _extract_jsonld_person(page_html: str) -> dict | None:
    """Ищет schema.org/Person или ResumeAction JSON-LD."""
    for match in _JSONLD_RE.finditer(page_html):
        try:
            data = json.loads(match.group(1))
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get("@type") in ("Person", "ResumeAction"):
                    return item
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def _format_hh_resume(data: dict, page_html: str) -> str:
    """
    Пробуем собрать текст из JSON-LD Person.
    Если данных мало — дополняем generic-извлечением из HTML.
    """
    parts: list[str] = []

    name = data.get("name", "")
    if name:
        parts.append(f"Кандидат: {name}")

    job_title = data.get("jobTitle", "")
    if job_title:
        parts.append(f"Должность: {job_title}")

    description = data.get("description", "")
    if description:
        parts.append(_strip_html(description))

    # Если JSON-LD дал мало — берём текст страницы как fallback
    if sum(len(p) for p in parts) < 300:
        logger.info("HH resume: JSON-LD мало данных, дополняем из HTML")
        generic = _extract_generic_text(page_html)
        if generic:
            parts.append(generic)

    return "\n\n".join(parts)


async def _fetch_hh_resume(url: str) -> str:
    async with aiohttp.ClientSession(
        headers=_HEADERS,
        connector=_make_ssl_connector(),
    ) as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15), allow_redirects=True) as resp:
            if resp.status == 403:
                raise ResumeParseError(
                    "Резюме закрыто или требует авторизации на hh.ru.\n"
                    "Сделай резюме публичным: Мои резюме → Настройки видимости → Всем."
                )
            if resp.status == 404:
                raise ResumeParseError("Резюме не найдено. Проверь ссылку.")
            if resp.status != 200:
                raise ResumeParseError(f"hh.ru вернул ошибку {resp.status}.")
            page_html = await resp.text()

    data = _extract_jsonld_person(page_html)
    if data:
        text = _format_hh_resume(data, page_html)
    else:
        logger.info("HH resume: JSON-LD Person не найден, используем generic")
        text = _extract_generic_text(page_html)

    if not text or len(text) < 100:
        raise ResumeParseError(
            "Не удалось извлечь текст резюме с hh.ru.\n"
            "Попробуй скопировать текст вручную или отправить PDF/DOCX."
        )

    return text


# ── Generic URL parser (fallback для любых публичных страниц) ─────────────────

_MAX_PARSED_CHARS = 10000  # потолок для любого URL-парсинга


def _extract_generic_text(page_html: str) -> str:
    """
    Убирает шумовые теги (script, style, nav...), потом стрипает HTML.
    Работает для большинства статичных страниц: портфолио, Google Docs (публичные), etc.
    """
    # Убираем шумовые блоки целиком
    clean = _NOISE_TAGS_RE.sub(" ", page_html)
    text = _strip_html(clean)

    # Убираем строки короче 20 символов (навигация, кнопки)
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 20]
    text = "\n".join(lines)

    # Умная обрезка: берём первые N символов до границы абзаца
    if len(text) > _MAX_PARSED_CHARS:
        cut = text[:_MAX_PARSED_CHARS]
        # Обрезаем до последнего переноса строки чтобы не рвать предложение
        last_nl = cut.rfind("\n")
        text = cut[:last_nl] if last_nl > _MAX_PARSED_CHARS // 2 else cut
        logger.info("Generic parser: текст обрезан до %d символов", len(text))

    return text


async def _fetch_generic_url(url: str) -> str:
    async with aiohttp.ClientSession(
        headers=_HEADERS,
        connector=_make_ssl_connector(),
    ) as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15), allow_redirects=True) as resp:
            if resp.status != 200:
                raise ResumeParseError(
                    f"Не удалось загрузить страницу (статус {resp.status}).\n"
                    "Убедись что ссылка публичная, или отправь текст/PDF/DOCX."
                )
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                raise ResumeParseError(
                    f"Ссылка ведёт не на HTML-страницу ({content_type}).\n"
                    "Отправь файл PDF/DOCX или скопируй текст резюме."
                )
            page_html = await resp.text()

    text = _extract_generic_text(page_html)
    if not text or len(text) < 100:
        raise ResumeParseError(
            "Страница пустая или рендерится через JavaScript — текст недоступен.\n"
            "Отправь PDF/DOCX или скопируй текст резюме вручную."
        )
    return text


# ── Публичный интерфейс ───────────────────────────────────────────────────────

async def fetch_resume_from_url(url: str) -> str:
    """
    Универсальная функция. Определяет тип ссылки и парсит соответственно.
    Возвращает текст резюме или бросает ResumeParseError.
    """
    url = url.strip()
    logger.info("Resume parser: обрабатываю %s", url)

    if is_hh_resume_url(url):
        logger.info("Resume parser: определён как hh.ru/resume")
        return await _fetch_hh_resume(url)

    # Явно отклоняем LinkedIn — не тратим время
    if "linkedin.com" in url.lower():
        raise ResumeParseError(
            "LinkedIn недоступен для парсинга — требует авторизацию.\n"
            "Экспортируй резюме в PDF: профиль → Ещё → Сохранить как PDF."
        )

    logger.info("Resume parser: generic URL fallback")
    return await _fetch_generic_url(url)

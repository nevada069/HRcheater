"""
Агент 2 — Vacancy Analyst.
Разбирает текст вакансии на must-have, nice-to-have, ключевые слова и сигналы грейда.
Запускается параллельно с Extractor (нет зависимостей).
"""

from pipeline.client import llm_json
from pipeline.models import VacancyAnalysis

_PROMPT = """Ты — аналитик вакансий. Разбери требования вакансии на составные части.
Будь точен: не добавляй ничего от себя, только то что написано в тексте.

ТЕКСТ ВАКАНСИИ:
{vacancy_text}

Верни ТОЛЬКО валидный JSON без комментариев:
{{
  "must_have": [
    "обязательное требование 1 (явно указано как обязательное или без оговорок)"
  ],
  "nice_to_have": [
    "желательное требование 1 (указано как 'плюс', 'желательно', 'будет преимуществом')"
  ],
  "keywords": [
    "ключевое слово для ATS-систем 1 (технологии, инструменты, методологии)"
  ],
  "seniority_signals": [
    "сигнал уровня позиции 1 (лет опыта, масштаб задач, лидерство и т.д.)"
  ],
  "role_essence": "суть роли в 1-2 предложениях — чем занимается человек на этой позиции"
}}"""


async def analyze_vacancy(vacancy_text: str) -> VacancyAnalysis:
    data = await llm_json(_PROMPT.format(vacancy_text=vacancy_text), temperature=0.1)

    return VacancyAnalysis(
        must_have=data.get("must_have", []),
        nice_to_have=data.get("nice_to_have", []),
        keywords=data.get("keywords", []),
        seniority_signals=data.get("seniority_signals", []),
        role_essence=data.get("role_essence", ""),
    )

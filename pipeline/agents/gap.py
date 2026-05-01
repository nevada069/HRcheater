"""
Агент 4 — Gap Analyst.
Сравнивает кандидата с требованиями вакансии.
Находит: сильные стороны, пробелы, что можно переформулировать.
"""

import json
from dataclasses import asdict

from pipeline.client import llm_json
from pipeline.models import ExtractedResume, VacancyAnalysis, GapReport

_PROMPT = """Ты — карьерный аналитик. Сравни кандидата с требованиями вакансии.
Будь конкретен: каждый пункт — это реальный факт, а не общая фраза.

ДАННЫЕ КАНДИДАТА:
{extracted_json}

ТРЕБОВАНИЯ ВАКАНСИИ:
{vacancy_json}

ЦЕЛЕВОЙ ГРЕЙД: {grade}
НАПРАВЛЕНИЕ: {direction}

{rag_context}

Верни ТОЛЬКО валидный JSON без комментариев:
{{
  "strengths": [
    "конкретный навык/опыт кандидата который прямо закрывает требование вакансии"
  ],
  "gaps": [
    "конкретное требование вакансии которое НЕ покрыто опытом кандидата"
  ],
  "reframeable": [
    "конкретный опыт кандидата который можно переформулировать под ключевые слова вакансии"
  ]
}}"""


async def analyze_gaps(
    extracted: ExtractedResume,
    vacancy: VacancyAnalysis,
    grade: str,
    direction: str,
    rag_context: str = "",
) -> GapReport:
    extracted_json = json.dumps(asdict(extracted), ensure_ascii=False, indent=2)
    vacancy_json = json.dumps(asdict(vacancy), ensure_ascii=False, indent=2)

    data = await llm_json(
        _PROMPT.format(
            extracted_json=extracted_json,
            vacancy_json=vacancy_json,
            grade=grade,
            direction=direction,
            rag_context=rag_context,
        ),
        temperature=0.3,
    )

    return GapReport(
        strengths=data.get("strengths", []),
        gaps=data.get("gaps", []),
        reframeable=data.get("reframeable", []),
    )

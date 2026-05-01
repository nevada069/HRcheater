"""
Агент 5 — Adaptor.
Пишет адаптированное резюме на основе данных кандидата и gap report.
Использует только реальные факты — не придумывает опыт.
"""

import json
from dataclasses import asdict

from pipeline.client import llm_json
from pipeline.models import (
    ExtractedResume, VacancyAnalysis, GapReport, ResumeData,
    ExperienceItem, EducationItem,
)
from prompts import GRADE_INSTRUCTIONS, DIRECTION_INSTRUCTIONS

_PROMPT = """Ты — опытный HR-копирайтер. Напиши адаптированное резюме.

ДАННЫЕ КАНДИДАТА (только эти факты можно использовать):
{extracted_json}

АНАЛИЗ ПРОБЕЛОВ:
{gap_json}

ТРЕБОВАНИЯ ВАКАНСИИ:
{vacancy_json}

ЦЕЛЕВОЙ ГРЕЙД: {grade}
НАПРАВЛЕНИЕ: {direction}
{grade_instruction}
{direction_instruction}

ДОПОЛНИТЕЛЬНЫЕ ПРЕДПОЧТЕНИЯ:
{extra_prefs}

{rag_context}

СТРОГИЕ ПРАВИЛА:
1. Используй ТОЛЬКО реальные данные кандидата — не добавляй компании, технологии или опыт которого не было
2. Переформулируй описание опыта под ключевые слова вакансии — там где это честно
3. Используй reframeable пункты чтобы закрыть gaps — переформулируй, не выдумывай
4. Продолжительность работы на каждом месте подбирай так чтобы суммарный стаж соответствовал грейду
5. Summary пиши под конкретную вакансию и грейд

Верни ТОЛЬКО валидный JSON без комментариев:
{{
  "name": "ФИО",
  "contacts": "телефон, email, город — через запятую",
  "summary": "3-4 предложения о кандидате под этот грейд и вакансию",
  "experience": [
    {{
      "company": "название компании",
      "role": "должность",
      "start": "месяц год, например Март 2022",
      "end": "месяц год или 'по настоящее время'",
      "description": "2-4 пункта через \\n, начиная с тире"
    }}
  ],
  "skills": ["навык1", "навык2"],
  "education": [
    {{
      "institution": "название учебного заведения",
      "degree": "степень и специальность",
      "year": "год окончания"
    }}
  ]
}}"""


def _build_extra_prefs_str(extra_prefs: dict) -> str:
    lines = []
    if extra_prefs.get("stack"):
        lines.append(f"- Желаемый стек: {extra_prefs['stack']}")
    if extra_prefs.get("company_size"):
        lines.append(f"- Размер компании: {extra_prefs['company_size']}")
    if extra_prefs.get("role"):
        lines.append(f"- Желаемая роль: {extra_prefs['role']}")
    if extra_prefs.get("country"):
        lines.append(f"- Рынок/страна: {extra_prefs['country']}")
    return "\n".join(lines) if lines else "Не указано"


async def adapt_resume(
    extracted: ExtractedResume,
    vacancy: VacancyAnalysis,
    gaps: GapReport,
    grade: str,
    direction: str,
    extra_prefs: dict,
    rag_context: str = "",
) -> ResumeData:
    data = await llm_json(
        _PROMPT.format(
            extracted_json=json.dumps(asdict(extracted), ensure_ascii=False, indent=2),
            gap_json=json.dumps(asdict(gaps), ensure_ascii=False, indent=2),
            vacancy_json=json.dumps(asdict(vacancy), ensure_ascii=False, indent=2),
            grade=grade,
            direction=direction,
            grade_instruction=GRADE_INSTRUCTIONS.get(grade, ""),
            direction_instruction=DIRECTION_INSTRUCTIONS.get(direction, ""),
            extra_prefs=_build_extra_prefs_str(extra_prefs),
            rag_context=rag_context,
        ),
        temperature=0.7,
    )

    experience = [
        ExperienceItem(
            company=e.get("company", ""),
            role=e.get("role", ""),
            start=e.get("start", ""),
            end=e.get("end", ""),
            description=e.get("description", ""),
        )
        for e in data.get("experience", [])
    ]
    education = [
        EducationItem(
            institution=e.get("institution", ""),
            degree=e.get("degree", ""),
            year=e.get("year", ""),
        )
        for e in data.get("education", [])
    ]

    return ResumeData(
        name=data.get("name", ""),
        contacts=data.get("contacts", ""),
        summary=data.get("summary", ""),
        experience=experience,
        skills=data.get("skills", []),
        education=education,
    )

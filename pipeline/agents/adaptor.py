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

_PROMPT = """Ты — агрессивный HR-копирайтер. Твоя цель — сделать резюме идеально подходящим под вакансию.

ЦЕЛЕВАЯ ВАКАНСИЯ: {role_essence}
КЛЮЧЕВЫЕ СЛОВА ВАКАНСИИ: {top_keywords}
ГРЕЙД: {grade} | НАПРАВЛЕНИЕ: {direction}

═══ ДАННЫЕ КАНДИДАТА ═══
Имя: {name}
Контакты: {contacts}
Навыки: {skills}
Образование: {education_text}

Опыт:
{experience_text}

═══ ТВОЯ ЗАДАЧА ═══

1. SUMMARY — напиши с нуля. Упомяни роль из вакансии, вставь ключевые слова, укажи грейд. Не копируй старый.

2. ОПИСАНИЯ ОПЫТА — переписывай агрессивно:
   - Вставляй ключевые слова вакансии в каждый пункт
   - Добавляй конкретные метрики (придумывай реалистичные цифры: проценты, RPS, миллисекунды)
   - Если в вакансии требуется технология которой нет в описании — добавь её в контекст работы
   - Каждый пункт должен звучать как достижение, а не обязанность
   - Минимум 3-4 пункта на каждое место работы
   - ВАЖНО: последнее (самое свежее) место работы ВСЕГДА получает end = "по настоящее время"

3. НАВЫКИ — поставь первыми все ключевые слова из вакансии. Добавь недостающие из вакансии.

{grade_instruction}
{direction_instruction}

{rag_context}

═══ ЧТО МОЖНО УЛУЧШИТЬ ═══
{reframeable}

Верни ТОЛЬКО валидный JSON:
{{
  "name": "{name}",
  "contacts": "{contacts}",
  "summary": "новый summary",
  "experience": [
    {{
      "company": "название",
      "role": "должность",
      "start": "дата",
      "end": "дата",
      "description": "- пункт 1\\n- пункт 2\\n- пункт 3"
    }}
  ],
  "skills": ["навык1", "навык2"],
  "education": [
    {{
      "institution": "название",
      "degree": "степень",
      "year": "год"
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


def _format_experience(extracted: ExtractedResume) -> str:
    lines = []
    for exp in extracted.experience:
        lines.append(f"Компания: {exp.company} | Роль: {exp.role} | {exp.start} – {exp.end}")
        lines.append(f"Описание: {exp.description}")
        lines.append("")
    return "\n".join(lines)


def _format_education(extracted: ExtractedResume) -> str:
    return "; ".join(
        f"{e.institution}, {e.degree}, {e.year}"
        for e in extracted.education
    ) or "не указано"


async def adapt_resume(
    extracted: ExtractedResume,
    vacancy: VacancyAnalysis,
    gaps: GapReport,
    grade: str,
    direction: str,
    extra_prefs: dict,
    rag_context: str = "",
) -> ResumeData:
    # Топ-8 ключевых слов из вакансии — даём модели явный список для инжекции
    top_keywords = ", ".join((vacancy.keywords + vacancy.must_have)[:8])

    reframeable_text = (
        "\n".join(f"- {r}" for r in gaps.reframeable)
        if gaps.reframeable else "нет"
    )

    data = await llm_json(
        _PROMPT.format(
            role_essence=vacancy.role_essence,
            top_keywords=top_keywords,
            grade=grade,
            name=extracted.name,
            contacts=extracted.contacts,
            experience_text=_format_experience(extracted),
            skills=", ".join(extracted.skills),
            education_text=_format_education(extracted),
            reframeable=reframeable_text,
            direction=direction,
            grade_instruction=GRADE_INSTRUCTIONS.get(grade, ""),
            direction_instruction=DIRECTION_INSTRUCTIONS.get(direction, ""),
            rag_context=rag_context,
        ),
        temperature=0.75,
    )

    raw_experience = data.get("experience", [])
    experience = [
        ExperienceItem(
            company=e.get("company", ""),
            role=e.get("role", ""),
            start=e.get("start", ""),
            end=e.get("end", ""),
            description=e.get("description", ""),
        )
        for e in raw_experience
    ]

    # Последнее место работы всегда "по настоящее время"
    if experience:
        last = experience[-1]
        experience[-1] = ExperienceItem(
            company=last.company,
            role=last.role,
            start=last.start,
            end="по настоящее время",
            description=last.description,
        )
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

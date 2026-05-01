"""
Агент 1 — Extractor.
Извлекает структурированные факты из сырого текста резюме.
Не интерпретирует, не оценивает — только то, что написано явно.
"""

from pipeline.client import llm_json
from pipeline.models import ExtractedResume, ExperienceItem, EducationItem

_PROMPT = """Ты — точный парсер резюме. Твоя единственная задача — извлечь структурированные данные.
НЕ интерпретируй, НЕ добавляй, НЕ оценивай. Только то, что написано явно.

ТЕКСТ РЕЗЮМЕ:
{resume_text}

Верни ТОЛЬКО валидный JSON без комментариев:
{{
  "name": "ФИО кандидата",
  "contacts": "телефон, email, город — через запятую (только то что есть)",
  "summary": "текст summary/objective если есть в резюме, иначе пустая строка",
  "skills": ["навык1", "навык2"],
  "experience": [
    {{
      "company": "название компании",
      "role": "должность",
      "start": "месяц год, например Март 2022",
      "end": "месяц год или 'по настоящее время'",
      "description": "описание обязанностей и достижений"
    }}
  ],
  "education": [
    {{
      "institution": "название учебного заведения",
      "degree": "степень и специальность",
      "year": "год окончания"
    }}
  ]
}}"""


async def extract_resume(resume_text: str) -> ExtractedResume:
    data = await llm_json(_PROMPT.format(resume_text=resume_text), temperature=0.1)

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

    return ExtractedResume(
        name=data.get("name", ""),
        contacts=data.get("contacts", ""),
        summary=data.get("summary", ""),
        skills=data.get("skills", []),
        experience=experience,
        education=education,
    )

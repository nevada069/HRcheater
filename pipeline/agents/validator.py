"""
Агент 6 — Validator + Scorer.

Два независимых источника оценки:
  1. LLM-score — с детальным рубриком, чтобы не сходился к 6.5
  2. Keyword overlap — детерминированная метрика (не зависит от настроения модели)

Финальный score = 0.55 * llm_score + 0.45 * keyword_score
"""

import re
import json
import logging
from dataclasses import asdict

from pipeline.client import llm_json
from pipeline.models import (
    ExtractedResume, VacancyAnalysis, ResumeData,
    ExperienceItem, EducationItem, PipelineResult, GapReport,
)

logger = logging.getLogger(__name__)

_PROMPT = """Ты — строгий независимый оценщик резюме. Твоя задача — честная оценка.

ОРИГИНАЛЬНЫЕ ДАННЫЕ КАНДИДАТА (то что есть на самом деле, до адаптации):
{extracted_json}

ТРЕБОВАНИЯ ВАКАНСИИ:
{vacancy_json}

КОЛИЧЕСТВО СОВПАВШИХ КЛЮЧЕВЫХ СЛОВ: {kw_matched} из {kw_total}

━━━ РУБРИК ОЦЕНКИ (строго следуй ему) ━━━

0.0–2.0 — Кандидат совершенно не подходит:
  профиль в другой области, нет ни одного требуемого навыка, опыт нерелевантен

3.0–4.0 — Слабое соответствие:
  есть 1-2 пересечения, но большинство must-have требований отсутствуют,
  опыт значительно ниже требуемого грейда

5.0–6.0 — Частичное соответствие:
  закрывает ~30-50% must-have требований, заметные gaps в ключевых навыках,
  либо опыт есть но не в нужном стеке

7.0–8.0 — Хорошее соответствие:
  закрывает 60-80% must-have требований, gaps есть но не критичные,
  кандидат реально может выполнять эту работу

9.0–10.0 — Отличное соответствие:
  закрывает 80%+ must-have требований, большинство nice-to-have тоже есть,
  опыт точно совпадает с грейдом и направлением

━━━ ВАЖНО ━━━
- Оценивай ОРИГИНАЛЬНОГО кандидата, не адаптированное резюме
- Используй дробные значения: 3.5, 6.8, 8.2 — не округляй до 5/6/7
- Если кандидат явно Junior а нужен Senior — это 2.0-3.5, не 6.0
- Если кандидат точно в стеке и грейде — это 8.5-9.5, не 7.0

━━━ ЗАДАЧА ━━━
Также проверь адаптированное резюме на галлюцинации:

АДАПТИРОВАННОЕ РЕЗЮМЕ:
{adapted_json}

Найди технологии/компании/факты которых НЕТ в оригинальных данных. Удали их.

Верни ТОЛЬКО валидный JSON:
{{
  "score": <число с одним знаком после запятой, строго по рубрику выше>,
  "score_reasoning": "2-3 конкретных предложения: сколько must-have закрыто, какие главные gaps, почему именно такой балл",
  "hallucinations_found": ["галлюцинация 1" или пустой список],
  "resume": {{
    "name": "ФИО",
    "contacts": "контакты",
    "summary": "summary",
    "experience": [
      {{"company": "название", "role": "должность", "start": "дата", "end": "дата", "description": "описание"}}
    ],
    "skills": ["навык1"],
    "education": [
      {{"institution": "название", "degree": "степень", "year": "год"}}
    ]
  }}
}}"""


# ── Keyword overlap — детерминированная метрика ───────────────────────────────

def _tokenize(text: str) -> set[str]:
    """Простая токенизация: строчные слова длиннее 2 символов."""
    return {w.lower() for w in re.findall(r"[a-zA-Zа-яёА-ЯЁ0-9#+.\-]{3,}", text)}


def keyword_overlap_score(extracted: ExtractedResume, vacancy: VacancyAnalysis) -> float:
    """
    Считает долю ключевых слов вакансии которые есть в резюме кандидата.
    Возвращает оценку 0.0–10.0.
    """
    # Текст кандидата: все поля вместе
    candidate_text = " ".join([
        extracted.summary,
        " ".join(extracted.skills),
        " ".join(e.description for e in extracted.experience),
        " ".join(e.role for e in extracted.experience),
    ])
    candidate_tokens = _tokenize(candidate_text)

    # Ключевые слова из вакансии: keywords + must_have
    vacancy_keywords = vacancy.keywords + vacancy.must_have
    if not vacancy_keywords:
        return 5.0  # нет данных — нейтральная оценка

    vacancy_tokens = _tokenize(" ".join(vacancy_keywords))
    if not vacancy_tokens:
        return 5.0

    matched = candidate_tokens & vacancy_tokens
    overlap = len(matched) / len(vacancy_tokens)

    # Шкалируем: 0% → 1.0, 100% → 10.0
    score = 1.0 + overlap * 9.0
    logger.info(
        "Keyword overlap: %d/%d tokens matched → raw_score=%.2f",
        len(matched), len(vacancy_tokens), score,
    )
    return round(min(score, 10.0), 1)


# ── Основная функция ──────────────────────────────────────────────────────────

async def validate_and_score(
    extracted: ExtractedResume,
    vacancy: VacancyAnalysis,
    adapted: ResumeData,
    gap_report: GapReport,
) -> PipelineResult:

    # Считаем keyword overlap заранее — инжектируем в промпт как подсказку
    kw_score = keyword_overlap_score(extracted, vacancy)
    kw_matched = len(
        _tokenize(" ".join([extracted.summary, " ".join(extracted.skills),
                            " ".join(e.description for e in extracted.experience)]))
        & _tokenize(" ".join(vacancy.keywords + vacancy.must_have))
    )
    kw_total = len(_tokenize(" ".join(vacancy.keywords + vacancy.must_have)))

    data = await llm_json(
        _PROMPT.format(
            extracted_json=json.dumps(asdict(extracted), ensure_ascii=False, indent=2),
            adapted_json=json.dumps(asdict(adapted), ensure_ascii=False, indent=2),
            vacancy_json=json.dumps(asdict(vacancy), ensure_ascii=False, indent=2),
            kw_matched=kw_matched,
            kw_total=kw_total,
        ),
        temperature=0.1,  # низкая температура — оценка должна быть стабильной
    )

    llm_score = float(data.get("score", 5.0))

    # Финальный score: взвешенная комбинация
    final_score = round(0.55 * llm_score + 0.45 * kw_score, 1)
    logger.info(
        "Scoring: llm=%.1f  keyword=%.1f  final=%.1f",
        llm_score, kw_score, final_score,
    )

    resume_raw = data.get("resume", {})
    experience = [
        ExperienceItem(
            company=e.get("company", ""),
            role=e.get("role", ""),
            start=e.get("start", ""),
            end=e.get("end", ""),
            description=e.get("description", ""),
        )
        for e in resume_raw.get("experience", [])
    ]
    education = [
        EducationItem(
            institution=e.get("institution", ""),
            degree=e.get("degree", ""),
            year=e.get("year", ""),
        )
        for e in resume_raw.get("education", [])
    ]

    final_resume = ResumeData(
        name=resume_raw.get("name", adapted.name),
        contacts=resume_raw.get("contacts", adapted.contacts),
        summary=resume_raw.get("summary", adapted.summary),
        experience=experience,
        skills=resume_raw.get("skills", adapted.skills),
        education=education,
    )

    # Дополняем reasoning информацией о keyword overlap
    llm_reasoning = data.get("score_reasoning", "")
    full_reasoning = (
        f"{llm_reasoning}\n\n"
        f"📊 Keyword overlap: {kw_matched}/{kw_total} ключевых слов вакансии "
        f"найдено в резюме ({kw_score}/10)"
    )

    return PipelineResult(
        score=final_score,
        score_reasoning=full_reasoning,
        resume=final_resume,
        gap_report=gap_report,
    )

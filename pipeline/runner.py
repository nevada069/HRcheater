"""
Pipeline Runner — оркестратор.

Граф выполнения:
  [extract_resume]  ─┐
  [analyze_vacancy] ─┼─→ [rag_retrieve] → [gap_analysis] → [adapt_resume] → [validate_and_score]
  (параллельно)     ─┘

Шаги 1, 2 и 3 (RAG) запускаются параллельно: шаги 1+2 не зависят друг от друга,
RAG зависит только от vacancy (keywords) — но мы запускаем его сразу с vacancy_text.
"""

import asyncio
import logging

from pipeline.models import PipelineResult
from pipeline.agents.extractor import extract_resume
from pipeline.agents.vacancy import analyze_vacancy
from pipeline.agents.gap import analyze_gaps
from pipeline.agents.adaptor import adapt_resume
from pipeline.agents.validator import validate_and_score
from rag.retriever import retrieve_context

logger = logging.getLogger(__name__)


async def run_pipeline(
    grade: str,
    direction: str,
    resume_text: str,
    vacancy_text: str,
    extra_prefs: dict,
) -> PipelineResult:

    # ── Шаг 1 + 2: параллельно ───────────────────────────────────────────────
    logger.info("Pipeline: step 1+2 (extract + vacancy) start")
    extracted, vacancy = await asyncio.gather(
        extract_resume(resume_text),
        analyze_vacancy(vacancy_text),
    )
    logger.info("Pipeline: step 1+2 done")

    # ── Шаг 3: RAG — параллельно с уже готовым vacancy ───────────────────────
    logger.info("Pipeline: step 3 (RAG retrieve) start")
    rag_context = await retrieve_context(
        grade=grade,
        direction=direction,
        vacancy_keywords=vacancy.keywords + vacancy.must_have,
    )
    logger.info("Pipeline: step 3 (RAG) done")

    # ── Шаг 4: gap analysis с RAG-контекстом ─────────────────────────────────
    logger.info("Pipeline: step 4 (gap analysis) start")
    gaps = await analyze_gaps(extracted, vacancy, grade, direction, rag_context)
    logger.info("Pipeline: step 4 done | strengths=%d gaps=%d reframeable=%d",
                len(gaps.strengths), len(gaps.gaps), len(gaps.reframeable))

    # ── Шаг 5: адаптация резюме с RAG-контекстом ─────────────────────────────
    logger.info("Pipeline: step 5 (adapt) start")
    adapted = await adapt_resume(extracted, vacancy, gaps, grade, direction, extra_prefs, rag_context)
    logger.info("Pipeline: step 5 done")

    # ── Шаг 6: валидация + score ──────────────────────────────────────────────
    logger.info("Pipeline: step 6 (validate + score) start")
    result = await validate_and_score(extracted, vacancy, adapted, gaps)
    logger.info("Pipeline: step 6 done | score=%.1f", result.score)

    return result

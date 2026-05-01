"""
RAG Retriever — публичный интерфейс.
Возвращает отформатированный контекст для инжекции в промпты агентов.
"""

import asyncio
import logging
from functools import partial

from rag.store import search

logger = logging.getLogger(__name__)


async def retrieve_context(
    grade: str,
    direction: str,
    vacancy_keywords: list[str],
    n_results: int = 6,
) -> str:
    """
    Возвращает строку с релевантными знаниями для инжекции в промпт.
    Запускается в executor чтобы не блокировать event loop (ChromaDB синхронный).
    """
    query = f"{grade} {direction} {' '.join(vacancy_keywords[:15])}"

    loop = asyncio.get_event_loop()
    docs = await loop.run_in_executor(
        None,
        partial(search, query=query, n_results=n_results, grade=grade, direction=direction),
    )

    if not docs:
        logger.warning("RAG: ничего не найдено для grade=%s direction=%s", grade, direction)
        return ""

    logger.info("RAG: найдено %d документов", len(docs))

    lines = ["=== БАЗА ЗНАНИЙ (релевантные советы и ключевые слова) ==="]
    for i, doc in enumerate(docs, 1):
        lines.append(f"{i}. {doc}")
    lines.append("=== КОНЕЦ БАЗЫ ЗНАНИЙ ===")

    return "\n".join(lines)

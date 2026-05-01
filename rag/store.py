"""
RAG Store — ChromaDB wrapper.
- Персистентная база в ./data/chroma
- Коллекция наполняется один раз при первом запуске, потом переиспользуется
- all-MiniLM-L6-v2 (ONNX) уже скачана и кэшируется в ~/.cache/chroma
"""

import os
import logging
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from rag.knowledge_base import DOCUMENTS

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "hr_knowledge"
_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma")

_collection = None


def _get_collection() -> chromadb.Collection:
    global _collection
    if _collection is not None:
        return _collection

    os.makedirs(_DB_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=_DB_PATH)
    ef = DefaultEmbeddingFunction()

    col = client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    # Наполняем только если коллекция пустая (первый запуск)
    if col.count() == 0:
        logger.info("RAG store: первый запуск, индексируем %d документов...", len(DOCUMENTS))
        col.add(
            ids=[d["id"] for d in DOCUMENTS],
            documents=[d["text"] for d in DOCUMENTS],
            metadatas=[
                {"grade": d["grade"], "direction": d["direction"], "doc_type": d["doc_type"]}
                for d in DOCUMENTS
            ],
        )
        logger.info("RAG store: индексация завершена")
    else:
        logger.info("RAG store: загружена существующая коллекция (%d документов)", col.count())

    _collection = col
    return _collection


def search(
    query: str,
    n_results: int = 5,
    grade: str | None = None,
    direction: str | None = None,
) -> list[str]:
    """
    Семантический поиск по базе знаний.
    Если указаны grade и/или direction — делаем два запроса:
    один с фильтром, один без (any), объединяем без дублей.
    """
    col = _get_collection()

    def _query(where: dict | None) -> list[str]:
        kwargs = dict(query_texts=[query], n_results=min(n_results, col.count()))
        if where:
            kwargs["where"] = where
        results = col.query(**kwargs)
        return results["documents"][0] if results["documents"] else []

    docs: list[str] = []
    seen: set[str] = set()

    # Специфичные документы (grade + direction)
    if grade and direction:
        for text in _query({"$and": [{"grade": grade}, {"direction": direction}]}):
            if text not in seen:
                docs.append(text)
                seen.add(text)

    # Общие для направления
    if direction:
        for text in _query({"direction": direction}):
            if text not in seen:
                docs.append(text)
                seen.add(text)

    # Общие для грейда
    if grade:
        for text in _query({"grade": grade}):
            if text not in seen:
                docs.append(text)
                seen.add(text)

    # Совсем общие (any/any)
    for text in _query({"$and": [{"grade": "any"}, {"direction": "any"}]}):
        if text not in seen:
            docs.append(text)
            seen.add(text)

    return docs[:n_results]

"""Adapter between the API layer and the established Phase 1 RAG pipeline."""
from functools import lru_cache

@lru_cache(maxsize=1)
def _pipeline():
    # Keep API startup independent from heavyweight model imports; load the
    # Phase 1 stack only when a user asks a question.
    from pipeline.rag_chain import RAGPipeline

    return RAGPipeline()


def answer_question(question: str, history: list[dict], document_id: str, user_id: str) -> dict:
    return _pipeline().ask(question=question, chat_history=history, document_ids=[document_id], user_id=user_id)

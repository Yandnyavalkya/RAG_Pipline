"""Per-upload ingestion using the same loaders, chunking, embeddings and Pinecone as Phase 1."""
import asyncio
from pathlib import Path

def ingest_file(file_path: str, document_id: str, user_id: str, document_name: str) -> dict:
    from embeddings.sentence_transformer import SentenceTransformerEmbedding
    from loaders.document_loader import load_single_file
    from rag.document_metadata import attach_document_metadata
    from splitters.text_splitter import split_documents
    from vectorstores.pinecone_store import PineconeVectorStore

    pages = load_single_file(file_path)
    chunks = split_documents(pages)
    chunks = attach_document_metadata(chunks, document_id=document_id, user_id=user_id, document_name=document_name)
    vectors = SentenceTransformerEmbedding().embed_documents([chunk.page_content for chunk in chunks])
    PineconeVectorStore().upsert_chunks(chunks=chunks, embeddings=vectors)
    return {"page_count": len(pages), "chunk_count": len(chunks)}


async def process_upload(file_path: str, document_id: str, user_id: str, document_name: str, repository) -> None:
    try:
        result = await asyncio.to_thread(ingest_file, file_path, document_id, user_id, document_name)
        await repository.update_owned(document_id, user_id, {**result, "status": "ready", "processing_error": None})
    except Exception as exc:
        await repository.update_owned(document_id, user_id, {"status": "failed", "processing_error": str(exc)[:500]})


def remove_file(file_path: str) -> None:
    Path(file_path).unlink(missing_ok=True)

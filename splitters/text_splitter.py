
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_SIZE, CHUNK_OVERLAP


def split_documents(
    documents,
    chunk_size=None,
    chunk_overlap=None,
):
    if not documents:
        raise ValueError("No documents received for splitting.")

    # Use supplied experiment settings, or fall back to .env settings.
    chunk_size = CHUNK_SIZE if chunk_size is None else chunk_size
    chunk_overlap = (
        CHUNK_OVERLAP if chunk_overlap is None else chunk_overlap
    )

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "Chunk overlap must be non-negative "
            "and smaller than chunk size."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
        add_start_index=True,
    )

    chunks = splitter.split_documents(documents)

    if not chunks:
        raise ValueError("Document splitting produced no chunks.")

    return chunks

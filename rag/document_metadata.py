import hashlib
from pathlib import Path


def document_name_from_source(source_path):
    if not source_path:
        return "Unknown source"

    return Path(str(source_path).replace("\\", "/")).name


def build_document_id(source_path):
    """Stable per-file identifier used for retrieval isolation."""

    if not source_path:
        return "unknown-document"

    normalized = str(source_path).replace("\\", "/").lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def attach_document_metadata(chunks):
    """Add document_id and document_name to each chunk before upsert."""

    for chunk in chunks:
        source_path = chunk.metadata.get("source", "")
        chunk.metadata["document_id"] = build_document_id(source_path)
        chunk.metadata["document_name"] = document_name_from_source(
            source_path
        )

    return chunks

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


def attach_document_metadata(
    chunks,
    document_id=None,
    user_id=None,
    document_name=None,
):
    """Add isolation metadata to each chunk before upsert."""

    for chunk in chunks:
        source_path = chunk.metadata.get("source", "")
        chunk.metadata["document_id"] = (
            document_id or build_document_id(source_path)
        )
        chunk.metadata["document_name"] = (
            document_name or document_name_from_source(source_path)
        )
        if user_id:
            chunk.metadata["user_id"] = user_id

    return chunks

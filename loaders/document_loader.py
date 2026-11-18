
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
)


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".csv"}


def load_single_file(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = file_path.suffix.lower()

    if extension == ".pdf":
        loader = PyPDFLoader(str(file_path))

    elif extension == ".txt":
        loader = TextLoader(
            str(file_path),
            encoding="utf-8"
        )

    elif extension == ".csv":
        loader = CSVLoader(
            str(file_path),
            encoding="utf-8"
        )

    else:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    documents = loader.load()

    # Keep source information in document metadata.
    for document in documents:
        document.metadata["source"] = str(
            file_path.resolve()
        )

    return documents


def load_documents(source_path):
    source_path = Path(source_path)

    if not source_path.exists():
        raise FileNotFoundError(
            f"Path not found: {source_path}"
        )

    if source_path.is_file():
        return load_single_file(source_path)

    documents = []

    for file_path in sorted(source_path.rglob("*")):
        if (
            file_path.is_file()
            and file_path.suffix.lower()
            in SUPPORTED_EXTENSIONS
        ):
            documents.extend(
                load_single_file(file_path)
            )

    if not documents:
        raise ValueError(
            f"No supported documents found in {source_path}"
        )

    return documents

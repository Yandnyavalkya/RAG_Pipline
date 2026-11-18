
from pathlib import Path

from loaders.document_loader import load_documents
from splitters.text_splitter import split_documents
from embeddings.sentence_transformer import (
    SentenceTransformerEmbedding
)


def main():
    print("\n--- PHASE 1 TEST ---")

    # Change this to your actual PDF file if needed.
    source_path = Path("data/raw")

    print("\n1. Loading documents...")
    documents = load_documents(source_path)

    print("Documents loaded:", len(documents))

    print("\n2. Splitting documents...")
    chunks = split_documents(documents)

    print("Chunks created:", len(chunks))
    print("First chunk preview:")
    print(chunks[0].page_content[:300])
    print("Metadata:", chunks[0].metadata)

    print("\n3. Testing embeddings...")
    embedding_model = SentenceTransformerEmbedding()

    vector = embedding_model.embed_query(
        "What is this document about?"
    )

    print("Embedding dimension:", len(vector))

    assert len(vector) == 384, (
        "Expected 384-dimensional embeddings"
    )

    print("\nPHASE 1 TEST PASSED!")


if __name__ == "__main__":
    main()

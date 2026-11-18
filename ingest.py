
from pathlib import Path

from loaders.document_loader import load_documents
from splitters.text_splitter import split_documents
from embeddings.sentence_transformer import SentenceTransformerEmbedding
from vectorstores.pinecone_store import PineconeVectorStore


def main():

    print("\n========== RAG INGESTION STARTED ==========")

    # Step 1: Load documents
    print("\n1. Loading documents...")

    documents = load_documents(Path("data/raw"))

    print("Documents loaded:", len(documents))

    # Step 2: Split documents
    print("\n2. Splitting documents...")

    chunks = split_documents(documents)

    print("Chunks created:", len(chunks))

    # Step 3: Generate embeddings
    print("\n3. Generating embeddings...")

    embedding_model = SentenceTransformerEmbedding()

    texts = [chunk.page_content for chunk in chunks]

    embeddings = embedding_model.embed_documents(texts)

    print("Embeddings generated:", len(embeddings))

    if len(embeddings) != len(chunks):
        raise ValueError("Embedding count does not match chunk count.")

    # Step 4: Connect to Pinecone
    print("\n4. Connecting to Pinecone...")

    vector_store = PineconeVectorStore()

    # Step 5: Upload vectors
    print("\n5. Uploading vectors to Pinecone...")

    uploaded = vector_store.upsert_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    print("\n========== INGESTION COMPLETED ==========")
    print("Total documents:", len(documents))
    print("Total chunks:", len(chunks))
    print("Total vectors uploaded:", uploaded)


if __name__ == "__main__":
    main()

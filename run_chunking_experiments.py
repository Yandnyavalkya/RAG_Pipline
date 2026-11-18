
from pathlib import Path

from loaders.document_loader import load_documents
from splitters.text_splitter import split_documents
from embeddings.sentence_transformer import SentenceTransformerEmbedding
from vectorstores.pinecone_store import PineconeVectorStore


EXPERIMENTS = [
    {
        "name": "A - Baseline",
        "chunk_size": 500,
        "chunk_overlap": 50,
        "namespace": "rag-chunk-500-50",
    },
    {
        "name": "B - Medium",
        "chunk_size": 700,
        "chunk_overlap": 100,
        "namespace": "rag-chunk-700-100",
    },
    {
        "name": "C - Large",
        "chunk_size": 1000,
        "chunk_overlap": 150,
        "namespace": "rag-chunk-1000-150",
    },
]


def main():

    print("\n========== CHUNKING EXPERIMENTS ==========")

    # Load documents only once.
    print("\n1. Loading documents...")

    documents = load_documents(Path("data/raw"))

    print("Documents loaded:", len(documents))

    # Load embedding model only once.
    print("\n2. Loading embedding model...")

    embedding_model = SentenceTransformerEmbedding()

    results = []

    for experiment in EXPERIMENTS:

        print("\n========================================")
        print("Experiment:", experiment["name"])
        print("Namespace:", experiment["namespace"])
        print("========================================")

        # Step 1: Split documents.
        chunks = split_documents(
            documents,
            chunk_size=experiment["chunk_size"],
            chunk_overlap=experiment["chunk_overlap"],
        )

        print("Chunks created:", len(chunks))

        # Step 2: Generate embeddings.
        texts = [chunk.page_content for chunk in chunks]

        embeddings = embedding_model.embed_documents(texts)

        print("Embeddings generated:", len(embeddings))

        if len(chunks) != len(embeddings):
            raise ValueError("Chunk and embedding counts do not match.")

        # Step 3: Connect to the experiment namespace.
        vector_store = PineconeVectorStore(
            namespace=experiment["namespace"]
        )

        # Step 4: Upload vectors.
        uploaded = vector_store.upsert_chunks(
            chunks=chunks,
            embeddings=embeddings,
        )

        results.append({
            "name": experiment["name"],
            "chunk_size": experiment["chunk_size"],
            "chunk_overlap": experiment["chunk_overlap"],
            "namespace": experiment["namespace"],
            "chunks": len(chunks),
            "uploaded": uploaded,
        })

    print("\n========== INGESTION SUMMARY ==========")

    for result in results:
        print("\nExperiment:", result["name"])
        print("Chunk size:", result["chunk_size"])
        print("Overlap:", result["chunk_overlap"])
        print("Namespace:", result["namespace"])
        print("Chunks:", result["chunks"])
        print("Uploaded:", result["uploaded"])

    print("\nALL EXPERIMENTS INGESTED SUCCESSFULLY!")


if __name__ == "__main__":
    main()

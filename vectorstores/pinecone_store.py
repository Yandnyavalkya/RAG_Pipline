
import hashlib

from pinecone import Pinecone

from config import (
    PINECONE_API_KEY,
    PINECONE_INDEX,
    PINECONE_NAMESPACE,
)


class PineconeVectorStore:

    def __init__(self, namespace=None):

        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is missing in .env")

        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index = self.pc.Index(PINECONE_INDEX)

        # Use an experiment namespace when supplied.
        # Otherwise, preserve the existing .env namespace.
        self.namespace = namespace or PINECONE_NAMESPACE

        self._validate_index()

    def _validate_index(self):
        stats = self.index.describe_index_stats()

        dimension = getattr(stats, "dimension", None)

        if dimension is None and isinstance(stats, dict):
            dimension = stats.get("dimension")

        if dimension != 384:
            raise ValueError(
                f"Pinecone index dimension is {dimension}; "
                "expected 384 for all-MiniLM-L6-v2."
            )

        print(f"Pinecone index connected: {PINECONE_INDEX}")
        print(f"Namespace: {self.namespace}")
        print(f"Index dimension: {dimension}")

    @staticmethod
    def _create_vector_id(document):
        metadata = document.metadata

        unique_content = (
            str(metadata.get("source", "unknown"))
            + str(metadata.get("page", ""))
            + str(metadata.get("start_index", ""))
            + document.page_content
        )

        return hashlib.sha256(
            unique_content.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _prepare_metadata(document):
        metadata = {}

        for key, value in document.metadata.items():
            if value is None:
                continue

            if isinstance(value, (str, int, float, bool)):
                metadata[key] = value
            else:
                metadata[key] = str(value)

        metadata["text"] = document.page_content

        return metadata

    def upsert_chunks(self, chunks, embeddings, batch_size=100):

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks and embeddings must be equal."
            )

        if not chunks:
            raise ValueError("No chunks received for Pinecone upsert.")

        total_uploaded = 0

        for start in range(0, len(chunks), batch_size):

            batch_chunks = chunks[start:start + batch_size]
            batch_embeddings = embeddings[start:start + batch_size]

            vectors = []

            for document, embedding in zip(
                batch_chunks, batch_embeddings
            ):
                vector_id = self._create_vector_id(document)
                metadata = self._prepare_metadata(document)
                metadata["chunk_id"] = vector_id

                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata,
                })

            self.index.upsert(
                vectors=vectors,
                namespace=self.namespace,
            )

            total_uploaded += len(vectors)

            print(
                f"Uploaded {total_uploaded}/{len(chunks)} chunks"
            )

        print("\nPinecone ingestion completed!")
        return total_uploaded

    def similarity_search(
        self,
        query_embedding,
        top_k=4,
        metadata_filter=None,
    ):

        query_kwargs = {
            "vector": query_embedding,
            "top_k": top_k,
            "namespace": self.namespace,
            "include_metadata": True,
        }

        if metadata_filter:
            query_kwargs["filter"] = metadata_filter

        response = self.index.query(**query_kwargs)

        return response.matches

    def delete_by_document_id(self, document_id, user_id=None):
        if not document_id:
            raise ValueError("document_id is required to delete vectors.")

        metadata_filter = {"document_id": {"$eq": document_id}}

        if user_id:
            metadata_filter = {
                "$and": [
                    {"document_id": {"$eq": document_id}},
                    {"user_id": {"$eq": user_id}},
                ]
            }

        self.index.delete(
            filter=metadata_filter,
            namespace=self.namespace,
        )

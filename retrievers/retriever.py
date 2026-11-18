
from langchain_core.documents import Document

from config import TOP_K
from embeddings.sentence_transformer import SentenceTransformerEmbedding
from vectorstores.pinecone_store import PineconeVectorStore


class PineconeRetriever:

    def __init__(self, top_k=TOP_K, namespace=None):

        self.top_k = top_k
        self.embedding_model = SentenceTransformerEmbedding()

        self.vector_store = PineconeVectorStore(
            namespace=namespace
        )

    def retrieve_with_scores(self, question):

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        query_embedding = self.embedding_model.embed_query(
            question
        )

        matches = self.vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=self.top_k,
        )

        results = []

        for match in matches:

            if isinstance(match, dict):
                vector_id = match.get("id")
                score = match.get("score")
                metadata = match.get("metadata") or {}
            else:
                vector_id = getattr(match, "id", None)
                score = getattr(match, "score", None)
                metadata = getattr(match, "metadata", None) or {}

            text = metadata.get("text", "")

            if not text:
                continue

            document_metadata = {
                key: value
                for key, value in metadata.items()
                if key != "text"
            }

            document = Document(
                page_content=text,
                metadata=document_metadata,
            )

            results.append({
                "id": vector_id,
                "score": score,
                "document": document,
            })

        return results

    def retrieve(self, question):

        results = self.retrieve_with_scores(question)

        return [
            result["document"]
            for result in results
        ]

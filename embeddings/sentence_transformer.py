
from sentence_transformers import SentenceTransformer

from config import EMBED_MODEL


class SentenceTransformerEmbedding:

    def __init__(self, model_name=EMBED_MODEL):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts):
        if not texts:
            return []

        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        return vectors.tolist()

    def embed_query(self, text):
        vector = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return vector.tolist()

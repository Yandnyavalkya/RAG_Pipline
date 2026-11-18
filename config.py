
import os
from pathlib import Path
from dotenv import load_dotenv

# Project root
BASE_DIR = Path(__file__).resolve().parent

# Load .env from project root
load_dotenv(BASE_DIR / ".env")


def get_env(name, default=None, required=False):
    value = os.getenv(name, default)

    if required and not value:
        raise ValueError(
            f"Missing environment variable: {name}. "
            "Check your .env file."
        )

    return value


# Embedding configuration
EMBED_MODEL = get_env(
    "EMBED_MODEL",
    "all-MiniLM-L6-v2"
)

# Pinecone configuration
PINECONE_API_KEY = (
    os.getenv("PINECONE_API_KEY")
    or os.getenv("PINECONE_API")
)

PINECONE_INDEX = get_env(
    "PINECONE_INDEX",
    "rag-vector-index"
)

# Use a new namespace for the refactored pipeline.
PINECONE_NAMESPACE = get_env(
    "PINECONE_NAMESPACE",
    "rag-combined-v2"
)

# Groq configuration
GROQ_API_KEY = (
    os.getenv("GROQ_API_KEY")
    or os.getenv("GROQ_API")
)

LLM_MODEL = get_env("LLM_MODEL")
LLM_TEMPERATURE = float(
    get_env("LLM_TEMPERATURE", "0.5")
)
# Chunking configuration
CHUNK_SIZE = int(get_env("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(get_env("CHUNK_OVERLAP", "50"))


# Retrieval configuration
TOP_K = int(get_env("TOP_K", "4"))

# Minimum cosine similarity score for retrieved chunks
SIMILARITY_THRESHOLD = float(
    get_env("SIMILARITY_THRESHOLD", "0.40")
)



def validate_config():
    if not PINECONE_API_KEY:
        raise ValueError(
            "PINECONE_API_KEY is missing from .env"
        )

    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is missing from .env"
        )

    if CHUNK_SIZE <= 0:
        raise ValueError("CHUNK_SIZE must be positive")

    if CHUNK_OVERLAP < 0 or CHUNK_OVERLAP >= CHUNK_SIZE:
        raise ValueError(
            "CHUNK_OVERLAP must be non-negative "
            "and smaller than CHUNK_SIZE"
        )

    if not 0.0 <= SIMILARITY_THRESHOLD <= 1.0:
        raise ValueError(
            "SIMILARITY_THRESHOLD must be between 0.0 and 1.0"
        )

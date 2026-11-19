# Modular Retrieval-Augmented Generation (RAG) Pipeline

A modular Retrieval-Augmented Generation (RAG) application built using Python, LangChain document processing components, Sentence Transformers, Pinecone, and the Groq API.

The application loads PDF, TXT, and CSV documents, splits them into smaller chunks, generates vector embeddings, stores them in Pinecone, and retrieves relevant information to answer user questions using a Groq-powered Large Language Model.

## Features

- **Document Loading:** Supports PDF, TXT, and CSV files.
- **Text Chunking:** Uses RecursiveCharacterTextSplitter with configurable chunk size and overlap.
- **Embeddings:** Uses Sentence Transformers (`all-MiniLM-L6-v2`).
- **Vector Database:** Stores and retrieves embeddings using Pinecone.
- **Semantic Search:** Retrieves relevant document chunks using cosine similarity.
- **Question Classification:** Routes document-summary, specific, and unrelated questions differently.
- **Similarity Filtering:** Rejects irrelevant specific questions using a calibrated similarity threshold. The threshold is not lowered for summary questions.
- **Relevance Validation:** Applies a server-side evidence check before generation.
- **Confidence Assessment:** Returns a calibrated confidence score from retrieval quality, coverage, citations, and grounding. Raw cosine similarity is not shown as a probability.
- **LLM Integration:** Uses the official Groq Python SDK.
- **Conversational Memory:** Supports contextual follow-up questions with recent conversation history.
- **Source Attribution:** Returns filename, page, chunk id, excerpt, and citation flags.
- **RAG Evaluation:** Evaluates answer faithfulness and relevance.
- **Chunking Experiments:** Compares different chunk sizes and overlaps using separate Pinecone namespaces.

## Architecture

```text
                PDF / TXT / CSV
                       |
                       v
                Document Loaders
                       |
                       v
                 Text Splitter
                       |
                       v
              Sentence Transformers
                       |
                       v
                Vector Embeddings
                       |
                       v
                Pinecone Database
                       |
                       v
User Question --> Retriever
                       |
                       v
              Similarity Filtering
                       |
                       v
                Retrieved Context
                       |
                       v
                  Groq LLM
                       |
                       v
              Generated Answer
                       |
                       v
              Answer with Sources

       Conversation Memory supports
             follow-up questions.
```

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Document Processing | LangChain Community |
| Text Splitting | LangChain Text Splitters |
| Embedding Model | all-MiniLM-L6-v2 |
| Vector Database | Pinecone |
| Language Model API | Groq |
| PDF Processing | PyPDF |
| Environment Management | python-dotenv |

## Project Structure

```text
RAG_Pipeline/
│
├── config.py
├── ingest.py
├── query.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── loaders/
│   └── document_loader.py
│
├── splitters/
│   └── text_splitter.py
│
├── embeddings/
│   └── sentence_transformer.py
│
├── vectorstores/
│   └── pinecone_store.py
│
├── retrievers/
│   └── retriever.py
│
├── llms/
│   └── groq_llm.py
│
├── prompts/
│   └── rag_prompt.py
│
├── memory/
│   └── conversation_memory.py
│
├── pipeline/
│   └── rag_chain.py
│
├── evaluation/
│   ├── answer_evaluator.py
│   ├── evaluation_dataset.py
│   ├── evaluation_runner.py
│   └── retrieval_metrics.py
│
├── data/
│   ├── raw/
│   └── processed/
│
└── reports/
```

## Setup and Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd RAG_Pipeline
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```cmd
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create your local `.env` file using `.env.example` as a template.

Configure the following:

- `GROQ_API_KEY`
- `LLM_MODEL`
- `PINECONE_API_KEY`
- `PINECONE_INDEX`
- `PINECONE_NAMESPACE`

Use credentials and a Groq model that are valid for your accounts.

### 5. Add documents

Place your PDF, TXT, and CSV files inside:

```text
data/raw/
```

The original documents are excluded from Git by default.

## Running the Application

### Step 1: Ingest documents

Run:

```bash
python ingest.py
```

The ingestion pipeline:

1. Loads supported documents.
2. Splits documents into chunks.
3. Generates embeddings.
4. Connects to Pinecone.
5. Uploads vectors to the configured namespace.

### Step 2: Ask questions

Run:

```bash
python query.py
```

The application supports:

| Command | Description |
|---|---|
| `history` | Displays recent conversation history |
| `clear` | Clears conversation memory |
| `exit` | Exits the application |

Ask questions related to your uploaded documents.

Examples:

- `What is the document about?` uses representative chunks and returns a grounded overview.
- `What is attention?` uses normal semantic retrieval.
- `How does photosynthesis work?` is rejected when the uploaded documents do not cover it.

Run the Phase 1 intelligence unit tests:

```bash
python test_intelligence.py
```

After changing ingestion metadata, re-run `python ingest.py` so Pinecone vectors include `document_id`, `document_name`, and `chunk_id`.

## Configuration

The main settings are controlled through `.env`.

| Variable | Baseline value | Description |
|---|---|---|
| `EMBED_MODEL` | `all-MiniLM-L6-v2` | Embedding model |
| `CHUNK_SIZE` | `500` | Number of characters per chunk |
| `CHUNK_OVERLAP` | `50` | Overlapping characters |
| `TOP_K` | `6` | Maximum retrieved chunks |
| `SIMILARITY_THRESHOLD` | `0.40` | Minimum accepted similarity |
| `LLM_TEMPERATURE` | `0.5` | Generation temperature |

The Pinecone index must have a vector dimension of 384 for the configured embedding model.

## Evaluation

The project includes evaluation components for:

- Retrieval precision.
- Retrieval reciprocal rank and MRR.
- Answer faithfulness.
- Answer relevance.
- Final RAG pipeline validation.
- Chunking configuration comparisons.

Run the final validation:

```bash
python test_final_validation.py
```

Run the chunking experiment:

```bash
python run_chunking_experiments.py
```

The chunking experiment compares:

| Experiment | Chunk Size | Overlap |
|---|---:|---:|
| A | 500 | 50 |
| B | 700 | 100 |
| C | 1000 | 150 |

Experimental vectors are stored in separate namespaces. Preserve existing production and legacy namespaces.

Evaluation reports are stored in `reports/`.

## Safety and Configuration Notes

- Never commit `.env` or API credentials.
- Keep `.env.example` limited to placeholder values.
- Do not commit original documents unless you have permission to distribute them.
- Use separate namespaces for experimental ingestion.
- Avoid deleting existing Pinecone namespaces or vectors.
- Keep your Groq and Pinecone API keys private.

## Future Improvements

See `docs/architecture.md` for the confirmed product direction:

- Multiple documents per user, with retrieval scoped by `document_id`.
- FastAPI backend with MongoDB, JWT, and document isolation.
- React + TypeScript dashboard, PDF viewer, and source highlighting.
- Suggested questions, feedback review, and production deployment.

## License

Add an appropriate license before distributing or reusing this project.

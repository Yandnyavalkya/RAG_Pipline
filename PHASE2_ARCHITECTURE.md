# Phase 2 Architecture

Inspection date: 2026-11-19.

This document is based on the current source code. Class names, function signatures, return keys, and environment variable names were verified in the repository. No Phase 1 RAG modules were modified during this inspection.

---

## 1. Existing architecture

Phase 1 is a modular CLI RAG pipeline. Ingestion and question answering are separate processes that share Pinecone, embeddings, and configuration.

```text
data/raw PDFs/TXT/CSV
        |
        v
loaders.document_loader.load_documents / load_single_file
        |
        v
splitters.text_splitter.split_documents
        |
        v
rag.document_metadata.attach_document_metadata
        |
        v
embeddings.sentence_transformer.SentenceTransformerEmbedding.embed_documents
        |
        v
vectorstores.pinecone_store.PineconeVectorStore.upsert_chunks
        |
        v
Pinecone index rag-vector-index / namespace rag-combined-v2

User question (query.py)
        |
        v
pipeline.rag_chain.RAGPipeline.ask
        |
        +--> memory.conversation_memory.ConversationMemory (in-process only)
        +--> contextualize_question -> llms.groq_llm.GroqLLM.generate
        +--> rag.question_classifier.classify_question
        +--> rag.retrieval.RetrievalOrchestrator.retrieve
                +--> retrievers.retriever.PineconeRetriever.retrieve_with_scores
        +--> rag.relevance_checker.validate_relevance
        +--> prompts.rag_prompt (system / summary / user prompts)
        +--> GroqLLM.generate
        +--> rag.source_validator.build_sources / mark_cited_sources
        +--> rag.confidence.assess_confidence
```

### 1.1 CLI entry points

| Role | File | Verified entry |
|---|---|---|
| Question answering CLI | `query.py` | `main()` constructs `RAGPipeline()` and `ConversationMemory(max_turns=5)`, then calls `rag.ask(question=..., chat_history=memory.get_history())` |
| Ingestion CLI | `ingest.py` | `main()` only. There is **no** reusable `ingest_file(...)` function. It always loads `Path("data/raw")` |

The working product CLI is `python query.py`. Preserve it.

### 1.2 Ingestion functions (verified)

`ingest.py` currently composes:

1. `load_documents(Path("data/raw"))` from `loaders/document_loader.py`
2. `split_documents(documents)` from `splitters/text_splitter.py`
3. `attach_document_metadata(chunks)` from `rag/document_metadata.py` with **no** `document_id` or `user_id` arguments
4. `SentenceTransformerEmbedding().embed_documents(texts)`
5. `PineconeVectorStore().upsert_chunks(chunks=chunks, embeddings=embeddings)`

`loaders.document_loader.load_single_file(file_path)` already exists and is the correct building block for per-upload ingestion. Supported extensions are `.pdf`, `.txt`, `.csv`. PyPDFLoader is used for PDFs.

`attach_document_metadata(chunks, document_id=None, user_id=None, document_name=None)`:

- Sets `chunk.metadata["document_id"]` to the provided `document_id`, or `build_document_id(source_path)` (SHA-256 of the lowercased normalized file path).
- Sets `chunk.metadata["document_name"]` to the provided name, or the source filename.
- Sets `chunk.metadata["user_id"]` **only if** `user_id` is provided.

CLI ingestion therefore stores path-hash `document_id` values and typically **omits** `user_id`.

### 1.3 Pinecone retrieval (verified)

`vectorstores.pinecone_store.PineconeVectorStore`:

- Index: `config.PINECONE_INDEX` (default `rag-vector-index`)
- Namespace: `config.PINECONE_NAMESPACE` (default `rag-combined-v2`)
- Validates index dimension `384`
- Vector id: SHA-256 of `source + page + start_index + page_content`
- Upsert metadata: all scalar chunk metadata plus `text` (full chunk) and `chunk_id` (same as vector id)
- `similarity_search(query_embedding, top_k=4, metadata_filter=None)` passes `filter` to `index.query` when provided
- `delete_by_document_id(document_id, user_id=None)` already exists and filters by `document_id` and optionally `user_id`

`retrievers.retriever.PineconeRetriever.retrieve_with_scores(question, metadata_filter=None, top_k=None)` embeds the query and returns:

```python
{"id": vector_id, "score": score, "document": langchain Document}
```

`rag.retrieval.build_metadata_filter(document_ids=None, user_id=None)`:

- one id → `{"document_id": {"$eq": id}}`
- several ids → `{"document_id": {"$in": [...]}}`
- optional `user_id` → `{"user_id": {"$eq": user_id}}`
- both → `{"$and": [...]}`
- neither → `None` (unfiltered search of the whole namespace)

`RAGPipeline.ask(..., document_ids=None, user_id=None)` already forwards those arguments into `RetrievalOrchestrator.retrieve`.

### 1.4 Groq LLM (verified)

`llms.groq_llm.GroqLLM`:

- Requires `GROQ_API_KEY` and `LLM_MODEL`
- `generate(system_prompt, user_prompt)` uses `groq.Groq` chat completions, `temperature=LLM_TEMPERATURE`, `max_tokens=1500`
- Raises `RuntimeError` on empty content

Synchronous SDK. Not async.

### 1.5 Conversation memory (verified)

`memory.conversation_memory.ConversationMemory`:

- In-memory list, `max_turns=5` in the CLI
- Turn shape: `{"question", "answer", "sources"}`
- `get_history()` returns a copy of that list
- Not persisted. Not user-aware. Not document-aware.

`RAGPipeline.contextualize_question` expects `chat_history` as a list of dicts with `question` and `answer` keys.

### 1.6 Source attribution and confidence (verified)

`rag.source_validator.build_sources(filtered_results)` returns dicts with:

- `source_id`, `chunk_id`, `document` (filename), `document_id`, `page`, `path`, `excerpt`, `start_index`, `score`, `cited`

`rag.confidence.assess_confidence(...)` returns:

```python
{
  "level": "high" | "medium" | "low" | "none",
  "score": float,  # calibrated composite, not raw cosine
  "signals": {
    "retrieval_relevance": float,
    "evidence_coverage": float,
    "citation_support": float,
    "answer_grounding": float,
  },
}
```

`RAGPipeline.ask` return value (success or refusal):

| Key | Meaning |
|---|---|
| `status` | `"success"` or `"rejected"` |
| `answer` | generated text or `REFUSAL_MESSAGE` |
| `question_type` | `"document_summary"` or `"specific"` (`rag.constants`) |
| `confidence` | structure above |
| `sources` | list from `build_sources` |
| `related_questions` | always `[]` in Phase 1 |
| `standalone_question` | after contextualization |
| `best_similarity_score` | top retrieved score or `None` |
| `retrieved_chunks` / `accepted_chunks` | counts |
| `retrieval_scores` | `[{vector_id, score}, ...]` |
| `relevance_reason` | string |
| `citation_report` | present on generated answers |
| `context` | assembled prompt context |

Unrelated questions are not classified as a third type. `validate_relevance` rejects them and `ask` returns `status="rejected"` with `rag.constants.REFUSAL_MESSAGE`.

### 1.7 Configuration and environment variables (verified)

`config.py` loads `.env` from the project root via `python-dotenv`.

| Variable | Default / notes |
|---|---|
| `EMBED_MODEL` | `all-MiniLM-L6-v2` |
| `PINECONE_API_KEY` or `PINECONE_API` | required at runtime |
| `PINECONE_INDEX` | `rag-vector-index` |
| `PINECONE_NAMESPACE` | `rag-combined-v2` |
| `GROQ_API_KEY` or `GROQ_API` | required at runtime |
| `LLM_MODEL` | no default; required by `GroqLLM` |
| `LLM_TEMPERATURE` | `0.5` |
| `CHUNK_SIZE` | `500` |
| `CHUNK_OVERLAP` | `50` |
| `TOP_K` | `4` in `config.py`; `.env.example` documents `6` |
| `SIMILARITY_THRESHOLD` | `0.40` |

Reuse these names in Phase 2. Do not introduce duplicate Groq/Pinecone variable names.

`.env.example` currently has only the Phase 1 variables above. `requirements.txt` currently has no FastAPI, MongoDB, JWT, bcrypt, or pytest packages.

### 1.8 Existing tests and reports (verified)

| Artifact | Type | External APIs |
|---|---|---|
| `test_intelligence.py` | Offline unit tests (classifier, relevance, confidence, sources, metadata filter). Runnable as `python test_intelligence.py` | No |
| `test_phase1.py` | Script: load `data/raw`, split, embed; asserts 384-d vectors | Local files + embedding model |
| `test_phase2.py` | Interactive retrieval against Pinecone | Pinecone |
| `test_final_validation.py` | Live `RAGPipeline.ask` cases; writes `reports/final_validation_report.json` | Groq + Pinecone |
| `test_phase5.py` | Offline retrieval-metric sanity checks | No |
| `test_chunking_configs.py` | Chunking experiments | Pinecone namespaces |
| `evaluation/` | Answer/retrieval evaluation runners | Groq/Pinecone depending on script |
| `reports/` | JSON inspection and validation outputs | Generated |

There is no pytest suite for HTTP APIs yet.

### 1.9 Incomplete backend stubs already in the tree

The repository already contains an unfinished `backend/` package. It is **not** a working FastAPI app:

- Present: `backend/app/core/{settings,database,security,exceptions,rag_runtime}.py`, `backend/app/schemas/{auth,chat,documents,feedback}.py`, `backend/app/repositories/user_repository.py`
- Missing: `main.py`, API routers, services, remaining repositories, middleware, tests, `uploads/`
- Stubs do not match the Phase 2 data model in this brief (see compatibility section)

Later steps should align or replace these stubs with the specified contracts rather than treating them as finished.

---

## 2. Proposed backend architecture

Keep Phase 1 at the project root. Add FastAPI as an application layer that **calls** existing modules.

```text
React (Phase 3) --> FastAPI /api/v1 --> services --> repositories --> MongoDB
                                        |
                                        +--> rag_adapter --> existing RAG modules
                                        |                      (pipeline, rag.*,
                                        |                       loaders, splitters,
                                        |                       embeddings,
                                        |                       pinecone_store)
                                        +--> uploads on disk
                                        +--> Pinecone (same index/namespace)
```

Recommended layout (adapted from the brief; keep `backend/app` as the Python package):

```text
backend/
    app/
        main.py
        api/                 # routers under /api/v1
            auth.py
            documents.py
            chat.py
            feedback.py
        core/
            config.py        # backend-only settings; reuse config.py for Groq/Pinecone
            security.py
            dependencies.py
        schemas/
            auth.py
            document.py
            chat.py
            feedback.py
        services/
            auth_service.py
            document_service.py
            ingestion_service.py
            chat_service.py
            feedback_service.py
            suggestion_service.py
        repositories/
            user_repository.py
            document_repository.py
            conversation_repository.py
            message_repository.py
            feedback_repository.py
        rag/
            rag_adapter.py
        middleware/
            error_handler.py
    tests/
        test_health.py
        test_documents.py
        test_chat.py
        test_auth.py
        test_feedback.py
    uploads/
```

Application rules:

- FastAPI + Pydantic v2
- API prefix `/api/v1`
- `/docs` (Swagger) and `/health` (no secrets)
- CORS from `FRONTEND_ORIGINS`
- JWT on all user-specific routes
- Motor (async) for MongoDB only; do not mix PyMongo
- Existing RAG/Pinecone/Groq/embedding code stays synchronous; call it with `asyncio.to_thread` from async endpoints
- FastAPI `BackgroundTasks` for first-pass ingestion
- One conversation ↔ one document in this version
- Ownership checks in services before every document/conversation/feedback access
- Feedback never writes to Pinecone

---

## 3. Existing modules that will be reused

Do not rewrite these. Import them from the project root (add the repo root to `PYTHONPATH` / run uvicorn from the repo root).

| Module | Reuse how |
|---|---|
| `config.py` | Groq, Pinecone, embedding, chunking, retrieval settings |
| `loaders.document_loader.load_single_file` | Per-upload PDF load |
| `splitters.text_splitter.split_documents` | Chunking |
| `rag.document_metadata.attach_document_metadata` | Pass Mongo `document_id`, `user_id`, original filename |
| `embeddings.sentence_transformer.SentenceTransformerEmbedding` | Ingestion embeddings |
| `vectorstores.pinecone_store.PineconeVectorStore` | `upsert_chunks`, `delete_by_document_id` |
| `pipeline.rag_chain.RAGPipeline.ask` | Chat generation |
| `rag.retrieval.build_metadata_filter` | Isolation (via `ask(document_ids=..., user_id=...)`) |
| `rag.constants.REFUSAL_MESSAGE`, question types | Response mapping and tests |
| `llms.groq_llm.GroqLLM` | Indirectly through `RAGPipeline` |
| `retrievers.retriever.PineconeRetriever` | Indirectly through `RAGPipeline` |
| `rag.question_classifier`, `relevance_checker`, `source_validator`, `confidence`, `prompts.rag_prompt` | Indirectly through `RAGPipeline` |
| `memory.conversation_memory.ConversationMemory` | Optional helper for turn windowing; persisted history lives in Mongo |

`query.py` and `ingest.py` stay as CLI entry points.

---

## 4. New modules that will be created

| New module | Responsibility |
|---|---|
| `backend/app/main.py` | FastAPI app, CORS, lifespan (Mongo connect/disconnect), router include, health |
| `backend/app/api/*.py` | HTTP routes |
| `backend/app/core/config.py` | `MONGODB_URI`, `MONGODB_DATABASE`, JWT, upload, CORS. No Groq/Pinecone duplicates |
| `backend/app/core/security.py` | bcrypt/Argon2 hashing, JWT encode/decode |
| `backend/app/core/dependencies.py` | Current user from Bearer token |
| `backend/app/middleware/error_handler.py` | Central exception handlers; no swallowed errors; no secret leakage |
| `backend/app/schemas/*` | Request/response models matching Mongo fields and `RAGPipeline.ask` output |
| `backend/app/services/ingestion_service.py` | Compose existing load/split/metadata/embed/upsert; update document status |
| `backend/app/services/document_service.py` | Upload validation, storage, ownership, delete (Mongo + Pinecone + file) |
| `backend/app/services/chat_service.py` | Ownership, completed-status gate, history window, persist messages |
| `backend/app/rag/rag_adapter.py` | Thin wrapper: `pipeline.ask(question, chat_history, document_ids=[id], user_id=id)` and map sources (`document` → `filename`) |
| `backend/app/services/auth_service.py` | Register/login/me |
| `backend/app/services/feedback_service.py` | Store review records only |
| `backend/app/services/suggestion_service.py` | Document-scoped related questions |
| `backend/app/repositories/*` | Async Motor access + indexes |
| `backend/tests/*` | pytest + TestClient with mocked Groq/Pinecone/Mongo |

Refresh tokens (`POST /api/v1/auth/refresh`) will be omitted unless a stored refresh-token design is implemented. Access tokens from env (`ACCESS_TOKEN_EXPIRE_MINUTES`) are sufficient for this version.

---

## 5. Integration points

### 5.1 Chat

```python
result = RAGPipeline.ask(
    question=question,
    chat_history=[{"question": ..., "answer": ...}, ...],  # last N Mongo messages
    document_ids=[str(document_id)],
    user_id=str(user_id),
)
```

Always pass both `document_ids` and `user_id` from the authenticated session and the owned document. Never rely on unfiltered namespace search.

Map Phase 1 source keys to the API:

| Pipeline key | API field |
|---|---|
| `document` | `filename` |
| `document_id` | `document_id` |
| `page` | `page` |
| `chunk_id` | `chunk_id` |
| `excerpt` | `excerpt` |
| `cited` | optional extra; keep if useful |

Return pipeline `confidence` and `question_type` unchanged. Do not invent scores. `related_questions` stays `[]` on `/chat/ask` until the suggestions endpoint fills them separately.

Chat history for contextualization: load recent user/assistant pairs from Mongo `messages` and convert to `{question, answer}`. Do not pass the in-memory CLI `ConversationMemory` singleton across users.

### 5.2 Ingestion

Background task should:

1. Set document `status="processing"`
2. `load_single_file(stored_path)`
3. `split_documents(documents)`
4. `attach_document_metadata(chunks, document_id=str(mongo_id), user_id=str(user_id), document_name=original_filename)`
5. Embed and `upsert_chunks`
6. Set `status="completed"` with `page_count` and `chunk_count`
7. On failure, set `status="failed"` and `processing_error`; never mark completed

Upload HTTP response returns `document_id` and `status` (`uploaded` or `processing`) immediately, before completion.

### 5.3 Delete

Use `PineconeVectorStore.delete_by_document_id(document_id, user_id=user_id)` plus Mongo deletes for conversations/messages/feedback owned by that user/document, plus the stored file. Do not delete unrelated vectors.

### 5.4 MongoDB collections and indexes

Use Motor. Treat `_id` as the canonical id (return hex strings in APIs). Recommended indexes:

- `users.email` unique
- `documents.user_id`, `documents.user_id + created_at`
- `conversations.user_id + document_id`, `conversations.user_id + updated_at`
- `messages.conversation_id + created_at`
- `feedback.user_id + created_at`, `feedback.message_id`

Every query for documents, conversations, messages, and feedback must include `user_id` from the JWT, not only the resource id.

Document statuses: `uploaded` | `processing` | `completed` | `failed`. Chat is allowed only when `completed`.

---

## 6. Potential compatibility issues

### 6.1 Pinecone namespace and old vectors (critical)

Existing CLI vectors in `rag-combined-v2` were ingested without `user_id` and with path-hash `document_id` values. They must **not** be deleted or overwritten.

Safe isolation strategy (no destructive migration):

1. Keep index `rag-vector-index`, dimension 384, namespace `rag-combined-v2`.
2. New API uploads upsert additional vectors whose metadata includes Mongo `document_id`, `user_id`, `document_name`/`filename`, `page`, and `chunk_id`.
3. API retrieval always uses `document_id $eq` and `user_id $eq`. Old CLI vectors will not match those filters, so they will not leak into another user's chat.
4. CLI `python ingest.py` / `python query.py` continue to operate as today (unfiltered or path-hash ids).
5. Do not run namespace delete, dimension changes, or bulk metadata rewrite.
6. Optional later (manual): users re-upload PDFs through the API if they want those files in the multi-user product. That is additive, not a wipe.

If a future admin job backfills `user_id` onto old vectors, it must be an explicit, reversible script. It is out of scope for automatic Phase 2 startup.

### 6.2 Vector id collisions

`_create_vector_id` hashes `source + page + start_index + content`. Unique stored upload paths (`backend/uploads/{user_id}/{uuid}.pdf`) make `source` unique even when two users upload the same filename or bytes. Do not ingest two files that share the same resolved path.

### 6.3 `ingest.py` is not an importable per-file API

Backend ingestion must compose existing functions in `ingestion_service.py`. Avoid changing `ingest.py` unless a thin extracted helper is later required; the CLI `main()` must remain.

### 6.4 Sync RAG inside async FastAPI

`RAGPipeline`, Groq, Pinecone, and SentenceTransformers are blocking. Calling them directly in `async def` endpoints would stall the event loop. Use `asyncio.to_thread` (or a worker later). Do not wrap Motor collections in sync PyMongo.

### 6.5 Conversation memory vs Mongo messages

CLI memory is process-local. The API must persist messages and reconstruct the last N turns. Sharing one `ConversationMemory` instance across requests would mix users.

### 6.6 Product brief vs `docs/architecture.md`

`docs/architecture.md` allows multi-document `document_ids` on a conversation. This Phase 2 brief requires **one document per conversation**. Implement the brief: store `document_id` (singular) on conversations; pass `document_ids=[that_id]` into `ask`. Multi-document combined queries stay a later extension.

### 6.7 Related questions

Phase 1 always returns `related_questions: []`. `/api/v1/documents/{document_id}/suggestions` must generate suggestions separately, using only that document's chunks/context, and must not invent citations.

### 6.8 Incomplete backend stubs vs this brief

Existing stubs differ from the required schema:

| Stub | Brief |
|---|---|
| `full_name`, extra `user_id` field | `name`, Mongo `_id` |
| `filename`, `size_bytes`, `error` | `original_filename`, `stored_filename`, `file_path`, `file_size`, `processing_error` |
| `document_ids` list on chat | single `document_id` |
| feedback `helpful` / `category` | `feedback_type` enum: `helpful`, `incorrect_answer`, `missing_information`, `incorrect_citation`, `other` |
| no `messages` collection | required `messages` collection |
| `MONGODB_DB_NAME`, `JWT_EXPIRE_MINUTES`, `CORS_ORIGINS`, `MAX_UPLOAD_BYTES` | `MONGODB_DATABASE`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `FRONTEND_ORIGINS`, `MAX_UPLOAD_SIZE_MB` |
| default `JWT_SECRET=change-this-jwt-secret` | require env secret; no hardcoded production secret |

Later steps should reshape these files to the brief.

### 6.9 Upload validation vs existing loader

The loader accepts TXT and CSV. Phase 2 upload API must accept PDF only, check extension **and** file content (`%PDF`), enforce `MAX_UPLOAD_SIZE_MB`, and sanitize stored names. TXT/CSV remain CLI-only.

### 6.10 Page numbers

Sources use `page_label` then `page`. PyPDFLoader typically stores 0-based `page`. The API should return the same value the pipeline already emits, not a fabricated 1-based page, unless a later explicit conversion is added in one place.

### 6.11 Git ignore gaps

`.gitignore` ignores `.env` and `data/raw/` / `data/processed/`. It does **not** yet ignore `backend/uploads/`, logs, or local DB files. That should be added in the environment step.

### 6.12 Health checks

`config.validate_config()` raises if keys are missing but must not be echoed. `/health` may report `mongodb: ok/error` and `pinecone_configured: true/false` without values of keys, URIs with credentials, or JWT secrets.

### 6.13 Process / import path

Uvicorn must run from the repository root so `from pipeline.rag_chain import RAGPipeline` and `from config import ...` keep working. The CLI entry points must not be moved.

---

## 7. Step 2.1 outcome

- Files created: `PHASE2_ARCHITECTURE.md`
- Files modified: none
- Existing RAG modules reused: none changed; listed for later reuse
- API endpoints added: none
- Tests executed: none (inspection only)
- Known limitations: backend stubs exist but are incomplete and schema-misaligned; live Pinecone CLI vectors lack `user_id`
- Next step: STEP 2.2 FastAPI application skeleton, after this report

Local commands used for this step: source inspection only. Phase 1 CLI remains:

```bash
python ingest.py
python query.py
python test_intelligence.py
```

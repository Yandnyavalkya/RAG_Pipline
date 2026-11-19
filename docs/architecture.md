# Document Intelligence Platform Architecture

## Confirmed product decisions

- **Document model:** multiple documents per user. A conversation can be scoped to one or more selected documents through `document_ids`.
- **Frontend (Phase 3):** React + TypeScript + Vite + Tailwind CSS.
- **Existing RAG stack:** Sentence Transformers, Pinecone, Groq. These remain the infrastructure layer.

## Why the first question failed

`What is the document about?` is a document-level summary request. Individual chunks rarely contain a sentence that is semantically close to that query, so a 0.40 cosine threshold rejects every match. That is not the same failure mode as an unrelated question such as photosynthesis.

Phase 1 therefore classifies the question first:

| Question type | Handling |
|---|---|
| Document summary | Retrieve representative chunks across pages and generate a grounded overview |
| Specific question | Normal semantic retrieval with the calibrated 0.40 threshold |
| Unrelated question | Reject in a dedicated relevance-validation stage |

The similarity threshold was not lowered. Confidence is a separate calibrated score and is never raw cosine similarity shown as a percentage.

## Target layered architecture

```text
React + TypeScript  ->  FastAPI  ->  services  ->  RAG modules  ->  MongoDB / Pinecone / files
```

Current Phase 1 keeps the working CLI pipeline and introduces the RAG intelligence modules that FastAPI will call in Phase 2:

- `rag/question_classifier.py`
- `rag/retrieval.py`
- `rag/relevance_checker.py`
- `rag/confidence.py`
- `rag/source_validator.py`
- `rag/document_metadata.py`

## Retrieval isolation

Every chunk now stores `document_id`, `document_name`, and `chunk_id`. `RAGPipeline.ask(..., document_ids=[...])` filters Pinecone results to the selected documents. Re-run ingestion so existing vectors receive the new metadata.

## API contracts (Phase 2)

The Phase 1 pipeline return value already follows the intended chat response shape:

- `status`: `success` or `rejected`
- `answer`
- `confidence.level` / `confidence.score`
- `sources[]` with filename, page, chunk_id, excerpt
- `related_questions` (empty until Phase 4)

## Roadmap

1. Phase 1 — RAG intelligence (this phase)
2. Phase 2 — FastAPI, MongoDB, JWT, document management
3. Phase 3 — React dashboard, PDF viewer, chat
4. Phase 4 — suggestions, feedback, admin review
5. Phase 5 — Docker, workers, monitoring, authorization hardening

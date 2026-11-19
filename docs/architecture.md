# Document Intelligence Platform

## Application layers

```text
React + TypeScript UI
        ↓ HTTPS / JSON + bearer token
FastAPI routes and schemas
        ↓ authenticated user id
Services: auth, upload, ingestion, chat, feedback
        ↓
Repositories (MongoDB)     RAG adapter (existing Phase 1 modules)
        ↓                              ↓
Users, PDFs, chats, feedback    Pinecone + Sentence Transformers + Groq
        ↓
Private PDF file storage
```

The React client contains presentation and API client code. FastAPI routes validate requests and require JWT authentication. Services enforce document ownership and coordinate work. Mongo repositories persist users, document metadata, conversations, messages, and feedback. The RAG adapter reuses the root pipeline rather than duplicating retrieval or answer generation.

## Document-scoped answer flow

1. Authenticated user uploads a PDF. The API validates its extension, PDF signature, and configured size limit, then saves it under a random filename.
2. Background ingestion creates chunks and embeddings and stores `document_id` and `user_id` on every Pinecone vector.
3. Chat checks that the selected document and conversation belong to the authenticated user and that the document is ready.
4. `RAGPipeline.ask` receives only the selected `document_id` and authenticated `user_id`. The relevance validator rejects insufficient or unrelated evidence before answer generation.
5. The API persists the question, grounded answer, confidence signals, and source excerpts. Sources include the PDF filename, one-based page, chunk id, and excerpt.
6. The client renders confidence and citations. Selecting a citation opens the stored PDF at its page. Users can submit a correction or feedback for review.

Confidence is the existing RAG pipeline's calibrated evidence score, not a probability. Refusals have no sources and a `none` confidence level. Suggested questions are drawn from text in the selected PDF and are also constrained to that document when submitted.

## Data and security boundaries

- JWT bearer token identifies a user for every protected endpoint.
- Mongo lookups for documents and conversations include the authenticated `user_id`.
- Pinecone retrieval filters by both selected `document_id` and `user_id`.
- PDF fetch and deletion require ownership. Deletion removes the document's vectors, file, conversation messages, conversations, and record.
- Feedback is stored for review and does not automatically alter model behavior or the source document.
- Reviewer accounts are selected by the `ADMIN_EMAILS` environment variable. Only those accounts can list or update feedback across users; ordinary users can see their own submissions.

## Docker deployment

`docker-compose.yml` runs the API, static React app behind Nginx, and MongoDB. Nginx proxies `/api/*` to FastAPI. Named volumes persist MongoDB data, uploaded PDFs, and the downloaded embedding model. Provide `.env` with model credentials, `JWT_SECRET`, and `ADMIN_EMAILS` before building.

## Local development

See the root README for environment setup and launch commands. The backend expects MongoDB, Pinecone, and Groq credentials. Frontend API origin can be overridden with `frontend/.env` (`VITE_API_URL`).

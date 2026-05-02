# Intelligent Document Analyzer — Astra DB Implementation Guide

This document adapts the original Supabase-based guide to use DataStax Astra (Document API + Vector search) and the existing server code in `/server`.

Summary:
- Backend: FastAPI + DataStax Astra (Document API) for metadata & chunks + SentenceTransformer embeddings
- LLM: Groq (same as before)
- Frontend: Next.js App Router talking to FastAPI endpoints

Project layout (relevant parts):

```
frontend/
├── app/
├── components/
├── server/
│   ├── main.py
│   ├── routes/
│   │   ├── documents.py
│   │   └── query.py
│   ├── services/
│   │   ├── astra_service.py     <-- Astra integration + embeddings
│   │   ├── document_processor.py
│   │   └── groq_service.py
│   └── requirements.txt
├── ASTRA_IMPLEMENTATION.md
└── .env.local (frontend)
```

IMPORTANT: The repo already contains an Astra-backed service at `server/services/astra_service.py`. This guide documents how to configure and run everything.

Part A — Backend (FastAPI + Astra)

1) Install Python dependencies

From `frontend/server`:

```bash
python -m venv venv
source venv/bin/activate   # mac/linux
pip install -r requirements.txt
```

2) Environment variables

Create `/server/.env` (copy from `/server/.env.example`) and set these values:

- `GROQ_API_KEY` — your Groq API key
- `ASTRA_DB_TOKEN` — Astra Application Token (with Data API access)
- `ASTRA_DB_API_ENDPOINT` — your Astra REST endpoint (something like `https://<db-id>-<region>.apps.astra.datastax.com`)
- `ASTRA_DB_KEYSPACE` — your keyspace name
- `ALLOWED_ORIGINS` — e.g. `http://localhost:3000`

How to get Astra token & endpoint:
- In the Astra console create an application and enable the Data API (Document API / REST). Create an Application Token with Data API permissions and copy the token and endpoint.

3) Create keyspace & collections

You can use the Astra UI or CQL to create a keyspace. The server expects two collections (document-style collections used by the Document API):

- `documents` — stores document metadata
  - `_id` (string/uuid), `filename` (string), `size` (int), `full_text` (string), `chunk_count` (int)
- `document_chunks` — stores chunked text + embeddings
  - `_id` (string/uuid), `document_id` (string), `chunk_text` (string), `chunk_index` (int), `$vector` (array of floats)

Notes on vector search/indexing in Astra:
- Astra provides vector search capabilities through the Document API (and integrated vector indexes). After inserting chunks with a `$vector` field (array of floats), you can query with a vector filter. Consult Astra docs to create any vector index if required for performance.

4) How the backend works (high level)

- `/api/documents/upload` (POST): extracts text (`document_processor.py`), chunks it, generates embeddings in `astra_service.py` (SentenceTransformer), stores metadata in the `documents` collection and chunks (with `$vector`) in `document_chunks`.
- `/api/documents/` (GET): lists documents from `documents` collection.
- `/api/documents/{id}` (DELETE): deletes chunks and metadata.
- `/api/query/` (POST): uses `astra_service.semantic_search` to retrieve top-k chunk texts for the given document and question, then sends that combined context to Groq via `groq_service.py`.

5) Run the backend

```bash
cd frontend/server
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for Swagger UI.

Part B — Frontend (Next.js)

The frontend communicates with the FastAPI backend — it does not need direct access to Astra. Keep your `.env.local` values as:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Endpoints used by the frontend (same as original guide):

- `POST /api/documents/upload` — upload file form/multipart
- `GET /api/documents/` — list documents
- `DELETE /api/documents/{id}` — delete
- `POST /api/query/` — ask question

Part C — Notes & differences versus Supabase approach

- Storage: The current Astra implementation stores the extracted text and chunks directly in the database. If you need to store raw binary files (PDF/DOCX) for download, add an object store (S3 or other) and save a reference path in the `documents` collection.
- Embeddings: `astra_service.py` uses `sentence-transformers` locally to compute embeddings. This avoids external embedding API costs but requires GPU/CPU time for large uploads.
- Vector search: Astra's Document API supports vector queries. Confirm your Astra tier and index configuration for performant nearest-neighbor search.
- Security: Keep `ASTRA_DB_TOKEN` secret — store it only in server-side `.env` and never in frontend env files.

Part D — Troubleshooting & tips

- If `sentence-transformers` installation is heavy, consider precomputing embeddings in a separate worker or use a hosted embedding API.
- If PDF extraction fails (image-based PDFs), use OCR (Tesseract) as a future enhancement.
- If Groq responds with rate-limit errors, add retry/backoff logic in `groq_service.py`.

Part E — Quick checklist (post-setup)

- [ ] Populate `/server/.env` with Astra + Groq keys
- [ ] Create Astra keyspace and collections (`documents`, `document_chunks`)
- [ ] Install server deps and run `uvicorn`
- [ ] Start Next.js frontend and test upload/query flows

Files to inspect in this repo:
- [server/main.py](server/main.py)
- [server/routes/documents.py](server/routes/documents.py)
- [server/routes/query.py](server/routes/query.py)
- [server/services/astra_service.py](server/services/astra_service.py)
- [server/services/document_processor.py](server/services/document_processor.py)
- [server/services/groq_service.py](server/services/groq_service.py)

If you want, I can:
- add a minimal `/server/.env` template with placeholders filled from your Astra project, or
- adjust `astra_service.py` to store raw file bytes to S3-compatible storage instead of only DB.

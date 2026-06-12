# INSIGHT.AI - Claude Context

## Project
INSIGHT.AI is a document assistant built around a shared RAG backend and a Streamlit browser UI.

The current implementation supports an AWS hybrid demo mode:
- Document upload, parsing, embedding, index storage, and retrieval run locally on the machine or EC2 instance.
- Answer generation uses Groq, so retrieved document excerpts are sent to Groq.
- Use public/demo documents only in hybrid mode.

Local Ollama support remains in `functions/chat_engine.py`, but the FastAPI chat endpoint currently configures Groq for backend chat.

## Entry Points
- FastAPI backend: `functions/api.py`
- Streamlit UI: `functions/dashboard.py`
- Local backend command: `py -3.13 -m uvicorn functions.api:app --host 127.0.0.1 --port 8000`
- Local UI command: `py -3.13 -m streamlit run functions/dashboard.py`
- AWS deployment notes: `deploy/aws_deployment.md`
- AWS service templates: `deploy/insight-api.service`, `deploy/insight-ui.service`, `deploy/nginx-insight-ai.conf`

## Environment
The app loads `.env` from the current working directory through `functions/env.py`.

Important variables:
- `GROQ_API_KEY`: required for Groq-backed chat.
- `GROQ_MODEL`: defaults to `llama-3.1-8b-instant`.
- `INSIGHT_STORAGE_DIR`: storage root. AWS target is `/opt/insight-ai/data`; local Windows development can use `.insight_data`.
- `INSIGHT_API_BASE_URL`: Streamlit API target, default `http://localhost:8000`.
- `INSIGHT_LLM_PROVIDER`: used by `setup_models`; set to `groq` for hybrid mode.

Do not commit real secrets. `.env` is ignored.

## Active Python Modules
- `functions/api.py`
  - FastAPI app.
  - Endpoints: `GET /health`, `GET /indexes`, `POST /indexes`, `DELETE /indexes/{index_id}`, `POST /chat`.
  - Uploads files to the configured storage directory, indexes them, lists saved indexes, deletes indexes, and chats against an index.

- `functions/dashboard.py`
  - Streamlit UI that calls the FastAPI backend over HTTP.
  - Lets users upload files, create a searchable collection, choose a saved collection, inspect its files, delete collections, and chat.
  - Stores `active_index` and `messages` in `st.session_state`; RAG state lives in the backend/storage layer.

- `functions/document_loader.py`
  - Loads one directory of uploaded files.
  - Extracts DOCX text with `python-docx`.
  - Extracts PDF text with `pypdf.PdfReader`.
  - Extracts XLSX/XLS-style workbook rows with `openpyxl`.
  - Prefixes text with source filename metadata for citation context.

- `functions/index_manager.py`
  - Persists indexes under `<INSIGHT_STORAGE_DIR>/indexes/<index_id>`.
  - Stores uploaded source files under `<INSIGHT_STORAGE_DIR>/uploads/<index_id>`.
  - Uses `<INSIGHT_STORAGE_DIR>/registry.json` for saved index metadata.
  - Sanitizes index IDs.
  - Splits non-spreadsheet documents with `SentenceSplitter(chunk_size=500, chunk_overlap=50)`.
  - Splits spreadsheet documents with `SentenceSplitter(chunk_size=4000, chunk_overlap=0)`.
  - Uses `VectorStoreIndex(all_nodes, show_progress=True)`.

- `functions/chat_engine.py`
  - Configures global LlamaIndex settings.
  - Embedding model: `BAAI/bge-small-en-v1.5`.
  - Local LLM option: Ollama `llama3.2:3b`.
  - Groq option: `GroqCompatibleLLM`, using the OpenAI SDK against `https://api.groq.com/openai/v1`.
  - Chat engine mode: `context`.
  - Retrieval: `similarity_top_k=5`.
  - Memory: `ChatMemoryBuffer.from_defaults(token_limit=3900)`.

- `functions/config.py`
  - Shared storage and model configuration.
  - Creates storage directories.

- `functions/env.py`
  - Lightweight `.env` loader.
  - Does not override environment variables that are already set.

## Storage
Default local storage:
- `~/INSIGHT_AI_storage`

Configurable storage:
- Base: `INSIGHT_STORAGE_DIR`
- Uploads: `<INSIGHT_STORAGE_DIR>/uploads`
- Indexes: `<INSIGHT_STORAGE_DIR>/indexes`
- Registry: `<INSIGHT_STORAGE_DIR>/registry.json`

Registry entries contain:
- `folder_path`
- `folder_name`
- `documents`, with each document's `filename` and `type`

## Supported File Types
- `.pdf` via `pypdf`
- `.docx` via `python-docx`
- `.xlsx` via `openpyxl`
- `.xls` is accepted by extension, but legacy binary Excel files may fail because `openpyxl` does not support true old-style `.xls` files.

## Tests
Current tests cover:
- DOCX loading.
- XLSX loading.
- Unsupported file handling.
- Index deletion and registry cleanup.

Verification commands:
- `py -3.13 -m compileall -q .\functions .\tests`
- `py -3.13 -m pytest -q`
- `py -3.13 -m pip check`

## Development Rules
- Keep retrieval, indexing, storage, and document parsing local unless the user explicitly asks otherwise.
- Be clear that Groq receives retrieved excerpts in AWS hybrid mode.
- Do not silently change `BAAI/bge-small-en-v1.5`, `llama3.2:3b`, or the default Groq model.
- Re-index documents after changing embeddings, chunking, storage paths, or document text formatting.
- Prefer focused changes that preserve the current FastAPI service plus Streamlit UI split.
- Keep secrets in environment variables or `.env`, never committed files.

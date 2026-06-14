# Document Analysis RAG - Claude Context

## Project

Document Analysis RAG is a FastAPI + Streamlit application for asking grounded questions over uploaded PDF, Word, and Excel files.

Current deployment mode:
- Document upload, parsing, embedding, index storage, and retrieval run locally on the machine or EC2 instance.
- Groq generates final answers in the deployed demo, so retrieved excerpts are sent to Groq.
- Use public/demo documents only in AWS hybrid mode.

## Entry Points

- FastAPI backend: `functions/api.py`
- Streamlit UI: `functions/dashboard.py`
- Runtime dependencies: `requirements.txt`
- Local backend: `py -3.13 -m uvicorn functions.api:app --host 127.0.0.1 --port 8000`
- Local UI: `py -3.13 -m streamlit run functions/dashboard.py`
- AWS walkthrough: `README_AWS_HYBRID.md`, `deploy/aws_deployment.md`
- AWS setup scripts: `deploy/setup_ec2.sh`, `deploy/update_app.sh`
- AWS service templates: `deploy/insight-api.service`, `deploy/insight-ui.service`, `deploy/nginx-insight-ai.conf`

## Environment

The app loads `.env` from the current working directory through `functions/env.py`.

Important variables:
- `GROQ_API_KEY`: required for backend chat.
- `GROQ_MODEL`: defaults to `llama-3.1-8b-instant`.
- `INSIGHT_STORAGE_DIR`: storage root. AWS target is `/opt/insight-ai/data`; local development can use `.insight_data`.
- `INSIGHT_API_BASE_URL`: Streamlit API target, default `http://localhost:8000`.

Do not commit real secrets. `.env` is ignored and should be recreated from `.env.example`.

## Repository Shape

- `functions/`: application source.
- `tests/`: unit tests.
- `documents/`: synthetic public corpus for RAG demos/evaluation.
- `deploy/`: systemd, Nginx, EC2 scripts, and deployment notes.
- `README.md`, `README_AWS_HYBRID.md`, `CLAUDE.md`: project and agent documentation.

Generated uploads, indexes, virtual environments, caches, and `.env` files should stay out of Git.

## Active Modules

- `functions/api.py`
  - FastAPI app.
  - Endpoints: `GET /health`, `GET /indexes`, `POST /indexes`, `DELETE /indexes/{index_id}`, `POST /chat`, `POST /retrieve`.
  - Handles upload persistence, index creation/deletion, chat, and retrieval debugging.
  - Uses small helper functions for upload directory replacement, file saving, default index naming, and `top_k` clamping.

- `functions/dashboard.py`
  - Streamlit UI that calls the FastAPI backend.
  - Handles collection upload, saved collection selection, deletion, chat, and source display.
  - Keeps UI state limited to `active_index` and chat `messages`; persisted RAG state lives in backend storage.

- `functions/document_loader.py`
  - Extracts DOCX text with `python-docx`.
  - Extracts PDF text with `pypdf.PdfReader`.
  - Extracts workbook rows with `openpyxl`.
  - Prefixes loaded text with filename/sheet context for better source grounding.

- `functions/index_manager.py`
  - Persists indexes under `<INSIGHT_STORAGE_DIR>/indexes/<index_id>`.
  - Stores uploaded source files under `<INSIGHT_STORAGE_DIR>/uploads/<index_id>`.
  - Uses `<INSIGHT_STORAGE_DIR>/registry.json` for saved collection metadata.
  - Sanitizes index IDs.
  - Splits text docs with `SentenceSplitter(chunk_size=500, chunk_overlap=50)`.
  - Splits spreadsheet docs with `SentenceSplitter(chunk_size=4000, chunk_overlap=0)`.

- `functions/chat_engine.py`
  - Embedding model: `BAAI/bge-small-en-v1.5`.
  - Groq-compatible LLM wrapper uses the OpenAI SDK against `https://api.groq.com/openai/v1`.
  - Chat mode: `context`.
  - Retrieval: `similarity_top_k=3`.
  - Returns source snippets with filename, type, score, and shortened text.

- `functions/config.py`
  - Storage and model configuration.
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

Local development can use `.insight_data`; it is ignored by Git.

## Supported File Types

- `.pdf` via `pypdf`
- `.docx` via `python-docx`
- `.xlsx` via `openpyxl`
- `.xls` is accepted by extension, but true legacy binary Excel files may fail because `openpyxl` does not support them.

## Evaluation

The synthetic corpus in `documents/` is designed to test:
- exact fact lookup
- spreadsheet value retrieval
- deployment incident lookup
- source/citation behavior
- answer-not-present abstention

Recent local evaluation with Ollama `llama3.1:8b` passed the core smoke questions semantically. The deployed app still uses Groq for final answer generation.

## Verification

Use:
- `py -3.13 -m compileall -q .\functions .\tests`
- `py -3.13 -m pytest -q`
- `py -3.13 -m pip check`

Current tests cover:
- DOCX loading.
- XLSX loading.
- Unsupported file handling.
- Index deletion and registry cleanup.
- Source-node formatting.

## Development Rules

- Keep retrieval, indexing, storage, and document parsing local unless explicitly asked otherwise.
- Be clear that Groq receives retrieved excerpts in AWS hybrid mode.
- Re-index documents after changing embeddings, chunking, storage paths, or document text formatting.
- Keep changes focused around the FastAPI backend and Streamlit UI split.
- Keep secrets in environment variables or `.env`, never committed files.
- Keep deployment docs pointed at `https://github.com/faisalcn24/insight-ai-2.git` unless the repo is renamed.

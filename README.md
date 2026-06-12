# ProjectINSIGHT.AI

> AWS hybrid mode warning: use public/demo documents only. Retrieval, indexing, and storage stay local to the machine or EC2 instance, but retrieved excerpts are sent to Groq for answer generation. See `README_AWS_HYBRID.md` and `deploy/aws_deployment.md`.

INSIGHT.AI is a document assistant for asking questions over uploaded PDF, Word, and Excel files. It uses a FastAPI backend for indexing/chat and a Streamlit UI for the browser experience.

## How It Works

1. Upload documents through the Streamlit UI.
2. FastAPI stores the uploads locally under the configured storage directory.
3. Documents are parsed based on file type.
4. Text is chunked and embedded locally with `BAAI/bge-small-en-v1.5`.
5. LlamaIndex stores the persisted vector index locally.
6. Chat requests retrieve relevant chunks from the local index.
7. Groq generates the final answer from the retrieved context.

## Supported File Types

| Format | Library |
| --- | --- |
| `.pdf` | `pypdf` |
| `.docx` | `python-docx` |
| `.xlsx` | `openpyxl` |

Legacy `.xls` files may not work because `openpyxl` does not support true old-style binary Excel files.

## Project Stack

- Python 3.13
- FastAPI backend
- Streamlit UI
- LlamaIndex retrieval/indexing
- HuggingFace local embeddings: `BAAI/bge-small-en-v1.5`
- Groq LLM for AWS hybrid/demo chat
- Optional local Ollama support in `functions/chat_engine.py`

## Setup

Create and activate a virtual environment:

```powershell
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements-aws.txt
```

Create a local `.env` file from the example:

```powershell
copy .env.example .env
```

Set at least:

```env
GROQ_API_KEY=replace-with-your-groq-key
GROQ_MODEL=llama-3.1-8b-instant
INSIGHT_API_BASE_URL=http://127.0.0.1:8000
INSIGHT_STORAGE_DIR=C:\ICT\ProjectINSIGHT.AI\.insight_data
```

For AWS, use:

```env
INSIGHT_STORAGE_DIR=/opt/insight-ai/data
```

## Run Locally

Start FastAPI in one terminal:

```powershell
py -3.13 -m uvicorn functions.api:app --host 127.0.0.1 --port 8000
```

Start Streamlit in another terminal:

```powershell
py -3.13 -m streamlit run functions/dashboard.py
```

Open:

```text
http://localhost:8501
```

## API

- `GET /health`
- `GET /indexes`
- `POST /indexes`
- `DELETE /indexes/{index_id}`
- `POST /chat`

## AWS Deployment

AWS is used as the host for the demo deployment:

- One EC2 instance runs FastAPI and Streamlit.
- Local EC2 disk stores uploads, indexes, and `registry.json`.
- Nginx routes `/api/*` to FastAPI and `/` to Streamlit.
- Groq is still the external LLM provider.

Deployment templates and notes are in `deploy/`.

## Development

Run checks:

```powershell
py -3.13 -m compileall -q .\functions .\tests
py -3.13 -m pytest -q
py -3.13 -m pip check
```

Do not commit `.env`, uploaded documents, indexes, or secrets.

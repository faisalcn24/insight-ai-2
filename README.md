# Document Analysis RAG

A document question-answering app for PDF, Word, and Excel files. It uses a FastAPI backend for ingestion/retrieval, a Streamlit UI for chat, local embeddings for search, and Groq for answer generation in the deployed demo.

> Demo privacy note: retrieval, indexing, and storage run locally or on EC2, but retrieved excerpts are sent to Groq for final answer generation. Use public/demo documents only.

## Highlights

- Upload PDF, DOCX, and XLSX files into named searchable collections.
- Embed and retrieve locally with `BAAI/bge-small-en-v1.5`.
- Persist uploaded files, vector indexes, and collection metadata across restarts.
- Return source snippets and retrieval scores with each answer.
- Expose `POST /retrieve` to inspect retrieved chunks without calling the LLM.
- Use document-aware chunking: smaller overlapping chunks for text, larger chunks for spreadsheets.
- Deploy on one Ubuntu EC2 instance with systemd, Nginx, and repeatable setup scripts.

## Demo Results

| Question | Result |
| --- | --- |
| What does FR-006 require? | Correctly answered from the product requirements document with a source snippet. |
| What is the Q3 Groq API budget? | Retrieved the spreadsheet value `75` from the budget workbook. |
| Why did `/api/health` return a 404? | Explained the Nginx config/default site issue from the incident log. |
| What is the company payroll for 2026? | Correctly said the answer is not present in the documents. |

## Evaluation Snapshot

Tested against the synthetic corpus in `documents/` using local Ollama `llama3.1:8b` for answer generation. The deployed demo uses Groq for faster responses.

| Metric | Result |
| --- | --- |
| Recall@5 | 100% |
| Citation Accuracy | 100% |
| Answer Correctness | 100% |
| Abstention Accuracy | 100% |
| Faithfulness | 100% on curated corpus |

## Architecture

```text
Streamlit UI
    |
    v
FastAPI backend
    |
    +-- document parsing: pypdf, python-docx, openpyxl
    +-- chunking: LlamaIndex SentenceSplitter
    +-- embeddings: BAAI/bge-small-en-v1.5
    +-- vector index: persisted LlamaIndex storage
    +-- answer generation: Groq-compatible OpenAI API
```

AWS demo shape:

```text
public HTTP :80 -> Nginx
    /api/*      -> FastAPI on 127.0.0.1:8000
    /           -> Streamlit on 127.0.0.1:8501
```

## API

- `GET /health`
- `GET /indexes`
- `POST /indexes`
- `DELETE /indexes/{index_id}`
- `POST /chat`
- `POST /retrieve`

## Quick Start

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Set these values in `.env`:

```env
GROQ_API_KEY=replace-with-your-groq-key
GROQ_MODEL=llama-3.1-8b-instant
INSIGHT_API_BASE_URL=http://127.0.0.1:8000
INSIGHT_STORAGE_DIR=.insight_data
```

Run the backend:

```powershell
py -3.13 -m uvicorn functions.api:app --host 127.0.0.1 --port 8000
```

Run the UI in another terminal:

```powershell
py -3.13 -m streamlit run functions/dashboard.py
```

Open `http://localhost:8501`.

## AWS Deployment

Deployment templates and notes are in `deploy/`.

Fresh EC2 setup after cloning:

```bash
bash deploy/setup_ec2.sh
```

Update an existing EC2 deployment:

```bash
bash deploy/update_app.sh
```

See [README_AWS_HYBRID.md](README_AWS_HYBRID.md) for the full EC2 walkthrough.

## Repository Map

- `functions/` - FastAPI backend, Streamlit UI, document loading, indexing, and chat setup.
- `documents/` - synthetic public test corpus for RAG evaluation.
- `tests/` - focused unit tests.
- `deploy/` - systemd, Nginx, and EC2 deployment scripts.

## Development Checks

```powershell
py -3.13 -m compileall -q .\functions .\tests
py -3.13 -m pytest -q
py -3.13 -m pip check
```

Do not commit `.env`, uploaded documents with private data, generated indexes, virtual environments, or secrets.

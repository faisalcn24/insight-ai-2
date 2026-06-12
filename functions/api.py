"""FastAPI backend for INSIGHT.AI."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

try:
    from .chat_engine import ask_index, setup_embeddings, setup_groq_llm
    from .config import ensure_storage_dirs, get_uploads_dir
    from .document_loader import load_documents
    from .index_manager import build_index, load_index, load_registry, remove_index, sanitize_index_id, update_registry
except ImportError:
    from chat_engine import ask_index, setup_embeddings, setup_groq_llm
    from config import ensure_storage_dirs, get_uploads_dir
    from document_loader import load_documents
    from index_manager import build_index, load_index, load_registry, remove_index, sanitize_index_id, update_registry


app = FastAPI(title="INSIGHT.AI API")


class ChatRequest(BaseModel):
    index_id: str
    message: str


@app.on_event("startup")
def startup() -> None:
    ensure_storage_dirs()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/indexes")
def list_indexes() -> dict:
    return {"indexes": [{"index_id": key, **value} for key, value in load_registry().items()]}


@app.post("/indexes")
def create_index(index_id: str | None = Form(default=None), files: list[UploadFile] = File(...)) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="At least one document is required")

    raw_name = index_id or Path(files[0].filename or f"upload-{uuid.uuid4().hex[:8]}").stem
    safe_index_id = sanitize_index_id(raw_name)
    upload_dir = get_uploads_dir() / safe_index_id
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    for upload in files:
        if not upload.filename:
            continue
        destination = upload_dir / Path(upload.filename).name
        with destination.open("wb") as out_file:
            shutil.copyfileobj(upload.file, out_file)

    raw_docs, warnings = load_documents(upload_dir)
    if not raw_docs:
        raise HTTPException(status_code=400, detail={"message": "No readable documents found", "warnings": warnings})

    setup_embeddings()
    build_index(raw_docs, safe_index_id)
    metadata = update_registry(safe_index_id, upload_dir, raw_docs)
    return {"index_id": safe_index_id, "documents": metadata["documents"], "warnings": warnings}


@app.delete("/indexes/{index_id}")
def delete_index(index_id: str) -> dict:
    safe_index_id = sanitize_index_id(index_id)
    if safe_index_id not in load_registry():
        raise HTTPException(status_code=404, detail="Index not found")
    if not remove_index(safe_index_id):
        raise HTTPException(status_code=500, detail="Could not remove index")
    upload_dir = get_uploads_dir() / safe_index_id
    if upload_dir.exists():
        shutil.rmtree(upload_dir, ignore_errors=True)
    return {"deleted": safe_index_id}


@app.post("/chat")
def chat(request: ChatRequest) -> dict:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")
    safe_index_id = sanitize_index_id(request.index_id)
    if safe_index_id not in load_registry():
        raise HTTPException(status_code=404, detail="Index not found")
    try:
        setup_embeddings()
        setup_groq_llm()
        index = load_index(safe_index_id)
        answer = ask_index(index, request.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat failed: {exc}") from exc
    return {"answer": answer}

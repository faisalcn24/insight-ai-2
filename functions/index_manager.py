"""Index creation, storage and registry management."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter

try:
    from .config import ensure_storage_dirs, get_indexes_dir, get_registry_file
except ImportError:
    from config import ensure_storage_dirs, get_indexes_dir, get_registry_file


def sanitize_index_id(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", name.strip()).strip("-")
    if not cleaned:
        raise ValueError("Index name must include at least one letter or number")
    return cleaned

def load_registry():
    ensure_storage_dirs()
    registry_file = get_registry_file()
    if registry_file.exists():
        with registry_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_registry(registry):
    ensure_storage_dirs()
    with get_registry_file().open("w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)

def get_index_dir(folder_name) -> Path:
    ensure_storage_dirs()
    return get_indexes_dir() / sanitize_index_id(folder_name)

def build_index(raw_docs, folder_name):
    # Save index locally.
    index_dir = get_index_dir(folder_name)
    if index_dir.exists():
        shutil.rmtree(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)

    xlsx_docs = [LlamaDocument(text=doc["text"], metadata={"filename": doc["filename"], "type": doc["type"]}) for doc in raw_docs if doc["type"] == "xlsx"]
    other_docs = [LlamaDocument(text=doc["text"], metadata={"filename": doc["filename"], "type": doc["type"]}) for doc in raw_docs if doc["type"] != "xlsx"]

    all_nodes = []

    if other_docs:
        splitter = SentenceSplitter(chunk_size=500, chunk_overlap=50)
        other_nodes = splitter.get_nodes_from_documents(other_docs)
        all_nodes.extend(other_nodes)

    # Process Excel docs with large chunk size to avoid mid-row splits
    if xlsx_docs:
        xlsx_splitter = SentenceSplitter(chunk_size=4000, chunk_overlap=0)
        xlsx_nodes = xlsx_splitter.get_nodes_from_documents(xlsx_docs)
        all_nodes.extend(xlsx_nodes)

    if not all_nodes:
        raise ValueError("No readable document text found to index")

    index = VectorStoreIndex(all_nodes, show_progress=True)
    index.storage_context.persist(persist_dir=str(index_dir))

    return index

def load_index(folder_name):
    # Load an existing index from local storage.
    index_dir = get_index_dir(folder_name)
    storage_context = StorageContext.from_defaults(persist_dir=str(index_dir))
    return load_index_from_storage(storage_context)

def remove_index(folder_name):
    # Delete existing index from local storage.
    try:
        index_dir = get_index_dir(folder_name)
        if index_dir.exists():
            shutil.rmtree(index_dir, ignore_errors=True)
        registry = load_registry()
        registry.pop(folder_name, None)
        save_registry(registry)
        return True
    except Exception:
        return False

def update_registry(folder_name, folder_path, raw_docs):
    # Update the registry with the latest index metadata.
    folder_name = sanitize_index_id(folder_name)
    registry = load_registry()
    registry[folder_name] = {
        "folder_path": str(folder_path),
        "folder_name": folder_name,
        "documents": [{"filename": d["filename"], "type": d["type"]} for d in raw_docs],
    }
    save_registry(registry)
    return registry[folder_name]




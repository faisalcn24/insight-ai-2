"""Shared configuration for INSIGHT.AI services."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from .env import load_dotenv_file
except ImportError:
    from env import load_dotenv_file


load_dotenv_file()

DEFAULT_STORAGE_DIR = Path.home() / "INSIGHT_AI_storage"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"


def get_storage_dir() -> Path:
    return Path(os.getenv("INSIGHT_STORAGE_DIR", str(DEFAULT_STORAGE_DIR))).expanduser().resolve()


def get_uploads_dir() -> Path:
    return get_storage_dir() / "uploads"


def get_indexes_dir() -> Path:
    return get_storage_dir() / "indexes"


def get_registry_file() -> Path:
    return get_storage_dir() / "registry.json"


def ensure_storage_dirs() -> None:
    get_storage_dir().mkdir(parents=True, exist_ok=True)
    get_uploads_dir().mkdir(parents=True, exist_ok=True)
    get_indexes_dir().mkdir(parents=True, exist_ok=True)


def get_groq_model() -> str:
    return os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)

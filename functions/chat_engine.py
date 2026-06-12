"""Configure LlamaIndex chat engines for local and AWS hybrid modes."""

from __future__ import annotations

import os
from collections.abc import Generator
from typing import Any

from llama_index.core.llms import CompletionResponse, CustomLLM, LLMMetadata
from llama_index.core import Settings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from openai import OpenAI

try:
    from .config import get_groq_model
except ImportError:
    from config import get_groq_model


SYSTEM_PROMPT = (
    "You are a document analysis assistant that answers questions based ONLY on the provided documents. "
    "Be concise and always cite the source document name when possible. "
    "Never make up or infer information not present in the documents. "
    "When asked to compare documents or versions, clearly identify differences in figures, content, "
    "sections, and conclusions between the documents, citing which version contains each piece of information. "
    "When working with spreadsheet data, report ALL figures and values exactly as they appear in the document "
    "without omitting any rows or entries. Never summarise or truncate tabular data. "
    "For calculations like totals or averages, show your working step by step. "
    "If a calculation seems complex or you are uncertain of the result, clearly state the raw figures and "
    "advise the user to verify calculations independently."
)


class GroqCompatibleLLM(CustomLLM):
    model: str
    api_key: str
    api_base: str = "https://api.groq.com/openai/v1"
    timeout: float = 120.0
    temperature: float = 0.1
    max_tokens: int | None = None

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=8192,
            num_output=self.max_tokens or 1024,
            is_chat_model=True,
            model_name=self.model,
        )

    def complete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponse:
        client = OpenAI(api_key=self.api_key, base_url=self.api_base, timeout=self.timeout)
        request_kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.temperature),
        }
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens

        response = client.chat.completions.create(**request_kwargs)
        text = response.choices[0].message.content or ""
        return CompletionResponse(text=text, raw=response)

    def stream_complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> Generator[CompletionResponse, None, None]:
        yield self.complete(prompt, formatted=formatted, **kwargs)


def setup_embeddings():
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")


def setup_ollama_llm():
    Settings.llm = Ollama(model="llama3.2:3b", request_timeout=300.0)


def setup_groq_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is required for Groq-backed chat")
    Settings.llm = GroqCompatibleLLM(
        model=get_groq_model(),
        api_key=api_key,
        timeout=120.0,
    )


def setup_models(provider: str | None = None):
    setup_embeddings()
    provider = provider or os.getenv("INSIGHT_LLM_PROVIDER", "ollama")
    if provider.lower() == "groq":
        setup_groq_llm()
    else:
        setup_ollama_llm()


def create_chat_engine(index):
    return index.as_chat_engine(
        chat_mode="context",
        similarity_top_k=5,
        memory=ChatMemoryBuffer.from_defaults(token_limit=3900),
        system_prompt=SYSTEM_PROMPT,
    )


def ask_index(index, message: str) -> str:
    return str(create_chat_engine(index).chat(message))

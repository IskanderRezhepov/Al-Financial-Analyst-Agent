"""Explicit provider selection; no credentials in source or browser code."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def provider() -> str:
    value = os.getenv("LLM_PROVIDER", "ollama").lower()
    if value not in {"ollama", "thesys"}:
        raise ValueError("LLM_PROVIDER must be ollama or thesys.")
    return value


def model_settings() -> dict:
    local = provider() == "ollama"
    key = "ollama-local" if local else os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise ValueError("Thesys mode requires your Thesys key in OPENAI_API_KEY in .env.")
    return {
        "model": os.getenv("OLLAMA_MODEL", "qwen3:4b-instruct") if local else os.getenv(
            "THESYS_MODEL", "c1/openai/gpt-5/v-20250930"
        ),
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1") if local
        else os.getenv("THESYS_BASE_URL", "https://api.thesys.dev/v1/embed/"),
        "api_key": key,
        "timeout": float(os.getenv("LLM_TIMEOUT_SECONDS", "240")),
        "max_retries": 0,
        **({"temperature": 0, "max_tokens": 1800} if local else {}),
    }


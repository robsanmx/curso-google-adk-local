"""Configuración compartida de modelos locales para los agentes de ADK Web."""
from __future__ import annotations

import json
import os
import urllib.request
from google.adk.models.lite_llm import LiteLlm


def get_local_model() -> LiteLlm | str:
    """Detecta automáticamente el mejor modelo disponible en Ollama local o recurre a fallback."""
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1.0)
        data = json.loads(req.read().decode())
        available = [m["name"] for m in data.get("models", [])]
        for candidate in ["llama3.2:latest", "llama3.2", "llama3.1:8b", "qwen2.5-coder:14b", "gemma3:12b-it-qat"]:
            if candidate in available:
                return LiteLlm(model=f"ollama_chat/{candidate}")
        if available:
            return LiteLlm(model=f"ollama_chat/{available[0]}")
    except Exception:
        pass
    if os.getenv("GOOGLE_API_KEY"):
        return "gemini-2.5-flash"
    return LiteLlm(model="ollama_chat/llama3.2:latest")

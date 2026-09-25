"""Agente DevOps con Human-in-the-Loop (HITL) para Google ADK."""
from __future__ import annotations

import json
import os
import urllib.request
from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool


def reiniciar_servicio(servicio: str, forzar: bool = False) -> str:
    """Reinicia un servicio en los servidores de producción o base de datos.

    Args:
        servicio: Nombre del servicio a reiniciar (ej: 'postgresql', 'nginx', 'redis').
        forzar: Si es True, realiza un reinicio forzado inmediato (SIGKILL / kill -9).
    """
    modo = "FORZADO (SIGKILL)" if forzar else "GRACEFUL"
    return f"✓ Servicio '{servicio}' reiniciado exitosamente en modo {modo}."


def validar_aprobacion(servicio: str = "", forzar: bool = False, **kwargs) -> bool:
    """Política de Seguridad: Requiere confirmación humana si el servicio es crítico o si forzar=True."""
    servicios_criticos = ["postgresql", "mysql", "production_db", "auth_service"]
    es_critico = servicio.lower() in servicios_criticos
    if forzar or es_critico:
        return True
    return False


# Herramienta protegida con Human-in-the-Loop
tool_reinicio_seguro = FunctionTool(
    func=reiniciar_servicio,
    require_confirmation=validar_aprobacion
)


def _get_model():
    """Detecta modelo local de Ollama o recurre a fallback."""
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1.0)
        data = json.loads(req.read().decode())
        available = [m["name"] for m in data.get("models", [])]
        for candidate in ["llama3.2:latest", "llama3.2", "llama3.1:8b", "qwen2.5-coder:14b"]:
            if candidate in available:
                return LiteLlm(model=f"ollama_chat/{candidate}")
        if available:
            return LiteLlm(model=f"ollama_chat/{available[0]}")
    except Exception:
        pass
    if os.getenv("GOOGLE_API_KEY"):
        return "gemini-2.5-flash"
    return LiteLlm(model="ollama_chat/llama3.2:latest")


# ADK Web descubrirá automáticamente este root_agent
root_agent = Agent(
    name="devops_agent",
    model=_get_model(),
    instruction=(
        "Eres un operador de infraestructura y DevOps senior. "
        "Ayudas al usuario a gestionar y reiniciar servicios del sistema. "
        "Cuando el usuario te pida reiniciar un servicio, utiliza la herramienta 'reiniciar_servicio'. "
        "Si la herramienta solicita confirmación humana, espera pacientemente la decisión del operador."
    ),
    tools=[tool_reinicio_seguro]
)

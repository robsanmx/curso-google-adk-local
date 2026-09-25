"""Agente DevOps con Human-in-the-Loop (Módulo 1)."""
from __future__ import annotations

import sys
from pathlib import Path

agents_dir = Path(__file__).parent.parent
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

from config import get_local_model
from google.adk.agents.llm_agent import Agent
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


tool_reinicio_seguro = FunctionTool(
    func=reiniciar_servicio,
    require_confirmation=validar_aprobacion
)

root_agent = Agent(
    name="hitl_agent",
    model=get_local_model(),
    instruction=(
        "Eres un operador de infraestructura y DevOps senior. "
        "Ayudas al usuario a gestionar y reiniciar servicios del sistema. "
        "Cuando el usuario te pida reiniciar un servicio, utiliza la herramienta 'reiniciar_servicio'. "
        "Si la herramienta solicita confirmación humana, espera pacientemente la decisión del operador."
    ),
    description="Agente de operaciones críticas con protección Human-in-the-Loop.",
    tools=[tool_reinicio_seguro]
)

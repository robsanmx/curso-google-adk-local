"""Orquestador con Patrón AgentTool (Módulo 4)."""
from __future__ import annotations

import sys
from pathlib import Path

agents_dir = Path(__file__).parent.parent
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

from config import get_local_model
from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool

local_model = get_local_model()

agente_seguridad = Agent(
    name="especialista_owasp",
    model=local_model,
    instruction=(
        "Eres un analista de ciberseguridad enfocado en el OWASP Top 10. "
        "Cuando te pasen un fragmento de código, endpoints o configuración, genera un reporte "
        "indicando vulnerabilidades detectadas, puntuación de severidad y recomendación de mitigación."
    ),
    description="Herramienta inteligente de auditoría de seguridad OWASP basada en un subagente LLM."
)

tool_seguridad = AgentTool(agente_seguridad)

root_agent = Agent(
    name="agent_tool_orchestrator",
    model=local_model,
    instruction=(
        "Eres el Tech Lead del equipo. Ayudas a los desarrolladores a construir software seguro y mantenible. "
        "Cuando el usuario te consulte sobre código o arquitectura con implicaciones de seguridad, "
        "delega la auditoría a tu herramienta 'especialista_owasp' mediante el patrón AgentTool. "
        "Integra los resultados devueltos por el especialista en tu respuesta final de forma didáctica."
    ),
    tools=[tool_seguridad],
    description="Orquestador Tech Lead que invoca a un agente especialista de seguridad como herramienta (AgentTool)."
)

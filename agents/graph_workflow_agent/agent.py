"""Flujo Basado en Grafos con Enrutamiento Dinámico (Módulo 3)."""
from __future__ import annotations

import sys
from pathlib import Path

agents_dir = Path(__file__).parent.parent
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

from config import get_local_model
from google.adk.agents.llm_agent import Agent
from google.adk.events.event import Event
from google.adk.workflow import Workflow

local_model = get_local_model()


def enrutador(node_input: str) -> Event:
    """Clasifica el incidente y determina la ruta especializada."""
    texto = node_input.lower()
    if any(k in texto for k in ["bug", "error", "traceback", "excepcion", "crash"]):
        return Event(output=node_input, route="codigo")
    elif any(k in texto for k in ["seguridad", "vulnerabilidad", "cve", "token", "inyeccion", "ataque"]):
        return Event(output=node_input, route="seguridad")
    return Event(output=node_input, route="__DEFAULT__")


agente_code = Agent(
    name="experto_bugs",
    model=local_model,
    instruction=(
        "Eres un ingeniero especialista en depuración de errores y bugs en producción. "
        "Analiza el problema recibido, identifica la causa raíz y provee un parche o fix concreto."
    )
)

agente_sec = Agent(
    name="experto_seguridad",
    model=local_model,
    instruction=(
        "Eres un analista de incidentes del SOC y ciberseguridad. "
        "Analiza el reporte de vulnerabilidad o brecha recibido y provee contramedidas inmediatas para mitigar el ataque."
    )
)

agente_gen = Agent(
    name="arquitecto_general",
    model=local_model,
    instruction=(
        "Eres un arquitecto de software y soporte de sistemas general. "
        "Brinda orientación estructurada y buenas prácticas sobre la consulta planteada."
    )
)

root_agent = Workflow(
    name="graph_workflow_agent",
    edges=[
        ("START", enrutador),
        (enrutador, {
            "codigo": agente_code,
            "seguridad": agente_sec,
            "__DEFAULT__": agente_gen
        })
    ],
    description="Workflow basado en grafos (ADK 2.0) con enrutamiento dinámico condicional a agentes especialistas."
)

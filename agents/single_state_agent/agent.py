"""Agente Individual con Inyección Dinámica de Estado (Módulo 1)."""
from __future__ import annotations

import sys
from pathlib import Path

agents_dir = Path(__file__).parent.parent
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

from config import get_local_model
from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    name="single_state_agent",
    model=get_local_model(),
    instruction=(
        "Eres un asistente de desarrollo y DevOps senior. "
        "Ayudas al usuario a depurar problemas, escribir scripts y gestionar infraestructura. "
        "Responde de forma concisa, con bloques de código limpios y buenas prácticas."
    ),
    description="Asistente de desarrollo individual para consultas técnicas y soporte DevOps."
)

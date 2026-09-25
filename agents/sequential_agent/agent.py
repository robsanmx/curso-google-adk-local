"""Pipeline Secuencial de Refactorización de Código (Módulo 2)."""
from __future__ import annotations

import sys
from pathlib import Path

agents_dir = Path(__file__).parent.parent
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

from config import get_local_model
from google.adk.agents.llm_agent import Agent
from google.adk.agents.sequential_agent import SequentialAgent

local_model = get_local_model()

agente_linter = Agent(
    name="agente_linter",
    model=local_model,
    instruction=(
        "Eres un analista de calidad de código estático (Linter). "
        "Analiza el código o requerimiento del usuario buscando errores, falta de type hints y problemas de legibilidad. "
        "Escribe un informe conciso con las debilidades encontradas."
    ),
    output_key="informe_lint"
)

agente_refactor = Agent(
    name="agente_refactor",
    model=local_model,
    instruction=(
        "Eres un desarrollador Python senior especialista en refactorización. "
        "Lee el informe de lint generado anteriormente: {informe_lint}. "
        "Genera la versión corregida del código aplicando buenas prácticas (PEP 8, type hints, docstrings) "
        "y explica brevemente las mejoras realizadas."
    ),
    output_key="codigo_refactorizado"
)

root_agent = SequentialAgent(
    name="sequential_agent",
    sub_agents=[agente_linter, agente_refactor],
    description="Pipeline secuencial determinista: Análisis estático (Linter) seguido de Refactorización."
)

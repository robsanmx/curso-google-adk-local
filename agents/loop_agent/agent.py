"""Bucle de Optimización Iterativa con EscalationChecker (Módulo 2)."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import AsyncGenerator

agents_dir = Path(__file__).parent.parent
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

from config import get_local_model
from google.adk.agents import BaseAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.llm_agent import Agent
from google.adk.events import Event, EventActions

local_model = get_local_model()


class EscalationChecker(BaseAgent):
    """Inspecciona el estado de la sesión. Si detecta aprobación o calidad suficiente, detiene el bucle."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        evaluacion = str(ctx.session.state.get("eval_calidad", ""))
        iter_num = ctx.session.state.get("num_iter", 0) + 1
        ctx.session.state["num_iter"] = iter_num

        if "APROBADO" in evaluacion.upper() or "CORRECTO" in evaluacion.upper():
            yield Event(
                author=self.name,
                actions=EventActions(escalate=True),
                text=f"✓ [EscalationChecker]: Criterio cumplido en iteración {iter_num}. Finalizando bucle."
            )
        else:
            yield Event(
                author=self.name,
                text=f"↻ [EscalationChecker]: Iteración {iter_num}. Continuando refinamiento..."
            )


generador = Agent(
    name="agente_optimizador",
    model=local_model,
    instruction=(
        "Eres un ingeniero de software senior experto en algoritmos de alto rendimiento. "
        "Analiza el código o problema enviado por el usuario. "
        "Propón una implementación optimizada en Python con type hints, manejo de excepciones y comentarios claros. "
        "Si recibes feedback previo en {eval_calidad}, aplícalo inmediatamente."
    ),
    output_key="codigo_actual"
)

evaluador = Agent(
    name="agente_evaluador",
    model=local_model,
    instruction=(
        "Eres un revisor de código muy riguroso. Evalúa la solución generada:\n"
        "{codigo_actual}\n\n"
        "Verifica complejidad computacional, type hints y legibilidad. "
        "Si la calidad es excelente, incluye 'APROBADO' en tu veredicto. "
        "De lo contrario, indica claramente qué debe corregirse."
    ),
    output_key="eval_calidad"
)

root_agent = LoopAgent(
    name="loop_agent",
    sub_agents=[generador, evaluador, EscalationChecker(name="stop_checker")],
    max_iterations=3,
    description="Bucle iterativo de mejora continua de código con parada temprana temprana de calidad."
)

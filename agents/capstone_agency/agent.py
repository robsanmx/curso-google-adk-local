"""Agencia de Arquitectura de Software y Seguridad Capstone (Proyecto Final)."""
from __future__ import annotations

import sys
from pathlib import Path

agents_dir = Path(__file__).parent.parent
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

from config import get_local_model
from google.adk.agents.llm_agent import Agent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.tools import ToolContext

local_model = get_local_model()


def puntuar_auditoria(area: str, nota_0_a_100: int, tool_context: ToolContext | None = None) -> dict:
    """Registra la puntuación técnica de un área evaluada en la sesión.

    Args:
        area: Especialidad analizada (ej: 'Base de Datos', 'Seguridad y Compliance').
        nota_0_a_100: Calificación numérica otorgada del 0 al 100.
    """
    if tool_context and hasattr(tool_context, "state"):
        scores = tool_context.state.get("scores_calidad", {})
        scores[area] = nota_0_a_100
        tool_context.state["scores_calidad"] = scores
    return {"status": "success", "mensaje": f"Puntuación {nota_0_a_100}/100 registrada para {area}."}


# 1. Product Manager
lead_pm = Agent(
    name="lead_pm",
    model=local_model,
    instruction=(
        "Eres un Lead Product Manager técnico de élite. "
        "Analiza el problema de negocio planteado por el usuario, delimita el alcance en 2 oraciones concisas "
        "y define los 3 componentes tecnológicos indispensables."
    ),
    output_key="analisis_producto"
)

# 2. Especialistas Concurrentes
arquitecto_datos = Agent(
    name="arquitecto_datos",
    model=local_model,
    instruction=(
        "Basándote en el análisis funcional:\n{analisis_producto}\n\n"
        "Diseña la arquitectura de datos: selección de motores (SQL relacional vs NoSQL/Documental), "
        "estrategia de particionamiento, réplicas de lectura y caché con Redis. "
        "Utiliza la herramienta 'puntuar_auditoria' para asentar tu calificación técnica (0-100)."
    ),
    tools=[puntuar_auditoria],
    output_key="dictamen_db"
)

ciso_seguridad = Agent(
    name="ciso_seguridad",
    model=local_model,
    instruction=(
        "Basándote en el análisis funcional:\n{analisis_producto}\n\n"
        "Audita la postura de seguridad: arquitectura Zero Trust, gestión de identidades (OAuth2/OIDC), "
        "cifrado en tránsito y reposo, y cumplimiento normativo aplicable (HIPAA, GDPR o PCI-DSS). "
        "Utiliza la herramienta 'puntuar_auditoria' para asentar tu calificación de seguridad (0-100)."
    ),
    tools=[puntuar_auditoria],
    output_key="dictamen_sec"
)

auditoria_concurrente = ParallelAgent(
    name="auditoria_concurrente",
    sub_agents=[arquitecto_datos, ciso_seguridad]
)

# 3. CTO Sintetizador
cto_ejecutivo = Agent(
    name="cto_ejecutivo",
    model=local_model,
    instruction=(
        "Eres el CTO Ejecutivo de la consultora. Has recibido los siguientes entregables:\n"
        "• Análisis de Producto: {analisis_producto}\n"
        "• Dictamen de Datos: {dictamen_db}\n"
        "• Dictamen de Seguridad: {dictamen_sec}\n\n"
        "Elabora el Blueprint Arquitectónico Final con:\n"
        "1. Diagrama de topología recomendado (Cloud / On-premise).\n"
        "2. Stack tecnológico definitivo justificado.\n"
        "3. Roadmap de entrega estructurado en 3 fases (MVP, Escalamiento, Hardening)."
    ),
    output_key="blueprint_final"
)

root_agent = SequentialAgent(
    name="capstone_agency",
    sub_agents=[lead_pm, auditoria_concurrente, cto_ejecutivo],
    description="Agencia de Arquitectura y Seguridad Capstone: Product Manager -> Auditoría Concurrente (Datos + Seguridad) -> Blueprint del CTO."
)

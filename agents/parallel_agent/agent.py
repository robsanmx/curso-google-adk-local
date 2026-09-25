"""Pipeline Concurrente con ParallelAgent y Agregador (Módulo 2)."""
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

local_model = get_local_model()

auditor_owasp = Agent(
    name="auditor_owasp",
    model=local_model,
    instruction=(
        "Eres un auditor de seguridad enfocado en el OWASP Top 10. "
        "Analiza el componente o código recibido y detecta vulnerabilidades como inyecciones, fallos de autenticación o exposición de datos."
    ),
    output_key="informe_owasp"
)

auditor_infra = Agent(
    name="auditor_infra",
    model=local_model,
    instruction=(
        "Eres un especialista en seguridad de infraestructura y contenedores. "
        "Evalúa configuraciones de Dockerfile, Kubernetes, permisos y puertos expuestos."
    ),
    output_key="informe_infra"
)

auditor_licencias = Agent(
    name="auditor_licencias",
    model=local_model,
    instruction=(
        "Eres un experto en compliance legal y auditoría de licencias open source (GPL, MIT, Apache). "
        "Evalúa riesgos de licencias en las dependencias."
    ),
    output_key="informe_licencias"
)

panel_auditoria = ParallelAgent(
    name="panel_auditoria_paralelo",
    sub_agents=[auditor_owasp, auditor_infra, auditor_licencias]
)

agente_sintetizador = Agent(
    name="agente_sintetizador",
    model=local_model,
    instruction=(
        "Eres el CISO (Director de Seguridad). Recibes 3 informes de auditoría generados en paralelo:\n"
        "1. OWASP: {informe_owasp}\n"
        "2. Infraestructura: {informe_infra}\n"
        "3. Licencias: {informe_licencias}\n\n"
        "Genera un resumen ejecutivo consolidado con tabla de riesgos y plan de acción recomendado."
    )
)

root_agent = SequentialAgent(
    name="parallel_agent",
    sub_agents=[panel_auditoria, agente_sintetizador],
    description="Auditoría de seguridad concurrente de triple factor (OWASP, Infra, Licencias) con síntesis ejecutiva."
)

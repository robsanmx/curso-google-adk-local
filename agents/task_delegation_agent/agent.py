"""Delegación de Tareas con Esquemas Pydantic en Task Mode (Módulo 4)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field, field_validator

agents_dir = Path(__file__).parent.parent
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

from config import get_local_model
from google.adk.agents.llm_agent import Agent

local_model = get_local_model()


class Vulnerabilidad(BaseModel):
    modulo: str = Field(description="Módulo o archivo afectado")
    severidad: str = Field(description="Nivel de severidad (ALTA, MEDIA, BAJA)")
    descripcion: str = Field(description="Explicación concisa del riesgo")


class ReporteAuditoria(BaseModel):
    resumen: str = Field(description="Resumen ejecutivo de la auditoría")
    vulnerabilidades: List[Vulnerabilidad] = Field(default_factory=list, description="Lista de hallazgos")
    aprobado_produccion: bool = Field(description="True si es seguro para producción, False si se bloquea")

    @field_validator("vulnerabilidades", mode="before")
    @classmethod
    def parse_vulnerabilidades(cls, v):
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else [parsed]
            except Exception:
                return []
        return v


subagente_auditor = Agent(
    name="auditor_task",
    model=local_model,
    mode="task",  # Inyecta automáticamente 'finish_task'
    output_schema=ReporteAuditoria,  # Validación de esquema tipado
    description="Audita componentes de software y retorna un ReporteAuditoria fuertemente tipado.",
    instruction=(
        "Eres un auditor técnico riguroso. Analiza la propuesta de release o código recibido. "
        "Evalúa si cumple con estándares de seguridad y finaliza tu tarea invocando la herramienta 'finish_task' "
        "con el esquema ReporteAuditoria estructurado."
    )
)

root_agent = Agent(
    name="task_delegation_agent",
    model=local_model,
    instruction=(
        "Eres el Release Manager responsable de autorizar o vetar pases a producción. "
        "1. Para cada propuesta o código enviado por el usuario, solicita una auditoría formal invocando a "
        "'request_task_auditor_task'. "
        "2. Examina el reporte estructurado devuelto. "
        "3. Si 'aprobado_produccion' es True, aprueba el despliegue con felicitaciones. "
        "4. Si 'aprobado_produccion' es False, bloquea el pase tajantemente, detallando cada vulnerabilidad y exigiendo correcciones."
    ),
    sub_agents=[subagente_auditor],
    description="Release Manager que delega auditorías a un subagente en Task Mode con validación Pydantic."
)

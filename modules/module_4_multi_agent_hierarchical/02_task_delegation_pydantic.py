"""
Módulo 4: Multi-Agent Avanzado - Lección 2: Task Delegation con Esquemas Pydantic
================================================================================
En ADK 2.0 se introdujo la delegación tipada de tareas (`mode="task"`):
- Al configurar `mode="task"` en un subagente, el coordinador recibe automáticamente
  una herramienta generada: `request_task_{nombre_subagente}`.
- El subagente recibe automáticamente la herramienta `finish_task` inyectada por el framework.
- Si se especifica `output_schema` (un modelo Pydantic), la salida del subagente es validada
  estrictamente antes de retornar el control al coordinador.

Esto elimina los errores de formato entre agentes y garantiza contratos de datos en sistemas complejos.
"""

import asyncio
from typing import List, Literal
from pydantic import BaseModel, Field
from google.adk.agents import Agent
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from config import get_local_model, print_environment_banner

# --- ESQUEMA DE CONTRATO DE DATOS (PYDANTIC) ---

class HallazgoSeguridad(BaseModel):
    componente: str = Field(description="Nombre del archivo o componente afectado.")
    gravedad: Literal["baja", "media", "alta", "critica"] = Field(description="Nivel de severidad técnica.")
    descripcion: str = Field(description="Explicación concisa de la vulnerabilidad.")


class InformeAuditoria(BaseModel):
    resumen_ejecutivo: str = Field(description="Resumen de alto nivel del análisis realizado.")
    hallazgos: List[HallazgoSeguridad] = Field(description="Lista estructurada de hallazgos detectados.")
    aprobado_para_produccion: bool = Field(description="True si es seguro desplegar, False si hay riesgos bloqueantes.")


async def main():
    print_environment_banner()
    local_model = get_local_model()

    # 1. Subagente con modo Task y Esquema Pydantic
    # ADK inyecta automáticamente la herramienta 'finish_task'
    auditor_seguridad = Agent(
        name="auditor_seguridad",
        model=local_model,
        mode="task",  # 'chat' | 'task' | 'single_turn'
        description="Audita especificaciones y emite un informe estructurado de seguridad.",
        instruction="""
        Eres un auditor de seguridad riguroso.
        Evalúa la entrada proporcionada y analiza posibles vulnerabilidades de inyección,
        autenticación o manejo de datos sensibles.
        Cuando hayas concluido, DEBES llamar a la herramienta 'finish_task' con el informe completo.
        """,
        output_schema=InformeAuditoria
    )

    # 2. Agente Coordinador
    # ADK inyecta automáticamente la herramienta 'request_task_auditor_seguridad'
    coordinador = Agent(
        name="coordinador_release",
        model=local_model,
        instruction="""
        Eres el Release Manager. Tu trabajo es coordinar la aprobación del lanzamiento a producción.
        1. Para evaluar la seguridad, delega la tarea al subagente auditor_seguridad.
        2. Analiza el informe estructurado que te devuelva.
        3. Si aprobado_para_produccion es False, indica los bloqueos críticos al usuario.
        4. Si es True, da luz verde para el despliegue.
        """,
        sub_agents=[auditor_seguridad]
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=coordinador, app_name="default_app", session_service=session_service)

    session_id = "sesion_task_delegation_02"
    user_id = "devops_lead"
    
    session = await session_service.create_session(app_name="default_app", session_id=session_id, user_id=user_id, state={})

    propuesta_despliegue = """
    Proponemos desplegar el servicio de pagos v2.
    Los logs guardan el número de tarjeta completo en texto plano para depuración rápida.
    La autenticación de la API interna no usa tokens JWT sino una IP en lista blanca.
    """

    print(f"[Propuesta de Despliegue recibida]:\n{propuesta_despliegue}\n")
    print("[*] Iniciando Coordinador con Task Delegation tipada...")

    async for event in runner.run_async(session_id=session.id, user_id=user_id, new_message=types.Content(role="user", parts=[types.Part.from_text(text=propuesta_despliegue)])):
        if event.author:
            print(f">> [Evento de: {event.author}]")
        if event.content:
            text = event.content.parts[0].text if hasattr(event.content, "parts") else str(event.content)
            print(f"[Contenido]:\n{text}\n")

if __name__ == "__main__":
    asyncio.run(main())

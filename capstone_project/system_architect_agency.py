"""
PROYECTO CAPSTONE: "LOCAL ARCHITECT & CODE REVIEW AGENCY" (ADK 2.0)
===================================================================
Este proyecto integra todos los conceptos del curso en una arquitectura multi-agente
robusta y ejecutable 100% de manera local:

1. Configuración dinámica con modelos locales (Ollama / LM Studio / MLX).
2. Herramientas personalizadas con ToolContext para lectura/escritura de estado y métricas.
3. Pipeline híbrido:
   - Etapa 1: Análisis y Desglose Funcional (Agent 1)
   - Etapa 2: Auditoría Paralela (Seguridad + Rendimiento de Base de Datos)
   - Etapa 3: Síntesis de Arquitectura y Generación de Plan de Acción (CTO Agent)
4. Trazabilidad completa con eventos de ADK y persistencia de estado de sesión.
"""

import asyncio
from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.tools import ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from config import get_local_model, print_environment_banner

# --- HERRAMIENTAS PERSONALIZADAS ---

def registrar_score_auditoria(
    modulo: str,
    puntuacion_0_a_100: int,
    tool_context: ToolContext
) -> dict:
    """Registra la puntuación numérica de calidad técnica de un módulo analizado.

    Args:
        modulo: Nombre del módulo analizado (ej. 'seguridad', 'base_de_datos').
        puntuacion_0_a_100: Calificación de 0 (muy malo) a 100 (excelente).

    Returns:
        dict confirmando el guardado en el estado de la sesión.
    """
    scores = tool_context.state.get("scores_calidad", {})
    scores[modulo] = puntuacion_0_a_100
    tool_context.state["scores_calidad"] = scores
    
    return {
        "status": "success",
        "mensaje": f"Puntuación de {puntuacion_0_a_100}/100 guardada para {modulo}."
    }


def construir_agencia_arquitectura(local_model):
    """Construye y ensambla el sistema multi-agente completo."""

    # 1. Agente Analista Funcional (Descompone el problema)
    analista_negocio = Agent(
        name="analista_funcional",
        model=local_model,
        instruction="""
        Eres un Lead Product Manager técnico.
        Recibes los requerimientos del usuario y debes:
        1. Resumir la visión del producto en 2 oraciones.
        2. Desglosar los 3 módulos técnicos principales necesarios.
        3. Identificar las entidades clave de datos.
        Sé sumamente estructurado.
        """,
        output_key="analisis_funcional"
    )

    # 2. Agente Especialista en Datos y Rendimiento (Paralelo)
    especialista_db = Agent(
        name="arquitecto_datos",
        model=local_model,
        instruction="""
        Eres un Administrador Principal de Bases de Datos (DBA).
        Basándote en el análisis funcional:
        {analisis_funcional}
        
        Diseña:
        - El modelo de datos óptimo (SQL vs NoSQL).
        - Estrategias de índices para consultas críticas.
        - Estrategia de caché (Redis / In-memory).
        
        Usa la herramienta 'registrar_score_auditoria' para puntuar la viabilidad de datos (0 a 100).
        """,
        tools=[registrar_score_auditoria],
        output_key="dictamen_datos"
    )

    # 3. Agente Auditor de Seguridad y Cloud (Paralelo)
    auditor_seguridad = Agent(
        name="auditor_seguridad_cloud",
        model=local_model,
        instruction="""
        Eres un Cloud Security Architect (CISO).
        Basándote en el análisis funcional:
        {analisis_funcional}
        
        Evalúa:
        - Autenticación y Autorización (OAuth2 / RBAC / Zero Trust).
        - Cifrado en reposo y en tránsito.
        - Vectores de ataque potenciales.
        
        Usa la herramienta 'registrar_score_auditoria' para puntuar el nivel de seguridad (0 a 100).
        """,
        tools=[registrar_score_auditoria],
        output_key="dictamen_seguridad"
    )

    # 4. Agente Síntesis Ejecutiva (CTO)
    cto_sintetizador = Agent(
        name="cto_sintetizador",
        model=local_model,
        instruction="""
        Eres el Chief Technology Officer (CTO).
        Has coordinado a tu equipo de ingeniería y tienes frente a ti:
        
        [ANÁLISIS FUNCIONAL]:
        {analisis_funcional}
        
        [DICTAMEN DE DATOS]:
        {dictamen_datos}
        
        [DICTAMEN DE SEGURIDAD]:
        {dictamen_seguridad}
        
        Elabora el Blueprint Arquitectónico Final:
        1. Diagrama conceptual de arquitectura (en formato texto/markdown).
        2. Stack tecnológico recomendado para producción.
        3. Roadmap de implementación en 3 fases ordenadas.
        """,
        output_key="blueprint_arquitectura_final"
    )

    # 5. Ensamblaje en Pipeline Multi-Agente: Secuencial -> Paralelo -> Secuencial
    sistema_agencia = SequentialAgent(
        name="agencia_arquitectura_software",
        sub_agents=[
            analista_negocio,
            ParallelAgent(
                name="auditoria_concurrente_especialistas",
                sub_agents=[especialista_db, auditor_seguridad]
            ),
            cto_sintetizador
        ],
        description="Agencia multi-agente de arquitectura de software local."
    )

    return sistema_agencia


async def main():
    print_environment_banner()
    local_model = get_local_model()

    agencia = construir_agencia_arquitectura(local_model)
    session_service = InMemorySessionService()
    runner = Runner(agent=agencia, app_name=\"agencia_app\", session_service=session_service)

    session_id = "capstone_agency_run_01"
    user_id = "founder_roberto"
    
    session = await session_service.create_session(
        session_id=session_id,
        user_id=user_id,
        state={
            "scores_calidad": {}
        }
    )

    caso_estudio = """
    Queremos construir una plataforma de telemedicina con videollamadas encriptadas de extremo a extremo,
    recetas médicas digitales firmadas criptográficamente y procesamiento de pagos con cumplimiento HIPAA / GDPR.
    Se esperan 10,000 médicos activos y 200,000 pacientes concurrentes.
    """

    print("=" * 70)
    print(" INICIANDO EJECUCIÓN DEL SISTEMA MULTI-AGENTE CAPSTONE")
    print("=" * 70)
    print(f"[Caso de Negocio]:\n{caso_estudio.strip()}\n")

    async for event in runner.run_async(session_id=session.id, user_id=user_id, prompt=caso_estudio):
        if event.author:
            print(f"\n>> -----------------------------------------------------------")
            print(f">> [FASE ACTIVA: {event.author.upper()}]")
            print(f">> -----------------------------------------------------------")
        if event.content:
            text = event.content.parts[0].text if hasattr(event.content, "parts") else str(event.content)
            # Mostrar los primeros 400 caracteres de cada etapa
            print(text[:450] + ("\n... [Contenido completo guardado en estado]" if len(text) > 450 else ""))

    # Resumen final de la sesión
    sesion_final = await session_service.get_session(session_id=session.id, user_id=user_id)
    print("\n" + "=" * 70)
    print(" RESUMEN DE EJECUCIÓN DE LA AGENCIA Y ESTADO CONSOLIDADO")
    print("=" * 70)
    print(f" • Scores de auditoría registrados por tools:")
    print(f"   {sesion_final.state.get('scores_calidad')}")
    print(f" • Claves de artefactos persistidos:")
    for key in ["analisis_funcional", "dictamen_datos", "dictamen_seguridad", "blueprint_arquitectura_final"]:
        presente = key in sesion_final.state
        print(f"   ✓ {key}: {'Generado con éxito' if presente else 'No generado'}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())

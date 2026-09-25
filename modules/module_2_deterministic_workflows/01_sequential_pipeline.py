"""
Módulo 2: Orquestación Determinista - Lección 1: SequentialAgent Pipeline
========================================================================
En arquitecturas de producción (y en especial con modelos locales), delegar la
orquestación enteramente a un LLM suele provocar alucinaciones, derivas de contexto
y sobrecosto computacional.

Google ADK ofrece "Workflow Agents" deterministas (`BaseAgent`).
`SequentialAgent` encadena múltiples agentes especializados en un orden estricto.
El estado (`state`) fluye de uno a otro mediante `output_key`.
"""

import asyncio
from google.adk.agents import Agent, SequentialAgent
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from config import get_local_model, print_environment_banner

async def main():
    print_environment_banner()
    local_model = get_local_model()

    # 1. Agente 1: Analizador de Requerimientos
    # Toma el requerimiento del usuario y genera un resumen estructurado
    analizador = Agent(
        name="analizador_requerimientos",
        model=local_model,
        instruction="""
        Eres un analista de sistemas.
        Lee el texto del usuario y extrae:
        1. Objetivo principal.
        2. Requisitos funcionales clave (máximo 3).
        3. Riesgos técnicos potenciales.
        Sé ultra conciso.
        """,
        output_key="analisis_tecnico"  # Guarda su resultado en session.state["analisis_tecnico"]
    )

    # 2. Agente 2: Arquitecto de Base de Datos
    # Lee el análisis producido por el Agente 1 usando {analisis_tecnico}
    arquitecto_db = Agent(
        name="arquitecto_datos",
        model=local_model,
        instruction="""
        Eres un especialista en modelado de bases de datos.
        Basándote en el siguiente análisis técnico:
        {analisis_tecnico}
        
        Diseña el esquema de tablas SQL relacionales necesario (incluye tipos de datos y claves primarias).
        """,
        output_key="esquema_sql"
    )

    # 3. Agente 3: Ingeniero de APIs
    # Sintetiza tanto el análisis como el esquema SQL para proponer endpoints REST
    disenador_api = Agent(
        name="disenador_api_rest",
        model=local_model,
        instruction="""
        Eres un arquitecto de APIs RESTful.
        Considerando el análisis:
        {analisis_tecnico}
        
        Y el esquema de datos diseñado:
        {esquema_sql}
        
        Diseña las rutas REST (método HTTP, URI y breve propósito) para cubrir los casos de uso.
        """,
        output_key="especificacion_api"
    )

    # 4. Componer la canalización determinista
    pipeline_secuencial = SequentialAgent(
        name="software_spec_pipeline",
        sub_agents=[analizador, arquitecto_db, disenador_api],
        description="Pipeline determinista de especificación de software técnico."
    )

    # 5. Ejecución con Runner
    session_service = InMemorySessionService()
    runner = Runner(agent=pipeline_secuencial, app_name="default_app", session_service=session_service)

    session_id = "sesion_seq_01"
    user_id = "product_owner"
    
    session = await session_service.create_session(app_name="default_app", 
        session_id=session_id,
        user_id=user_id,
        state={}
    )

    input_caso = "Necesitamos una plataforma para reservas de canchas de pádel con pagos y cancelaciones automáticas."
    print(f"[Solicitud de Entrada]:\n{input_caso}\n")
    print("[*] Iniciando ejecución secuencial de agentes en cadena...\n")

    async for event in runner.run_async(session_id=session.id, user_id=user_id, new_message=types.Content(role="user", parts=[types.Part.from_text(text=input_caso)])):
        if event.author:
            print(f"\n>> [Turno de Agente: {event.author}]")
        if event.content:
            text = event.content.parts[0].text if hasattr(event.content, "parts") else str(event.content)
            print(text[:400] + ("..." if len(text) > 400 else ""))

    # 6. Inspeccionar el estado final acumulado
    final_session = await session_service.get_session(app_name="default_app", session_id=session.id, user_id=user_id)
    print("\n" + "=" * 60)
    print("[*] Resumen de Claves generadas en session.state:")
    for k in ["analisis_tecnico", "esquema_sql", "especificacion_api"]:
        contenido = final_session.state.get(k, "NO_DISPONIBLE")
        print(f"  • {k} (longitud: {len(str(contenido))} caracteres)")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

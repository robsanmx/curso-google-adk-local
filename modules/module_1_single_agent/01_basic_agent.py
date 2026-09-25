"""
Módulo 1: Fundamentos de ADK 2.0 - Lección 1: Agente Básico Individual
========================================================================
Este script muestra cómo inicializar y ejecutar un LlmAgent básico en Google ADK 2.0
utilizando un modelo local (Ollama / LM Studio / MLX).

Conceptos clave:
1. Agent (LlmAgent): Unidad cognitiva mínima.
2. Inyección dinámica en instrucciones mediante placeholders {state_key}.
3. InMemorySessionService y Runner para orquestar la interacción.
"""

import asyncio
from google.adk.agents import Agent
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from config import get_local_model, print_environment_banner

async def main():
    print_environment_banner()
    
    # 1. Obtener el modelo local (Ollama / LM Studio / MLX vía LiteLLM)
    local_model = get_local_model()

    # 2. Definir el Agente con inyección dinámica de estado
    # Los placeholders como {user_name} o {system_role} se sustituyen automáticamente
    # a partir de session.state.
    asistente = Agent(
        name="local_assistant",
        model=local_model,
        description="Asistente general de ingeniería de software local.",
        instruction="""
        Eres un {system_role}.
        Estás asistiendo a {user_name}.
        
        Reglas de comportamiento:
        - Responde de forma técnica, concisa y profesional en español.
        - Si no tienes certeza sobre algo, dilo abiertamente en lugar de especular.
        - Destaca siempre consideraciones de rendimiento y buenas prácticas.
        """,
        output_key="last_response"  # Guarda automáticamente la respuesta en session.state
    )

    # 3. Configurar el servicio de sesiones en memoria y el Runner
    session_service = InMemorySessionService()
    runner = Runner(agent=asistente, app_name="default_app", session_service=session_service)

    # 4. Crear una sesión con estado inicial
    session_id = "sesion_demo_01"
    user_id = "dev_roberto"
    
    session = await session_service.create_session(
        session_id=session_id,
        user_id=user_id,
        state={
            "user_name": "Roberto",
            "system_role": "Experto en Arquitecturas de Software e IA Agéntica",
        }
    )

    print(f"[*] Sesión creada: ID={session.id}")
    print(f"[*] Estado inicial: {session.state}\n")

    # 5. Enviar un mensaje al agente
    prompt_usuario = "¿Cuáles son las ventajas de ejecutar agentes con ADK 2.0 de manera local?"
    print(f"[Usuario]: {prompt_usuario}\n")

    # Ejecutar el agente y escuchar los eventos generados
    print("[Agente pensando...]:")
    async for event in runner.run_async(session_id=session.id, user_id=user_id, new_message=types.Content(role="user", parts=[types.Part.from_text(text=prompt_usuario)])):
        # Cada evento representa un paso en el ciclo de vida del agente
        if event.content:
            # Imprimir el contenido devuelto por el modelo
            print(f"{event.content.parts[0].text if hasattr(event.content, 'parts') else event.content}")

    # 6. Inspeccionar el estado actualizado de la sesión
    updated_session = await session_service.get_session(session_id=session.id, user_id=user_id)
    print("\n" + "-" * 50)
    print("[*] Estado de la sesión tras la ejecución:")
    print(f"    output_key ('last_response'): {updated_session.state.get('last_response')[:120]}...")
    print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())

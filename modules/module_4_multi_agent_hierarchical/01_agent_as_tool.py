"""
Módulo 4: Multi-Agent Avanzado - Lección 1: Agente Invocado como Herramienta (AgentTool)
========================================================================================
Una de las preguntas arquitectónicas más habituales en sistemas multi-agente es:
¿Cuándo debo delegar el control conversacional completo a un subagente y cuándo
debo mantener el control en el agente padre?

En el patrón "Agent as a Tool" (`AgentTool`):
- El agente padre NO cede el control del diálogo al subagente.
- El subagente especialista se empaqueta como una herramienta (`AgentTool(specialist)`).
- El agente padre invoca al especialista de forma análoga a una función ordinaria,
  recibe su respuesta técnica y continúa razonando con el usuario.
"""

import asyncio
from google.adk.agents import Agent
from google.adk.tools import AgentTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from config import get_local_model, print_environment_banner

async def main():
    print_environment_banner()
    local_model = get_local_model()

    # 1. Agente Especialista: Analista de Vulnerabilidades Criptográficas
    # Este agente tiene un prompt muy especializado y enfocado
    criptografo_agent = Agent(
        name="especialista_criptografia",
        model=local_model,
        description="Analiza algoritmos criptográficos, suites de cifrado, hashing y gestión de claves.",
        instruction="""
        Eres un criptógrafo de seguridad.
        Tu misión es analizar cualquier propuesta o algoritmo criptográfico y señalar:
        - Si es obsoleto o inseguro (ej. MD5, SHA1, DES, ECB mode).
        - Si cumple estándares modernos (ej. AES-GCM, Argon2id, Ed25519).
        - Entrega una recomendación técnica puntual.
        """
    )

    # 2. Agente Coordinador / Arquitecto General
    # Utiliza al especialista a través de AgentTool
    coordinador = Agent(
        name="arquitecto_seguridad_principal",
        model=local_model,
        instruction="""
        Eres el Arquitecto Principal de Software.
        Conversas con el usuario sobre el diseño integral de su aplicación.
        Cuando el usuario pregunte sobre algoritmos de cifrado, almacenamiento de contraseñas
        o protocolos de seguridad criptográfica, DEBES invocar a tu especialista usando la herramienta disponible.
        Luego, integra la respuesta del especialista en una explicación clara para el cliente.
        """,
        # Envolvemos el agente especialista en AgentTool
        tools=[AgentTool(criptografo_agent)]
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=coordinador, session_service=session_service)

    session_id = "sesion_agent_tool_01"
    user_id = "dev_lead"
    
    session = await session_service.create_session(session_id=session_id, user_id=user_id, state={})

    consulta = "Para guardar contraseñas de usuarios en nuestra base de datos, planeamos usar MD5 con un salt estático. ¿Qué opinas?"
    print(f"[Usuario]: {consulta}\n")
    print("[*] Ejecutando Agente Coordinador con AgentTool...")

    async for event in runner.run_async(session_id=session.id, user_id=user_id, prompt=consulta):
        if event.author:
            print(f">> [Evento de: {event.author}]")
        if event.content:
            text = event.content.parts[0].text if hasattr(event.content, "parts") else str(event.content)
            print(f"[Respuesta]:\n{text}")

if __name__ == "__main__":
    asyncio.run(main())

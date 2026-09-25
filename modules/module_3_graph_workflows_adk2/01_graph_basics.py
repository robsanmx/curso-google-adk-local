"""
Módulo 3: ADK 2.0 Graph Workflow API - Lección 1: Fundamentos de Grafos
========================================================================
ADK 2.0 introduce una arquitectura basada en GRAFOS DIRIGIDOS para flujos de trabajo.
En lugar de depender exclusivamente de árboles anidados de agentes, un `Workflow`
define nodos (funciones de procesamiento, agentes LLM, herramientas) y aristas (`edges`).

Conceptos esenciales de ADK 2.0 Workflows:
1. `START`: Nodo inicial built-in que recibe la entrada del usuario.
2. Nodos: Callables o LlmAgents se auto-envuelven en FunctionNodes / AgentWrappers.
3. Inyección automática de parámetros:
   - `node_input`: Salida generada por el nodo predecesor.
   - `ctx`: Objeto Context de ADK para acceder al estado o servicios.
   - Cualquier otro parámetro: Se busca en `ctx.state[nombre_parametro]`.
"""

import asyncio
from google.adk.workflow import Workflow
from google.genai import types
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from config import get_local_model, print_environment_banner

# --- NODOS DEL GRAFO (Funciones Python normales auto-envueltas) ---

def preprocesar_consulta(node_input: str) -> str:
    """Nodo 1: Limpia y normaliza el texto recibido desde 'START'."""
    texto_limpio = node_input.strip()
    print(f"\n[Nodo Preprocesar]: Entrada recibida: '{texto_limpio}'")
    return texto_limpio.upper()


def enriquecer_contexto(node_input: str, user_role: str) -> dict:
    """Nodo 2: Toma la salida del nodo anterior y accede a state['user_role'] automáticamente."""
    print(f"[Nodo Enriquecer]: Contexto de rol inyectado: '{user_role}'")
    return {
        "consulta_original": node_input,
        "rol_autorizado": user_role,
        "timestamp_iso": "2026-09-24T12:00:00Z"
    }


async def main():
    print_environment_banner()
    local_model = get_local_model()

    # Nodo 3: Un LlmAgent que opera como nodo del grafo
    agente_solucionador = Agent(
        name="agente_solucionador",
        model=local_model,
        instruction="""
        Eres un asistente de soporte técnico nivel 3.
        Recibes un diccionario con información estructurada de la consulta y el rol.
        Proporciona una solución técnica estructurada con pasos a seguir.
        """
    )

    # Definición del Grafo mediante Aristas (edges)
    # Flujo: START -> preprocesar_consulta -> enriquecer_contexto -> agente_solucionador
    grafo_soporte = Workflow(
        name="workflow_soporte_tecnico",
        description="Flujo en grafo para procesamiento y respuesta de tickets.",
        edges=[
            ("START", preprocesar_consulta),
            (preprocesar_consulta, enriquecer_contexto),
            (enriquecer_contexto, agente_solucionador),
        ]
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=grafo_soporte, app_name="default_app", session_service=session_service)

    session_id = "sesion_graph_01"
    user_id = "usuario_soporte"
    
    session = await session_service.create_session(
        session_id=session_id,
        user_id=user_id,
        state={
            "user_role": "Administrador Senior de Kubernetes"
        }
    )

    ticket = "Los pods en el namespace production están en estado CrashLoopBackOff tras rotación de certificados."
    print(f"[Ticket recibido]:\n{ticket}\n")
    print("[*] Ejecutando grafo en ADK 2.0...")

    async for event in runner.run_async(session_id=session.id, user_id=user_id, new_message=types.Content(role="user", parts=[types.Part.from_text(text=ticket)])):
        if event.author:
            print(f">> [Evento de Nodo: {event.author}]")
        if event.content:
            text = event.content.parts[0].text if hasattr(event.content, "parts") else str(event.content)
            print(text)

if __name__ == "__main__":
    asyncio.run(main())

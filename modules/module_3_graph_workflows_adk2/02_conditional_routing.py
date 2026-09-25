"""
Módulo 3: ADK 2.0 Graph Workflow API - Lección 2: Enrutamiento Condicional
==========================================================================
En ADK 2.0, los grafos soportan bifurcaciones condicionales dinámicas basadas en
el resultado de un nodo clasificador.

Mecanismo:
1. Un nodo emite un `Event(output=..., route="nombre_ruta")`.
2. Las aristas del Workflow asocian el nodo de origen, el nodo destino y la ruta esperada:
   `edges = [(clasificador, destino_a, "ruta_a"), (clasificador, destino_b, "ruta_b"), (clasificador, fallback, "__DEFAULT__")]`
"""

import asyncio
from google.adk.workflow import Workflow
from google.genai import types
from google.adk.events.event import Event
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from config import get_local_model, print_environment_banner

# --- NODO CLASIFICADOR / ROUTER ---

def clasificar_intencion(node_input: str) -> Event:
    """Clasifica la intención del usuario y emite una ruta específica."""
    texto = node_input.lower()
    print(f"\n[Nodo Router]: Analizando intención de entrada...")
    
    if any(k in texto for k in ["bug", "error", "traceback", "exception", "código", "funcion"]):
        print(" -> Ruta seleccionada: 'codigo'")
        return Event(output=node_input, route="codigo")
    elif any(k in texto for k in ["cve", "vulnerabilidad", "inyeccion", "token", "password", "seguridad"]):
        print(" -> Ruta seleccionada: 'seguridad'")
        return Event(output=node_input, route="seguridad")
    else:
        print(" -> Ruta seleccionada: '__DEFAULT__' (arquitectura general)")
        return Event(output=node_input, route="__DEFAULT__")


async def main():
    print_environment_banner()
    local_model = get_local_model()

    # Agentes especializados para cada rama del grafo
    agente_codigo = Agent(
        name="especialista_codigo",
        model=local_model,
        instruction="Eres un debugger de software senior. Identifica la causa raíz y provee código de solución."
    )

    agente_seguridad = Agent(
        name="especialista_seguridad",
        model=local_model,
        instruction="Eres un analista de SOC y seguridad de aplicaciones. Evalúa el impacto y medidas de mitigación."
    )

    agente_general = Agent(
        name="especialista_arquitectura",
        model=local_model,
        instruction="Eres un arquitecto de soluciones de software. Explica principios y recomendaciones de diseño."
    )

    # Definir el Grafo con aristas condicionales y fallback __DEFAULT__
    grafo_enrutado = Workflow(
        name="workflow_enrutamiento_dinamico",
        edges=[
            ("START", clasificar_intencion),
            (clasificar_intencion, agente_codigo, "codigo"),
            (clasificar_intencion, agente_seguridad, "seguridad"),
            (clasificar_intencion, agente_general, "__DEFAULT__"),
        ]
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=grafo_enrutado, app_name="default_app", session_service=session_service)

    # Probar diferentes entradas
    casos = [
        ("caso_seguridad", "Detectamos una posible inyección SQL en el endpoint de autenticación con bypass de token."),
        ("caso_codigo", "Tengo un traceback IndexError: list index out of range al iterar un array vacío."),
    ]

    for sid, prompt in casos:
        print("\n" + "=" * 65)
        print(f"[*] EJECUTANDO PROMPT: '{prompt}'")
        session = await session_service.create_session(session_id=sid, user_id="dev", state={})
        
        async for event in runner.run_async(session_id=session.id, user_id="dev", new_message=types.Content(role="user", parts=[types.Part.from_text(text=prompt)])):
            if event.author:
                print(f">> [Activado nodo: {event.author}]")
            if event.content:
                text = event.content.parts[0].text if hasattr(event.content, "parts") else str(event.content)
                print(f"[Respuesta]:\n{text[:350]}...\n")

if __name__ == "__main__":
    asyncio.run(main())

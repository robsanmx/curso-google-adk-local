"""
Módulo 3: ADK 2.0 Graph Workflow API - Lección 3: Fan-Out y Fan-In con JoinNode
==============================================================================
En arquitecturas complejas de grafos, suele requerirse bifurcar la ejecución en ramas
concurrentes (Fan-Out) y posteriormente unir y sincronizar sus resultados (Fan-In).

ADK 2.0 proporciona `JoinNode`:
- Recibe las salidas de todas las ramas predecesoras.
- Emite un diccionario tipado indexado por el nombre de cada nodo predecesor:
  `{"rama_a": resultado_a, "rama_b": resultado_b}`.
- Sincroniza la ejecución antes de pasar al nodo sintetizador final.
"""

import asyncio
from google.adk.workflow import Workflow, JoinNode
from google.genai import types
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from config import get_local_model, print_environment_banner

# --- FUNCIONES DE RAMAS PARALELAS ---

def estimar_costos_nube(node_input: str) -> dict:
    """Calcula el costo estimado de computación e infraestructura."""
    print("[Rama 1]: Calculando estimaciones de costo de cómputo...")
    return {
        "costo_mensual_usd": 420.50,
        "instancias_sugeridas": "2x 4vCPU 16GB RAM + Cloud SQL db-f1-micro",
        "estrategia_ahorro": "Instancias Spot / Commitments 1 año"
    }


def auditar_latencia_red(node_input: str) -> dict:
    """Calcula los tiempos de respuesta y SLAs esperados."""
    print("[Rama 2]: Simulando latencias de red y CDN...")
    return {
        "p95_latencia_ms": 45,
        "p99_latencia_ms": 110,
        "regiones_recomendadas": ["us-central1", "southamerica-west1"],
        "requiere_cdn": True
    }


async def main():
    print_environment_banner()
    local_model = get_local_model()

    # Nodo de Unión de ADK 2.0
    sincronizador = JoinNode(name="sincronizador_metricas")

    # Nodo Final: Agente que sintetiza los datos agregados por el JoinNode
    arquitecto_decisor = Agent(
        name="arquitecto_infraestructura",
        model=local_model,
        instruction="""
        Eres el Chief Technology Officer (CTO).
        Recibes un diccionario con datos de costo y latencia agregados por el JoinNode:
        {node_input}
        
        Elabora un dictamen de viabilidad técnica y financiera para el despliegue del proyecto.
        """
    )

    # Definir el Grafo con Fan-out y Fan-in:
    # 1. Fan-out: START se bifurca a estimar_costos_nube y auditar_latencia_red
    # 2. Fan-in: Ambas ramas convergen en sincronizador (JoinNode)
    # 3. Flujo final: sincronizador alimenta a arquitecto_decisor
    grafo_fanout_join = Workflow(
        name="workflow_infra_evaluation",
        edges=[
            ("START", (estimar_costos_nube, auditar_latencia_red)),
            ((estimar_costos_nube, auditar_latencia_red), sincronizador),
            (sincronizador, arquitecto_decisor),
        ]
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=grafo_fanout_join, app_name="default_app", session_service=session_service)

    session_id = "sesion_join_03"
    user_id = "infra_manager"
    
    session = await session_service.create_session(session_id=session_id, user_id=user_id, state={})

    solicitud = "Despliegue de un microservicio de scoring crediticio con picos de 5,000 req/sec en Latinoamérica."
    print(f"[Proyecto a evaluar]:\n{solicitud}\n")
    print("[*] Ejecutando Grafo con Fan-Out y Fan-In...")

    async for event in runner.run_async(session_id=session.id, user_id=user_id, new_message=types.Content(role="user", parts=[types.Part.from_text(text=solicitud)])):
        if event.author:
            print(f">> [Evento de: {event.author}]")
        if event.content:
            text = event.content.parts[0].text if hasattr(event.content, "parts") else str(event.content)
            print(f"[Dictamen Final]:\n{text}")

if __name__ == "__main__":
    asyncio.run(main())

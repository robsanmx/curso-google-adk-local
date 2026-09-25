"""
Módulo 2: Orquestación Determinista - Lección 2: Concurrencia con ParallelAgent
=============================================================================
Cuando diferentes tareas no dependen entre sí, ejecutarlas secuencialmente desperdicia
tiempo. Con `ParallelAgent`, múltiples agentes operan simultáneamente sobre la misma entrada.

Regla de oro de ADK para ParallelAgent:
Cada agente paralelo DEBE tener un `output_key` único en su definición.
De lo contrario, sobreescribirán concurrentemente la misma entrada en `session.state`,
causando condiciones de carrera (race conditions).
"""

import asyncio
from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from config import get_local_model, print_environment_banner

async def main():
    print_environment_banner()
    local_model = get_local_model()

    # 1. Agente Paralelo A: Auditor de Seguridad
    auditor_seguridad = Agent(
        name="auditor_seguridad",
        model=local_model,
        instruction="""
        Eres un auditor de ciberseguridad enfocado en OWASP Top 10.
        Analiza el código o requerimiento provisto y lista vulnerabilidades potenciales.
        Sé directo y enumera puntos concretos.
        """,
        output_key="reporte_seguridad"  # Clave única
    )

    # 2. Agente Paralelo B: Optimizador de Rendimiento
    optimizador_rendimiento = Agent(
        name="optimizador_rendimiento",
        model=local_model,
        instruction="""
        Eres un ingeniero de rendimiento y alta concurrencia.
        Analiza el código o requerimiento provisto y lista cuellos de botella (CPU, I/O, memoria).
        Propón optimizaciones claras.
        """,
        output_key="reporte_rendimiento"  # Clave única
    )

    # 3. Agente Paralelo C: Experto en Experiencia de Desarrollador (DX) y Mantenibilidad
    experto_dx = Agent(
        name="experto_mantenibilidad",
        model=local_model,
        instruction="""
        Eres un defensor de Clean Code, SOLID y diseño modular.
        Evalúa la legibilidad, modularidad y facilidad de prueba del código o requerimiento.
        """,
        output_key="reporte_mantenibilidad"  # Clave única
    )

    # 4. Agente Síntesis / Árbitro
    sintetizador = Agent(
        name="lider_tecnico_sintesis",
        model=local_model,
        instruction="""
        Eres el Líder Técnico Principal. Has recibido tres reportes independientes:
        
        [REPORTE SEGURIDAD]:
        {reporte_seguridad}
        
        [REPORTE RENDIMIENTO]:
        {reporte_rendimiento}
        
        [REPORTE MANTENIBILIDAD]:
        {reporte_mantenibilidad}
        
        Consolida una decisión ejecutiva final con un plan de acción priorizado (P0, P1, P2).
        """,
        output_key="dictamen_final"
    )

    # 5. Composición híbrida: Fan-out en paralelo seguido de convergencia secuencial
    equipo_auditoria_completo = SequentialAgent(
        name="auditoria_concurrente_pipeline",
        sub_agents=[
            ParallelAgent(
                name="auditorias_en_paralelo",
                sub_agents=[auditor_seguridad, optimizador_rendimiento, experto_dx]
            ),
            sintetizador
        ]
    )

    # 6. Ejecución
    session_service = InMemorySessionService()
    runner = Runner(agent=equipo_auditoria_completo, app_name="default_app", session_service=session_service)

    session_id = "sesion_parallel_02"
    user_id = "tech_lead"
    
    session = await session_service.create_session(session_id=session_id, user_id=user_id, state={})

    codigo_muestra = """
    @app.route('/login', methods=['POST'])
    def login():
        user = request.form['username']
        pwd = request.form['password']
        # Consulta directa
        query = f"SELECT * FROM users WHERE username = '{user}' AND password = '{pwd}'"
        result = db.execute(query).fetchall()
        if len(result) > 0:
            return jsonify({"status": "ok", "token": generate_token(user)})
        return jsonify({"status": "failed"}), 401
    """

    print(f"[Código a evaluar en paralelo]:\n{codigo_muestra}\n")
    print("[*] Disparando análisis paralelo con 3 agentes concurrentes...\n")

    async for event in runner.run_async(session_id=session.id, user_id=user_id, new_message=types.Content(role="user", parts=[types.Part.from_text(text=codigo_muestra)])):
        if event.author:
            print(f">> [Evento de: {event.author}]")
        if event.content:
            text = event.content.parts[0].text if hasattr(event.content, "parts") else str(event.content)
            print(text[:300] + ("..." if len(text) > 300 else ""))

    # Verificar el estado acumulado
    final_session = await session_service.get_session(session_id=session.id, user_id=user_id)
    print("\n" + "=" * 60)
    print("[*] Claves generadas concurrentemente en session.state:")
    for k in ["reporte_seguridad", "reporte_rendimiento", "reporte_mantenibilidad", "dictamen_final"]:
        print(f"  • {k} -> Presente en estado (longitud {len(str(final_session.state.get(k)))})")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

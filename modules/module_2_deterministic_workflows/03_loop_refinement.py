"""
Módulo 2: Orquestación Determinista - Lección 3: Bucles de Refinamiento con LoopAgent
====================================================================================
Muchos problemas agénticos requieren un ciclo de "Generar -> Evaluar -> Refinar".
`LoopAgent` ejecuta secuencialmente sus subagentes y repite el ciclo hasta que:
1. Se alcanza `max_iterations` (parada de seguridad para evitar loops infinitos).
2. Un subagente o herramienta emite un evento con `escalate=True` (parada temprana).

En este ejemplo implementamos:
- Agente Generador: Genera una función de código Python.
- Agente Evaluador: Revisa si cumple pruebas y criterios de calidad.
- EscalationChecker: Un BaseAgent personalizado que revisa el resultado y activa `escalate=True`.
"""

import asyncio
from typing import AsyncGenerator
from google.adk.agents import Agent, BaseAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from config import get_local_model, print_environment_banner

# --- SUBAGENTE PERSONALIZADO DE PARADA: ESCALATION CHECKER ---
class EscalationChecker(BaseAgent):
    """
    Agente evaluador determinista. Inspecciona el estado de la sesión.
    Si la evaluación indica 'APROBADO', emite un EventActions(escalate=True)
    que indica al LoopAgent terminar de inmediato.
    """
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        evaluacion = ctx.session.state.get("evaluacion_calidad", "")
        iteracion_actual = ctx.session.state.get("iteracion_bucle", 0) + 1
        ctx.session.state["iteracion_bucle"] = iteracion_actual
        
        print(f"\n[EscalationChecker - Iteración {iteracion_actual}]: Inspeccionando evaluación...")
        
        if "APROBADO" in evaluacion.upper():
            print(" -> ¡Criterio cumplido! Emitiendo escalate=True para terminar el LoopAgent.")
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            print(" -> Criterio NO cumplido. Continuando la siguiente iteración del bucle.")
            yield Event(author=self.name)


async def main():
    print_environment_banner()
    local_model = get_local_model()

    # 1. Agente Redactor / Optimizador de Código
    generador = Agent(
        name="generador_codigo",
        model=local_model,
        instruction="""
        Eres un programador Python. Tu objetivo es implementar o mejorar la solución.
        
        Código actual previo:
        {codigo_actual}
        
        Feedback o críticas previas:
        {evaluacion_calidad}
        
        Escribe el código Python limpio, optimizado y documentado.
        """,
        output_key="codigo_actual"
    )

    # 2. Agente Revisor / Crítico
    evaluador = Agent(
        name="evaluador_codigo",
        model=local_model,
        instruction="""
        Eres un revisor de código estricto.
        Analiza el código generado:
        {codigo_actual}
        
        Verifica:
        1. ¿Tiene manejo de errores robusto?
        2. ¿Tiene anotaciones de tipos completas (type hints)?
        3. ¿Tiene complejidad temporal óptima?
        
        Si cumple TODO rigurosamente, responde con la palabra 'APROBADO' en la primera línea
        y explica por qué. Si falta algo, responde 'RECHAZADO' y explica qué debe corregirse.
        """,
        output_key="evaluacion_calidad"
    )

    # 3. Componer el LoopAgent con EscalationChecker
    bucle_refinamiento = LoopAgent(
        name="bucle_calidad_codigo",
        sub_agents=[
            generador,
            evaluador,
            EscalationChecker(name="verificador_parada")
        ],
        max_iterations=3  # Máximo 3 intentos para ahorrar cómputo local
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=bucle_refinamiento, app_name=\"bucle_refinamiento_app\", session_service=session_service)

    session_id = "sesion_loop_03"
    user_id = "ingeniero"
    
    session = await session_service.create_session(
        session_id=session_id,
        user_id=user_id,
        state={
            "codigo_actual": "def fib(n): return n if n<=1 else fib(n-1)+fib(n-2)",  # Código ineficiente O(2^n)
            "evaluacion_calidad": "Código inicial muy lento, sin tipos y sin manejo de casos negativos.",
            "iteracion_bucle": 0
        }
    )

    print("[*] Iniciando LoopAgent de refinamiento iterativo...")
    async for event in runner.run_async(session_id=session.id, user_id=user_id, prompt="Optimiza la función fibonacci"):
        if event.author and event.author != "verificador_parada":
            print(f"\n>> [{event.author}]:")
            if event.content:
                text = event.content.parts[0].text if hasattr(event.content, "parts") else str(event.content)
                print(text[:250] + ("..." if len(text) > 250 else ""))

    final_session = await session_service.get_session(session_id=session.id, user_id=user_id)
    print("\n" + "=" * 60)
    print(f"[*] Loop finalizado tras {final_session.state.get('iteracion_bucle')} iteraciones.")
    print("[*] Código final obtenido:")
    print(final_session.state.get("codigo_actual"))
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

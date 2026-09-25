"""
Módulo 1: Fundamentos de ADK 2.0 - Lección 3: Human-in-the-Loop y Confirmación de Herramientas
=============================================================================================
En entornos empresariales y de desarrollo seguro, los agentes nunca deben ejecutar
acciones destructivas (borrar bases de datos, desplegar en producción, transferir fondos)
sin supervisión humana.

Google ADK proporciona soporte de primer nivel con:
1. `FunctionTool(func, require_confirmation=True)` (confirmación incondicional).
2. `FunctionTool(func, require_confirmation=callback)` (confirmación basada en reglas).
"""

import asyncio
from google.adk.agents import Agent
from google.genai import types
from google.adk.tools import FunctionTool, ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from config import get_local_model, print_environment_banner

# Acción potencialmente destructiva
def reiniciar_servicio_produccion(servicio: str, forzar: bool) -> dict:
    """Reinicia un servicio crítico de infraestructura.

    Args:
        servicio: Nombre del servicio a reiniciar (ej. 'nginx', 'postgresql', 'redis').
        forzar: Si es True, fuerza la terminación inmediata de procesos activos.

    Returns:
        dict con el resultado de la operación.
    """
    print(f"\n[SISTEMA - ALERTA]: Ejecutando reinicio de {servicio} (forzado={forzar})...")
    return {
        "status": "success",
        "mensaje": f"El servicio '{servicio}' ha sido reiniciado satisfactoriamente.",
        "servicio": servicio,
        "forzado": forzar
    }

# Lógica de confirmación condicional
def validar_necesidad_confirmacion(servicio: str, forzar: bool = False, **kwargs) -> bool:
    """
    Determina si la acción requiere confirmación humana.
    Si el servicio es una base de datos o forzar es True, requiere confirmación.
    """
    servicios_criticos = ["postgresql", "mysql", "mongodb", "redis"]
    if servicio.lower() in servicios_criticos or forzar:
        return True
    return False

# Envolver la función con FunctionTool y su regla de confirmación
herramienta_segura = FunctionTool(
    func=reiniciar_servicio_produccion,
    require_confirmation=validar_necesidad_confirmacion
)

async def main():
    print_environment_banner()
    local_model = get_local_model()

    ops_agent = Agent(
        name="ops_security_agent",
        model=local_model,
        instruction="""
        Eres un agente de mantenimiento de servidores.
        Puedes reiniciar servicios cuando el usuario lo solicite.
        Sé transparente sobre las consecuencias de reiniciar servicios críticos.
        """,
        tools=[herramienta_segura]
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=ops_agent, app_name="default_app", session_service=session_service)

    session_id = "sesion_hitl_03"
    user_id = "security_officer"
    
    session = await session_service.create_session(
        session_id=session_id,
        user_id=user_id,
        state={"perfil": "operador"}
    )

    solicitud = "Por favor reinicia el servicio postgresql de inmediato de forma forzada."
    print(f"[Usuario]: {solicitud}\n")

    print("[*] Iniciando ejecución. Observa cómo el motor de ADK detecta la necesidad de confirmación:")
    async for event in runner.run_async(session_id=session.id, user_id=user_id, new_message=types.Content(role="user", parts=[types.Part.from_text(text=solicitud)])):
        # Si el evento requiere confirmación de tool, el runner emitirá una señal
        if hasattr(event, "actions") and event.actions:
            print(f" -> Evento de acción detectado: {event.actions}")
        if event.content:
            text = event.content.parts[0].text if hasattr(event.content, "parts") else str(event.content)
            print(f"[Agente]:\n{text}")

if __name__ == "__main__":
    asyncio.run(main())

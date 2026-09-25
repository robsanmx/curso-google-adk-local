"""
Módulo 1: Fundamentos de ADK 2.0 - Lección 2: Herramientas y ToolContext
========================================================================
Este script muestra cómo dotar de herramientas (Function Calling) a un agente,
y cómo utilizar ToolContext para interactuar directamente con el estado de la sesión.

Reglas estrictas de Tools en Google ADK:
1. Docstrings claros (el LLM los usa para decidir cuándo y cómo llamar a la herramienta).
2. Type hints obligatorios en todos los parámetros (NO valores por defecto ambiguos).
3. Debe retornar un diccionario serializable en JSON (ej. {"status": "success", ...}).
4. Si se inyecta `tool_context: ToolContext`, NO debe mencionarse en el docstring.
"""

import asyncio
import platform
import psutil
from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from config import get_local_model, print_environment_banner

# --- DEFINICIÓN DE HERRAMIENTAS PERSONALIZADAS ---

def obtener_metricas_sistema() -> dict:
    """Obtiene el estado de hardware del servidor o máquina local donde corren los modelos.

    Returns:
        dict con el porcentaje de uso de CPU, memoria disponible y plataforma.
    """
    cpu_percent = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    
    return {
        "status": "success",
        "cpu_usage_percent": cpu_percent,
        "memory_total_gb": round(mem.total / (1024**3), 2),
        "memory_used_gb": round(mem.used / (1024**3), 2),
        "memory_free_gb": round(mem.available / (1024**3), 2),
        "system_os": platform.system(),
        "platform_release": platform.release(),
    }


def registrar_alerta_incidente(
    severidad: str,
    descripcion: str,
    tool_context: ToolContext
) -> dict:
    """Registra una alerta técnica en el estado de la sesión para auditoría.

    Args:
        severidad: Nivel de la alerta ('baja', 'media', 'alta', 'critica').
        descripcion: Detalle técnico del incidente o alerta detectada.

    Returns:
        dict con confirmación y el ID de auditoría generado.
    """
    # ToolContext nos da acceso directo al estado de la sesión activa
    alertas_previas = tool_context.state.get("alertas_registradas", [])
    
    nueva_alerta = {
        "severidad": severidad.lower(),
        "descripcion": descripcion,
        "usuario_activo": tool_context.state.get("user_name", "anonimo")
    }
    
    alertas_previas.append(nueva_alerta)
    tool_context.state["alertas_registradas"] = alertas_previas
    
    return {
        "status": "success",
        "mensaje": f"Alerta registrada correctamente con severidad '{severidad}'",
        "total_alertas_en_sesion": len(alertas_previas)
    }


async def main():
    print_environment_banner()
    local_model = get_local_model()

    # Definir el agente con herramientas
    diagnostico_agent = Agent(
        name="diagnostico_hardware_agent",
        model=local_model,
        instruction="""
        Eres un agente de monitoreo de infraestructura local.
        Tienes acceso a herramientas para consultar el estado del hardware y registrar alertas.
        
        Reglas de operación:
        - Si el usuario pregunta por el estado de la máquina o recursos, llama a 'obtener_metricas_sistema'.
        - Si la memoria usada supera el 85% o la CPU el 90%, usa 'registrar_alerta_incidente' con severidad alta o crítica.
        - Sé preciso y presenta los datos de forma legible en Markdown.
        """,
        tools=[obtener_metricas_sistema, registrar_alerta_incidente],
        output_key="diagnostico_final"
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=diagnostico_agent, app_name=\"diagnostico_agent_app\", session_service=session_service)

    session_id = "sesion_herramientas_02"
    user_id = "ops_admin"
    
    session = await session_service.create_session(
        session_id=session_id,
        user_id=user_id,
        state={
            "user_name": "Administrador DevOps",
            "alertas_registradas": []
        }
    )

    consulta = "Revisa el estado de la máquina local y dime cómo están los recursos del sistema."
    print(f"[Usuario]: {consulta}\n")

    async for event in runner.run_async(session_id=session.id, user_id=user_id, prompt=consulta):
        # Inspeccionar si el evento contiene una llamada a tool o respuesta
        if hasattr(event, "actions") and event.actions:
            print(f" -> [Acción de Agente/Tool]: {event.actions}")
        if event.content:
            text = event.content.parts[0].text if hasattr(event.content, "parts") else str(event.content)
            print(f"[Respuesta]:\n{text}")

    # Verificar qué guardó ToolContext en la sesión
    updated_session = await session_service.get_session(session_id=session.id, user_id=user_id)
    print("\n" + "=" * 50)
    print(f"[*] Alertas guardadas en session.state por ToolContext:")
    print(f"    {updated_session.state.get('alertas_registradas')}")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())

"""
Script para generar el Jupyter Notebook completo del Curso Google ADK 2.0.
Crea el archivo curso_adk2_completo.ipynb con todas las explicaciones y ejemplos ejecutables.
"""

import json

def make_cell(cell_type, source, execution_count=None):
    if isinstance(source, str):
        lines = [line + "\n" for line in source.split("\n")]
        # Eliminar el último salto de línea innecesario
        if lines and lines[-1] == "\n":
            lines[-1] = ""
    else:
        lines = source

    cell = {
        "cell_type": cell_type,
        "metadata": {},
    }
    if cell_type == "code":
        cell["execution_count"] = execution_count
        cell["outputs"] = []
        cell["source"] = lines
    elif cell_type == "markdown":
        cell["source"] = lines
    return cell

def build_notebook():
    cells = []

    # -------------------------------------------------------------
    # PORTADA Y PRESENTACIÓN
    # -------------------------------------------------------------
    cells.append(make_cell("markdown", """# 🚀 Curso Google ADK 2.0: De Single-Agent a Arquitecturas Multi-Agente
### Guía Interactiva Paso a Paso con Ejecución 100% Local (Ollama, LM Studio o MLX)
**Basado en las mejores prácticas de Google Agents-CLI y el Agent Development Lifecycle (ADLC)**

---

### 🎯 Contenido del Notebook:
1. **Configuración del Runtime Local:** Conexión con Ollama, LM Studio y MLX mediante `LiteLlm`.
2. **Módulo 1 - Single Agent:** Anatomía de `Agent`, inyección dinámica de estado `{state_key}` y persistencia con `output_key`.
3. **Módulo 1 - Herramientas y ToolContext:** Function Calling riguroso y manipulación directa de `session.state`.
4. **Módulo 1 - Human-in-the-Loop:** Puertas de confirmación de seguridad con `FunctionTool(require_confirmation=...)`.
5. **Módulo 2 - Orquestación Determinista:**
   - 5.1 `SequentialAgent` (Pipelines lineales y paso de datos).
   - 5.2 `ParallelAgent` (Concurrencia local y aislamiento de `output_key`).
   - 5.3 `LoopAgent` (Bucles de refinamiento y parada temprana con `EscalationChecker`).
6. **Módulo 3 - ADK 2.0 Graph Workflow API:**
   - 6.1 Fundamentos de Grafos: `Workflow`, nodo `START` y auto-wrapping de nodos.
   - 6.2 Enrutamiento Condicional Dinámico (`Event(route=...)` y fallback `__DEFAULT__`).
   - 6.3 Concurrencia con Fan-Out y Fan-In (`JoinNode`).
7. **Módulo 4 - Multi-Agente Jerárquico Avanzado:**
   - 7.1 Patrón `AgentTool` (Invocación sin cesión de la conversación).
   - 7.2 Delegación Tipada con Pydantic (`mode="task"`, `request_task` y `finish_task`).
8. **Proyecto Capstone:** Agencia Local de Arquitectura de Software y Auditoría de Seguridad.
"""))

    # -------------------------------------------------------------
    # INSTALACIÓN Y REQUISITOS
    # -------------------------------------------------------------
    cells.append(make_cell("markdown", """## 0. Instalación de Dependencias y Preparación
Ejecuta la siguiente celda para asegurarte de tener las librerías necesarias instaladas.
Habilitamos `nest_asyncio` para poder ejecutar llamadas asíncronas (`asyncio.run` / `run_async`) fluidamente dentro de celdas de Jupyter."""))

    cells.append(make_cell("code", """# Instalación de dependencias (descomenta si no las has instalado previamente)
# !pip install -q google-adk>=2.0.0 litellm>=1.40.0 pydantic>=2.7.0 python-dotenv nest-asyncio psutil

import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import nest_asyncio
nest_asyncio.apply()

def extraer_texto(event) -> str:
    # Extrae de forma limpia el texto o resumen de herramientas de un evento
    if not event or not getattr(event, 'content', None):
        return ''
    if getattr(event.content, 'parts', None):
        parts_text = [p.text.strip() for p in event.content.parts if getattr(p, 'text', None) and p.text.strip()]
        if parts_text:
            return "\\n".join(parts_text)
        tool_calls = [
            f"⚙️ [Tool Invocada: {p.function_call.name}({dict(p.function_call.args or {})})]"
            for p in event.content.parts
            if getattr(p, 'function_call', None) and p.function_call.name != 'adk_request_confirmation'
        ]
        if tool_calls:
            return "\\n".join(tool_calls)
        tool_responses = []
        for p in event.content.parts:
            if getattr(p, 'function_response', None):
                if p.function_response.name == 'adk_request_confirmation':
                    continue
                res = p.function_response.response
                if isinstance(res, dict) and 'error' in res and 'requires confirmation' in str(res.get('error', '')):
                    continue
                res_str = str(res)
                if len(res_str) > 250:
                    res_str = res_str[:250] + "..."
                tool_responses.append(f"📦 [Retorno de Tool '{p.function_response.name}']: {res_str}")
        if tool_responses:
            return "\\n".join(tool_responses)
    return ''

print("✓ nest_asyncio, filtros de warnings y utilidades configurados correctamente.")
"""))

    # -------------------------------------------------------------
    # SECCIÓN 1: CONFIGURACIÓN LOCAL
    # -------------------------------------------------------------
    cells.append(make_cell("markdown", """## 1. Conexión con Modelos Locales (Ollama, LM Studio y MLX)
Google ADK utiliza el adaptador `google.adk.models.lite_llm.LiteLlm` para conectarse a cualquier servidor local compatible:
* **Ollama:** Por defecto en `http://localhost:11434` (Prefijo: `ollama_chat/<modelo>`).
* **LM Studio:** Servidor local OpenAI-compatible en `http://localhost:1234/v1`.
* **MLX (Apple Silicon):** `mlx-lm.server` o LocalAI en `http://localhost:8080/v1`.

> 💡 **Modelos recomendados para agentes locales:** `qwen2.5:7b-instruct` (o 14B) y `llama3.1:8b-instruct`. Cuentan con un excelente seguimiento de instrucciones y formateo estricto para Function Calling."""))

    cells.append(make_cell("code", """import os
from google.adk.models.lite_llm import LiteLlm

def get_local_model(provider="ollama", model_name=None, temperature=0.2):
    \"\"\"Instancia el modelo local configurado para Google ADK 2.0.
    Detecta automáticamente modelos disponibles en Ollama local si no se especifica model_name.
    \"\"\"
    provider = provider.lower()
    
    if provider == "ollama":
        api_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        if not model_name:
            try:
                import urllib.request, json
                with urllib.request.urlopen(f"{api_base}/api/tags", timeout=1.5) as r:
                    models = [m["name"] for m in json.loads(r.read().decode()).get("models", [])]
                    for preferred in ["llama3.2:latest", "llama3.2", "qwen3:4b", "llama3.1:8b", "qwen2.5-coder:14b", "qwen2.5:7b-instruct", "mistral-nemo:latest"]:
                        if preferred in models:
                            model_name = preferred
                            break
                    if not model_name and models:
                        model_name = models[0]
            except Exception:
                pass
        target = model_name or "llama3.2:latest"
        model_str = f"ollama_chat/{target}" if not target.startswith("ollama_chat/") else target
        return LiteLlm(
            model=model_str,
            api_base=api_base,
            temperature=temperature
        )
    elif provider == "lmstudio":
        target = model_name or "qwen2.5-7b-instruct"
        model_str = f"openai/{target}" if not target.startswith("openai/") else target
        return LiteLlm(
            model=model_str,
            api_base=os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
            api_key="not-needed",
            temperature=temperature
        )
    elif provider == "mlx":
        target = model_name or "mlx-community/Qwen2.5-7B-Instruct-4bit"
        model_str = f"openai/{target}" if not target.startswith("openai/") else target
        return LiteLlm(
            model=model_str,
            api_base=os.getenv("MLX_BASE_URL", "http://localhost:8080/v1"),
            api_key="not-needed",
            temperature=temperature
        )
    else:
        raise ValueError(f"Proveedor '{provider}' no soportado.")

# Inicializamos el modelo para todo el notebook (auto-detecta Ollama o cámbialo a 'lmstudio' / 'mlx')
local_model = get_local_model(provider="ollama")
endpoint = getattr(local_model, "_additional_args", {}).get("api_base", "default")
print(f"✓ Modelo local configurado: {local_model.model} (endpoint: {endpoint})")
"""
))

    # -------------------------------------------------------------
    # SECCIÓN 2: SINGLE AGENT
    # -------------------------------------------------------------
    cells.append(make_cell("markdown", """## 2. Módulo 1: Single-Agent con Inyección Dinámica de Estado
En Google ADK, un agente se define mediante `Agent` (alias de `LlmAgent`):
1. **`instruction`:** Soporta placeholders como `{rol}` o `{usuario}` que ADK sustituye automáticamente desde `session.state`.
2. **`output_key`:** Guarda la respuesta final del agente directamente en `session.state[output_key]`.
3. **`InMemorySessionService` y `Runner`:** Gestionan el almacenamiento de memoria y el despacho de eventos asíncronos."""))

    cells.append(make_cell("code", """import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# 1. Definición del Agente con plantilla dinámica
asistente_dev = Agent(
    name="senior_dev_assistant",
    model=local_model,
    instruction=\"\"\"
    Eres un {rol_tecnico}.
    Estás asesorando a {nombre_usuario}.
    
    Reglas de respuesta:
    - Responde de forma técnica y concisa.
    - Cita siempre consideraciones de seguridad y arquitectura.
    \"\"\",
    output_key="respuesta_asistente"  # Persistencia automática en el estado
)

# 2. Configurar la sesión y el Runner
session_service = InMemorySessionService()
runner = Runner(agent=asistente_dev, app_name="asistente_dev_app", session_service=session_service)

# 3. Crear sesión con variables de estado iniciales
session = await session_service.create_session(
    app_name="asistente_dev_app",
    session_id="sesion_01_single",
    user_id="roberto",
    state={
        "rol_tecnico": "Arquitecto Senior de Software",
        "nombre_usuario": "Roberto"
    }
)

# 4. Ejecutar consulta
prompt = "¿Cuáles son las ventajas de ejecutar agentes con ADK 2.0 en local?"
print(f"👤 [Usuario]: {prompt}\\n")
print("🤖 [Agente]:")

async for event in runner.run_async(session_id=session.id, user_id="roberto", prompt=prompt):
    text = extraer_texto(event)
    if text:
        print(text)

# 5. Comprobar que output_key guardó el valor en session.state
sesion_actualizada = await session_service.get_session(app_name="asistente_dev_app", session_id=session.id, user_id="roberto")
print("\\n" + "=" * 50)
print("✓ Clave guardada en session.state['respuesta_asistente']:")
print(str(sesion_actualizada.state.get("respuesta_asistente") or "")[:150] + "...")
"""))

    # -------------------------------------------------------------
    # SECCIÓN 3: TOOLS Y TOOLCONTEXT
    # -------------------------------------------------------------
    cells.append(make_cell("markdown", """## 3. Módulo 1: Herramientas (Tools) y `ToolContext`
### Reglas de Oro de Tools en Google ADK:
1. **Docstring obligatorio y claro:** El LLM planifica su uso leyendo exclusivamente la descripción y la sección `Args:` y `Returns:`.
2. **Anotaciones de tipo estrictas:** No usar parámetros ambiguos o sin tipo.
3. **Retorno en diccionario serializable (`dict`):** Siempre devolver estructuras JSON.
4. **`ToolContext`:** Parámetro especial que ADK inyecta automáticamente. Permite leer y mutar `session.state` sin ensuciar el prompt."""))

    cells.append(make_cell("code", """import platform
import psutil
from google.adk.tools import ToolContext

def obtener_metricas_servidor() -> dict:
    \"\"\"Obtiene métricas de hardware de la máquina local (CPU, Memoria, SO).

    Returns:
        dict con el porcentaje de uso de CPU, memoria disponible y plataforma.
    \"\"\"
    mem = psutil.virtual_memory()
    return {
        "status": "success",
        "cpu_usage_percent": psutil.cpu_percent(interval=0.1),
        "memoria_libre_gb": round(mem.available / (1024**3), 2),
        "so": platform.system()
    }

def registrar_alerta_sistema(severidad: str, detalle: str, tool_context: ToolContext) -> dict:
    \"\"\"Registra una alerta técnica de seguridad en la sesión.

    Args:
        severidad: Nivel de la alerta ('baja', 'media', 'alta', 'critica').
        detalle: Explicación de la vulnerabilidad o anomalía.

    Returns:
        dict con el estado de guardado y total de alertas en la sesión.
    \"\"\"
    # ToolContext nos permite acceder y mutar session.state directamente
    alertas = tool_context.state.get("alertas_sistema", [])
    alertas.append({"severidad": severidad.lower(), "detalle": detalle})
    tool_context.state["alertas_sistema"] = alertas
    
    return {
        "status": "success",
        "mensaje": f"Alerta guardada con severidad '{severidad}'",
        "total_alertas": len(alertas)
    }

# Creamos un agente con las herramientas integradas
agente_monitor = Agent(
    name="agente_monitoreo",
    model=local_model,
    instruction=\"\"\"
    Eres un agente de monitoreo de servidores locales.
    - Si el usuario te pide ver el estado del servidor, usa 'obtener_metricas_servidor'.
    - Si detectas alguna anomalía o te piden registrar un incidente, usa 'registrar_alerta_sistema'.
    \"\"\",
    tools=[obtener_metricas_servidor, registrar_alerta_sistema]
)

session_tools = await session_service.create_session(
    app_name="agente_monitor_app",
    session_id="sesion_02_tools",
    user_id="sysadmin",
    state={"alertas_sistema": []}
)
runner_tools = Runner(agent=agente_monitor, app_name="agente_monitor_app", session_service=session_service)

consulta = "Consulta el estado del hardware de este equipo y dime si está operativo."
print(f"👤 [Usuario]: {consulta}\\n")

async for event in runner_tools.run_async(session_id=session_tools.id, user_id="sysadmin", prompt=consulta):
    text = extraer_texto(event)
    if text:
        print(f"{text}\\n")
"""))

    # -------------------------------------------------------------
    # SECCIÓN 4: HUMAN IN THE LOOP
    # -------------------------------------------------------------
    cells.append(make_cell("markdown", """## 4. Módulo 1: Human-in-the-Loop (HITL) y Confirmación de Acciones Críticas

En sistemas de producción nunca se debe permitir que un agente autónomo ejecute acciones destructivas o irreversibles (como formatear volúmenes, reiniciar bases de datos en producción o procesar pagos) sin supervisión humana explícita.

### ¿Por qué HITL pertenece a una interfaz interactiva (`adk web`) y no a una celda de Notebook?
* **En un Jupyter Notebook**, la ejecución es inherentemente síncrona y lineal. Interceptar llamadas que requieren confirmación humana exige pausar el bucle, capturar IDs de llamada, simular manualmente eventos de `FunctionResponse(confirmed=True)` y reinyectarlos al Runner. Esto resulta artificial e incómodo.
* **Google ADK resuelve esto nativamente con ADK Web UI (`adk web`)**: Cuando una herramienta declara `require_confirmation`, el servidor de ADK Web **pausa la ejecución automáticamente** y presenta un modal interactivo en pantalla con botones para **Aprobar** (*Approve*) o **Rechazar** (*Reject*). Al pulsar el botón, la interfaz web envía la confirmación al agente y reanuda el flujo de manera natural.

A continuación:
1. Diseñamos la herramienta con política de confirmación mediante `FunctionTool(func, require_confirmation=...)`.
2. Verificamos la política de seguridad con `check_require_confirmation()`.
3. Exploramos el micro-agente interactivo creado en `hitl_agent/` listo para ser ejecutado con `adk web`."""))

    cells.append(make_cell("code", """from google.adk.tools import FunctionTool, ToolContext

def reiniciar_servicio(servicio: str, forzar: bool = False) -> str:
    \"\"\"Reinicia un servicio crítico de infraestructura.

    Args:
        servicio: Nombre del servicio (ej. 'nginx', 'postgresql', 'redis').
        forzar: Si es True, fuerza la terminación inmediata (SIGKILL).
    \"\"\"
    modo = "FORZADO (SIGKILL)" if forzar else "GRACEFUL"
    return f"✓ Servicio '{servicio}' reiniciado exitosamente en modo {modo}."

def validar_aprobacion(servicio: str = "", forzar: bool = False, **kwargs) -> bool:
    \"\"\"Regla de Seguridad:
    Requiere confirmación humana si el servicio es una base de datos crítica o si forzar=True.
    \"\"\"
    servicios_criticos = ["postgresql", "mysql", "production_db", "auth_service"]
    es_critico = servicio.lower() in servicios_criticos
    return forzar or es_critico

# Envolvemos la función con confirmación condicional
tool_reinicio_seguro = FunctionTool(
    func=reiniciar_servicio,
    require_confirmation=validar_aprobacion
)

# Evaluamos la política contra diferentes escenarios operativos
escenarios = [
    {"servicio": "nginx", "forzar": False, "desc": "Servidor web estándar (parada limpia)"},
    {"servicio": "postgresql", "forzar": False, "desc": "Base de datos principal (servicio crítico)"},
    {"servicio": "redis", "forzar": True, "desc": "Servicio de caché (reinicio forzado)"},
]

print("🛡️ [EVALUACIÓN DE POLÍTICA DE SEGURIDAD HUMAN-IN-THE-LOOP]:\\n")
for esc in escenarios:
    args = {"servicio": esc["servicio"], "forzar": esc["forzar"]}
    requiere_humano = await tool_reinicio_seguro.check_require_confirmation(args, None)
    badge = "🔴 REQUIERE APROBACIÓN HUMANA" if requiere_humano else "🟢 EJECUCIÓN DIRECTA PERMITIDA"
    print(f"• Escenario: {esc['desc']}")
    print(f"  Argumentos: {args}")
    print(f"  Decisión de ADK: {badge}\\n")
"""))

    cells.append(make_cell("markdown", """### 4.1 Ejecución Interactiva del Agente HITL con `adk web`

Para probar la experiencia real con interfaz gráfica interactiva, hemos empaquetado este agente en el subdirectorio `hitl_agent/`:

```
hitl_agent/
├── __init__.py     # Exporta root_agent
├── agent.py        # Define el agente DevOps con tool_reinicio_seguro y modelo local
└── README.md       # Guía de pruebas y escenarios
```

#### 🚀 Comando para lanzar el agente interactivo en tu terminal:

```bash
adk web hitl_agent --port 8000
```
*(O desde el entorno virtual: `.venv/bin/adk web hitl_agent --port 8000`)*

Luego abre en tu navegador: **[http://localhost:8000](http://localhost:8000)**

**Prueba estos dos mensajes en el chat de la Web UI:**
1. *"Reinicia el servicio nginx de forma normal"* $\\\\rightarrow$ Se ejecuta de inmediato.
2. *"Por favor reinicia el servicio postgresql de forma forzada"* $\\\\rightarrow$ **ADK Web detendrá la ejecución y mostrará un modal interactivo solicitando tu aprobación (`Approve` / `Reject`)** antes de continuar."""))

    cells.append(make_cell("code", """from pathlib import Path
from google.adk.cli.utils.agent_loader import AgentLoader

# 1. Verificar la estructura del paquete standalone
ruta_agente = Path("hitl_agent/agent.py")
print(f"📄 Ruta del agente standalone: {ruta_agente.resolve()}")
print(f"   Tamaño: {ruta_agente.stat().st_size} bytes\\n")

# 2. Cargar el agente usando el cargador oficial de ADK
loader = AgentLoader(".")
agente_hitl = loader.load_agent("hitl_agent")

print(f"✓ Agente descubierto por ADK Web: {agente_hitl.name}")
print(f"✓ Herramientas protegidas con HITL: {[t.name for t in agente_hitl.tools]}")
print(f"✓ Modelo asignado: {getattr(agente_hitl.model, 'model', str(agente_hitl.model))}")
print("\\n💡 Recuerda: ejecuta en tu terminal para probar la UI interactiva:")
print("   adk web hitl_agent --port 8000")
"""))

    # -------------------------------------------------------------
    # SECCIÓN 5: ORQUESTACIÓN DETERMINISTA
    # -------------------------------------------------------------
    cells.append(make_cell("markdown", """## 5. Módulo 2: Orquestación Determinista (`BaseAgent` Composites)
**Regla de Oro en Arquitectura de Agentes:**
> No delegues a la improvisación de un LLM las transiciones que tu lógica de negocio ya conoce de antemano.

Google ADK ofrece 3 agentes compuestos deterministas:
1. `SequentialAgent`: Ejecuta una lista ordenada de subagentes. Cada agente escribe en su `output_key` y el siguiente la lee en su prompt mediante `{output_key}`.
2. `ParallelAgent`: Ejecuta múltiples subagentes concurrentemente. Cada subagente **debe** tener un `output_key` único.
3. `LoopAgent`: Bucle iterativo de mejora continua con parada temprana mediante un `EscalationChecker` que emite `EventActions(escalate=True)`."""))

    cells.append(make_cell("markdown", """### 5.1 `SequentialAgent` Pipeline
Veamos cómo encadenar 3 especialistas:
1. **Analizador de Requisitos** (output: `analisis_req`)
2. **Arquitecto de Base de Datos** (lee `{analisis_req}`, output: `schema_sql`)
3. **Diseñador de API REST** (lee `{schema_sql}`, output: `api_spec`)"""))

    cells.append(make_cell("code", """from google.adk.agents import SequentialAgent

analizador = Agent(
    name="analizador",
    model=local_model,
    instruction="Analiza los requerimientos del usuario y extrae los 2 requisitos funcionales clave de forma muy concisa.",
    output_key="analisis_req"
)

arquitecto_db = Agent(
    name="arquitecto_db",
    model=local_model,
    instruction=\"\"\"
    Basándote en el análisis:
    {analisis_req}
    Diseña el esquema de tablas SQL relacionales necesario (muy breve).
    \"\"\",
    output_key="schema_sql"
)

disenador_api = Agent(
    name="disenador_api",
    model=local_model,
    instruction=\"\"\"
    Basándote en el esquema de base de datos:
    {schema_sql}
    Diseña los 2 endpoints REST principales necesarios (Método y URI).
    \"\"\",
    output_key="api_spec"
)

pipeline_secuencial = SequentialAgent(
    name="pipeline_ingenieria",
    sub_agents=[analizador, arquitecto_db, disenador_api]
)

session_seq = await session_service.create_session(app_name="pipeline_secuencial_app", session_id="sesion_seq", user_id="lead", state={})
runner_seq = Runner(agent=pipeline_secuencial, app_name="pipeline_secuencial_app", session_service=session_service)

input_proyecto = "Queremos un sistema para reservas de bicicletas compartidas con pago por minuto."
print(f"📋 [Caso]: {input_proyecto}\\n")

async for event in runner_seq.run_async(session_id=session_seq.id, user_id="lead", prompt=input_proyecto):
    if event.author:
        print(f"👉 [Turno de: {event.author}]")
    text = extraer_texto(event)
    if text:
        print(text[:250] + ("..." if len(text) > 250 else "") + "\\n")
"""))

    cells.append(make_cell("markdown", """### 5.2 `ParallelAgent` Concurrente y Agregación
Ejecutamos en paralelo una auditoría de **Seguridad**, una de **Rendimiento** y una de **Mantenibilidad**.
Posteriormente, un agente sintetizador consolidará los 3 reportes."""))

    cells.append(make_cell("code", """from google.adk.agents import ParallelAgent

auditor_seguridad = Agent(
    name="auditor_sec",
    model=local_model,
    instruction="Analiza el código y señala posibles vulnerabilidades de seguridad en 2 líneas.",
    output_key="rep_seguridad"  # Clave única
)

optimizador_rendimiento = Agent(
    name="optimizador_perf",
    model=local_model,
    instruction="Analiza el código y señala posibles cuellos de botella de rendimiento en 2 líneas.",
    output_key="rep_rendimiento"  # Clave única
)

sintetizador = Agent(
    name="cto_sintesis",
    model=local_model,
    instruction=\"\"\"
    Has recibido dos reportes de auditoría:
    [SEGURIDAD]: {rep_seguridad}
    [RENDIMIENTO]: {rep_rendimiento}
    
    Emite una decisión ejecutiva final en 3 líneas priorizando acciones.
    \"\"\",
    output_key="dictamen_final"
)

pipeline_hibrido = SequentialAgent(
    name="pipeline_auditoria_paralela",
    sub_agents=[
        ParallelAgent(name="auditorias_simultaneas", sub_agents=[auditor_seguridad, optimizador_rendimiento]),
        sintetizador
    ]
)

session_par = await session_service.create_session(app_name="pipeline_hibrido_app", session_id="sesion_par", user_id="dev", state={})
runner_par = Runner(agent=pipeline_hibrido, app_name="pipeline_hibrido_app", session_service=session_service)

codigo_test = \"\"\"
@app.route('/login', methods=['POST'])
def login():
    u, p = request.form['u'], request.form['p']
    q = f"SELECT * FROM users WHERE u = '{u}' AND p = '{p}'"
    return db.execute(q).fetchall()
\"\"\"

print("⚡ [Iniciando análisis concurrente de seguridad y rendimiento...]\\n")
async for event in runner_par.run_async(session_id=session_par.id, user_id="dev", prompt=codigo_test):
    if event.author:
        print(f">> [Evento de: {event.author}]")
    text = extraer_texto(event)
    if text:
        print(text[:250] + ("..." if len(text) > 250 else "") + "\\n")
"""))

    cells.append(make_cell("markdown", """### 5.3 `LoopAgent` de Refinamiento con `EscalationChecker`
El bucle ejecuta cíclicamente:
1. **Generador:** Escribe o mejora una función.
2. **Evaluador:** Revisa calidad. Si está aprobada, escribe `"APROBADO"`.
3. **EscalationChecker (`BaseAgent`):** Si ve `"APROBADO"`, emite `EventActions(escalate=True)`, lo que cancela el bucle de inmediato sin esperar a `max_iterations`."""))

    cells.append(make_cell("code", """from typing import AsyncGenerator
from google.adk.agents import BaseAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

class EscalationChecker(BaseAgent):
    \"\"\"Inspecciona el estado. Si la evaluación contiene 'APROBADO', detiene el Loop.\"\"\"
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        evaluacion = ctx.session.state.get("eval_calidad", "")
        iter_num = ctx.session.state.get("num_iter", 0) + 1
        ctx.session.state["num_iter"] = iter_num
        
        print(f"🔍 [EscalationChecker - Iteración {iter_num}]: Comprobando nota...")
        if "APROBADO" in evaluacion.upper():
            print("  ✓ ¡Criterio cumplido! Emitiendo escalate=True para terminar el Loop.")
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            print("  ✗ Calidad insuficiente. Continuando siguiente iteración.")
            yield Event(author=self.name)

generador = Agent(
    name="coder",
    model=local_model,
    instruction=\"\"\"
    Optimiza esta función Python en pocas líneas con memoización y type hints:
    {codigo_actual}
    Feedback previo: {eval_calidad}
    Escribe sólo la función Python concisa.
    \"\"\",
    output_key="codigo_actual"
)

evaluador = Agent(
    name="reviewer",
    model=local_model,
    instruction=\"\"\"
    Evalúa el código: {codigo_actual}
    Si contiene type hints o memoización, responde exactamente 'APROBADO' en la 1ra línea.
    De lo contrario responde 'RECHAZADO' en 1 línea.
    \"\"\",
    output_key="eval_calidad"
)

bucle = LoopAgent(
    name="bucle_calidad",
    sub_agents=[generador, evaluador, EscalationChecker(name="stop_checker")],
    max_iterations=2  # Parada de seguridad
)

session_loop = await session_service.create_session(
    app_name="bucle_app",
    session_id="sesion_loop",
    user_id="dev",
    state={
        "codigo_actual": "def fib(n): return n if n<=1 else fib(n-1)+fib(n-2)",
        "eval_calidad": "Código lento e ineficiente, sin type hints.",
        "num_iter": 0
    }
)
runner_loop = Runner(agent=bucle, app_name="bucle_app", session_service=session_service)

print("🔄 [Iniciando Bucle de Refinamiento Iterativo...]\\n")
async for event in runner_loop.run_async(session_id=session_loop.id, user_id="dev", prompt="Optimiza Fibonacci"):
    if event.author and event.author != "stop_checker":
        print(f"[{event.author}]:")
        text = extraer_texto(event)
        if text:
            print(text[:200] + "...\\n")
"""))

    # -------------------------------------------------------------
    # SECCIÓN 6: GRAPH WORKFLOWS
    # -------------------------------------------------------------
    cells.append(make_cell("markdown", """## 6. Módulo 3: El Nuevo Graph Workflow API de ADK 2.0
ADK 2.0 introduce flujos basados en **Grafos Dirigidos (`Workflow`)**:
* **`START`:** Nodo de entrada estándar que recibe la petición del usuario.
* **Auto-Wrapping:** Cualquier función Python ordinaria o `Agent` colocado en una arista (`edge`) es convertido en nodo automáticamente.
* **Resolución de Parámetros:**
  - `node_input`: Salida generada por el nodo predecesor.
  - `ctx`: Contexto del workflow.
  - Cualquier otro nombre: Se extrae de `ctx.state[nombre]`.
* **Aristas (`edges`):**
  - Secuencial: `[('START', a), (a, b)]`
  - Condicional: `[(clasificador, nodo_a, "ruta_a"), (clasificador, nodo_b, "__DEFAULT__")]`
  - Fan-Out / Fan-In con `JoinNode`: Bifurca y sincroniza en un diccionario `{nodo_a: salida_a, nodo_b: salida_b}`."""))

    cells.append(make_cell("markdown", """### 6.1 Grafo Básico con `START` y Nodos de Función"""))

    cells.append(make_cell("code", """from google.adk.workflow import Workflow

def preprocesar(node_input: str) -> str:
    \"\"\"Nodo 1: Limpia y normaliza el texto recibido desde START.\"\"\"
    return node_input.strip().upper()

def enriquecer(node_input: str, rol_usuario: str) -> dict:
    \"\"\"Nodo 2: Recibe la salida del anterior e inyecta state['rol_usuario'].\"\"\"
    return {
        "texto_procesado": node_input,
        "autorizado_por": rol_usuario
    }

agente_resolutor = Agent(
    name="resolutor_ticket",
    model=local_model,
    instruction="Recibes un diccionario con el ticket y el rol autorizado. Da una respuesta técnica estructurada."
)

# Definición del Grafo con sus aristas
grafo_simple = Workflow(
    name="workflow_tickets",
    edges=[
        ("START", preprocesar),
        (preprocesar, enriquecer),
        (enriquecer, agente_resolutor)
    ]
)

session_graph = await session_service.create_session(
    app_name="grafo_simple_app",
    session_id="sesion_g1",
    user_id="analista",
    state={"rol_usuario": "DevOps Senior L3"}
)
runner_graph = Runner(agent=grafo_simple, app_name="grafo_simple_app", session_service=session_service)

ticket = "CrashLoopBackOff en pod auth-service tras rotar secrets."
print(f"🎫 [Ticket]: {ticket}\\n")

async for event in runner_graph.run_async(session_id=session_graph.id, user_id="analista", prompt=ticket):
    if event.author:
        print(f">> [Nodo Activo: {event.author}]")
    text = extraer_texto(event)
    if text:
        print(text[:300] + "...\\n")
"""))

    cells.append(make_cell("markdown", """### 6.2 Enrutamiento Condicional Dinámico en Grafos
El nodo clasificador emite un `Event(output=..., route="nombre_ruta")`.
Las aristas dirigen la ejecución al agente correspondiente usando un mapeo `{ruta: agente}`."""))

    cells.append(make_cell("code", """from google.adk.events.event import Event

def enrutador(node_input: str) -> Event:
    texto = node_input.lower()
    if any(k in texto for k in ["bug", "error", "traceback", "excepcion"]):
        return Event(output=node_input, route="codigo")
    elif any(k in texto for k in ["seguridad", "vulnerabilidad", "cve", "token"]):
        return Event(output=node_input, route="seguridad")
    return Event(output=node_input, route="__DEFAULT__")

agente_code = Agent(name="experto_bugs", model=local_model, instruction="Eres un debugger. Corrige el bug.")
agente_sec = Agent(name="experto_sec", model=local_model, instruction="Eres un auditor de seguridad. Mitiga el fallo.")
agente_gen = Agent(name="experto_general", model=local_model, instruction="Eres un arquitecto general. Brinda orientación.")

grafo_dinamico = Workflow(
    name="router_workflow",
    edges=[
        ("START", enrutador),
        (enrutador, {
            "codigo": agente_code,
            "seguridad": agente_sec,
            "__DEFAULT__": agente_gen
        })
    ]
)

session_router = await session_service.create_session(app_name="grafo_dinamico_app", session_id="sesion_router", user_id="dev", state={})
runner_router = Runner(agent=grafo_dinamico, app_name="grafo_dinamico_app", session_service=session_service)

test_prompt = "Detectamos una vulnerabilidad de inyección SQL con fuga de tokens de sesión."
print(f"🚨 [Consulta]: {test_prompt}\\n")

async for event in runner_router.run_async(session_id=session_router.id, user_id="dev", prompt=test_prompt):
    if event.author:
        print(f"🎯 [Rama Activada: {event.author}]")
    text = extraer_texto(event)
    if text:
        print(text[:300] + "...\\n")
"""))

    cells.append(make_cell("markdown", """### 6.3 Concurrencia con Fan-Out y Fan-In (`JoinNode`)
Bifurcamos en ramas paralelas y convergemos en `JoinNode`.
`JoinNode` emite un diccionario con las respuestas de cada rama indexadas por el nombre del nodo."""))

    cells.append(make_cell("code", """from google.adk.workflow import JoinNode

def calcular_costos_infra(node_input: str) -> dict:
    return {"costo_estimado_usd": 380.0, "servidores": "2x Standard-4 (16GB RAM)"}

def auditar_latencia_red(node_input: str) -> dict:
    return {"p95_latencia_ms": 38, "region": "us-central1", "cdn": True}

sincronizador = JoinNode(name="merge_analisis")

decisor_cto = Agent(
    name="cto_infra",
    model=local_model,
    instruction="Recibes un diccionario con costos y latencia agregados por el JoinNode. Emite una conclusión de viabilidad técnica concisa."
)

grafo_join = Workflow(
    name="workflow_infra_join",
    edges=[
        ("START", (calcular_costos_infra, auditar_latencia_red)),  # Fan-Out
        ((calcular_costos_infra, auditar_latencia_red), sincronizador),  # Fan-In convergente
        (sincronizador, decisor_cto)
    ]
)

session_join = await session_service.create_session(app_name="grafo_join_app", session_id="sesion_join", user_id="cto", state={})
runner_join = Runner(agent=grafo_join, app_name="grafo_join_app", session_service=session_service)

req_infra = "Despliegue de un microservicio de pagos con 2,000 transacciones concurrentes por minuto."
print(f"🏗️ [Requerimiento de Infraestructura]: {req_infra}\\n")

async for event in runner_join.run_async(session_id=session_join.id, user_id="cto", prompt=req_infra):
    if event.author:
        print(f">> [Evento de: {event.author}]")
    text = extraer_texto(event)
    if text:
        print(text[:350] + "...\\n")
"""))

    # -------------------------------------------------------------
    # SECCIÓN 7: MULTI-AGENT AVANZADO
    # -------------------------------------------------------------
    cells.append(make_cell("markdown", """## 7. Módulo 4: Arquitecturas Multi-Agente Avanzadas
### 7.1 Patrón `AgentTool` (Agente Invocado como Herramienta)
* El agente coordinador **no cede** el diálogo al subagente.
* El subagente opera como una función inteligente con su propio prompt y modelo.
* El coordinador recibe la respuesta y continúa su razonamiento."""))

    cells.append(make_cell("code", """from google.adk.tools import AgentTool

especialista_cripto = Agent(
    name="experto_criptografia",
    model=local_model,
    description="Analiza suites de cifrado, TLS, firmas y hashing.",
    instruction="Eres un criptógrafo. Analiza los algoritmos de seguridad y señala si son obsoletos o seguros."
)

coordinador = Agent(
    name="coordinador_arquitectura",
    model=local_model,
    instruction=\"\"\"
    Eres el Arquitecto Principal. Atiendes al usuario.
    Si pregunta sobre cifrado o almacenamiento seguro de claves, consulta a tu especialista con la herramienta.
    \"\"\",
    tools=[AgentTool(especialista_cripto)]
)

session_at = await session_service.create_session(app_name="coordinador_app", session_id="sesion_agent_tool", user_id="dev", state={})
runner_at = Runner(agent=coordinador, app_name="coordinador_app", session_service=session_service)

pregunta_cripto = "Queremos almacenar contraseñas en MySQL usando MD5 con salt. ¿Es buena idea?"
print(f"👤 [Usuario]: {pregunta_cripto}\\n")

async for event in runner_at.run_async(session_id=session_at.id, user_id="dev", prompt=pregunta_cripto):
    if event.author:
        print(f">> [Evento de: {event.author}]")
    text = extraer_texto(event)
    if text:
        print(text[:300] + "...\\n")
"""))

    cells.append(make_cell("markdown", """### 7.2 ADK 2.0 Task Delegation con Esquemas Pydantic (`mode="task"`)
* Configurar `mode="task"` en un subagente le inyecta automáticamente la tool `finish_task`.
* El coordinador recibe automáticamente la tool `request_task_{nombre_subagente}`.
* Mediante `output_schema` con modelos **Pydantic**, la respuesta se valida antes de volver al coordinador."""))

    cells.append(make_cell("code", """from pydantic import BaseModel, Field, field_validator
from typing import List, Literal
import json

class Vulnerabilidad(BaseModel):
    modulo: str = Field(description="Módulo afectado")
    severidad: str = Field(description="Severidad")
    descripcion: str = Field(description="Explicación del riesgo")

class ReporteAuditoria(BaseModel):
    resumen: str = Field(description="Resumen de auditoría")
    vulnerabilidades: List[Vulnerabilidad] = Field(default_factory=list, description="Lista de hallazgos")
    aprobado_produccion: bool = Field(description="True si se aprueba")

    @field_validator("vulnerabilidades", mode="before")
    @classmethod
    def parse_vulnerabilidades(cls, v):
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else [parsed]
            except Exception:
                return []
        return v

subagente_auditor = Agent(
    name="auditor_task",
    model=local_model,
    mode="task",  # Inyecta 'finish_task'
    output_schema=ReporteAuditoria,  # Contrato garantizado con Pydantic
    description="Audita componentes de software y retorna un ReporteAuditoria estructurado.",
    instruction="Audita el código y llama a finish_task con el modelo ReporteAuditoria completo."
)

coordinador_release = Agent(
    name="release_manager",
    model=local_model,
    instruction=\"\"\"
    Eres el Release Manager.
    1. Delega la revisión técnica usando la herramienta request_task_auditor_task.
    2. Analiza el reporte estructurado devuelto.
    3. Si aprobado_produccion es False, bloquea el pase y explica los riesgos.
    \"\"\",
    sub_agents=[subagente_auditor]  # Inyecta 'request_task_auditor_task'
)

session_task = await session_service.create_session(app_name="coordinador_release_app", session_id="sesion_task_mode", user_id="lead", state={})
runner_task = Runner(agent=coordinador_release, app_name="coordinador_release_app", session_service=session_service)

propuesta = "Lanzamiento de API de facturación: Se guarda el token de pago en logs en texto claro para depuración."
print(f"📦 [Propuesta de Release]: {propuesta}\\n")

async for event in runner_task.run_async(session_id=session_task.id, user_id="lead", prompt=propuesta):
    if event.author:
        print(f">> [Evento de: {event.author}]")
    text = extraer_texto(event)
    if text:
        print(text[:300] + "...\\n")
"""))

    # -------------------------------------------------------------
    # SECCIÓN 8: PROYECTO CAPSTONE
    # -------------------------------------------------------------
    cells.append(make_cell("markdown", """## 8. Proyecto Capstone: Local Software Architect & Security Agency
Integramos todo lo aprendido en una agencia multi-agente de arquitectura de software:
1. **Product Manager (Analista Funcional):** Desglose de requisitos y entidades.
2. **Auditoría Paralela:**
   - Especialista en Rendimiento de Base de Datos y Caché.
   - Especialista en Ciberseguridad y Normativas (OAuth2, HIPAA, Zero Trust).
   - Uso de `ToolContext` para calificar el nivel de madurez técnica (`scores_calidad`).
3. **CTO Sintetizador:** Genera el Blueprint de Arquitectura final y el Roadmap en 3 fases."""))

    cells.append(make_cell("code", """def puntuar_auditoria(area: str, nota_0_a_100: int, tool_context: ToolContext) -> dict:
    \"\"\"Registra la puntuación técnica de un área en el estado de la sesión.\"\"\"
    scores = tool_context.state.get("scores_calidad", {})
    scores[area] = nota_0_a_100
    tool_context.state["scores_calidad"] = scores
    return {"status": "success", "mensaje": f"Puntuación {nota_0_a_100}/100 guardada para {area}"}

# 1. Analista Funcional
pm = Agent(
    name="lead_pm",
    model=local_model,
    instruction="Resume en 2 oraciones la visión del producto y lista los 2 módulos técnicos indispensables.",
    output_key="analisis_producto"
)

# 2. Especialistas Paralelos con Tools
arquitecto_db = Agent(
    name="arquitecto_datos",
    model=local_model,
    instruction=\"\"\"
    Basándote en {analisis_producto}:
    Diseña el modelo de datos (SQL vs NoSQL) y estrategia de caché.
    Usa la tool puntuar_auditoria para registrar tu calificación (0-100).
    \"\"\",
    tools=[puntuar_auditoria],
    output_key="dictamen_db"
)

auditor_ciso = Agent(
    name="ciso_seguridad",
    model=local_model,
    instruction=\"\"\"
    Basándote en {analisis_producto}:
    Evalúa autenticación (OAuth2), cifrado y cumplimiento (HIPAA / GDPR).
    Usa la tool puntuar_auditoria para registrar tu calificación (0-100).
    \"\"\",
    tools=[puntuar_auditoria],
    output_key="dictamen_sec"
)

# 3. CTO Sintetizador
cto = Agent(
    name="cto_ejecutivo",
    model=local_model,
    instruction=\"\"\"
    Eres el CTO. Has recibido:
    - Análisis: {analisis_producto}
    - Datos: {dictamen_db}
    - Seguridad: {dictamen_sec}
    
    Elabora el Blueprint Arquitectónico Final con stack recomendado y Roadmap en 3 fases.
    \"\"\",
    output_key="blueprint_final"
)

# Ensamblaje en pipeline híbrido: Secuencial -> Paralelo -> Secuencial
agencia = SequentialAgent(
    name="agencia_arquitectura_local",
    sub_agents=[
        pm,
        ParallelAgent(name="auditoria_concurrente", sub_agents=[arquitecto_db, auditor_ciso]),
        cto
    ]
)

session_capstone = await session_service.create_session(
    app_name="agencia_app",
    session_id="sesion_capstone",
    user_id="founder",
    state={"scores_calidad": {}}
)
runner_capstone = Runner(agent=agencia, app_name="agencia_app", session_service=session_service)

caso_telemedicina = \"\"\"
Plataforma de telemedicina con videollamadas encriptadas de extremo a extremo,
recetas médicas firmadas digitalmente y cobros recurrentes para 50,000 pacientes.
\"\"\"

print("🏢 [INICIANDO EJECUCIÓN DE LA AGENCIA MULTI-AGENTE CAPSTONE]\\n")
async for event in runner_capstone.run_async(session_id=session_capstone.id, user_id="founder", prompt=caso_telemedicina):
    if event.author:
        print(f"⭐ [FASE: {event.author.upper()}]")
    text = extraer_texto(event)
    if text:
        print(text[:300] + "...\\n")

sesion_final = await session_service.get_session(session_id=session_capstone.id, user_id="founder")
print("=" * 60)
print("📊 [RESUMEN FINAL CONSOLIDADO EN ESTADO]:")
print("• Scores registrados por las tools:", sesion_final.state.get("scores_calidad"))
print("• Clave 'blueprint_final' presente:", "blueprint_final" in sesion_final.state)
print("=" * 60)
"""))

    # -------------------------------------------------------------
    # SECCIÓN 9: CONCLUSIONES Y MEJORES PRÁCTICAS
    # -------------------------------------------------------------
    cells.append(make_cell("markdown", """## 9. Ciclo de Vida del Agente (ADLC) y Buenas Prácticas
Basado en las recomendaciones del equipo de **Google Agents-CLI**:

1. **Scaffolding Estandarizado:** Mantén tus agentes desacoplados con carpetas claras (`agent.py`, `tools.py`, `.env`).
2. **Temperatura Baja en Modelos Locales:** Usa `temperature=0.1` o `0.2` para asegurar que las llamadas a herramientas y formatos JSON no alucinen.
3. **Limpieza de Historial Conversacional:** En subagentes especializados, usa `include_contents='none'` para que no carguen el historial del diálogo padre.
4. **Evaluaciones con Datasets:** Usa `agents-cli eval run` con criterios de "LLM-as-a-judge" antes de pasar cualquier agente a producción.
5. **Observabilidad:** Monitoriza eventos de parada, tiempos de respuesta y tokens mediante OpenTelemetry."""))

    cells.append(make_cell("markdown", """### 9.1 Catálogo Completo de Agentes en ADK Web (`adk web agents`)

Hemos transformado **todos los agentes del curso** en paquetes modulares dentro del directorio `agents/`:

| Subcarpeta | Agente | Arquitectura / Módulo |
|---|---|---|
| `agents/single_state_agent` | `single_state_agent` | Single-Agent con inyección de estado (Módulo 1) |
| `agents/devops_tools_agent` | `devops_tools_agent` | Herramientas Kubernetes y métricas (Módulo 1) |
| `agents/hitl_agent` | `hitl_agent` | Human-in-the-Loop y confirmación interactiva (Módulo 1) |
| `agents/sequential_agent` | `sequential_agent` | Pipeline secuencial Linter $\\\\rightarrow$ Refactor (Módulo 2) |
| `agents/parallel_agent` | `parallel_agent` | Auditoría concurrente triple con síntesis ejecutiva (Módulo 2) |
| `agents/loop_agent` | `loop_agent` | Bucle iterativo de optimización con `EscalationChecker` (Módulo 2) |
| `agents/graph_workflow_agent` | `graph_workflow_agent` | Grafo de enrutamiento condicional dinámico (Módulo 3) |
| `agents/agent_tool_orchestrator` | `agent_tool_orchestrator` | Patrón `AgentTool` como subagente especialista (Módulo 4) |
| `agents/task_delegation_agent` | `task_delegation_agent` | Delegación en Task Mode con validación Pydantic (Módulo 4) |
| `agents/capstone_agency` | `capstone_agency` | Consultora de Arquitectura y Seguridad Capstone (Proyecto Final) |

#### 🌐 Cómo lanzar el panel completo en tu navegador:
```bash
adk web agents --port 8000
```
*(O directamente: `.venv/bin/adk web agents --port 8000`)*

Luego abre **[http://localhost:8000](http://localhost:8000)**: En la esquina superior izquierda encontrarás el menú desplegable para alternar y probar cualquiera de los 10 agentes interactivamente con tu LLM local."""))

    cells.append(make_cell("code", """from google.adk.cli.utils.agent_loader import AgentLoader

# Verificamos programáticamente el catálogo completo de agentes
loader = AgentLoader("agents")
agentes_disponibles = loader.list_agents()

print(f"📦 Se encontraron {len(agentes_disponibles)} agentes listos para ADK Web:\\n")
for nombre in agentes_disponibles:
    agente = loader.load_agent(nombre)
    tipo_cls = type(agente).__name__
    desc = getattr(agente, "description", "")[:60]
    print(f"  ✓ {nombre:<26} [{tipo_cls:<15}] -> {desc}...")

print("\\n🚀 Para ejecutarlos todos a la vez en la interfaz web:")
print("   adk web agents --port 8000")
"""))

    cells.append(make_cell("markdown", """### 9.2 Batería de Pruebas Oficial para ADK Web

A continuación se define la **batería oficial de pruebas** para cada uno de los 10 agentes del curso. Cada caso de prueba está calibrado para activar las características clave de cada arquitectura (Tools, Human-in-the-Loop, paralelismo, enrutamiento condicional, Task Mode y blueprints de arquitectura).

Puedes copiar estos prompts directamente en el chat de **ADK Web UI** (`http://localhost:8000`) o probarlos de inmediato en este notebook mediante la función `probar_agente()`:"""))

    cells.append(make_cell("code", """bateria_pruebas = [
    {
        "id": 1,
        "agente": "single_state_agent",
        "modulo": "Módulo 1: Single-Agent & Estado",
        "prompt": "¿Cómo configuro una conexión a PostgreSQL con SQLAlchemy usando variables de entorno?",
        "esperado": "Asistencia técnica personalizada con buenas prácticas y bloques de código."
    },
    {
        "id": 2,
        "agente": "devops_tools_agent",
        "modulo": "Módulo 1: Tools & ToolContext",
        "prompt": "Revisa el estado del pod auth-service y las métricas de cpu del servidor prod-db-01.",
        "esperado": "Llamadas a 'consultar_estado_pod' y 'obtener_metricas_servidor' con diagnóstico estructurado."
    },
    {
        "id": 3,
        "agente": "hitl_agent",
        "modulo": "Módulo 1: Human-in-the-Loop",
        "prompt": "Por favor reinicia el servicio postgresql de forma forzada.",
        "esperado": "Interrupción de seguridad y modal interactivo de aprobación (Approve / Reject) en ADK Web."
    },
    {
        "id": 4,
        "agente": "sequential_agent",
        "modulo": "Módulo 2: Sequential Pipeline",
        "prompt": "Analiza y refactoriza esta función: def calc(x): return x*2 if x>0 else 0",
        "esperado": "Paso 1: informe_lint del linter -> Paso 2: código refactorizado con type hints."
    },
    {
        "id": 5,
        "agente": "parallel_agent",
        "modulo": "Módulo 2: Parallel Concurrent",
        "prompt": "Audita un microservicio de pagos con Node.js y un Dockerfile que corre como root con dependencias GPL.",
        "esperado": "Auditoría simultánea (OWASP, Infraestructura, Licencias) y síntesis ejecutiva del CISO."
    },
    {
        "id": 6,
        "agente": "loop_agent",
        "modulo": "Módulo 2: Loop & Escalation",
        "prompt": "Optimiza la función de fibonacci recursiva para que tenga complejidad O(n) y type hints.",
        "esperado": "Bucle iterativo generador-evaluador con parada temprana cuando EscalationChecker aprueba."
    },
    {
        "id": 7,
        "agente": "graph_workflow_agent",
        "modulo": "Módulo 3: Graph Workflow API",
        "prompt": "Detectamos una vulnerabilidad de fuga de secrets y SQL injection en el login.",
        "esperado": "START -> Enrutador condicional dinámico derivando al especialista en ciberseguridad."
    },
    {
        "id": 8,
        "agente": "agent_tool_orchestrator",
        "modulo": "Módulo 4: AgentTool Pattern",
        "prompt": "Tech Lead, por favor audita la seguridad de nuestro nuevo servicio de pagos.",
        "esperado": "El Tech Lead invoca a especialista_owasp como herramienta inteligente mediante AgentTool."
    },
    {
        "id": 9,
        "agente": "task_delegation_agent",
        "modulo": "Módulo 4: Task Mode & Pydantic",
        "prompt": "Release Manager: Solicitamos pase a producción del endpoint de facturación con tokens en logs.",
        "esperado": "Delegación formal con 'request_task' y validación fuertemente tipada con Pydantic."
    },
    {
        "id": 10,
        "agente": "capstone_agency",
        "modulo": "Proyecto Capstone: Agencia Completa",
        "prompt": "Diseña la arquitectura para una app de telemedicina con videollamadas cifradas E2E y cobros para 50,000 usuarios.",
        "esperado": "Pipeline híbrido completo: PM -> Auditoría Concurrente (Datos + CISO) -> Blueprint del CTO."
    }
]

print("=" * 80)
print("🧪 BATERÍA OFICIAL DE PRUEBAS PARA ADK WEB (http://localhost:8000)")
print("=" * 80)
for p in bateria_pruebas:
    print(f"\\n[{p['id']}] Agente: {p['agente']} ({p['modulo']})")
    print(f"    💬 Prompt: '{p['prompt']}'")
    print(f"    🎯 Esperado: {p['esperado']}")

# Función auxiliar para probar cualquier agente de la batería directamente en este notebook
async def probar_agente(nombre_agente: str, prompt: str):
    agente_obj = loader.load_agent(nombre_agente)
    sess_service = InMemorySessionService()
    sess = await sess_service.create_session(app_name=nombre_agente, session_id="test_sess", user_id="tester", state={})
    runner = Runner(agent=agente_obj, app_name=nombre_agente, session_service=sess_service)
    
    print(f"\\n--- Ejecutando prueba de '{nombre_agente}' en local ---")
    print(f"💬 Prompt: '{prompt}'\\n")
    async for event in runner.run_async(session_id=sess.id, user_id="tester", prompt=prompt):
        if event.author:
            print(f">> [Evento de: {event.author}]")
        txt = extraer_texto(event)
        if txt:
            print(f"{txt}\\n")

# Ejecutamos una prueba en vivo como demostración inmediata:
print("\\n" + "=" * 80)
print("▶️ EJECUTANDO PRUEBA DEMOSTRATIVA EN VIVO CON 'devops_tools_agent':")
print("=" * 80)
await probar_agente("devops_tools_agent", bateria_pruebas[1]["prompt"])
"""))

    cells.append(make_cell("markdown", """---
**¡Felicitaciones! Has dominado Google ADK 2.0 y la construcción de sistemas multi-agente en local.**
"""))

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbformat": 4,
                "nbformat_minor": 5,
                "pygments_lexer": "ipython3",
                "version": "3.11.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

    target_path = "/Users/roberto/proyectods/cursoADK/curso_adk2_completo.ipynb"
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2, ensure_ascii=False)

    print(f"✓ Notebook creado exitosamente con {len(cells)} celdas en: {target_path}")

if __name__ == "__main__":
    build_notebook()

---
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #0f172a
color: #f8fafc
---

# Google ADK 2.0 & Arquitecturas Multi-Agente Locales
### Desde Single-Agent hasta Grafos y Delegación Jerárquica
**Ejecución 100% Local con Ollama, LM Studio y MLX**  
*Basado en las mejores prácticas de Google Agents-CLI y ADK 2.0*

---

## 🎯 Agenda del Curso

1. **Fundamentos:** Qué es Google ADK 2.0 y el Ciclo de Vida ADLC.
2. **Runtime Local:** Integración con Ollama, LM Studio y MLX vía LiteLLM.
3. **Single-Agent:** Prompts dinámicos, `ToolContext` y Human-in-the-Loop.
4. **Orquestación Determinista:** `SequentialAgent`, `ParallelAgent` y `LoopAgent`.
5. **Graph Workflows de ADK 2.0:** Nodos, aristas, enrutamiento dinámico y `JoinNode`.
6. **Sistemas Multi-Agente Avanzados:** `AgentTool` y Task Delegation tipada con Pydantic.
7. **Proyecto Capstone:** Agencia Local de Arquitectura y Auditoría de Software.

---

## 🏛️ ¿Qué es Google ADK? (Agent Development Kit)

Framework de ingeniería de software de Google diseñado para construir sistemas agénticos robustos, modulares y de producción:

1. **Filosofía Code-First & Tipado Estricto:** Clases Python nativas con Pydantic y typing. Sin abstracciones opacas ni prompts ocultos; lo que ves en el código es lo que se ejecuta.
2. **100% Agnóstico de Modelo (Local & Cloud):** Funciona con Gemini, pero optimizado para correr **100% en local** con **Ollama, LM Studio, MLX y vLLM** vía LiteLLM. Cero coste por token y máxima privacidad de datos.
3. **Orquestación Determinista y Grafos:** Mezcla razonamiento probabilístico con control de flujo determinista (`SequentialAgent`, `ParallelAgent`, `LoopAgent` y el nuevo **Graph Workflow API** con `JoinNode`).
4. **Ecosistema Completo: ADK Web & Agents-CLI:** UI interactiva local (`adk web agents`), soporte nativo de Human-in-the-Loop interactivo, visor de topología y ciclo de vida de ingeniería (ADLC).

> 💡 **Regla de Oro:** *No delegues a la improvisación de un LLM lo que tu lógica de negocio ya conoce de antemano.*

---

## 🧩 Primitivas Fundamentales de ADK

| Primitiva | Función en ADK |
| :--- | :--- |
| **`Agent` / `LlmAgent`** | Unidad cognitiva central que razona, usa herramientas y delega. |
| **`Tool`** | Función ejecutable (`FunctionTool`, `AgentTool`) expuesta al LLM. |
| **`Session`** | Hilo de conversación persistente con historial de eventos y memoria. |
| **`State`** | Diccionario de variables clave-valor accesible en la sesión. |
| **`Runner`** | Motor asíncrono de orquestación y despacho de eventos. |
| **`Event`** | Unidad atómica de comunicación y efectos colaterales (`EventActions`). |

---

## 💻 Runtime Local: Privacidad y Coste Cero

¿Por qué ejecutar agentes localmente?
- **Privacidad Total:** Los datos de tu código y empresa nunca salen de tu máquina.
- **Coste Cero por Token:** Ilimitadas iteraciones de pruebas y experimentación.
- **Baja Latencia de Red:** Sin cuellos de botella de conectores externos.

```python
from google.adk.models.lite_llm import LiteLlm

# Conexión con Ollama
model = LiteLlm(model="ollama_chat/qwen2.5:7b-instruct", api_base="http://localhost:11434")

# Conexión con LM Studio
model = LiteLlm(model="openai/qwen2.5-7b-instruct", api_base="http://localhost:1234/v1")

# Conexión con MLX (Apple Silicon)
model = LiteLlm(model="openai/Qwen2.5-7B-Instruct-4bit", api_base="http://localhost:8080/v1")
```

---

## 🤖 Single-Agent con Inyección Dinámica

En ADK, las instrucciones soportan inyección automática desde `session.state`:

```python
from google.adk.agents import Agent

asistente = Agent(
    name="senior_engineer",
    model=local_model,
    instruction="""
    Eres un {rol_tecnico}.
    Asistes al usuario {nombre_usuario}.
    Contexto del proyecto: {arquitectura_actual}
    
    Reglas:
    - Responde con código riguroso y optimizado.
    - Cita consideraciones de seguridad.
    """,
    output_key="respuesta_asistente"  # Se guarda directamente en el estado
)
```

---

## 🛠️ Herramientas Robustas y `ToolContext`

### Reglas de Oro en Tools para Agentes Locales:
1. **Docstrings exhaustivos:** El modelo decide invocar la tool sólo leyendo su docstring.
2. **Type hints estrictos:** Parámetros fuertemente tipados; evitar `kwargs` ambiguos.
3. **Retorno en dict:** Siempre devolver diccionarios JSON-serializables.
4. **`ToolContext`:** Accede y muta `session.state` sin ensuciar el prompt.

```python
def registrar_incidente(severidad: str, detalle: str, tool_context: ToolContext) -> dict:
    """Registra un evento de seguridad en el sistema de auditoría."""
    historial = tool_context.state.get("incidentes", [])
    historial.append({"severidad": severidad, "detalle": detalle})
    tool_context.state["incidentes"] = historial
    return {"status": "ok", "total": len(historial)}
```

---

## 🛡️ Human-in-the-Loop y Puertas de Aprobación

Nunca permitas que un agente ejecute acciones irreversibles sin autorización:

```python
from google.adk.tools import FunctionTool

def validar_reinicio(servicio: str, forzar: bool = False, **kwargs) -> bool:
    # Si es base de datos o forzado, exige confirmación humana
    return servicio in ["postgresql", "redis"] or forzar

herramienta_segura = FunctionTool(
    func=reiniciar_servicio_produccion,
    require_confirmation=validar_reinicio
)
```
- El `Runner` detecta la solicitud y pausa el ciclo esperando la aprobación del usuario.
- En **ADK Web UI** (`adk web agents`), el usuario recibe una tarjeta interactiva con botones para **Aprobar** o **Rechazar** la ejecución de la herramienta en tiempo real.

---

## ⛓️ Orquestación Determinista: `SequentialAgent`

**Regla de Arquitectura:** No uses razonamiento LLM para flujos que ya son predecibles.

```python
from google.adk.agents import SequentialAgent, Agent

analizador = Agent(name="analizador", output_key="resumen")
generador = Agent(name="generador", instruction="Crea código basado en: {resumen}")

pipeline = SequentialAgent(
    name="pipeline_desarrollo",
    sub_agents=[analizador, generador]
)
```
- Los agentes se ejecutan secuencialmente en orden estricto.
- El estado fluye de manera transparente mediante `output_key`.

---

## ⚡ Concurrencia con `ParallelAgent`

Ejecuta múltiples agentes en paralelo para tareas independientes:

```python
from google.adk.agents import ParallelAgent, SequentialAgent

pipeline = SequentialAgent(
    name="pipeline_auditoria",
    sub_agents=[
        ParallelAgent(
            name="auditorias_simultaneas",
            sub_agents=[
                auditor_seguridad,     # output_key="reporte_seguridad"
                optimizador_rendimiento, # output_key="reporte_rendimiento"
                analista_mantenibilidad  # output_key="reporte_dx"
            ]
        ),
        sintetizador_final # Lee {reporte_seguridad}, {reporte_rendimiento}, etc.
    ]
)
```
> ⚠️ **Importante:** Cada agente paralelo **debe** tener un `output_key` distinto para evitar condiciones de carrera.

---

## 🔁 Bucles de Refinamiento: `LoopAgent`

Modela ciclos iterativos de **Generar -> Evaluar -> Corregir**:

```python
from google.adk.agents import LoopAgent
from google.adk.events import Event, EventActions

class EscalationChecker(BaseAgent):
    async def _run_async_impl(self, ctx):
        if ctx.session.state.get("calidad") == "APROBADO":
            # Termina el bucle de inmediato
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            yield Event(author=self.name)

bucle = LoopAgent(
    name="refinamiento_codigo",
    sub_agents=[programador, revisor, EscalationChecker("stop_checker")],
    max_iterations=4 # Parada de seguridad (Circuit Breaker)
)
```

---

## 🌐 La Revolución de ADK 2.0: Graph Workflows

Los flujos agénticos modernos se modelan como **Grafos Dirigidos (`Workflow`)**:

```text
               ┌───────────────┐
               │     START     │
               └───────┬───────┘
                       │
             ┌─────────▼─────────┐
             │    Clasificador   │
             └────┬─────────┬────┘
      "codigo"    │         │  "seguridad"
       ┌──────────▼───┐ ┌───▼───────────┐
       │ Agente Debug │ │ Agente SecOps │
       └──────────────┘ └───────────────┘
```

- Nodos: Funciones Python, LLMs o Tools.
- Aristas (`edges`): Conexiones y rutas de control de flujo.

---

## 🔀 Enrutamiento Condicional en Grafos

```python
from google.adk.workflow import Workflow
from google.adk.events.event import Event

def router(node_input: str) -> Event:
    if "bug" in node_input:
        return Event(output=node_input, route="codigo")
    elif "seguridad" in node_input:
        return Event(output=node_input, route="seguridad")
    return Event(output=node_input, route="__DEFAULT__")

grafo = Workflow(
    name="router_workflow",
    edges=[
        ("START", router),
        (router, agente_codigo, "codigo"),
        (router, agente_seguridad, "seguridad"),
        (router, agente_general, "__DEFAULT__"),
    ]
)
```

---

## 🔀 Fan-Out y Fan-In con `JoinNode`

Bifurca la ejecución hacia ramas paralelas y sincroniza sus salidas:

```python
from google.adk.workflow import Workflow, JoinNode

sincronizador = JoinNode(name="merge_metrics")

grafo_infra = Workflow(
    name="evaluador_infra",
    edges=[
        # 1. Fan-out hacia dos ramas
        ("START", (analizar_costos, auditar_latencia)),
        # 2. Fan-in convergente hacia JoinNode
        ((analizar_costos, auditar_latencia), sincronizador),
        # 3. JoinNode pasa un dict con las dos salidas al decisor final
        (sincronizador, arquitecto_decisor)
    ]
)
```

---

## 🤝 Multi-Agente Jerárquico: `AgentTool`

El agente padre conserva la titularidad de la conversación y usa al especialista como herramienta:

```python
from google.adk.agents import Agent
from google.adk.tools import AgentTool

especialista_cripto = Agent(
    name="especialista_cripto",
    description="Analiza suites de cifrado, TLS y funciones hash.",
    instruction="Analiza la propuesta técnica y advierte sobre algoritmos vulnerables."
)

coordinador = Agent(
    name="coordinador_principal",
    instruction="Conversa con el usuario. Usa 'especialista_cripto' cuando surjan dudas de cifrado.",
    tools=[AgentTool(especialista_cripto)]
)
```

---

## 📋 ADK 2.0 Task Delegation con Pydantic

Delegación fuertemente tipada con `mode="task"`:

```python
from pydantic import BaseModel, Field

class AuditReport(BaseModel):
    score: int = Field(description="Calificación de 0 a 100")
    aprobado: bool = Field(description="Aprobado para producción")

auditor = Agent(
    name="auditor",
    mode="task",              # ADK auto-inyecta 'finish_task'
    output_schema=AuditReport, # Salida fuertemente tipada
    description="Audita componentes críticos de software."
)

coordinador = Agent(
    name="coordinador",
    # ADK auto-inyecta 'request_task_auditor'
    sub_agents=[auditor]
)
```

---

## 🏆 Proyecto Capstone: Software Architect Agency

Arquitectura integral multi-agente para evaluación y diseño de software:
- **Analista Funcional:** Desglose de requisitos de negocio.
- **Auditoría Concurrente:**
  - Especialista en Modelado de Datos y Rendimiento.
  - Arquitecto de Ciberseguridad y Cumplimiento Normativo (HIPAA / GDPR).
- **Métricas Compartidas:** Uso de `ToolContext` para calificar el nivel de madurez técnica.
- **Síntesis Ejecutiva (CTO):** Blueprint consolidado y roadmap de despliegue.

*Código listo en `capstone_project/system_architect_agency.py`.*

---

## 📐 Mejores Prácticas de Ingeniería (ADLC)

1. **Gestión de Contexto:** Aísla el historial de los subagentes (`include_contents='none'` cuando corresponda).
2. **Evaluaciones Rigurosas:** Usa datasets dorados con `agents-cli eval run` para prevenir regresiones.
3. **Observabilidad:** Habilita telemetría unificada para auditar tiempos de latencia y llamadas a tools.
4. **Resiliencia Local:** Configura timeouts y reintentos (`RetryConfig`) ante caídas de sockets en servidores locales.

---

## 🚀 ¡Comienza a Construir!

```bash
# 1. Configurar entorno
cp .env.example .env

# 2. Iniciar tu servidor local (ej. Ollama con Qwen 2.5)
ollama run qwen2.5:7b-instruct

# 3. Ejecutar las lecciones
python modules/module_1_single_agent/01_basic_agent.py
python capstone_project/system_architect_agency.py
```

**Google ADK 2.0** te ofrece la arquitectura más limpia y modular para construir la próxima generación de sistemas de IA.

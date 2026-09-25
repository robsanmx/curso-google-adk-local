# Curso Profesional: Google ADK 2.0 y Arquitecturas Multi-Agente Locales

> **Framework:** Google Agent Development Kit (ADK 2.0)  
> **Toolchain de Referencia:** [google/agents-cli](https://github.com/google/agents-cli)  
> **Entorno de Ejecución:** 100% Local (Ollama / LM Studio / MLX)  
> **Lenguaje:** Python >= 3.11  

---

## 🎯 Objetivo del Curso

Capacitar a ingenieros de software, arquitectos de IA y desarrolladores en el diseño, desarrollo, orquestación y despliegue de agentes inteligentes utilizando la especificación **Google ADK 2.0**. El curso abarca la progresión completa: desde un **Single-Agent** con Function Calling hasta **Arquitecturas Multi-Agente Complejas** (Compuestas, Grafos Dirigidos y Delegación Jerárquica Tipada), garantizando privacidad, coste cero de inferencia y baja latencia mediante modelos ejecutados localmente.

---

## 🏗️ Mapa de Contenidos

```text
cursoADK/
├── curso_adk2_completo.ipynb                      # 📓 JUPYTER NOTEBOOK COMPLETO (32 celdas interactivas)
├── config.py                                      # Conector unificado para Ollama, LM Studio y MLX
├── pyproject.toml / requirements.txt              # Dependencias del proyecto
├── .env.example                                   # Plantilla de variables de entorno locales
├── modules/
│   ├── module_1_single_agent/                    # Módulo 1: Fundamentos y Single-Agent
│   │   ├── 01_basic_agent.py                     # LlmAgent, inyección dinámica {state_key}, sesiones
│   │   ├── 02_tools_and_context.py               # FunctionTool, docstrings estrictos, ToolContext
│   │   └── 03_human_confirmation.py             # Human-in-the-Loop y confirmación de herramientas
│   ├── module_2_deterministic_workflows/          # Módulo 2: Orquestación Determinista
│   │   ├── 01_sequential_pipeline.py             # SequentialAgent y paso de estado con output_key
│   │   ├── 02_parallel_fanout.py                 # Concurrencia con ParallelAgent y agregación
│   │   └── 03_loop_refinement.py                 # Bucles de refinamiento y EscalationChecker
│   ├── module_3_graph_workflows_adk2/            # Módulo 3: El nuevo Graph Workflow API de ADK 2.0
│   │   ├── 01_graph_basics.py                    # Nodos, aristas y punto de entrada 'START'
│   │   ├── 02_conditional_routing.py             # Event(route="...") y aristas con fallback
│   │   └── 03_fanout_join_graph.py               # Bifurcación Fan-Out y sincronización JoinNode
│   └── module_4_multi_agent_hierarchical/         # Módulo 4: Multi-Agente Jerárquico Avanzado
│       ├── 01_agent_as_tool.py                   # Patrón AgentTool (invocación sin cesión de control)
│       └── 02_task_delegation_pydantic.py        # mode="task", request_task y finish_task tipados
├── capstone_project/                              # Proyecto Final Integrador
│   └── system_architect_agency.py                # Agencia completa de Arquitectura de Software
└── diapositivas/                                  # Material de Presentación
    ├── slides.html                               # Diapositivas Interactivas Web (HTML5/Tailwind)
    └── slides.md                                 # Diapositivas en Markdown (Marp/Slidev compatible)
```

---

## ⚡ Preparación del Entorno Local

### 1. Requisitos Previos
- **Python >= 3.11**
- Al menos uno de los siguientes servidores locales de inferencia:
  - **Ollama**: [https://ollama.ai](https://ollama.ai) (Recomendado para Mac, Linux y Windows)
  - **LM Studio**: [https://lmstudio.ai](https://lmstudio.ai) (Ideal para interfaces gráficas)
  - **MLX**: `mlx-lm` (Optimizado para Apple Silicon con Metal)

### 2. Modelos Locales Recomendados para Agentes
Para que un modelo local funcione adecuadamente con agentes, requiere capacidades sólidas de **razonamiento y Function Calling (Tool Calling)**:
1. `qwen2.5:7b-instruct` o `qwen2.5:14b-instruct` (Máxima precisión en llamadas a funciones y JSON).
2. `llama3.1:8b-instruct` (Estándar abierto con excelente seguimiento de instrucciones).
3. `mistral-nemo:12b-instruct` (Excelente ventana de contexto de 128k tokens).

Para descargarlos en Ollama:
```bash
ollama run qwen2.5:7b-instruct
```

### 3. Instalación de Dependencias
```bash
# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Configuración del Archivo `.env`
Copia la plantilla y ajústala a tu servidor local:
```bash
cp .env.example .env
```

Contenido típico para Ollama:
```env
LOCAL_LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b-instruct
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 📖 Desglose Teórico y Metodológico de los Módulos

### Módulo 1: Fundamentos de ADK 2.0 y el Ciclo de Vida ADLC
- **Arquitectura de ADK:** Frente a frameworks que mezclan prompts, lógica y orquestación, ADK 2.0 desacopla rigurosamente los componentes:
  - `Agent` / `LlmAgent`: El motor cognitivo.
  - `Tool`: Capacidades ejecutables externas.
  - `Session` & `State`: Memoria y almacén de variables clave-valor.
  - `Runner`: El orquestador que gestiona la cola de eventos asíncronos (`Event`).
- **Prácticas en Tools:**
  - Anotaciones de tipos Python obligatorias.
  - Docstrings detallados (el LLM sólo lee el docstring para planificar su uso).
  - Inyección de `ToolContext` para que la herramienta lea o altere el estado sin acoplarse al prompt.
- **Human-in-the-Loop:** `FunctionTool(require_confirmation=...)` permite interceptar llamadas peligrosas antes de que se ejecuten.

### Módulo 2: Orquestación Determinista de Agentes
- En sistemas de producción locales, **la orquestación no debe dejarse enteramente a la improvisación de un modelo LLM pequeño**:
  - `SequentialAgent`: Encadena pasos predecibles (Analizador -> Diseñador -> Implementador).
  - `ParallelAgent`: Distribuye tareas que no dependen entre sí para aprovechar CPUs multinúcleo o GPUs. Cada subagente debe contar con un `output_key` independiente.
  - `LoopAgent`: Modela ciclos iterativos de mejora continua. Mediante un `EscalationChecker` que emite `EventActions(escalate=True)`, el bucle se detiene en cuanto se satisface el criterio de calidad.

### Módulo 3: El Nuevo Graph Workflow API de ADK 2.0
- La innovación central de Google ADK 2.0 es el paso a **Grafos Dirigidos de Agentes (`Workflow`)**:
  - `START`: Nodo inicial built-in.
  - **Nodos:** Funciones Python, herramientas o agentes LLM (auto-envueltos como nodos).
  - **Aristas Condicionales:** `(nodo_origen, nodo_destino, "nombre_ruta")`. Los nodos retornan `Event(route="nombre_ruta", output=...)`.
  - **Ruta de respaldo:** Si ninguna condición coincide, se activa `'__DEFAULT__'`.
  - **Fan-Out y Fan-In:** Bifurcaciones hacia múltiples nodos y convergencia en `JoinNode`, que entrega un diccionario consolidado `{nombre_nodo: resultado}`.

### Módulo 4: Arquitecturas Multi-Agente Jerárquicas y Tipadas
- **AgentTool:** El coordinador mantiene el control de la conversación y ve al especialista como una herramienta invocable.
- **ADK 2.0 Task Delegation (`mode="task"`):**
  - El coordinador adquiere la herramienta `request_task_{nombre}`.
  - El subagente recibe automáticamente la herramienta `finish_task`.
  - Mediante esquemas Pydantic (`output_schema`), se valida el contrato de datos antes de devolver la respuesta al coordinador, eliminando alucinaciones estructurales.

### Módulo 5: Mejores Prácticas de Ingeniería (Inspiradas en `agents-cli`)
- **ADLC (Agent Development Lifecycle):**
  1. *Scaffold:* Estructura estandarizada con `agent.py`, `tools.py` y `.env`.
  2. *Eval:* Evaluación sistemática con datasets dorados y LLM-as-a-judge (`eval_config.yaml`).
  3. *Observabilidad:* Trazabilidad de cada evento, tool call y tokens consumidos.
  4. *Seguridad:* Barreras de contención, aislamiento de variables sensibles y confirmación previa a mutaciones de estado.

---

## 💻 Ejecución de los Ejemplos

Cada lección es un script autónomo:

```bash
# Módulo 1: Single Agent & Tools
python modules/module_1_single_agent/01_basic_agent.py
python modules/module_1_single_agent/02_tools_and_context.py
python modules/module_1_single_agent/03_human_confirmation.py

# Módulo 2: Orquestación Determinista
python modules/module_2_deterministic_workflows/01_sequential_pipeline.py
python modules/module_2_deterministic_workflows/02_parallel_fanout.py
python modules/module_2_deterministic_workflows/03_loop_refinement.py

# Módulo 3: Graph Workflows en ADK 2.0
python modules/module_3_graph_workflows_adk2/01_graph_basics.py
python modules/module_3_graph_workflows_adk2/02_conditional_routing.py
python modules/module_3_graph_workflows_adk2/03_fanout_join_graph.py

# Módulo 4: Multi-Agente Avanzado y Delegación
python modules/module_4_multi_agent_hierarchical/01_agent_as_tool.py
python modules/module_4_multi_agent_hierarchical/02_task_delegation_pydantic.py

# Proyecto Capstone Completo
python capstone_project/system_architect_agency.py
```

---

## 🖥️ Diapositivas de la Presentación

Se incluyen dos formatos de diapositivas en la carpeta `diapositivas/`:

### 1. Presentación Interactiva Web (`slides.html`)
La presentación cuenta con navegación fluida, diseño responsive, barra de progreso superior, atajos de teclado y modal de índice:
- **Opción A (Recomendada con servidor local):**
  ```bash
  python3 run_slides.py
  ```
  Esto inicia un servidor local y abre automáticamente las diapositivas en tu navegador en `http://localhost:8000/diapositivas/slides.html`.

- **Opción B (Directo en macOS):**
  ```bash
  open diapositivas/slides.html
  ```

**Controles interactivos de navegación:**
- `→` / `Espacio` / `PageDown` : Siguiente diapositiva.
- `←` / `Backspace` / `PageUp` : Diapositiva anterior.
- `M` : Abrir o cerrar el Índice del curso para saltar a cualquier tema.
- `F` : Activar / desactivar el Modo Pantalla Completa para proyecciones.

### 2. Versión en Markdown (`slides.md`)
- Ubicada en [`diapositivas/slides.md`](file:///Users/roberto/proyectods/cursoADK/diapositivas/slides.md).
- Lista para ser exportada a PDF o presentada con herramientas como [Marp](https://marp.app) o Slidev.


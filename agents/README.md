# 🤖 Catálogo de Agentes de Google ADK 2.0 para `adk web`

Este directorio contiene todos los agentes del curso convertidos a paquetes standalone compatibles con **ADK Web UI** (`adk web`).

---

## 🚀 Cómo Iniciar Todos los Agentes en `adk web`

Para iniciar el servidor y acceder a todos los agentes desde un único selector/dropdown en tu navegador:

```bash
# Iniciar ADK Web apuntando al directorio de agentes
.venv/bin/adk web agents --port 8000
```

Abre tu navegador en:
👉 **[http://localhost:8000](http://localhost:8000)**

*(En la esquina superior izquierda de la interfaz podrás alternar entre cualquiera de los 10 agentes disponibles).*

---

## 🎯 Cómo Ejecutar un Agente Individual

También puedes lanzar directamente un agente específico apuntando a su subcarpeta:

```bash
.venv/bin/adk web agents/<nombre_agente> --port 8000
```

Ejemplo:
```bash
.venv/bin/adk web agents/capstone_agency --port 8000
```

---

## 📋 Directorio y Casos de Prueba de los Agentes

| Agente | Tipo | Módulo | Prueba Sugerida en el Chat |
|---|---|---|---|
| **`single_state_agent`** | `LlmAgent` | Módulo 1 | *"¿Cómo configuro una conexión a PostgreSQL con SQLAlchemy usando variables de entorno?"* |
| **`devops_tools_agent`** | `LlmAgent` + Tools | Módulo 1 | *"Revisa el estado del pod auth-service y las métricas de cpu del servidor prod-db-01"* |
| **`hitl_agent`** | `LlmAgent` + HITL | Módulo 1 | *"Por favor reinicia el servicio postgresql de forma forzada"* *(detiene la ejecución y pide aprobación)* |
| **`sequential_agent`** | `SequentialAgent` | Módulo 2 | *"Analiza y refactoriza esta función: `def calc(x): return x*2 if x>0 else 0`"* |
| **`parallel_agent`** | `ParallelAgent` + Agregador | Módulo 2 | *"Audita este Dockerfile y endpoint Express con JWT almacenado en localStorage"* |
| **`loop_agent`** | `LoopAgent` + Escalation | Módulo 2 | *"Optimiza la función de fibonacci recursiva para que tenga complejidad O(n) y type hints"* |
| **`graph_workflow_agent`** | `Workflow` (ADK 2.0 Graph) | Módulo 3 | *"Detectamos una vulnerabilidad de fuga de secrets en los logs de producción"* |
| **`agent_tool_orchestrator`** | `AgentTool` Pattern | Módulo 4 | *"Tech Lead, por favor audita la seguridad de nuestro nuevo servicio de pagos"* |
| **`task_delegation_agent`** | `Agent` (`mode="task"`) | Módulo 4 | *"Release Manager: Solicitamos pase a producción del endpoint de facturación con tokens en logs"* |
| **`capstone_agency`** | Agencia Multi-Agente Completa | Proyecto Final | *"Diseña la arquitectura para una app de telemedicina con videollamadas encriptadas y 50k usuarios"* |

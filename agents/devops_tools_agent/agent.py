"""Agente DevOps con Herramientas y ToolContext (Módulo 1)."""
from __future__ import annotations

import sys
from pathlib import Path

agents_dir = Path(__file__).parent.parent
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

from config import get_local_model
from google.adk.agents.llm_agent import Agent
from google.adk.tools import ToolContext


def consultar_estado_pod(pod_name: str, namespace: str = "default", tool_context: ToolContext | None = None) -> dict:
    """Consulta el estado operativo, reinicios e IP de un pod de Kubernetes.

    Args:
        pod_name: Nombre o prefijo del pod (ej: 'auth-service', 'payment-api').
        namespace: Namespace de Kubernetes (por defecto 'default').
    """
    estado = "CrashLoopBackOff" if "auth" in pod_name.lower() else "Running"
    restarts = 5 if estado == "CrashLoopBackOff" else 0
    return {
        "pod": pod_name,
        "namespace": namespace,
        "status": estado,
        "ready": estado == "Running",
        "restart_count": restarts,
        "node": "k8s-worker-node-02",
        "ip": "10.244.1.45"
    }


def obtener_metricas_servidor(servidor: str) -> dict:
    """Obtiene el consumo de CPU, memoria y disco de un servidor o nodo.

    Args:
        servidor: Identificador del host o nodo (ej: 'prod-db-01', 'k8s-worker-node-02').
    """
    return {
        "host": servidor,
        "cpu_usage_pct": 87.4,
        "mem_usage_pct": 74.2,
        "disk_free_gb": 128.5,
        "load_average_15m": 3.82,
        "alerta": "CPU_HIGH" if 87.4 > 80.0 else "OK"
    }


root_agent = Agent(
    name="devops_tools_agent",
    model=get_local_model(),
    instruction=(
        "Eres un operador de infraestructura y monitorización de Kubernetes. "
        "Utiliza tus herramientas para consultar el estado de pods (`consultar_estado_pod`) "
        "y el consumo de recursos de los servidores (`obtener_metricas_servidor`). "
        "Siempre presenta un diagnóstico claro resumiendo los hallazgos y proponiendo los siguientes pasos."
    ),
    description="Agente DevOps con herramientas para inspeccionar Kubernetes y métricas de servidores.",
    tools=[consultar_estado_pod, obtener_metricas_servidor]
)

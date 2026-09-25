# Agente Human-in-the-Loop (HITL) con Google ADK Web

Este proyecto contiene un agente especializado en DevOps (`devops_agent`) configurado con políticas de seguridad **Human-in-the-Loop** utilizando Google ADK 2.0.

## ¿Por qué ejecutar este agente con `adk web`?

En una celda lineal de Jupyter Notebook, interceptar llamadas a herramientas que requieren confirmación humana exige pausar el bucle, capturar IDs de llamada, simular manualmente eventos de `FunctionResponse(confirmed=True)` y reinyectarlos al Runner.

En entornos de producción o desarrollo interactivo, **ADK Web UI (`adk web`)** ofrece una experiencia nativa:
1. El usuario solicita una acción de alto impacto (por ejemplo: *"Reinicia el servicio postgresql de forma forzada"*).
2. El agente detecta la necesidad de usar la herramienta `reiniciar_servicio`.
3. La política de seguridad `validar_aprobacion` evalúa los argumentos y activa `require_confirmation`.
4. **ADK Web pausa la ejecución y despliega un modal interactivo en pantalla con botones de "Aprobar" (Approve) o "Rechazar" (Reject)**.
5. El operador humano revisa los parámetros y presiona el botón correspondiente.
6. ADK Web despacha la confirmación y el agente finaliza la ejecución de forma segura.

---

## Cómo ejecutar el agente en tu navegador

Abre una terminal en la raíz de este repositorio y ejecuta:

```bash
# Activa el entorno virtual si aún no está activo
source .venv/bin/activate

# Inicia el servidor Web interactivo de Google ADK
adk web hitl_agent --port 8000
```

O directamente con el binario del entorno virtual:
```bash
.venv/bin/adk web hitl_agent --port 8000
```

Abre tu navegador en:
👉 **[http://localhost:8000](http://localhost:8000)**

### Pruebas sugeridas en el chat:

1. **Operación segura (sin confirmación):**
   > *"Reinicia el servicio nginx de forma normal"*
   *Observa cómo se ejecuta inmediatamente.*

2. **Operación crítica (dispara confirmación humana):**
   > *"Por favor reinicia el servicio postgresql de forma forzada"*
   *Observa cómo la interfaz Web detiene la acción y solicita tu aprobación explícita.*

"""
Gestor de Configuración de Modelos Locales para Google ADK 2.0.

Soporta integración fluida con:
- Ollama (nativo con endpoint http://localhost:11434)
- LM Studio (endpoint OpenAI-compatible en http://localhost:1234/v1)
- MLX / mlx-lm server (endpoint OpenAI-compatible en http://localhost:8080/v1)
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno si existe un archivo .env
load_dotenv()

def get_local_model(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.2,
):
    """
    Retorna una instancia de modelo compatible con Google ADK 2.0 para ejecución local.
    
    Utiliza el adaptador LiteLlm de google.adk.models.lite_llm para conectar
    con los servidores locales de Ollama, LM Studio o MLX.
    """
    from google.adk.models.lite_llm import LiteLlm

    provider = (provider or os.getenv("LOCAL_LLM_PROVIDER", "ollama")).lower()
    
    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        target_model = model_name or os.getenv("OLLAMA_MODEL")
        if not target_model:
            try:
                import urllib.request, json
                with urllib.request.urlopen(f"{base_url}/api/tags", timeout=1.5) as r:
                    models = [m["name"] for m in json.loads(r.read().decode()).get("models", [])]
                    for preferred in ["llama3.2:latest", "llama3.2", "llama3.1:8b", "qwen2.5:7b-instruct", "qwen2.5:7b", "mistral-nemo:latest", "qwen3:4b"]:
                        if preferred in models:
                            target_model = preferred
                            break
                    if not target_model and models:
                        target_model = models[0]
            except Exception:
                pass
        target_model = target_model or "llama3.2:latest"
        lite_model_str = f"ollama_chat/{target_model}" if not target_model.startswith("ollama_chat/") else target_model
        
        return LiteLlm(
            model=lite_model_str,
            api_base=base_url,
            temperature=temperature
        )

    elif provider == "lmstudio":
        target_model = model_name or os.getenv("LMSTUDIO_MODEL", "qwen2.5-7b-instruct")
        base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        api_key = os.getenv("LMSTUDIO_API_KEY", "not-needed")
        # LM Studio implementa la API estándar de OpenAI
        lite_model_str = f"openai/{target_model}" if not target_model.startswith("openai/") else target_model

        return LiteLlm(
            model=lite_model_str,
            api_base=base_url,
            api_key=api_key,
            temperature=temperature
        )

    elif provider == "mlx":
        target_model = model_name or os.getenv("MLX_MODEL", "mlx-community/Qwen2.5-7B-Instruct-4bit")
        base_url = os.getenv("MLX_BASE_URL", "http://localhost:8080/v1")
        api_key = os.getenv("MLX_API_KEY", "not-needed")
        lite_model_str = f"openai/{target_model}" if not target_model.startswith("openai/") else target_model

        return LiteLlm(
            model=lite_model_str,
            api_base=base_url,
            api_key=api_key,
            temperature=temperature
        )

    else:
        raise ValueError(
            f"Proveedor '{provider}' no soportado. "
            "Usa 'ollama', 'lmstudio' o 'mlx'."
        )


def print_environment_banner():
    """Imprime un resumen visual del entorno local configurado."""
    provider = os.getenv("LOCAL_LLM_PROVIDER", "ollama")
    print("=" * 65)
    print("   CURSO GOOGLE ADK 2.0 - RUNTIME LOCAL DE AGENTES")
    print("=" * 65)
    print(f" • Proveedor activo: {provider.upper()}")
    if provider == "ollama":
        print(f" • Endpoint: {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}")
        print(f" • Modelo:   {os.getenv('OLLAMA_MODEL', 'qwen2.5:7b-instruct')}")
    elif provider == "lmstudio":
        print(f" • Endpoint: {os.getenv('LMSTUDIO_BASE_URL', 'http://localhost:1234/v1')}")
        print(f" • Modelo:   {os.getenv('LMSTUDIO_MODEL', 'qwen2.5-7b-instruct')}")
    elif provider == "mlx":
        print(f" • Endpoint: {os.getenv('MLX_BASE_URL', 'http://localhost:8080/v1')}")
        print(f" • Modelo:   {os.getenv('MLX_MODEL', 'mlx-community/Qwen2.5-7B-Instruct-4bit')}")
    print("=" * 65 + "\n")

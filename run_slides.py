"""
Servidor local y lanzador de diapositivas para el Curso Google ADK 2.0.

Uso:
    python3 run_slides.py
    
Abre automáticamente las diapositivas interactivas en tu navegador web predeterminado.
"""

import os
import sys
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import socket

PORT = 8000

def encontrar_puerto_disponible(puerto_inicial=8000):
    puerto = puerto_inicial
    while puerto < puerto_inicial + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', puerto)) != 0:
                return puerto
        puerto += 1
    return puerto_inicial

def main():
    directorio_raiz = os.path.dirname(os.path.abspath(__file__))
    os.chdir(directorio_raiz)

    puerto = encontrar_puerto_disponible(PORT)
    url = f"http://localhost:{puerto}/diapositivas/slides.html"

    print("=" * 65)
    print("   LANZADOR DE DIAPOSITIVAS INTERACTIVAS - GOOGLE ADK 2.0")
    print("=" * 65)
    print(f" • Servidor local activo en: {url}")
    print(f" • Atajos de navegación en la presentación:")
    print("     [→] o [Espacio]  : Siguiente diapositiva")
    print("     [←]              : Diapositiva anterior")
    print("     [M]              : Menú de índice de temas")
    print("     [F]              : Modo Pantalla Completa")
    print(" • Presiona Ctrl+C para detener el servidor.")
    print("=" * 65)

    # Abrir navegador automáticamente
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Aviso: Abre manualmente la URL en tu navegador: {url}")

    class ManejadorSilencioso(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass # Silenciar logs de requests para mantener limpia la consola

    server = ThreadingHTTPServer(('127.0.0.1', puerto), ManejadorSilencioso)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor de diapositivas detenido.")
        server.server_close()

if __name__ == "__main__":
    main()

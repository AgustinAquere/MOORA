"""Lanzador de la aplicación.

1. Verifica que estén instalados todos los paquetes de ``requirements.txt`` (con la
   versión pedida) e instala los que falten o estén desactualizados.
2. Inicia Streamlit en un puerto libre y abre el navegador cuando el servidor está listo.

Lo usa «Iniciar MOORA.bat» (doble clic). También se puede ejecutar con:  python launcher.py
Solo usa la biblioteca estándar, para poder correr aunque falten dependencias.
"""

from __future__ import annotations

import importlib
import os
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIREMENTS = ROOT / "requirements.txt"
MIN_PYTHON = (3, 10)
FIRST_PORT = 8501
STARTUP_TIMEOUT = 90  # segundos (la primera ejecución puede tardar más)


# ---------------------------------------------------------------------------
# Dependencias
# ---------------------------------------------------------------------------

def read_requirements(path: Path = REQUIREMENTS) -> list[str]:
    """Líneas de requisitos, sin comentarios, líneas vacías ni opciones de pip (``-r``, ``--index-url``...)."""
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line and not line.startswith("-"):
            lines.append(line)
    return lines


def missing_requirements(path: Path = REQUIREMENTS) -> list[str]:
    """Requisitos no instalados o cuya versión instalada no cumple lo pedido.

    Cada elemento es la línea del requisito con una aclaración, p. ej. «plotly>=6.0 (instalado 5.9)».
    """
    lines = read_requirements(path)
    try:
        from packaging.requirements import InvalidRequirement, Requirement
    except ImportError:
        # «packaging» llega como dependencia de Streamlit: si no está, falta casi todo.
        return [f"{line} (no se pudo verificar)" for line in lines]

    missing = []
    for line in lines:
        try:
            req = Requirement(line)
        except InvalidRequirement:
            missing.append(f"{line} (requisito inválido)")
            continue
        if req.marker is not None and not req.marker.evaluate():
            continue  # no aplica a esta plataforma o versión de Python
        try:
            installed = version(req.name)
        except PackageNotFoundError:
            missing.append(f"{line} (no instalado)")
            continue
        if req.specifier and not req.specifier.contains(installed, prereleases=True):
            missing.append(f"{line} (instalado {installed})")
    return missing


def ensure_requirements(path: Path = REQUIREMENTS) -> bool:
    """Instala con pip lo que falte. Devuelve ``True`` si al final está todo instalado."""
    print("Verificando dependencias...")
    missing = missing_requirements(path)
    if not missing:
        print("  Todas las dependencias están instaladas.")
        return True
    print("  Faltan o están desactualizadas:")
    for item in missing:
        print(f"    - {item}")
    print("  Instalando (requiere conexión a internet)...\n")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(path)], cwd=ROOT)
    importlib.invalidate_caches()
    still = missing_requirements(path)
    if result.returncode != 0 or still:
        print("\nNo se pudieron instalar todas las dependencias:")
        for item in still:
            print(f"    - {item}")
        print("Revise la conexión a internet y los mensajes de pip de arriba.")
        return False
    print("\n  Dependencias instaladas correctamente.")
    return True


# ---------------------------------------------------------------------------
# Servidor
# ---------------------------------------------------------------------------


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def free_port(start: int) -> int:
    port = start
    while port_in_use(port):
        port += 1
    return port


def server_ready(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1) as resp:
            return resp.status == 200
    except OSError:
        return False


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)
    if sys.version_info < MIN_PYTHON:
        print(f"Se necesita Python {'.'.join(map(str, MIN_PYTHON))} o superior "
              f"(este es {sys.version.split()[0]}). Instale una versión más nueva y borre la carpeta .venv.")
        return 1
    if not ensure_requirements():
        return 1
    print()

    port = free_port(FIRST_PORT)
    url = f"http://localhost:{port}"
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
        "--server.port", str(port),
        "--server.address", "localhost",
        "--server.headless", "true",  # el navegador lo abre este script, cuando el servidor ya responde
        "--browser.gatherUsageStats", "false",
    ]
    print("=" * 64)
    print("  MOORA - Decisión multicriterio")
    print(f"  Iniciando la aplicación en {url} ...")
    print("  Para cerrar la aplicación, cierre esta ventana.")
    print("=" * 64)

    proc = subprocess.Popen(cmd, cwd=ROOT)
    try:
        deadline = time.monotonic() + STARTUP_TIMEOUT
        while not server_ready(port):
            if proc.poll() is not None:
                print("\nEl servidor se cerró inesperadamente. Revise los mensajes de arriba.")
                return 1
            if time.monotonic() > deadline:
                print(f"\nEl servidor no respondió en {STARTUP_TIMEOUT} s. Abra {url} manualmente.")
                break
            time.sleep(0.5)
        else:
            print(f"\nAplicación lista: {url}")
            if not os.environ.get("MOORA_NO_BROWSER"):
                webbrowser.open(url)
        return proc.wait()
    except KeyboardInterrupt:
        return 0
    finally:
        if proc.poll() is None:
            proc.terminate()


if __name__ == "__main__":
    sys.exit(main())

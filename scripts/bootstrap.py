#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_MINORS = (13, 12, 11, 10)


class BootstrapError(RuntimeError):
    pass


def log(message: str) -> None:
    print(message, flush=True)


def format_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def run(
    command: list[str],
    *,
    check: bool = True,
    capture_output: bool = False,
    cwd: Path = PROJECT_ROOT,
) -> subprocess.CompletedProcess[str]:
    log(f"$ {format_command(command)}")
    return subprocess.run(
        command,
        cwd=cwd,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def unique_commands(commands: list[list[str]]) -> list[list[str]]:
    seen = set()
    unique = []
    for command in commands:
        key = tuple(command)
        if key in seen:
            continue
        seen.add(key)
        unique.append(command)
    return unique


def candidate_commands(cli_python: str | None) -> list[list[str]]:
    if cli_python:
        return [shlex.split(cli_python)]

    commands: list[list[str]] = []
    env_python = os.environ.get("ROBOTAXI_PYTHON")
    if env_python:
        commands.append(shlex.split(env_python))

    for minor in SUPPORTED_MINORS:
        commands.append([f"python3.{minor}"])

    commands.extend(
        [
            ["python3"],
            ["python"],
        ]
    )

    if shutil.which("py"):
        for minor in SUPPORTED_MINORS:
            commands.append(["py", f"-3.{minor}"])
        commands.append(["py", "-3"])

    return unique_commands(commands)


def probe_python(command: list[str]) -> dict | None:
    probe = (
        "import json, platform, sys; "
        "print(json.dumps({"
        "'executable': sys.executable, "
        "'major': sys.version_info.major, "
        "'minor': sys.version_info.minor, "
        "'micro': sys.version_info.micro, "
        "'platform': platform.system()"
        "}))"
    )

    try:
        result = subprocess.run(
            command + ["-c", probe],
            cwd=PROJECT_ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None

    data = json.loads(result.stdout.strip())
    data["command"] = command
    return data


def choose_python(cli_python: str | None) -> dict:
    discovered = []
    for command in candidate_commands(cli_python):
        info = probe_python(command)
        if info is not None:
            discovered.append(info)

    if not discovered:
        raise BootstrapError("No se encontró ninguna instalación utilizable de Python.")

    for minor in SUPPORTED_MINORS:
        for info in discovered:
            if info["major"] == 3 and info["minor"] == minor:
                return info

    return discovered[0]


def venv_dir(python_info: dict) -> Path:
    suffix = f"py{python_info['major']}{python_info['minor']}"
    return PROJECT_ROOT / f".venv-{suffix}"


def venv_python_path(directory: Path) -> Path:
    if platform.system() == "Windows":
        return directory / "Scripts" / "python.exe"
    return directory / "bin" / "python"


def ensure_venv(python_info: dict) -> Path:
    directory = venv_dir(python_info)
    python_executable = venv_python_path(directory)
    if python_executable.exists():
        return python_executable

    command = python_info["command"] + ["-m", "venv"]
    if platform.system() == "Linux":
        command.append("--system-site-packages")
    command.append(str(directory))
    run(command)
    return python_executable


def requirements_file() -> Path:
    for filename in ("requirements.txt", "requeriments.txt"):
        path = PROJECT_ROOT / filename
        if path.exists():
            return path
    raise BootstrapError("No se encontró requirements.txt ni requeriments.txt.")


def runtime_status(python_executable: Path) -> dict:
    script = """
import json
import sys

def module_available(name):
    try:
        __import__(name)
        return True
    except Exception:
        return False

status = {
    "python": sys.executable,
    "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    "tkinter": module_available("tkinter"),
    "pygame": module_available("pygame"),
}
print(json.dumps(status))
"""
    env = os.environ.copy()
    env["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

    result = subprocess.run(
        [str(python_executable), "-c", script],
        cwd=PROJECT_ROOT,
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise BootstrapError("No se pudo leer el estado del entorno Python.")
    return json.loads(lines[-1])


def gui_status() -> tuple[bool, str]:
    system = platform.system()

    if system == "Windows":
        return True, "Entorno grafico asumido en Windows."

    if system == "Darwin":
        if os.environ.get("SSH_CONNECTION") and not os.environ.get("DISPLAY"):
            return False, "Sesión SSH sin reenvío gráfico detectada en macOS."
        return True, "Entorno grafico disponible en macOS."

    if system == "Linux":
        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or os.environ.get("MIR_SOCKET"):
            return True, "Entorno grafico detectado en Linux."
        return False, "No se detectó DISPLAY, WAYLAND_DISPLAY ni MIR_SOCKET."

    return True, f"No hay validación específica de GUI para {system}."


def linux_package_manager() -> tuple[list[str], dict[str, list[str]]] | tuple[None, None]:
    if shutil.which("dnf"):
        return ["sudo", "dnf", "install", "-y"], {
            "tkinter": ["python3-tkinter"],
            "pygame": ["python3-pygame"],
        }
    if shutil.which("apt-get"):
        return ["sudo", "apt-get", "install", "-y"], {
            "tkinter": ["python3-tk"],
            "pygame": ["python3-pygame"],
        }
    if shutil.which("pacman"):
        return ["sudo", "pacman", "-Sy", "--noconfirm"], {
            "tkinter": ["tk"],
            "pygame": ["python-pygame"],
        }
    return None, None


def install_linux_runtime_packages(python_executable: Path) -> None:
    status = runtime_status(python_executable)
    if status["tkinter"] and status["pygame"]:
        return

    install_prefix, package_map = linux_package_manager()
    if install_prefix is None or package_map is None:
        raise BootstrapError(
            "No se pudo detectar un gestor de paquetes compatible para instalar tkinter/pygame."
        )

    packages: list[str] = []
    if not status["tkinter"]:
        packages.extend(package_map["tkinter"])
    if not status["pygame"]:
        packages.extend(package_map["pygame"])

    if packages:
        run(install_prefix + packages)


def install_macos_runtime_packages(python_info: dict, python_executable: Path) -> None:
    status = runtime_status(python_executable)
    if status["tkinter"] and status["pygame"]:
        return

    if status["tkinter"]:
        return

    if not shutil.which("brew"):
        raise BootstrapError(
            "tkinter no está disponible en macOS y no se encontró Homebrew. "
            "Instala Python desde python.org o instala Homebrew y vuelve a ejecutar `setup`."
        )

    formulae = [
        f"python-tk@{python_info['major']}.{python_info['minor']}",
        "python-tk",
    ]

    for formula in formulae:
        try:
            run(["brew", "install", formula])
            return
        except subprocess.CalledProcessError:
            log(f"Aviso: Homebrew no pudo instalar {formula}. Se intenta otra opción.")

    raise BootstrapError(
        "No se pudo instalar tkinter automáticamente en macOS. "
        "Prueba con el instalador oficial de Python de python.org o revisa tu instalación de Homebrew."
    )


def install_python_dependencies(python_executable: Path) -> None:
    status = runtime_status(python_executable)
    if status["pygame"]:
        log("pygame ya está disponible en el entorno. Se omite la instalación por pip.")
        return

    run([str(python_executable), "-m", "ensurepip", "--upgrade"])
    try:
        run([str(python_executable), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    except subprocess.CalledProcessError:
        log("Aviso: no se pudieron actualizar pip/setuptools/wheel. Se continúa con lo disponible.")

    try:
        run([str(python_executable), "-m", "pip", "install", "-r", str(requirements_file())])
    except subprocess.CalledProcessError as error:
        status = runtime_status(python_executable)
        if status["pygame"]:
            log("Aviso: pip falló, pero pygame ya está disponible. Se continúa.")
            return

        if platform.system() == "Darwin":
            log("La instalación por pip falló en macOS. Se validarán dependencias del sistema.")
            return

        if platform.system() != "Linux":
            raise BootstrapError("Falló la instalación de dependencias con pip.") from error

        log("La instalación por pip falló. Intentando dependencias del sistema para pygame/tkinter...")
        install_linux_runtime_packages(python_executable)

        try:
            run([str(python_executable), "-m", "pip", "install", "-r", str(requirements_file())])
        except subprocess.CalledProcessError:
            status = runtime_status(python_executable)
            if not status["pygame"]:
                raise BootstrapError(
                    "pygame sigue sin estar disponible después de intentar la instalación automática."
                ) from error


def validate_runtime(python_executable: Path) -> None:
    status = runtime_status(python_executable)
    missing = [name for name in ("tkinter", "pygame") if not status[name]]
    if not missing:
        return

    joined = ", ".join(missing)
    raise BootstrapError(
        f"El entorno todavía no está listo. Faltan módulos: {joined}. "
        "Ejecuta `make doctor` o revisa la salida de `scripts/bootstrap.py doctor`."
    )


def ensure_ready(cli_python: str | None) -> tuple[dict, Path]:
    python_info = choose_python(cli_python)
    python_executable = ensure_venv(python_info)
    install_python_dependencies(python_executable)
    if platform.system() == "Linux":
        install_linux_runtime_packages(python_executable)
    if platform.system() == "Darwin":
        install_macos_runtime_packages(python_info, python_executable)
    validate_runtime(python_executable)
    return python_info, python_executable


def command_doctor(cli_python: str | None) -> int:
    python_info = choose_python(cli_python)
    python_executable = ensure_venv(python_info)
    status = runtime_status(python_executable)
    gui_ok, gui_message = gui_status()

    log("Diagnóstico del entorno")
    log(f"- Sistema operativo: {platform.system()} {platform.release()}")
    log(f"- Python base: {python_info['executable']} ({python_info['major']}.{python_info['minor']}.{python_info['micro']})")
    log(f"- Python del entorno: {status['python']}")
    log(f"- tkinter disponible: {'si' if status['tkinter'] else 'no'}")
    log(f"- pygame disponible: {'si' if status['pygame'] else 'no'}")
    log(f"- GUI disponible: {'si' if gui_ok else 'no'}")
    log(f"- Detalle GUI: {gui_message}")
    log(f"- Archivo de dependencias: {requirements_file().name}")

    return 0 if status["tkinter"] and status["pygame"] and gui_ok else 1


def command_setup(cli_python: str | None) -> int:
    python_info, python_executable = ensure_ready(cli_python)
    log(
        f"Entorno listo con Python {python_info['major']}.{python_info['minor']} en {python_executable}"
    )
    return 0


def command_run(cli_python: str | None) -> int:
    _, python_executable = ensure_ready(cli_python)
    gui_ok, gui_message = gui_status()
    if not gui_ok:
        raise BootstrapError(
            "La aplicación requiere interfaz gráfica. "
            f"Motivo detectado: {gui_message}"
        )
    run([str(python_executable), "main.py"])
    return 0


def command_test(cli_python: str | None) -> int:
    _, python_executable = ensure_ready(cli_python)
    run(
        [
            str(python_executable),
            "-m",
            "compileall",
            "main.py",
            "application",
            "mundo",
            "algoritmosBusqueda",
            "tests",
            "ui",
        ]
    )
    run([str(python_executable), "tests/test_grid.py"])
    run([str(python_executable), "tests/test_bfs.py"])
    return 0


def command_clean() -> int:
    for path in PROJECT_ROOT.glob(".venv-py*"):
        if path.is_dir():
            log(f"Eliminando {path.name}")
            shutil.rmtree(path)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Automatiza la instalación, validación y ejecución de robotaxi-zoox."
    )
    parser.add_argument(
        "command",
        choices=("doctor", "setup", "run", "test", "clean"),
        help="Acción a ejecutar.",
    )
    parser.add_argument(
        "--python",
        dest="python_command",
        help="Comando de Python a usar, por ejemplo: --python 'python3.13'",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if args.command == "doctor":
            return command_doctor(args.python_command)
        if args.command == "setup":
            return command_setup(args.python_command)
        if args.command == "run":
            return command_run(args.python_command)
        if args.command == "test":
            return command_test(args.python_command)
        if args.command == "clean":
            return command_clean()
    except KeyboardInterrupt:
        log("Interrumpido por el usuario.")
        return 130
    except BootstrapError as error:
        log(f"ERROR: {error}")
        return 1
    except subprocess.CalledProcessError as error:
        log(f"ERROR: Falló el comando: {format_command(error.cmd)}")
        return error.returncode or 1

    return 1


if __name__ == "__main__":
    sys.exit(main())

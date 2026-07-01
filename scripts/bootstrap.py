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
    """Indica un fallo controlado al preparar o validar el entorno.

    Example:
        >>> raise BootstrapError("Entorno incompleto")
        Traceback (most recent call last):
        ...
        BootstrapError: Entorno incompleto
    """


def log(message: str) -> None:
    """Imprime un mensaje y fuerza su escritura inmediata.

    Args:
        message (str): Texto que se enviará a la salida estándar.

    Returns:
        None.

    Example:
        >>> log("Entorno listo")
        Entorno listo
    """
    print(message, flush=True)


def format_command(command: list[str]) -> str:
    """Formatea un comando para mostrarlo de forma segura en la terminal.

    Args:
        command (list[str]): Programa y argumentos.

    Returns:
        str: Comando con cada componente escapado para la shell.

    Example:
        >>> format_command(["python", "archivo con espacios.py"])
        "python 'archivo con espacios.py'"
    """
    return " ".join(shlex.quote(part) for part in command)


def run(
    command: list[str],
    *,
    check: bool = True,
    capture_output: bool = False,
    cwd: Path = PROJECT_ROOT,
) -> subprocess.CompletedProcess[str]:
    """Muestra y ejecuta un proceso externo.

    Args:
        command (list[str]): Programa y argumentos que se ejecutarán.
        check (bool): Si es ``True``, falla ante un código distinto de cero.
        capture_output (bool): Si se capturan las salidas estándar y de error.
        cwd (Path): Directorio de trabajo del proceso.

    Returns:
        subprocess.CompletedProcess[str]: Resultado del proceso.

    Raises:
        subprocess.CalledProcessError: Si ``check`` está activo y el proceso
            termina con error.

    Example:
        >>> run(["python", "--version"], capture_output=True).returncode
        0
    """
    log(f"$ {format_command(command)}")
    return subprocess.run(
        command,
        cwd=cwd,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def unique_commands(commands: list[list[str]]) -> list[list[str]]:
    """Elimina comandos duplicados conservando el orden.

    Args:
        commands (list[list[str]]): Comandos candidatos.

    Returns:
        list[list[str]]: Comandos únicos.

    Example:
        >>> unique_commands([["python"], ["python"], ["python3"]])
        [['python'], ['python3']]
    """
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
    """Construye la lista de intérpretes de Python que se deben probar.

    Args:
        cli_python (str | None): Comando indicado explícitamente por el usuario.

    Returns:
        list[list[str]]: Comandos candidatos sin duplicados.

    Example:
        >>> candidate_commands("python3.12")
        [['python3.12']]
    """
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
    """Consulta la versión y plataforma de un intérprete.

    Args:
        command (list[str]): Comando base del intérprete.

    Returns:
        dict | None: Metadatos del intérprete o ``None`` si no es utilizable.

    Example:
        >>> info = probe_python([sys.executable])
        >>> info["major"] == sys.version_info.major
        True
    """
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
    """Selecciona el intérprete compatible de mayor preferencia.

    Args:
        cli_python (str | None): Comando solicitado explícitamente.

    Returns:
        dict: Metadatos del intérprete elegido.

    Raises:
        BootstrapError: Si no se encuentra ningún intérprete utilizable.

    Example:
        >>> choose_python(sys.executable)["major"]
        3
    """
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
    """Calcula el directorio del entorno virtual para una versión.

    Args:
        python_info (dict): Metadatos con las claves ``major`` y ``minor``.

    Returns:
        Path: Ruta del entorno virtual versionado.

    Example:
        >>> venv_dir({"major": 3, "minor": 12}).name
        '.venv-py312'
    """
    suffix = f"py{python_info['major']}{python_info['minor']}"
    return PROJECT_ROOT / f".venv-{suffix}"


def venv_python_path(directory: Path) -> Path:
    """Obtiene el ejecutable de Python dentro de un entorno virtual.

    Args:
        directory (Path): Directorio raíz del entorno.

    Returns:
        Path: Ruta del ejecutable según el sistema operativo.

    Example:
        >>> venv_python_path(Path(".venv")).name in {"python", "python.exe"}
        True
    """
    if platform.system() == "Windows":
        return directory / "Scripts" / "python.exe"
    return directory / "bin" / "python"


def ensure_venv(python_info: dict) -> Path:
    """Crea el entorno virtual si todavía no existe.

    Args:
        python_info (dict): Metadatos y comando del intérprete base.

    Returns:
        Path: Ejecutable Python del entorno virtual.

    Raises:
        subprocess.CalledProcessError: Si falla la creación.

    Example:
        >>> executable = ensure_venv(info)  # doctest: +SKIP
        >>> executable.exists()  # doctest: +SKIP
        True
    """
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
    """Localiza el archivo de dependencias del proyecto.

    Returns:
        Path: Primer archivo de requisitos existente.

    Raises:
        BootstrapError: Si no existe ningún nombre reconocido.

    Example:
        >>> requirements_file().name
        'requirements.txt'
    """
    for filename in ("requirements.txt", "requeriments.txt"):
        path = PROJECT_ROOT / filename
        if path.exists():
            return path
    raise BootstrapError("No se encontró requirements.txt ni requeriments.txt.")


def runtime_status(python_executable: Path) -> dict:
    """Comprueba Python, Tkinter y Pygame dentro de un entorno.

    Args:
        python_executable (Path): Intérprete que realizará la comprobación.

    Returns:
        dict: Versión, ejecutable y disponibilidad de módulos.

    Raises:
        BootstrapError: Si el proceso no produce una respuesta válida.

    Example:
        >>> runtime_status(Path(sys.executable))["python"]  # doctest: +ELLIPSIS
        '...python...'
    """
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
    """Detecta si el sistema parece disponer de una sesión gráfica.

    Returns:
        tuple[bool, str]: Disponibilidad estimada y explicación.

    Example:
        >>> disponible, detalle = gui_status()
        >>> isinstance(disponible, bool) and isinstance(detalle, str)
        True
    """
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
    """Detecta un gestor Linux y los paquetes de interfaz requeridos.

    Returns:
        tuple[list[str], dict[str, list[str]]] | tuple[None, None]: Prefijo de
        instalación y paquetes, o dos valores nulos si no hay compatibilidad.

    Example:
        >>> resultado = linux_package_manager()
        >>> len(resultado)
        2
    """
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
    """Instala en Linux los paquetes faltantes de Tkinter o Pygame.

    Args:
        python_executable (Path): Intérprete cuyo entorno se valida.

    Returns:
        None.

    Raises:
        BootstrapError: Si falta un módulo y no hay gestor compatible.

    Example:
        >>> install_linux_runtime_packages(Path(sys.executable))  # doctest: +SKIP
    """
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
    """Instala Tkinter mediante Homebrew cuando falta en macOS.

    Args:
        python_info (dict): Versión del intérprete base.
        python_executable (Path): Intérprete del entorno virtual.

    Returns:
        None.

    Raises:
        BootstrapError: Si Tkinter no puede instalarse automáticamente.

    Example:
        >>> install_macos_runtime_packages(info, executable)  # doctest: +SKIP
    """
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
    """Instala las dependencias Python y aplica alternativas del sistema.

    Args:
        python_executable (Path): Intérprete del entorno virtual.

    Returns:
        None.

    Raises:
        BootstrapError: Si Pygame sigue sin estar disponible.

    Example:
        >>> install_python_dependencies(executable)  # doctest: +SKIP
    """
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
    """Verifica que Tkinter y Pygame estén disponibles.

    Args:
        python_executable (Path): Intérprete que se comprobará.

    Returns:
        None.

    Raises:
        BootstrapError: Si falta alguno de los módulos requeridos.

    Example:
        >>> validate_runtime(Path(sys.executable))  # doctest: +SKIP
    """
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
    """Prepara y valida un entorno completo para la aplicación.

    Args:
        cli_python (str | None): Intérprete solicitado por el usuario.

    Returns:
        tuple[dict, Path]: Metadatos del Python base y ejecutable del entorno.

    Example:
        >>> info, executable = ensure_ready(None)  # doctest: +SKIP
    """
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
    """Ejecuta el diagnóstico de dependencias y sesión gráfica.

    Args:
        cli_python (str | None): Intérprete solicitado.

    Returns:
        int: 0 si todo está disponible; 1 si falta algún requisito.

    Example:
        >>> command_doctor(sys.executable) in {0, 1}
        True
    """
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
    """Prepara el entorno de ejecución.

    Args:
        cli_python (str | None): Intérprete solicitado.

    Returns:
        int: 0 cuando la preparación finaliza correctamente.

    Example:
        >>> command_setup(None)  # doctest: +SKIP
        0
    """
    python_info, python_executable = ensure_ready(cli_python)
    log(
        f"Entorno listo con Python {python_info['major']}.{python_info['minor']} en {python_executable}"
    )
    return 0


def command_run(cli_python: str | None) -> int:
    """Prepara el entorno y abre la aplicación gráfica.

    Args:
        cli_python (str | None): Intérprete solicitado.

    Returns:
        int: 0 cuando la aplicación termina correctamente.

    Raises:
        BootstrapError: Si no se detecta una sesión gráfica.

    Example:
        >>> command_run(None)  # doctest: +SKIP
        0
    """
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
    """Compila los módulos y ejecuta las pruebas principales.

    Args:
        cli_python (str | None): Intérprete solicitado.

    Returns:
        int: 0 si todas las comprobaciones finalizan correctamente.

    Example:
        >>> command_test(None)  # doctest: +SKIP
        0
    """
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
    """Elimina los entornos virtuales versionados del proyecto.

    Returns:
        int: 0 después de completar la limpieza.

    Example:
        >>> command_clean()  # doctest: +SKIP
        0
    """
    for path in PROJECT_ROOT.glob(".venv-py*"):
        if path.is_dir():
            log(f"Eliminando {path.name}")
            shutil.rmtree(path)
    return 0


def parse_args() -> argparse.Namespace:
    """Analiza la acción y el intérprete recibidos por línea de comandos.

    Returns:
        argparse.Namespace: Argumentos ``command`` y ``python_command``.

    Example:
        >>> args = parse_args()  # doctest: +SKIP
        >>> args.command in {"doctor", "setup", "run", "test", "clean"}  # doctest: +SKIP
        True
    """
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
    """Despacha el subcomando solicitado y normaliza los errores.

    Returns:
        int: Código de salida; 0 indica éxito.

    Example:
        >>> main()  # doctest: +SKIP
        0
    """
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

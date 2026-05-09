# robotaxi-zoox
Proyecto del curso "Inteligencia artificial" el cual consta de lo siguiente: El objetivo de este proyecto es utilizar algoritmos de búsqueda para ayudar al vehículo inteligente a ubicar a todos los pasajeros y luego encontrar un camino hasta el destino. Para efectos de la simulación, se supondrá que todos los pasajeros se dirigen a un mismo punto. 

## Ejecucion automatica

El proyecto incluye automatizacion para preparar el entorno, validar dependencias y ejecutar la aplicacion con validaciones previas. La meta no es “prometer cero errores” en cualquier maquina del mundo, sino detectar antes los problemas previsibles y decir exactamente que falta.

### Una sola instruccion

- Unix, Linux, macOS o Git Bash:

```bash
make run
```

- Alternativa sin `make`:

```bash
bash scripts/run.sh
```

- Windows sin Bash:

```bash
launchers\windows\run.bat
```

- macOS con Finder o Terminal:

```bash
./launchers/macos/run.command
```

## Comandos disponibles

```bash
make doctor
make setup
make run
make test
make clean
```

En Windows tambien existen:

```bat
launchers\windows\doctor.bat
launchers\windows\setup.bat
launchers\windows\run.bat
launchers\windows\test.bat
```

En macOS tambien existen:

```bash
./launchers/macos/doctor.command
./launchers/macos/setup.command
./launchers/macos/run.command
./launchers/macos/test.command
```

## Que hace la automatizacion

- detecta una version utilizable de Python
- crea un entorno virtual separado por version
- instala `pygame`
- valida que `tkinter` y `pygame` esten disponibles
- valida si hay entorno grafico antes de ejecutar la interfaz
- en Linux intenta instalar dependencias del sistema si `pip` falla con `pygame`

## Alcance real de la automatizacion

Lo que si cubre bien:

- maquinas con Python instalado
- Windows con `py` o `python`
- Linux con `dnf`, `apt-get` o `pacman`
- macOS con `python3` y, si hace falta, Homebrew para completar `tkinter`
- equipos con entorno grafico disponible

Lo que no se puede garantizar al 100% solo desde el codigo fuente:

- maquinas sin permisos de administrador cuando falta `tkinter` o `pygame`
- equipos sin internet y sin paquetes del sistema disponibles
- servidores o sesiones SSH sin entorno grafico
- instalaciones de Python dañadas o no registradas correctamente

Si en algun momento quieres una experiencia realmente cerrada y de menor riesgo para terceros, el siguiente paso no es mas Bash sino empaquetar binarios por sistema operativo.

## Estructura relevante

```text
robotaxi-zoox/
  Makefile
  scripts/
    bootstrap.py
    doctor.sh
    setup.sh
    run.sh
    test.sh
  launchers/
    README.md
    windows/
      doctor.bat
      setup.bat
      run.bat
      test.bat
    macos/
      doctor.command
      setup.command
      run.command
      test.command
  application/
  mundo/
    io/
    models/
  algoritmosBusqueda/
  tests/
  mapas/
    test/
```

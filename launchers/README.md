# Launchers por plataforma

Este directorio agrupa los wrappers de ejecución para no dejar archivos sueltos en la raíz.

## Estructura

```text
launchers/
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
```

## Uso

- Windows:
  `launchers\windows\run.bat`

- macOS:
  `./launchers/macos/run.command`

Los scripts delegan toda la lógica real a `scripts/bootstrap.py`.

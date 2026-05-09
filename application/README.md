# Arquitectura de `application`

Este paquete agrupa el flujo principal del programa para que `main.py` quede limpio.

## Estructura

```text
application/
  __init__.py
  README.md
  config.py
  carga.py
  ejecucion.py
  runner.py
```

## Responsabilidad de cada archivo

- `config.py`
  Define constantes globales como el tamaño de ventana, el título y el mapeo entre nombres de algoritmos y modos internos.

- `carga.py`
  Se encarga de seleccionar el archivo del mapa y construir el `Grid`.

- `ejecucion.py`
  Ejecuta el algoritmo seleccionado y muestra el resultado por consola.

- `runner.py`
  Orquesta el flujo completo:
  1. cargar mapa
  2. mostrar estado inicial
  3. seleccionar algoritmo
  4. ejecutar búsqueda
  5. mostrar animación y reporte

## Punto de entrada real

Aunque `main.py` es el entrypoint del proyecto, la lógica principal vive en:

```python
from application.runner import main
```

## Orden recomendado de lectura

Si quieres entender el flujo del programa, lee en este orden:

1. `runner.py`
2. `ejecucion.py`
3. `carga.py`
4. `config.py`

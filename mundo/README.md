# Arquitectura de `mundo`

Este paquete concentra el modelo del problema y la carga del mapa.

## Estructura

```text
mundo/
  __init__.py
  README.md
  models/
    grid.py
    node.py
  io/
    map_loader.py
```

## Que archivo mirar primero

- `models/node.py`
  Define el estado de busqueda: posicion, pasajeros recogidos, padre, costo y heuristica.

- `models/grid.py`
  Define el entorno: tipos de celda, costo de movimiento, transitabilidad y generacion de vecinos.

- `io/map_loader.py`
  Carga el mapa desde los archivos `.txt`.

## API publica

El resto del proyecto deberia importar desde `mundo`:

```python
from mundo import Grid, Node, leer_mapa
```

Asi los modulos externos no dependen de la estructura interna del paquete.

from mundo import Node

from algoritmosBusqueda.informada.wrapper import busqueda_informada
from algoritmosBusqueda.noinformada.wrapper import busqueda_no_informada

from .config import ALGORITHM_CONFIG


def ejecutar_algoritmo(nombre, grid):
    tipo_busqueda, modo = ALGORITHM_CONFIG[nombre]

    if tipo_busqueda == "informada":
        return busqueda_informada(grid, grid.inicio, grid.destino, grid.pasajeros, modo)

    pasajeros = frozenset(grid.pasajeros)
    nodo_inicial = Node(posicion=grid.inicio, pasajeros_recogidos=frozenset())
    return busqueda_no_informada(grid, nodo_inicial, pasajeros, modo)


def imprimir_resultado(resultado):
    tiempo_busqueda_ms = resultado.get("tiempo_busqueda_ms", resultado.get("tiempo"))
    print(f"✅ Solución encontrada. Costo: {resultado['costo']}")
    print(f"Pasos: {len(resultado['camino'])}")
    print(f"camino: {resultado['camino']}")
    print(f"nodos expandidos: {resultado['nodos_expandidos']}")
    print(f"profundidad: {resultado['profundidad']}")
    if tiempo_busqueda_ms is not None:
        print(f"tiempo de búsqueda: {tiempo_busqueda_ms} ms")
    if "heuristica" in resultado:
        print(f"heuristica: {resultado['heuristica']}")

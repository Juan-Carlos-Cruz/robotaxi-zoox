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
    print(f"✅ Solución encontrada. Costo: {resultado['costo']}")
    print(f"Pasos: {len(resultado['camino'])}")
    print(f"camino: {resultado['camino']}")
    print(f"nodos expandidos: {resultado['nodos_expandidos']}")
    print(f"profundidad: {resultado['profundidad']}")

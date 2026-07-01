from mundo import Node

from algoritmosBusqueda.informada.wrapper import busqueda_informada
from algoritmosBusqueda.noinformada.wrapper import busqueda_no_informada

from .config import ALGORITHM_CONFIG


def ejecutar_algoritmo(nombre, grid):
    """Ejecuta el algoritmo configurado sobre una cuadrícula.

    Args:
        nombre (str): Clave registrada en ``ALGORITHM_CONFIG``.
        grid (Grid): Mapa con inicio, destino y pasajeros identificados.

    Returns:
        dict[str, object] | None: Resultado de la búsqueda o ``None`` si no
        existe solución.

    Raises:
        KeyError: Si ``nombre`` no está registrado en la configuración.

    Example:
        >>> from mundo import Grid
        >>> ejecutar_algoritmo("amplitud", Grid([[2, 5]]))["costo"]
        1
    """
    tipo_busqueda, modo = ALGORITHM_CONFIG[nombre]

    if tipo_busqueda == "informada":
        return busqueda_informada(grid, grid.inicio, grid.destino, grid.pasajeros, modo)

    pasajeros = frozenset(grid.pasajeros)
    nodo_inicial = Node(posicion=grid.inicio, pasajeros_recogidos=frozenset())
    return busqueda_no_informada(grid, nodo_inicial, pasajeros, modo)


def imprimir_resultado(resultado):
    """Imprime por consola las métricas de una búsqueda.

    Args:
        resultado (Mapping[str, object]): Resultado con camino, costo, nodos
            expandidos y profundidad; puede incluir tiempo y heurística.

    Returns:
        None.

    Example:
        >>> imprimir_resultado({
        ...     "costo": 1, "camino": [(0, 0), (0, 1)],
        ...     "nodos_expandidos": 2, "profundidad": 1
        ... })  # doctest: +ELLIPSIS
        ✅ Solución encontrada. Costo: 1
        ...
    """
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

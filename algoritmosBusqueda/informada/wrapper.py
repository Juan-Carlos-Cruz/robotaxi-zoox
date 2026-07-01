import heapq

from mundo import Node


def heuristica_manhattan(pos1, pos2):
    """Calcula la distancia Manhattan entre dos posiciones.

    Args:
        pos1 (tuple[int, int]): Primera posición ``(fila, columna)``.
        pos2 (tuple[int, int]): Segunda posición ``(fila, columna)``.

    Returns:
        int: Suma de las diferencias absolutas entre las coordenadas.

    Example:
        >>> heuristica_manhattan((0, 0), (2, 3))
        5
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def calcular_heuristica(nodo, destino, pasajeros, meta_pasajeros):
    """Estima la distancia al siguiente objetivo pendiente.

    Si ya se recogieron todos los pasajeros, estima la distancia al destino;
    de lo contrario, usa la distancia al pasajero pendiente más cercano.

    Args:
        nodo (Node): Estado para el que se calcula la estimación.
        destino (tuple[int, int]): Posición final del recorrido.
        pasajeros (Collection[tuple[int, int]]): Posiciones de pasajeros.
        meta_pasajeros (frozenset[tuple[int, int]]): Conjunto que debe haberse
            recogido antes de llegar al destino.

    Returns:
        int: Distancia Manhattan al siguiente objetivo relevante.

    Example:
        >>> nodo = Node((0, 0))
        >>> calcular_heuristica(nodo, (2, 2), [(0, 2)], frozenset({(0, 2)}))
        2
    """
    if nodo.pasajeros_recogidos == meta_pasajeros:
        return heuristica_manhattan(nodo.posicion, destino)

    pasajeros_faltantes = [p for p in pasajeros if p not in nodo.pasajeros_recogidos]
    return min(heuristica_manhattan(nodo.posicion, p) for p in pasajeros_faltantes)


def busqueda_informada(grid, inicio, destino, pasajeros, modo):
    """Busca una ruta completa mediante búsqueda avara o A*.

    La solución debe recoger todos los pasajeros antes de terminar en el
    destino. La prioridad usa solo ``h`` en modo avaro y ``g + h`` en A*.

    Args:
        grid (Grid): Mapa que proporciona vecinos y costos.
        inicio (tuple[int, int]): Posición inicial.
        destino (tuple[int, int]): Posición final.
        pasajeros (Collection[tuple[int, int]]): Pasajeros requeridos.
        modo (str): Estrategia; debe ser ``"avara"`` o ``"a_estrella"``.

    Returns:
        dict[str, object] | None: Métricas y camino de la solución, o ``None``
        si no existe una ruta válida.

    Raises:
        ValueError: Si ``modo`` no corresponde a una estrategia soportada.

    Example:
        >>> from mundo import Grid
        >>> grid = Grid([[2, 4, 5]])
        >>> busqueda_informada(
        ...     grid, grid.inicio, grid.destino, grid.pasajeros, "a_estrella"
        ... )["costo"]
        2
    """
    meta_pasajeros = frozenset(pasajeros)
    nodo_inicial = Node(
        posicion=inicio,
        pasajeros_recogidos=frozenset(),
        padre=None,
        g=0,
        h=0,
    )
    nodo_inicial.h = calcular_heuristica(nodo_inicial, destino, pasajeros, meta_pasajeros)
    nodo_inicial.f = nodo_inicial.g + nodo_inicial.h

    frontera = []
    contador = 0
    nodos_expandidos = 0

    if modo == "avara":
        heapq.heappush(frontera, (nodo_inicial.h, contador, nodo_inicial))
        visitados = set()
    elif modo == "a_estrella":
        heapq.heappush(frontera, (nodo_inicial.f, contador, nodo_inicial))
        best_g = {}
    else:
        raise ValueError(f"Modo no soportado: {modo}")

    contador += 1

    while frontera:
        _, _, nodo = heapq.heappop(frontera)
        nodos_expandidos += 1

        if nodo.pasajeros_recogidos == meta_pasajeros and nodo.posicion == destino:
            return {
                "camino": nodo.obtener_camino(),
                "costo": nodo.g,
                "nodos_expandidos": nodos_expandidos,
                "profundidad": nodo.profundidad,
                "heuristica": nodo.h,
            }

        estado = (nodo.posicion, nodo.pasajeros_recogidos)

        if modo == "avara":
            if estado in visitados:
                continue
            visitados.add(estado)
        else:
            if estado in best_g and best_g[estado] <= nodo.g:
                continue
            best_g[estado] = nodo.g

        for vecino in grid.get_vecinos(nodo):
            vecino.h = calcular_heuristica(vecino, destino, pasajeros, meta_pasajeros)
            vecino.f = vecino.g + vecino.h

            prioridad = vecino.h if modo == "avara" else vecino.f
            heapq.heappush(frontera, (prioridad, contador, vecino))
            contador += 1

    return None

from collections import deque
import heapq


def busqueda_no_informada(grid, nodo_inicial, pasajeros_totales, modo):
    """Busca una ruta completa sin usar una función heurística.

    Permite recorrer la frontera por amplitud, profundidad o costo uniforme.
    Un estado se considera meta cuando alcanza el destino después de recoger
    todos los pasajeros.

    Args:
        grid (Grid): Mapa que genera los estados vecinos.
        nodo_inicial (Node): Estado desde el que comienza la búsqueda.
        pasajeros_totales (frozenset[tuple[int, int]]): Pasajeros requeridos.
        modo (str): Estrategia ``"bfs"``, ``"dfs"`` o ``"ucs"``.

    Returns:
        dict[str, object] | None: Camino y métricas de la solución, o ``None``
        cuando la meta es inalcanzable.

    Raises:
        ValueError: Si se solicita un modo no soportado.

    Example:
        >>> from mundo import Grid, Node
        >>> grid = Grid([[2, 5]])
        >>> resultado = busqueda_no_informada(
        ...     grid, Node(grid.inicio), frozenset(), "bfs"
        ... )
        >>> resultado["camino"]
        [(0, 0), (0, 1)]
    """
    visitados = set()
    nodos_expandidos = 0

    if modo == "bfs":
        frontera = deque([nodo_inicial])

        def push(nodo):
            """Agrega un nodo al final de la cola BFS.

            Args:
                nodo (Node): Estado que se añadirá a la frontera.

            Returns:
                None.

            Example:
                ``push(vecino)`` encola ``vecino`` para explorarlo después.
            """
            frontera.append(nodo)

        def pop():
            """Extrae el nodo más antiguo de la cola BFS.

            Returns:
                Node: Siguiente estado en orden de llegada.

            Example:
                ``nodo = pop()`` obtiene el frente de la cola.
            """
            return frontera.popleft()

    elif modo == "dfs":
        frontera = [nodo_inicial]

        def push(nodo):
            """Agrega un nodo al final de la pila DFS.

            Args:
                nodo (Node): Estado que se añadirá a la frontera.

            Returns:
                None.

            Example:
                ``push(vecino)`` apila ``vecino``.
            """
            frontera.append(nodo)

        def pop():
            """Extrae el nodo más reciente de la pila DFS.

            Returns:
                Node: Último estado agregado a la frontera.

            Example:
                ``nodo = pop()`` obtiene la cima de la pila.
            """
            return frontera.pop()

    elif modo == "ucs":
        frontera = []
        contador = 0
        heapq.heappush(frontera, (nodo_inicial.g, contador, nodo_inicial))

        def push(nodo):
            """Inserta un nodo en la cola de prioridad UCS.

            Args:
                nodo (Node): Estado que se ordenará por costo acumulado.

            Returns:
                None.

            Example:
                ``push(vecino)`` agenda el vecino según su atributo ``g``.
            """
            nonlocal contador
            contador += 1
            heapq.heappush(frontera, (nodo.g, contador, nodo))

        def pop():
            """Extrae el nodo de menor costo de la frontera UCS.

            Returns:
                Node: Estado con el menor costo acumulado disponible.

            Example:
                ``nodo = pop()`` obtiene el siguiente estado de costo mínimo.
            """
            return heapq.heappop(frontera)[2]

    else:
        raise ValueError(f"Modo no soportado: {modo}")

    while frontera:
        nodo = pop()
        estado = (nodo.posicion, nodo.pasajeros_recogidos)

        if estado in visitados:
            continue

        visitados.add(estado)
        nodos_expandidos += 1

        if nodo.posicion == grid.destino and nodo.pasajeros_recogidos == pasajeros_totales:
            return {
                "camino": nodo.obtener_camino(),
                "nodos_expandidos": nodos_expandidos,
                "profundidad": nodo.profundidad,
                "costo": nodo.g,
            }

        for vecino in grid.get_vecinos(nodo):
            push(vecino)

    return None

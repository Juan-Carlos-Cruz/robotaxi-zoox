from collections import deque
import heapq


def busqueda_no_informada(grid, nodo_inicial, pasajeros_totales, modo):
    visitados = set()
    nodos_expandidos = 0

    if modo == "bfs":
        frontera = deque([nodo_inicial])

        def push(nodo):
            frontera.append(nodo)

        def pop():
            return frontera.popleft()

    elif modo == "dfs":
        frontera = [nodo_inicial]

        def push(nodo):
            frontera.append(nodo)

        def pop():
            return frontera.pop()

    elif modo == "ucs":
        frontera = []
        contador = 0
        heapq.heappush(frontera, (nodo_inicial.g, contador, nodo_inicial))

        def push(nodo):
            nonlocal contador
            contador += 1
            heapq.heappush(frontera, (nodo.g, contador, nodo))

        def pop():
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

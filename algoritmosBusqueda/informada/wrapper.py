import heapq

from mundo import Node


def heuristica_manhattan(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def calcular_heuristica(nodo, destino, pasajeros, meta_pasajeros):
    if nodo.pasajeros_recogidos == meta_pasajeros:
        return heuristica_manhattan(nodo.posicion, destino)

    pasajeros_faltantes = [p for p in pasajeros if p not in nodo.pasajeros_recogidos]
    return min(heuristica_manhattan(nodo.posicion, p) for p in pasajeros_faltantes)


def busqueda_informada(grid, inicio, destino, pasajeros, modo):
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

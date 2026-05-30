from .node import Node


class Grid:
    LIBRE = 0
    MURO = 1
    INICIO = 2
    FLUJO_ALTO = 3
    PASAJERO = 4
    DESTINO = 5

    def __init__(self, matriz):
        self.matriz = matriz
        self.filas = len(matriz)
        self.columnas = len(matriz[0]) if matriz else 0
        self.inicio = self._encontrar_posicion(Grid.INICIO)
        self.destino = self._encontrar_posicion(Grid.DESTINO)
        self.pasajeros = self._encontrar_todas_posiciones(Grid.PASAJERO)

    def _encontrar_posicion(self, valor):
        for fila in range(self.filas):
            for columna in range(self.columnas):
                if self.matriz[fila][columna] == valor:
                    return (fila, columna)
        return None

    def _encontrar_todas_posiciones(self, valor):
        posiciones = []
        for fila in range(self.filas):
            for columna in range(self.columnas):
                if self.matriz[fila][columna] == valor:
                    posiciones.append((fila, columna))
        return posiciones

    def es_valida(self, fila, col):
        return 0 <= fila < self.filas and 0 <= col < self.columnas

    def es_transitable(self, fila, col):
        return self.es_valida(fila, col) and self.matriz[fila][col] != Grid.MURO

    def costo_movimiento(self, fila, col):
        tipo = self.matriz[fila][col]
        if tipo in [Grid.LIBRE, Grid.INICIO, Grid.PASAJERO, Grid.DESTINO]:
            return 1
        if tipo == Grid.FLUJO_ALTO:
            return 7
        return 1

    def get_vecinos(self, nodo):
        vecinos = []
        fila, col = nodo.posicion
        movimientos = [(0, 1), (-1, 0), (1, 0), (0, -1)]

        for delta_fila, delta_columna in movimientos:
            nueva_fila = fila + delta_fila
            nueva_columna = col + delta_columna

            if not self.es_transitable(nueva_fila, nueva_columna):
                continue

            costo = nodo.g + self.costo_movimiento(nueva_fila, nueva_columna)
            nuevos_pasajeros = set(nodo.pasajeros_recogidos)

            if self.matriz[nueva_fila][nueva_columna] == Grid.PASAJERO:
                nuevos_pasajeros.add((nueva_fila, nueva_columna))

            vecinos.append(
                Node(
                    posicion=(nueva_fila, nueva_columna),
                    pasajeros_recogidos=frozenset(nuevos_pasajeros),
                    padre=nodo,
                    g=costo,
                )
            )

        return vecinos

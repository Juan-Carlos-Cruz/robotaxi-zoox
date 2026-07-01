from .node import Node


class Grid:
    """Modela el mapa y las reglas de movimiento del robotaxi.

    Attributes:
        matriz (list[list[int]]): Tipos de celda que componen el mapa.
        filas (int): Número de filas del mapa.
        columnas (int): Número de columnas del mapa.
        inicio (tuple[int, int] | None): Posición inicial del taxi.
        destino (tuple[int, int] | None): Posición final requerida.
        pasajeros (list[tuple[int, int]]): Posiciones de los pasajeros.

    Example:
        >>> grid = Grid([[Grid.INICIO, Grid.DESTINO]])
        >>> grid.inicio, grid.destino
        ((0, 0), (0, 1))
    """

    LIBRE = 0
    MURO = 1
    INICIO = 2
    FLUJO_ALTO = 3
    PASAJERO = 4
    DESTINO = 5

    def __init__(self, matriz):
        """Inicializa la cuadrícula e identifica sus celdas especiales.

        Args:
            matriz (list[list[int]]): Matriz rectangular de tipos de celda.

        Returns:
            None.

        Example:
            >>> grid = Grid([[2, 0, 5]])
            >>> grid.columnas
            3
        """
        self.matriz = matriz
        self.filas = len(matriz)
        self.columnas = len(matriz[0]) if matriz else 0
        self.inicio = self._encontrar_posicion(Grid.INICIO)
        self.destino = self._encontrar_posicion(Grid.DESTINO)
        self.pasajeros = self._encontrar_todas_posiciones(Grid.PASAJERO)

    def _encontrar_posicion(self, valor):
        """Busca la primera celda que contiene un valor.

        Args:
            valor (int): Tipo de celda que se desea localizar.

        Returns:
            tuple[int, int] | None: Posición encontrada o ``None``.

        Example:
            >>> Grid([[2, 5]])._encontrar_posicion(Grid.DESTINO)
            (0, 1)
        """
        for fila in range(self.filas):
            for columna in range(self.columnas):
                if self.matriz[fila][columna] == valor:
                    return (fila, columna)
        return None

    def _encontrar_todas_posiciones(self, valor):
        """Obtiene todas las posiciones que contienen un valor.

        Args:
            valor (int): Tipo de celda que se desea localizar.

        Returns:
            list[tuple[int, int]]: Posiciones encontradas en orden de lectura.

        Example:
            >>> Grid([[2, 4], [4, 5]])._encontrar_todas_posiciones(Grid.PASAJERO)
            [(0, 1), (1, 0)]
        """
        posiciones = []
        for fila in range(self.filas):
            for columna in range(self.columnas):
                if self.matriz[fila][columna] == valor:
                    posiciones.append((fila, columna))
        return posiciones

    def es_valida(self, fila, col):
        """Comprueba si unas coordenadas pertenecen al mapa.

        Args:
            fila (int): Índice de fila.
            col (int): Índice de columna.

        Returns:
            bool: ``True`` si las coordenadas están dentro de los límites.

        Example:
            >>> Grid([[2, 5]]).es_valida(0, 1)
            True
        """
        return 0 <= fila < self.filas and 0 <= col < self.columnas

    def es_transitable(self, fila, col):
        """Indica si el taxi puede ocupar una celda.

        Args:
            fila (int): Índice de fila.
            col (int): Índice de columna.

        Returns:
            bool: ``True`` si la celda existe y no es un muro.

        Example:
            >>> Grid([[2, 1, 5]]).es_transitable(0, 1)
            False
        """
        return self.es_valida(fila, col) and self.matriz[fila][col] != Grid.MURO

    def costo_movimiento(self, fila, col):
        """Calcula el costo de ingresar en una celda.

        Args:
            fila (int): Índice de fila de destino.
            col (int): Índice de columna de destino.

        Returns:
            int: Costo 7 para tráfico alto y 1 para las demás celdas.

        Example:
            >>> Grid([[2, 3, 5]]).costo_movimiento(0, 1)
            7
        """
        tipo = self.matriz[fila][col]
        if tipo in [Grid.LIBRE, Grid.INICIO, Grid.PASAJERO, Grid.DESTINO]:
            return 1
        if tipo == Grid.FLUJO_ALTO:
            return 7
        return 1

    def get_vecinos(self, nodo):
        """Genera los estados transitables adyacentes a un nodo.

        Al entrar en una celda de pasajero, registra su posición en el nuevo
        estado y acumula el costo del movimiento.

        Args:
            nodo (Node): Estado desde el que se generan movimientos.

        Returns:
            list[Node]: Nodos vecinos en las direcciones derecha, arriba,
            abajo e izquierda.

        Example:
            >>> grid = Grid([[2, 4, 5]])
            >>> vecinos = grid.get_vecinos(Node((0, 0)))
            >>> vecinos[0].posicion
            (0, 1)
        """
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

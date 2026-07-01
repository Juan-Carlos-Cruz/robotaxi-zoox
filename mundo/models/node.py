class Node:
    """Representa un estado explorado por un algoritmo de búsqueda.

    Attributes:
        posicion (tuple[int, int]): Coordenadas ``(fila, columna)`` del estado.
        pasajeros_recogidos (frozenset[tuple[int, int]]): Pasajeros recogidos.
        padre (Node | None): Estado desde el que se alcanzó este nodo.
        g (int | float): Costo acumulado desde el inicio.
        h (int | float): Estimación heurística hasta el objetivo.
        f (int | float): Prioridad total calculada como ``g + h``.
        profundidad (int): Cantidad de movimientos desde el nodo raíz.

    Example:
        >>> nodo = Node((0, 0), g=2, h=3)
        >>> nodo.f
        5
    """

    def __init__(self, posicion, pasajeros_recogidos=None, padre=None, g=0, h=0):
        """Inicializa un estado de búsqueda y calcula su prioridad.

        Args:
            posicion (tuple[int, int]): Coordenadas del nodo en la cuadrícula.
            pasajeros_recogidos (Collection[tuple[int, int]] | None): Posiciones
                de los pasajeros ya recogidos. Si es ``None``, usa un conjunto
                inmutable vacío.
            padre (Node | None): Nodo predecesor en el camino.
            g (int | float): Costo acumulado desde el origen.
            h (int | float): Valor heurístico estimado.

        Returns:
            None.

        Example:
            >>> raiz = Node((0, 0))
            >>> hijo = Node((0, 1), padre=raiz, g=1)
            >>> hijo.profundidad
            1
        """
        self.posicion = posicion
        self.pasajeros_recogidos = pasajeros_recogidos if pasajeros_recogidos is not None else frozenset()
        self.padre = padre
        self.g = g
        self.h = h
        self.f = g + h
        self.profundidad = (padre.profundidad + 1) if padre else 0

    def __eq__(self, other):
        """Compara dos nodos por posición y pasajeros recogidos.

        Args:
            other (Node): Nodo con el que se realiza la comparación.

        Returns:
            bool: ``True`` si ambos representan el mismo estado.

        Example:
            >>> Node((1, 2)) == Node((1, 2))
            True
        """
        return self.posicion == other.posicion and self.pasajeros_recogidos == other.pasajeros_recogidos

    def __lt__(self, other):
        """Determina si el nodo tiene menor prioridad total que otro.

        Args:
            other (Node): Nodo cuya prioridad se compara.

        Returns:
            bool: ``True`` cuando el valor ``f`` actual es menor.

        Example:
            >>> Node((0, 0), g=1, h=1) < Node((0, 1), g=2, h=2)
            True
        """
        return self.f < other.f

    def __hash__(self):
        """Calcula el hash del estado para usarlo en conjuntos y diccionarios.

        Returns:
            int: Hash compuesto por la posición y los pasajeros recogidos.

        Example:
            >>> isinstance(hash(Node((0, 0))), int)
            True
        """
        return hash((self.posicion, self.pasajeros_recogidos))

    def obtener_camino(self):
        """Reconstruye el camino desde la raíz hasta el nodo actual.

        Returns:
            list[tuple[int, int]]: Posiciones ordenadas desde el origen.

        Example:
            >>> raiz = Node((0, 0))
            >>> Node((0, 1), padre=raiz).obtener_camino()
            [(0, 0), (0, 1)]
        """
        camino = []
        nodo = self
        while nodo:
            camino.append(nodo.posicion)
            nodo = nodo.padre
        return list(reversed(camino))

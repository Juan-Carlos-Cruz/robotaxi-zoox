class Node:
    def __init__(self, posicion, pasajeros_recogidos=None, padre=None, g=0, h=0):
        self.posicion = posicion
        self.pasajeros_recogidos = pasajeros_recogidos if pasajeros_recogidos is not None else frozenset()
        self.padre = padre
        self.g = g
        self.h = h
        self.f = g + h
        self.profundidad = (padre.profundidad + 1) if padre else 0

    def __eq__(self, other):
        return self.posicion == other.posicion and self.pasajeros_recogidos == other.pasajeros_recogidos

    def __lt__(self, other):
        return self.f < other.f

    def __hash__(self):
        return hash((self.posicion, self.pasajeros_recogidos))

    def obtener_camino(self):
        camino = []
        nodo = self
        while nodo:
            camino.append(nodo.posicion)
            nodo = nodo.padre
        return list(reversed(camino))

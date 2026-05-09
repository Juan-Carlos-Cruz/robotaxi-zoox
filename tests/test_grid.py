import os
import sys

RUTA_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RUTA_RAIZ)

from mundo import Grid, leer_mapa


def probar_grid():
    print("=" * 50)
    print("PRUEBA DE LA CLASE GRID")
    print("=" * 50)

    print("Leyendo mapa...")
    matriz = leer_mapa()
    if not matriz:
        print("ERROR, No se pudo cargar el mapa")
        return

    print("Creando Grid...")
    grid = Grid(matriz)

    print("\nGrid creado correctamente")
    print(f"Dimensiones: {grid.filas} filas x {grid.columnas} columnas")
    print(f"Inicio: {grid.inicio}")
    print(f"Destino: {grid.destino}")
    print(f"Pasajeros: {grid.pasajeros}")

    print("\nProbando métodos:")
    pruebas = [
        ("es_valida(0,0)", grid.es_valida(0, 0), True),
        ("es_valida(10,10)", grid.es_valida(10, 10), False),
        ("es_transitable(0,0)", grid.es_transitable(0, 0), True),
        ("es_transitable(0,1)", grid.es_transitable(0, 1), False),
        ("costo_movimiento(0,0)", grid.costo_movimiento(0, 0), 1),
        ("costo_movimiento(1,6)", grid.costo_movimiento(1, 6), 7),
    ]

    for nombre, obtenido, esperado in pruebas:
        estado = "OK" if obtenido == esperado else "ERROR"
        print(f"{estado} {nombre}: {obtenido} (esperado: {esperado})")


if __name__ == "__main__":
    probar_grid()

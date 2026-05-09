import os
import sys

RUTA_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RUTA_RAIZ)

from mundo import Grid, Node, leer_mapa
from algoritmosBusqueda.noinformada.wrapper import busqueda_no_informada
from algoritmosBusqueda.informada.wrapper import busqueda_informada

# 1. Cargar el mapa
matriz = leer_mapa()
grid   = Grid(matriz)

# 2. Crear nodo inicial
nodo_inicial = Node(
    posicion            = grid.inicio,
    pasajeros_recogidos = frozenset()
)

# 3. Definir todos los pasajeros que hay que recoger
pasajeros_totales = frozenset(grid.pasajeros)


print(f"Celda (1,0): {grid.matriz[1][0]}")
print(f"Celda (0,0): {grid.matriz[0][0]}")
print(f"Es transitable (1,0): {grid.es_transitable(1,0)}")
print(f"Vecinos del nodo inicial:")
nodo_prueba = Node(posicion=grid.inicio, pasajeros_recogidos=frozenset())
for v in grid.get_vecinos(nodo_prueba):
    print(f"  {v.posicion}")


# 4. Ejecutar BFS
resultado = busqueda_no_informada(grid, nodo_inicial, pasajeros_totales, "bfs")


# ejecutar por costo
resultado2 = busqueda_no_informada(grid, nodo_inicial, pasajeros_totales, "ucs")

#Ejecutar por profundidad evitando ciclos
resultado3 = busqueda_no_informada(grid, nodo_inicial, pasajeros_totales, "dfs")


# 5. Ver resultado
if resultado:
    print("✅ BFS - Solución encontrada!")
    print(f"Camino: {resultado['camino']}")
    print(f"Nodos expandidos: {resultado['nodos_expandidos']}")
    print(f"Profundidad: {resultado['profundidad']}")
    print(f"Costo: {resultado['costo']}")
else:
    print("❌ BFS - No se encontró solución")

if resultado2:
    print("✅ bcu - Solución encontrada!")
    print(f"Camino: {resultado2['camino']}")
    print(f"Nodos expandidos: {resultado2['nodos_expandidos']}")
    print(f"Profundidad: {resultado2['profundidad']}")
    print(f"Costo: {resultado2['costo']}")
else:
    print("❌ UCS - No se encontró solución")

if resultado3:
    print("✅ dfs - Solución encontrada!")
    print(f"Camino: {resultado3['camino']}")
    print(f"Nodos expandidos: {resultado3['nodos_expandidos']}")
    print(f"Profundidad: {resultado3['profundidad']}")
    print(f"Costo: {resultado3['costo']}")
else:
    print("❌ UCS - No se encontró solución")

    #---------------------- PRUEBA DE A* -------------

    # Bloque principal que se ejecuta solo si este archivo se ejecuta directamente
if __name__ == "__main__":
    print("="*60)
    print("PRUEBA DEL ALGORITMO A*")
    print("="*60)

    # Lee el mapa desde el archivo
    matriz = leer_mapa()
    if not matriz:
        print("❌ No se pudo cargar el mapa")
        exit(1)

    # Crea el grid (mundo) con la matriz leída
    grid = Grid(matriz)

    # Prueba: verifica que get_vecinos funciona correctamente
    print("\n🔍 Probando get_vecinos...")
    nodo_prueba = Node(posicion=grid.inicio, pasajeros_recogidos=frozenset())
    vecinos = grid.get_vecinos(nodo_prueba)
    print(f"Vecinos desde inicio ({grid.inicio}): {len(vecinos)}")
    for v in vecinos:
        print(f"  {v.posicion}, g={v.g}")

    # Muestra información del grid
    print(f"Inicio: {grid.inicio}")
    print(f"Destino: {grid.destino}")
    print(f"Pasajeros: {grid.pasajeros}")

    # Ejecuta el algoritmo A*
    resultado = busqueda_informada(grid, grid.inicio, grid.destino, grid.pasajeros, "a_estrella")

    # Muestra el resultado
    if resultado:
        print("\n✅ SOLUCIÓN ENCONTRADA")
        print(f"Costo: {resultado['costo']}")
        print(f"Nodos expandidos: {resultado['nodos_expandidos']}")
        print(f"Profundidad: {resultado['profundidad']}")
        print(f"Pasos: {len(resultado['camino'])}")

        # Verifica que se recogieron todos los pasajeros
        recogidos = []
        for pos in resultado['camino']:
            if pos in grid.pasajeros:
                recogidos.append(pos)

        print(f"\nPasajeros recogidos: {recogidos}")
        if set(recogidos) == set(grid.pasajeros):
            print("✅ Todos los pasajeros fueron recogidos")
        else:
            print("❌ Faltan pasajeros")

        # Verifica que termina en el destino correcto
        if resultado['camino'][-1] == grid.destino:
            print("✅ Termina en destino correcto")
        else:
            print("❌ Termina en otro lugar")
    else:
        print("\n❌ No se encontró solución")

        # ==================== PRUEBA AVARA ====================
# Bloque principal que se ejecuta solo si este archivo se ejecuta directamente
if __name__ == "__main__":
    print("="*60)
    print("PRUEBA DEL ALGORITMO AVARA")
    print("="*60)

    # Lee el mapa desde el archivo
    matriz = leer_mapa()
    if not matriz:
        print("❌ No se pudo cargar el mapa")
        exit(1)

    # Crea el grid (mundo) con la matriz leída
    grid = Grid(matriz)

    # Muestra información del grid
    print(f"Inicio: {grid.inicio}")
    print(f"Destino: {grid.destino}")
    print(f"Pasajeros: {grid.pasajeros}")

    # Ejecuta el algoritmo Avara
    resultado = busqueda_informada(grid, grid.inicio, grid.destino, grid.pasajeros, "avara")

    # Muestra el resultado
    if resultado:
        print("\n✅ SOLUCIÓN ENCONTRADA")
        print(f"Costo: {resultado['costo']}")
        print(f"Nodos expandidos: {resultado['nodos_expandidos']}")
        print(f"Profundidad: {resultado['profundidad']}")
        print(f"Pasos: {len(resultado['camino'])}")

        # Verifica que se recogieron todos los pasajeros
        recogidos = []
        for pos in resultado['camino']:
            if pos in grid.pasajeros:
                recogidos.append(pos)

        print(f"\nPasajeros recogidos: {recogidos}")
        if set(recogidos) == set(grid.pasajeros):
            print("✅ Todos los pasajeros fueron recogidos")
        else:
            print("❌ Faltan pasajeros")

        # Verifica que termina en el destino correcto
        if resultado['camino'][-1] == grid.destino:
            print("✅ Termina en destino correcto")
        else:
            print("❌ Termina en otro lugar")
    else:
        print("\n❌ No se encontró solución")

import sys
import os

RUTA_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RUTA_RAIZ)

from ui.visualizador import Visualizador
from mundo import Grid, leer_mapa
from algoritmosBusqueda.informada.wrapper import busqueda_informada

# ==================== PRUEBA DEL VISUALIZADOR ====================
if __name__ == "__main__":
    print("="*60)
    print("PRUEBA DEL VISUALIZADOR")
    print("="*60)

    # Cargar mapa
    matriz = leer_mapa()
    if not matriz:
        print("❌ No se pudo cargar el mapa")
        exit(1)

    # Crear grid
    grid = Grid(matriz)
    print(f"Inicio: {grid.inicio}")
    print(f"Destino: {grid.destino}")
    print(f"Pasajeros: {grid.pasajeros}")

    # Ejecutar A*
    print("\n🔍 Ejecutando A*...")
    resultado = busqueda_informada(grid, grid.inicio, grid.destino, grid.pasajeros, "a_estrella")

    if not resultado:
        print("❌ No se encontró solución")
        exit(1)

    print(f"✅ Solución encontrada. Costo: {resultado['costo']}")
    print(f"Pasos: {resultado['profundidad']}")
    print("\n🎬 Mostrando animación...")

    vis = Visualizador(grid, "Robotaxi Zoox - A*")
    resultado["tiempo"] = 0
    vis.animar_camino(resultado["camino"], resultado, "a_estrella", delay=200)

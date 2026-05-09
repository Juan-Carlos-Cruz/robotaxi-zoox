import sys
import time

import pygame

from ui.menu import mostrar_menu, mostrar_submenu
from ui.visualizador import Visualizador

from .carga import cargar_grid
from .config import TITULO_APP, WINDOW_SIZE
from .ejecucion import ejecutar_algoritmo, imprimir_resultado


def seleccionar_algoritmo():
    pygame.init()
    ventana = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption(TITULO_APP)

    categoria = mostrar_menu(ventana, *WINDOW_SIZE)
    return mostrar_submenu(ventana, *WINDOW_SIZE, categoria)


def main():
    grid = cargar_grid()
    if grid is None:
        sys.exit()

    visualizador = Visualizador(grid, TITULO_APP)
    visualizador.dibujar_grid()
    pygame.time.wait(2000)

    algoritmo = seleccionar_algoritmo()
    print(f"Ejecutando: {algoritmo}...")

    tiempo_inicio = time.perf_counter()
    resultado = ejecutar_algoritmo(algoritmo, grid)
    tiempo_fin = time.perf_counter()

    if not resultado:
        print("No se encontró solución :c")
        pygame.quit()
        sys.exit()

    resultado["tiempo"] = round((tiempo_fin - tiempo_inicio) * 1000, 2)
    imprimir_resultado(resultado)
    print("\n🎬 Mostrando animación...")
    visualizador.animar_camino(resultado["camino"], resultado, algoritmo, delay=200)

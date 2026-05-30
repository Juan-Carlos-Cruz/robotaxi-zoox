import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from mundo import Grid, leer_mapa

RUTA_MAPAS = Path(__file__).resolve().parents[1] / "mapas" / "test"


def seleccionar_archivo():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.update()
    ruta = filedialog.askopenfilename(
        title="Selecciona el mapa",
        filetypes=[("Archivos de texto", "*.txt")],
        initialdir=str(RUTA_MAPAS),
    )
    root.destroy()
    return ruta if ruta else None


def cargar_grid_desde_ruta(ruta):
    matriz = leer_mapa(ruta)
    if not matriz:
        print("Error al leer el mapa")
        return None

    return Grid(matriz)


def cargar_grid():
    ruta = seleccionar_archivo()
    if not ruta:
        print("No se seleccionó ningún archivo")
        return None

    return cargar_grid_desde_ruta(ruta)

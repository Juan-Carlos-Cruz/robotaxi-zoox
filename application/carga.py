import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from mundo import Grid, leer_mapa

RUTA_MAPAS = Path(__file__).resolve().parents[1] / "mapas" / "test"


def seleccionar_archivo():
    """Muestra un diálogo para seleccionar un mapa de texto.

    Returns:
        str | None: Ruta seleccionada, o ``None`` si el usuario cancela.

    Example:
        >>> ruta = seleccionar_archivo()  # doctest: +SKIP
        >>> ruta is None or ruta.endswith(".txt")  # doctest: +SKIP
        True
    """
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
    """Construye una cuadrícula a partir de un archivo de mapa.

    Args:
        ruta (str | Path): Ruta del archivo que contiene la matriz.

    Returns:
        Grid | None: Cuadrícula cargada, o ``None`` si el mapa no pudo leerse.

    Example:
        >>> grid = cargar_grid_desde_ruta("mapas/test/Prueba1.txt")
        >>> isinstance(grid, Grid)
        True
    """
    matriz = leer_mapa(ruta)
    if not matriz:
        print("Error al leer el mapa")
        return None

    return Grid(matriz)


def cargar_grid():
    """Solicita un archivo al usuario y carga su cuadrícula.

    Returns:
        Grid | None: Mapa seleccionado, o ``None`` si se cancela o falla.

    Example:
        >>> grid = cargar_grid()  # doctest: +SKIP
        >>> grid is None or isinstance(grid, Grid)  # doctest: +SKIP
        True
    """
    ruta = seleccionar_archivo()
    if not ruta:
        print("No se seleccionó ningún archivo")
        return None

    return cargar_grid_desde_ruta(ruta)

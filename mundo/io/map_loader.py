from pathlib import Path

RUTA_PROYECTO = Path(__file__).resolve().parents[2]


def _ruta_mapa_predeterminada():
    """Construye la ruta del mapa usado cuando no se especifica uno.

    Returns:
        Path: Ruta absoluta al archivo ``Prueba1.txt``.

    Example:
        >>> _ruta_mapa_predeterminada().name
        'Prueba1.txt'
    """
    return RUTA_PROYECTO / "mapas" / "test" / "Prueba1.txt"


def leer_mapa(ruta=None):
    """Lee un mapa de texto y lo convierte en una matriz de enteros.

    Ignora las líneas vacías. Los errores de lectura se informan por consola y
    producen un resultado nulo.

    Args:
        ruta (str | Path | None): Archivo que se leerá. Si es ``None``, usa el
            mapa predeterminado del proyecto.

    Returns:
        list[list[int]] | None: Matriz leída, o ``None`` si el archivo está
        vacío, no existe o no puede procesarse.

    Example:
        >>> matriz = leer_mapa()
        >>> isinstance(matriz, list)
        True
    """
    ruta_mapa = Path(ruta) if ruta is not None else _ruta_mapa_predeterminada()

    try:
        with ruta_mapa.open("r", encoding="utf-8") as archivo:
            matriz = []
            for linea in archivo:
                linea = linea.strip()
                if not linea:
                    continue

                fila = [int(valor) for valor in linea.split()]
                matriz.append(fila)

            return matriz if matriz else None

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {ruta_mapa}")
        return None
    except Exception as error:
        print(f"Error al leer archivo: {error}")
        return None

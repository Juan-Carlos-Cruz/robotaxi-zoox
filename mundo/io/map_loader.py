from pathlib import Path

RUTA_PROYECTO = Path(__file__).resolve().parents[2]


def _ruta_mapa_predeterminada():
    return RUTA_PROYECTO / "mapas" / "test" / "Prueba1.txt"


def leer_mapa(ruta=None):
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

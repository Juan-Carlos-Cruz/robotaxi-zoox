WINDOW_SIZE = (1400, 900)
TITULO_APP = "Robotaxi Zoox"
HEADER_HEIGHT = 88
PANEL_WIDTH = 340
APP_PADDING = 24
ANIMATION_DELAY_MS = 260

ALGORITHM_CONFIG = {
    "a_estrella": ("informada", "a_estrella"),
    "avara": ("informada", "avara"),
    "amplitud": ("no_informada", "bfs"),
    "costo": ("no_informada", "ucs"),
    "profundidad": ("no_informada", "dfs"),
}

CATEGORY_LABELS = {
    "no_informada": "No informada",
    "informada": "Informada",
}

ALGORITHM_GROUPS = {
    "no_informada": [
        ("Amplitud", "amplitud"),
        ("Costo uniforme", "costo"),
        ("Profundidad", "profundidad"),
    ],
    "informada": [
        ("Avara", "avara"),
        ("A*", "a_estrella"),
    ],
}

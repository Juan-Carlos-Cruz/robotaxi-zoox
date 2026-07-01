import sys
import time
from pathlib import Path

import pygame

from ui.visualizador import Visualizador

from .audio import AudioManager
from .carga import cargar_grid_desde_ruta, seleccionar_archivo
from .config import (
    ALGORITHM_GROUPS,
    ANIMATION_DELAY_MS,
    APP_PADDING,
    CATEGORY_LABELS,
    HEADER_HEIGHT,
    PANEL_WIDTH,
    TITULO_APP,
    WINDOW_SIZE,
)
from .ejecucion import ejecutar_algoritmo, imprimir_resultado


COLOR_APP_BG = (19, 24, 29)
COLOR_PANEL = (27, 33, 39)
COLOR_CARD = (34, 42, 49)
COLOR_CARD_ALT = (43, 54, 63)
COLOR_BORDER = (82, 96, 108)
COLOR_TEXT = (235, 240, 244)
COLOR_TEXT_MUTED = (164, 176, 188)
COLOR_ACCENT = (71, 157, 255)
COLOR_ACCENT_ALT = (57, 127, 206)
COLOR_SUCCESS = (42, 177, 103)
COLOR_WARNING = (232, 182, 69)
COLOR_OVERLAY = (8, 12, 16, 175)


class RobotaxiApp:
    """Coordina la interfaz, las búsquedas, la animación y el audio.

    Attributes:
        grid (Grid | None): Mapa activo.
        visualizador (Visualizador | None): Renderizador del mapa.
        selected_algorithm (str | None): Clave del algoritmo elegido.
        current_result (dict | None): Resultado de la última búsqueda.
        animating (bool): Indica si el taxi está recorriendo una solución.

    Example:
        >>> app = RobotaxiApp()  # doctest: +SKIP
        >>> app.grid is None  # doctest: +SKIP
        True
    """

    def __init__(self):
        """Inicializa Pygame y el estado completo de la aplicación.

        Returns:
            None.

        Example:
            >>> app = RobotaxiApp()  # doctest: +SKIP
            >>> app.modal_visible  # doctest: +SKIP
            False
        """
        pygame.init()
        self.window = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
        pygame.display.set_caption(TITULO_APP)
        self.clock = pygame.time.Clock()
        self.audio = AudioManager()

        self.font_title = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_subtitle = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_body = pygame.font.SysFont("Arial", 18)
        self.font_small = pygame.font.SysFont("Arial", 15)
        self.font_button = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_modal_title = pygame.font.SysFont("Arial", 28, bold=True)

        self.grid = None
        self.map_path = None
        self.visualizador = None

        self.selected_category = None
        self.selected_algorithm = None
        self.current_result = None
        self.displayed_path = None
        self.displayed_step = 0
        self.status_message = "Selecciona una categoría para ver sus algoritmos."

        self.animating = False
        self.animation_result = None
        self.animation_algorithm = None
        self.animation_started_at = 0
        self.animation_progress = 0.0
        self.animation_seen_passengers = set()

        self.modal_visible = False
        self.modal_title = ""
        self.modal_lines = []

        self.header_rect = pygame.Rect(0, 0, 0, 0)
        self.map_panel_rect = pygame.Rect(0, 0, 0, 0)
        self.panel_rect = pygame.Rect(0, 0, 0, 0)
        self.ambient_toggle_button = pygame.Rect(0, 0, 0, 0)
        self.change_map_button = pygame.Rect(0, 0, 0, 0)
        self.category_buttons = []
        self.algorithm_buttons = []
        self.modal_close_button = pygame.Rect(0, 0, 0, 0)
        self.modal_x_button = pygame.Rect(0, 0, 0, 0)

    def iniciar(self):
        """Solicita el mapa inicial y lo incorpora a la aplicación.

        Returns:
            bool: ``True`` si se seleccionó y cargó un mapa válido.

        Example:
            >>> app = RobotaxiApp()  # doctest: +SKIP
            >>> app.iniciar()  # doctest: +SKIP
            True
        """
        print("Abriendo selector de mapa...")
        ruta = seleccionar_archivo()
        if not ruta:
            return False

        return self._cargar_mapa(ruta)

    def _cargar_mapa(self, ruta):
        """Carga un mapa y reinicia el estado de resultado y animación.

        Args:
            ruta (str | Path): Ruta del archivo de mapa.

        Returns:
            bool: ``True`` si el mapa se cargó correctamente.

        Example:
            >>> app = RobotaxiApp()  # doctest: +SKIP
            >>> app._cargar_mapa("mapas/test/Prueba1.txt")  # doctest: +SKIP
            True
        """
        grid = cargar_grid_desde_ruta(ruta)
        if grid is None:
            self.status_message = "No se pudo cargar el mapa seleccionado."
            return False

        self.grid = grid
        self.map_path = Path(ruta)
        self.displayed_path = None
        self.displayed_step = 0
        self.current_result = None
        self.animating = False
        self.animation_result = None
        self.animation_algorithm = None
        self.animation_progress = 0.0
        self.animation_seen_passengers = set()
        self.modal_visible = False
        self.status_message = f"Mapa cargado: {self.map_path.name}"
        self.audio.stop_drive_loop()

        self._actualizar_layout()

        if self.visualizador is None:
            self.visualizador = Visualizador(self.grid, TITULO_APP, surface=self.window, viewport=self.map_panel_rect.inflate(-18, -18))
        else:
            self.visualizador.set_grid(self.grid)
            self.visualizador.set_surface(self.window, self.map_panel_rect.inflate(-18, -18))
        return True

    def ejecutar(self):
        """Ejecuta el bucle principal hasta que se solicita el cierre.

        Procesa eventos, actualiza la animación, dibuja cada fotograma y
        libera los recursos de audio y Pygame al terminar.

        Returns:
            None.

        Example:
            >>> app.ejecutar()  # doctest: +SKIP
        """
        self.audio.play_ambient()
        while True:
            self._actualizar_layout()
            if not self._procesar_eventos():
                break
            self._actualizar_animacion()
            self._dibujar()
            self.clock.tick(60)

        self.audio.shutdown()
        pygame.quit()

    def _actualizar_layout(self):
        """Recalcula paneles y botones según el tamaño de la ventana.

        Returns:
            None.

        Example:
            >>> app._actualizar_layout()  # doctest: +SKIP
            >>> app.panel_rect.width == PANEL_WIDTH  # doctest: +SKIP
            True
        """
        full = self.window.get_rect()
        self.header_rect = pygame.Rect(APP_PADDING, APP_PADDING, full.width - APP_PADDING * 2, HEADER_HEIGHT)

        body_top = self.header_rect.bottom + APP_PADDING
        body_height = full.height - body_top - APP_PADDING
        self.panel_rect = pygame.Rect(full.width - APP_PADDING - PANEL_WIDTH, body_top, PANEL_WIDTH, body_height)
        self.map_panel_rect = pygame.Rect(APP_PADDING, body_top, self.panel_rect.left - APP_PADDING * 2, body_height)

        self.change_map_button = pygame.Rect(self.header_rect.right - 184, self.header_rect.y + 20, 164, 46)
        self.ambient_toggle_button = pygame.Rect(self.change_map_button.x - 172, self.header_rect.y + 20, 152, 46)

        self.status_rect = pygame.Rect(self.panel_rect.x + 24, self.panel_rect.y + 94, self.panel_rect.width - 48, 50)
        self.search_type_label_y = self.status_rect.bottom + 14

        self.category_buttons = []
        category_width = (self.panel_rect.width - 48 - 12) // 2
        category_y = self.search_type_label_y + self.font_body.get_height() + 12
        for index, category in enumerate(CATEGORY_LABELS):
            rect = pygame.Rect(self.panel_rect.x + 24 + index * (category_width + 12), category_y, category_width, 46)
            self.category_buttons.append((category, rect))

        self.algorithm_buttons = []
        self.suboptions_label_y = category_y + 64
        algo_y = self.suboptions_label_y + self.font_body.get_height() + 16
        if self.selected_category is not None:
            for label, key in ALGORITHM_GROUPS[self.selected_category]:
                rect = pygame.Rect(self.panel_rect.x + 24, algo_y, self.panel_rect.width - 48, 54)
                self.algorithm_buttons.append((label, key, rect))
                algo_y += 68

        modal_width = min(560, full.width - 80)
        modal_height = 380
        modal_rect = pygame.Rect(0, 0, modal_width, modal_height)
        modal_rect.center = full.center
        self.modal_rect = modal_rect
        self.modal_x_button = pygame.Rect(modal_rect.right - 52, modal_rect.y + 18, 34, 34)
        self.modal_close_button = pygame.Rect(modal_rect.centerx - 82, modal_rect.bottom - 68, 164, 44)

        if self.visualizador is not None and self.grid is not None:
            self.visualizador.set_surface(self.window, self.map_panel_rect.inflate(-18, -18))

    def _procesar_eventos(self):
        """Atiende los eventos pendientes de Pygame.

        Returns:
            bool: ``False`` si se recibió un evento de cierre; ``True`` en los
            demás casos.

        Example:
            >>> continuar = app._procesar_eventos()  # doctest: +SKIP
            >>> isinstance(continuar, bool)  # doctest: +SKIP
            True
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.VIDEORESIZE:
                width = max(1180, event.w)
                height = max(760, event.h)
                self.window = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                self._actualizar_layout()
                continue

            if event.type == pygame.KEYDOWN and self.modal_visible and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.modal_visible = False
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._manejar_click(event.pos)

        return True

    def _manejar_click(self, pos):
        """Procesa un clic según el control ubicado en la posición indicada.

        Args:
            pos (tuple[int, int]): Coordenadas del clic en la ventana.

        Returns:
            None.

        Example:
            >>> app._manejar_click((100, 100))  # doctest: +SKIP
        """
        if self.modal_visible:
            if self.modal_close_button.collidepoint(pos) or self.modal_x_button.collidepoint(pos):
                self.audio.play_ui_click()
                self.modal_visible = False
            return

        if self.animating:
            return

        if self.change_map_button.collidepoint(pos):
            self.audio.play_ui_click()
            ruta = seleccionar_archivo()
            if ruta:
                self._cargar_mapa(ruta)
            else:
                self.status_message = "Cambio de mapa cancelado."
            return

        if self.ambient_toggle_button.collidepoint(pos):
            self.audio.play_ui_click()
            if not self.audio.enabled:
                self.status_message = "Audio no disponible en este entorno."
                return

            nuevo_estado = not self.audio.ambient_enabled
            self.audio.set_ambient_enabled(nuevo_estado)
            if nuevo_estado:
                self.status_message = "Música ambiente activada."
            else:
                self.status_message = "Música ambiente desactivada."
            return

        for category, rect in self.category_buttons:
            if rect.collidepoint(pos):
                self.audio.play_ui_click()
                self.selected_category = category
                self.selected_algorithm = None
                self.status_message = f"Categoría activa: {CATEGORY_LABELS[category]}"
                return

        for label, key, rect in self.algorithm_buttons:
            if rect.collidepoint(pos):
                self.audio.play_ui_click()
                self._ejecutar_algoritmo(key, label)
                return

    def _ejecutar_algoritmo(self, algorithm_key, label):
        """Ejecuta una búsqueda y prepara la animación de su resultado.

        Args:
            algorithm_key (str): Clave registrada del algoritmo.
            label (str): Nombre legible mostrado en la interfaz.

        Returns:
            None.

        Example:
            >>> app._ejecutar_algoritmo("amplitud", "Amplitud")  # doctest: +SKIP
        """
        if self.grid is None:
            return

        self.selected_algorithm = algorithm_key
        self.status_message = f"Ejecutando {label}..."
        print(f"Ejecutando: {algorithm_key}...")
        self.audio.stop_drive_loop()
        self.animation_seen_passengers = set()

        tiempo_inicio = time.perf_counter()
        resultado = ejecutar_algoritmo(algorithm_key, self.grid)
        tiempo_fin = time.perf_counter()

        if not resultado:
            self.displayed_path = None
            self.displayed_step = 0
            self.current_result = None
            self._mostrar_modal("Sin solución", ["No se encontró solución para este algoritmo."])
            self.status_message = f"{label}: no se encontró solución."
            return

        tiempo_busqueda_ms = round((tiempo_fin - tiempo_inicio) * 1000, 2)
        resultado["tiempo"] = tiempo_busqueda_ms
        resultado["tiempo_busqueda_ms"] = tiempo_busqueda_ms
        imprimir_resultado(resultado)

        self.current_result = resultado
        self.displayed_path = resultado["camino"]
        self.displayed_step = 0
        self.animation_progress = 0.0
        self.animating = len(self.displayed_path) > 1
        self.animation_result = resultado
        self.animation_algorithm = label
        self.animation_started_at = pygame.time.get_ticks()
        if self.animating:
            self.audio.start_drive_loop()
            self.status_message = f"Animando {label}..."
        else:
            self.audio.play_finish_jingle()
            self._mostrar_modal(self.animation_algorithm or "Resultado", self._lineas_resultado(self.animation_result))
            self.status_message = f"Último algoritmo ejecutado: {self.animation_algorithm}"

    def _actualizar_animacion(self):
        """Avanza la animación de acuerdo con el tiempo transcurrido.

        Al llegar a una nueva celda reproduce sus efectos y, al finalizar,
        muestra el modal con las métricas de la búsqueda.

        Returns:
            None.

        Example:
            >>> app._actualizar_animacion()  # doctest: +SKIP
        """
        if not self.animating or not self.displayed_path:
            return

        ahora = pygame.time.get_ticks()
        transcurrido = ahora - self.animation_started_at
        self.animation_progress = min(1.0, max(0.0, transcurrido / ANIMATION_DELAY_MS))

        if self.animation_progress < 1.0:
            return

        siguiente_pos = self.displayed_path[self.displayed_step + 1]
        self._procesar_audio_de_celda(siguiente_pos)

        if self.displayed_step < len(self.displayed_path) - 2:
            self.displayed_step += 1
            self.animation_started_at = ahora
            self.animation_progress = 0.0
            return

        self.displayed_step = len(self.displayed_path) - 1
        self.animation_progress = 0.0
        self.animating = False
        self.audio.stop_drive_loop()
        self.audio.play_finish_jingle()
        self._mostrar_modal(self.animation_algorithm or "Resultado", self._lineas_resultado(self.animation_result))
        self.status_message = f"Último algoritmo ejecutado: {self.animation_algorithm}"

    def _procesar_audio_de_celda(self, posicion):
        """Activa los efectos asociados con una celda visitada.

        Args:
            posicion (tuple[int, int]): Posición alcanzada durante la animación.

        Returns:
            None.

        Example:
            >>> app._procesar_audio_de_celda((0, 1))  # doctest: +SKIP
        """
        if self.grid is None:
            return

        fila, columna = posicion
        tipo = self.grid.matriz[fila][columna]

        if tipo == self.grid.FLUJO_ALTO:
            self.audio.play_traffic_horn()

        if posicion in self.grid.pasajeros and posicion not in self.animation_seen_passengers:
            self.animation_seen_passengers.add(posicion)
            self.audio.play_pickup_horn()

    def _mostrar_modal(self, title, lines):
        """Configura y abre un cuadro modal.

        Args:
            title (str): Encabezado del modal.
            lines (list[str]): Líneas de contenido que se mostrarán.

        Returns:
            None.

        Example:
            >>> app._mostrar_modal("Resultado", ["Costo: 4"])  # doctest: +SKIP
            >>> app.modal_visible  # doctest: +SKIP
            True
        """
        self.modal_title = title
        self.modal_lines = lines
        self.modal_visible = True

    def _lineas_resultado(self, resultado):
        """Convierte las métricas de búsqueda en líneas para el modal.

        Args:
            resultado (Mapping[str, object]): Métricas de una solución.

        Returns:
            list[str]: Textos listos para ser renderizados.

        Example:
            >>> lineas = app._lineas_resultado({  # doctest: +SKIP
            ...     "nodos_expandidos": 2, "profundidad": 1,
            ...     "camino": [(0, 0), (0, 1)], "costo": 1
            ... })
            >>> "Costo total: 1" in lineas  # doctest: +SKIP
            True
        """
        tiempo_busqueda_ms = resultado.get("tiempo_busqueda_ms", resultado.get("tiempo", 0))
        lineas = [
            f"Nodos expandidos: {resultado['nodos_expandidos']}",
            f"Profundidad: {resultado['profundidad']}",
            f"Pasos del camino: {len(resultado['camino'])}",
            f"Costo total: {resultado['costo']}",
            f"Tiempo de búsqueda: {tiempo_busqueda_ms} ms",
        ]
        if "heuristica" in resultado:
            lineas.append(f"Heuristica (h): {resultado['heuristica']}")
        return lineas

    def _dibujar(self):
        """Dibuja un fotograma completo y actualiza la pantalla.

        Returns:
            None.

        Example:
            >>> app._dibujar()  # doctest: +SKIP
        """
        self.window.fill(COLOR_APP_BG)
        self._dibujar_header()
        self._dibujar_panel_mapa()
        self._dibujar_panel_lateral()
        if self.modal_visible:
            self._dibujar_modal()
        pygame.display.flip()

    def _dibujar_header(self):
        """Dibuja el encabezado y sus controles de audio y mapa.

        Returns:
            None.

        Example:
            >>> app._dibujar_header()  # doctest: +SKIP
        """
        pygame.draw.rect(self.window, COLOR_PANEL, self.header_rect, border_radius=24)
        pygame.draw.rect(self.window, COLOR_BORDER, self.header_rect, 1, border_radius=24)

        titulo = self.font_title.render(TITULO_APP, True, COLOR_TEXT)
        self.window.blit(titulo, (self.header_rect.x + 26, self.header_rect.y + 18))

        mapa_texto = "Sin mapa"
        if self.map_path is not None:
            mapa_texto = f"Mapa actual: {self.map_path.name}"
        subtitulo = self.font_body.render(mapa_texto, True, COLOR_TEXT_MUTED)
        self.window.blit(subtitulo, (self.header_rect.x + 30, self.header_rect.y + 52))

        self._dibujar_boton(
            self.ambient_toggle_button,
            self._texto_boton_ambiente(),
            activo=self.audio.enabled and self.audio.ambient_enabled,
            color_base=COLOR_CARD_ALT,
            color_hover=(60, 75, 88),
        )

        self._dibujar_boton(
            self.change_map_button,
            "Cambiar mapa",
            activo=False,
            color_base=COLOR_SUCCESS,
            color_hover=(55, 195, 117),
        )

    def _dibujar_panel_mapa(self):
        """Dibuja el contenedor del mapa y el estado actual del taxi.

        Returns:
            None.

        Example:
            >>> app._dibujar_panel_mapa()  # doctest: +SKIP
        """
        pygame.draw.rect(self.window, COLOR_PANEL, self.map_panel_rect, border_radius=28)
        pygame.draw.rect(self.window, COLOR_BORDER, self.map_panel_rect, 1, border_radius=28)

        if self.visualizador is not None:
            paso = 0
            progreso = 0.0
            if self.displayed_path:
                paso = min(self.displayed_step, len(self.displayed_path) - 1)
                progreso = self.animation_progress if self.animating else 0.0
            self.visualizador.dibujar_grid(self.displayed_path, paso, taxi_progreso=progreso)

        etiqueta = self.font_small.render("Vista del mapa", True, COLOR_TEXT_MUTED)
        self.window.blit(etiqueta, (self.map_panel_rect.x + 24, self.map_panel_rect.y + 16))

    def _dibujar_panel_lateral(self):
        """Dibuja categorías, algoritmos y estado de la búsqueda.

        Returns:
            None.

        Example:
            >>> app._dibujar_panel_lateral()  # doctest: +SKIP
        """
        pygame.draw.rect(self.window, COLOR_PANEL, self.panel_rect, border_radius=28)
        pygame.draw.rect(self.window, COLOR_BORDER, self.panel_rect, 1, border_radius=28)

        titulo = self.font_subtitle.render("Algoritmos", True, COLOR_TEXT)
        self.window.blit(titulo, (self.panel_rect.x + 24, self.panel_rect.y + 24))

        descripcion = self.font_body.render("Elige una familia y luego el metodo.", True, COLOR_TEXT_MUTED)
        self.window.blit(descripcion, (self.panel_rect.x + 24, self.panel_rect.y + 56))

        pygame.draw.rect(self.window, COLOR_CARD, self.status_rect, border_radius=16)
        pygame.draw.rect(self.window, COLOR_BORDER, self.status_rect, 1, border_radius=16)
        estado = self.font_small.render(self.status_message, True, COLOR_TEXT)
        self.window.blit(estado, (self.status_rect.x + 14, self.status_rect.centery - estado.get_height() // 2))

        subtitulo = self.font_body.render("Tipo de busqueda", True, COLOR_TEXT)
        self.window.blit(subtitulo, (self.panel_rect.x + 24, self.search_type_label_y))

        for category, rect in self.category_buttons:
            self._dibujar_boton(
                rect,
                CATEGORY_LABELS[category],
                activo=self.selected_category == category,
                color_base=COLOR_CARD_ALT,
                color_hover=(60, 75, 88),
            )

        if self.selected_category is None:
            ayuda_rect = pygame.Rect(self.panel_rect.x + 24, self.category_buttons[0][1].bottom + 28, self.panel_rect.width - 48, 120)
            pygame.draw.rect(self.window, COLOR_CARD, ayuda_rect, border_radius=18)
            pygame.draw.rect(self.window, COLOR_BORDER, ayuda_rect, 1, border_radius=18)
            ayuda = [
                "1. Selecciona Informada o No informada.",
                "2. Apareceran sus subopciones abajo.",
                "3. Haz clic en un algoritmo para animarlo.",
            ]
            for idx, texto in enumerate(ayuda):
                linea = self.font_small.render(texto, True, COLOR_TEXT_MUTED)
                self.window.blit(linea, (ayuda_rect.x + 16, ayuda_rect.y + 20 + idx * 28))
            return

        seccion = self.font_body.render("Subopciones", True, COLOR_TEXT)
        self.window.blit(seccion, (self.panel_rect.x + 24, self.suboptions_label_y))

        for label, key, rect in self.algorithm_buttons:
            self._dibujar_boton(
                rect,
                label,
                activo=self.selected_algorithm == key,
                color_base=COLOR_ACCENT_ALT,
                color_hover=COLOR_ACCENT,
            )

        nota_y = self.panel_rect.bottom - 88
        nota_rect = pygame.Rect(self.panel_rect.x + 24, nota_y, self.panel_rect.width - 48, 60)
        pygame.draw.rect(self.window, COLOR_CARD, nota_rect, border_radius=16)
        pygame.draw.rect(self.window, COLOR_BORDER, nota_rect, 1, border_radius=16)
        texto = "Animacion en curso..." if self.animating else "Cierra el modal y prueba otro algoritmo."
        nota = self.font_small.render(texto, True, COLOR_TEXT_MUTED)
        self.window.blit(nota, (nota_rect.x + 16, nota_rect.y + 20))

    def _dibujar_modal(self):
        """Dibuja el modal activo sobre una capa semitransparente.

        Returns:
            None.

        Example:
            >>> app._dibujar_modal()  # doctest: +SKIP
        """
        overlay = pygame.Surface(self.window.get_size(), pygame.SRCALPHA)
        overlay.fill(COLOR_OVERLAY)
        self.window.blit(overlay, (0, 0))

        pygame.draw.rect(self.window, COLOR_PANEL, self.modal_rect, border_radius=24)
        pygame.draw.rect(self.window, COLOR_BORDER, self.modal_rect, 1, border_radius=24)

        titulo = self.font_modal_title.render(self.modal_title, True, COLOR_TEXT)
        self.window.blit(titulo, (self.modal_rect.x + 28, self.modal_rect.y + 22))

        pygame.draw.rect(self.window, COLOR_CARD_ALT, self.modal_x_button, border_radius=12)
        pygame.draw.rect(self.window, COLOR_BORDER, self.modal_x_button, 1, border_radius=12)
        x_label = self.font_button.render("X", True, COLOR_TEXT)
        self.window.blit(x_label, (self.modal_x_button.centerx - x_label.get_width() // 2, self.modal_x_button.centery - x_label.get_height() // 2))

        for idx, texto in enumerate(self.modal_lines):
            linea = self.font_body.render(texto, True, COLOR_TEXT)
            self.window.blit(linea, (self.modal_rect.x + 36, self.modal_rect.y + 96 + idx * 38))

        pie = self.font_small.render("Cerrar este modal te deja volver al mapa y probar otro algoritmo.", True, COLOR_TEXT_MUTED)
        self.window.blit(pie, (self.modal_rect.x + 36, self.modal_rect.bottom - 112))

        self._dibujar_boton(
            self.modal_close_button,
            "Cerrar",
            activo=False,
            color_base=COLOR_ACCENT,
            color_hover=(90, 174, 255),
        )

    def _dibujar_boton(self, rect, texto, activo=False, color_base=COLOR_CARD_ALT, color_hover=None):
        """Dibuja un botón con estados normal, activo y bajo el cursor.

        Args:
            rect (pygame.Rect): Área ocupada por el botón.
            texto (str): Etiqueta del botón.
            activo (bool): Indica si debe resaltarse como seleccionado.
            color_base (tuple[int, int, int]): Color normal del fondo.
            color_hover (tuple[int, int, int] | None): Color al pasar el cursor;
                si es ``None``, conserva ``color_base``.

        Returns:
            None.

        Example:
            >>> app._dibujar_boton(  # doctest: +SKIP
            ...     pygame.Rect(0, 0, 100, 40), "Aceptar"
            ... )
        """
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)
        color = color_base
        borde = COLOR_BORDER

        if color_hover is None:
            color_hover = color_base

        if activo:
            color = COLOR_ACCENT
            borde = (143, 197, 255)
        elif hover:
            color = color_hover

        pygame.draw.rect(self.window, color, rect, border_radius=14)
        pygame.draw.rect(self.window, borde, rect, 1, border_radius=14)

        label = self.font_button.render(texto, True, COLOR_TEXT)
        self.window.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

    def _texto_boton_ambiente(self):
        """Obtiene la etiqueta del botón de música ambiente.

        Returns:
            str: Estado visible del audio: no disponible, activado o
            desactivado.

        Example:
            >>> texto = app._texto_boton_ambiente()  # doctest: +SKIP
            >>> texto.startswith("Ambiente")  # doctest: +SKIP
            True
        """
        if not self.audio.enabled:
            return "Ambiente N/D"
        if self.audio.ambient_enabled:
            return "Ambiente On"
        return "Ambiente Off"


def main():
    """Inicia la aplicación y ejecuta su bucle principal.

    Si el usuario no selecciona un mapa, cierra Pygame y termina el proceso.

    Returns:
        None.

    Example:
        >>> main()  # doctest: +SKIP
    """
    app = RobotaxiApp()
    if not app.iniciar():
        pygame.quit()
        sys.exit()
    app.ejecutar()

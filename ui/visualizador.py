import os
import sys

import pygame

ruta_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ruta_raiz)

from mundo import Grid


COLOR_FONDO = (168, 180, 190)
COLOR_BORDE_CELDA = (47, 56, 66)
COLOR_CAMINO_LINEA = (84, 212, 255)
COLOR_CAMINO_RELLENO = (84, 212, 255, 92)
COLOR_CAMINO_PUNTO = (233, 248, 255, 220)
COLOR_SOMBRA = (15, 21, 29, 70)
COLOR_INICIO = (40, 196, 118)
COLOR_DESTINO = (255, 200, 74)

TAM_CELDA_BASE = 60
TAM_CELDA_MIN = 42
TAM_CELDA_MAX = 92


class Visualizador:
    """Renderiza el mapa, sus marcadores y la animación del robotaxi.

    Puede crear su propia ventana o dibujar dentro de una superficie y un
    viewport administrados por la aplicación principal.

    Attributes:
        grid (Grid): Mapa que se representa.
        ventana (pygame.Surface): Superficie de dibujo.
        viewport (pygame.Rect): Área disponible para el mapa.
        tam_celda (int): Tamaño calculado de cada celda en píxeles.
        own_display (bool): Indica si controla su propia ventana.

    Example:
        >>> visualizador = Visualizador(grid)  # doctest: +SKIP
        >>> visualizador.grid is grid  # doctest: +SKIP
        True
    """

    def __init__(self, grid, titulo="robotaxi-zoox", surface=None, viewport=None):
        """Inicializa el renderizador y adapta sus recursos al mapa.

        Args:
            grid (Grid): Cuadrícula que se mostrará.
            titulo (str): Título usado al crear una ventana propia.
            surface (pygame.Surface | None): Superficie externa opcional.
            viewport (pygame.Rect | tuple | None): Región de dibujo opcional.

        Returns:
            None.

        Example:
            >>> Visualizador(grid, surface=surface)  # doctest: +SKIP
        """
        if not pygame.get_init():
            pygame.init()

        self.titulo = titulo
        self.grid = None
        self.own_display = surface is None
        self.reloj = pygame.time.Clock()
        self.viewport = pygame.Rect(0, 0, 1, 1)
        self.map_rect = pygame.Rect(0, 0, 1, 1)
        self.tam_celda = TAM_CELDA_BASE
        self.ancho = 0
        self.alto = 0
        self.sprite_size = 0
        self.taxi_sprite_size = 0
        self.passenger_sprite_size = 0
        self.traffic_signal_size = 0
        self.marker_label_font = None
        self.marker_label_size = 0
        self.pasajeros_originales = set()

        if self.own_display:
            ancho = max(640, grid.columnas * TAM_CELDA_BASE)
            alto = max(640, grid.filas * TAM_CELDA_BASE)
            self.ventana = pygame.display.set_mode((ancho, alto))
            pygame.display.set_caption(titulo)
            self.viewport = self.ventana.get_rect()
        else:
            self.ventana = surface
            self.viewport = pygame.Rect(viewport) if viewport is not None else self.ventana.get_rect()

        self._cargar_fuentes()
        self.set_grid(grid)
        self.set_surface(self.ventana, self.viewport)

    def _cargar_fuentes(self):
        """Carga las imágenes originales del taxi, pasajero y terreno.

        Returns:
            None.

        Example:
            >>> visualizador._cargar_fuentes()  # doctest: +SKIP
        """
        self.img_taxi_source = self._cargar_fuente_imagen("imagenes", "robot_taxi.png")
        self.img_pasajero_source = self._cargar_fuente_imagen("imagenes", "pasajero_robot.png")
        self.tile_sources = {
            "road": self._cargar_fuente_imagen("imagenes", "tiles", "road_tile.png"),
            "houses": self._cargar_fuente_imagen("imagenes", "tiles", "houses_tile.png"),
        }

    def _cargar_fuente_imagen(self, *ruta_relativa):
        """Carga una imagen del proyecto conservando el canal alfa.

        Args:
            *ruta_relativa (str): Componentes de la ruta desde la raíz.

        Returns:
            pygame.Surface | None: Imagen cargada o ``None`` si falla.

        Example:
            >>> imagen = visualizador._cargar_fuente_imagen(  # doctest: +SKIP
            ...     "imagenes", "robot_taxi.png"
            ... )
        """
        ruta = os.path.join(ruta_raiz, *ruta_relativa)
        try:
            return pygame.image.load(ruta).convert_alpha()
        except Exception:
            return None

    def set_surface(self, surface, viewport=None):
        """Asigna la superficie de destino y recalcula el diseño.

        Args:
            surface (pygame.Surface): Nueva superficie de dibujo.
            viewport (pygame.Rect | tuple | None): Región disponible; por
                defecto se usa toda la superficie.

        Returns:
            None.

        Example:
            >>> visualizador.set_surface(surface, surface.get_rect())  # doctest: +SKIP
        """
        nuevo_viewport = pygame.Rect(viewport) if viewport is not None else surface.get_rect()
        if surface is self.ventana and nuevo_viewport == self.viewport:
            return
        self.ventana = surface
        self.viewport = nuevo_viewport
        self._recalcular_layout()

    def set_grid(self, grid):
        """Cambia el mapa y conserva sus pasajeros como referencia.

        Args:
            grid (Grid): Nueva cuadrícula que se representará.

        Returns:
            None.

        Example:
            >>> visualizador.set_grid(Grid([[2, 5]]))  # doctest: +SKIP
        """
        self.grid = grid
        self.pasajeros_originales = set(grid.pasajeros)
        self._recalcular_layout()

    def _recalcular_layout(self):
        """Ajusta el mapa, las celdas, los sprites y las fuentes al viewport.

        Returns:
            None.

        Example:
            >>> visualizador._recalcular_layout()  # doctest: +SKIP
            >>> visualizador.tam_celda >= TAM_CELDA_MIN  # doctest: +SKIP
            True
        """
        if self.grid is None:
            return

        if self.own_display:
            self.viewport = self.ventana.get_rect()

        tam_anterior = self.tam_celda
        map_rect_anterior = self.map_rect.copy()
        ancho_celda = max(1, self.viewport.width // self.grid.columnas)
        alto_celda = max(1, self.viewport.height // self.grid.filas)
        self.tam_celda = max(TAM_CELDA_MIN, min(TAM_CELDA_MAX, min(ancho_celda, alto_celda)))

        map_width = self.grid.columnas * self.tam_celda
        map_height = self.grid.filas * self.tam_celda
        map_x = self.viewport.x + (self.viewport.width - map_width) // 2
        map_y = self.viewport.y + (self.viewport.height - map_height) // 2
        self.map_rect = pygame.Rect(map_x, map_y, map_width, map_height)
        self.ancho = map_width
        self.alto = map_height
        self.sprite_size = max(30, int(self.tam_celda * 0.78))
        self.taxi_sprite_size = max(34, int(self.tam_celda * 0.92))
        self.passenger_sprite_size = max(32, int(self.tam_celda * 0.9))
        self.traffic_signal_size = max(18, min(int(self.taxi_sprite_size * 0.6), int(self.tam_celda * 0.58)))
        marker_label_size = max(10, min(16, int(self.tam_celda * 0.24)))
        if self.marker_label_font is None or self.marker_label_size != marker_label_size:
            self.marker_label_size = marker_label_size
            self.marker_label_font = pygame.font.SysFont("Arial", marker_label_size, bold=True)
        if tam_anterior != self.tam_celda or map_rect_anterior.size != self.map_rect.size:
            self._actualizar_assets_escalados()

    def _actualizar_assets_escalados(self):
        """Regenera sprites, tiles y variantes con el tamaño de celda actual.

        Returns:
            None.

        Example:
            >>> visualizador._actualizar_assets_escalados()  # doctest: +SKIP
        """
        self.img_taxi = self._escalar_sprite(self.img_taxi_source, self.taxi_sprite_size, self._crear_taxi_fallback)
        self.img_pasajero = self._escalar_sprite(self.img_pasajero_source, self.passenger_sprite_size, self._crear_pasajero_fallback)

        road = self._escalar_superficie(self.tile_sources["road"], self.tam_celda, self._crear_tile_asfalto)
        houses = self._escalar_superficie(self.tile_sources["houses"], self.tam_celda, self._crear_tile_houses)
        traffic = self._crear_tile_trafico(road)

        self.tiles = {
            "road": road,
            "road_plain": self._crear_tile_asfalto_plano(),
            "houses": houses,
            "traffic": traffic,
        }
        self.tile_variantes = {
            "road": {
                0: self.tiles["road"],
                90: pygame.transform.rotate(self.tiles["road"], 90),
            },
            "traffic": {
                0: self.tiles["traffic"],
                90: pygame.transform.rotate(self.tiles["traffic"], 90),
            },
        }

    def _escalar_imagen(self, source, size, fallback_factory):
        """Escala una imagen cuadrada o construye su reemplazo.

        Args:
            source (pygame.Surface | None): Imagen original.
            size (int): Tamaño final en píxeles.
            fallback_factory (Callable[[], pygame.Surface]): Creador alterno.

        Returns:
            pygame.Surface: Imagen escalada o recurso alternativo.

        Example:
            >>> imagen = visualizador._escalar_imagen(  # doctest: +SKIP
            ...     None, 32, visualizador._crear_taxi_fallback
            ... )
        """
        if source is None:
            return fallback_factory()
        return pygame.transform.smoothscale(source, (size, size))

    def _escalar_sprite(self, source, size, fallback_factory):
        """Recorta el contenido visible de un sprite y lo escala.

        Args:
            source (pygame.Surface | None): Sprite original.
            size (int): Ancho y alto finales.
            fallback_factory (Callable[[], pygame.Surface]): Creador alterno.

        Returns:
            pygame.Surface: Sprite cuadrado escalado.

        Example:
            >>> sprite = visualizador._escalar_sprite(  # doctest: +SKIP
            ...     None, 48, visualizador._crear_pasajero_fallback
            ... )
        """
        if source is None:
            return fallback_factory()

        bbox = source.get_bounding_rect(min_alpha=1)
        if bbox.width <= 0 or bbox.height <= 0:
            return fallback_factory()

        pad_x = max(6, bbox.width // 16)
        pad_y = max(6, bbox.height // 16)
        recorte = pygame.Rect(
            max(0, bbox.x - pad_x),
            max(0, bbox.y - pad_y),
            min(source.get_width() - max(0, bbox.x - pad_x), bbox.width + pad_x * 2),
            min(source.get_height() - max(0, bbox.y - pad_y), bbox.height + pad_y * 2),
        )
        sprite = source.subsurface(recorte).copy()
        return pygame.transform.smoothscale(sprite, (size, size))

    def _escalar_superficie(self, source, size, fallback_factory):
        """Escala un tile o usa una fábrica si el original no existe.

        Args:
            source (pygame.Surface | None): Tile original.
            size (int): Tamaño final de cada lado.
            fallback_factory (Callable[[], pygame.Surface]): Creador alterno.

        Returns:
            pygame.Surface: Tile listo para dibujarse.

        Example:
            >>> tile = visualizador._escalar_superficie(  # doctest: +SKIP
            ...     None, 60, visualizador._crear_tile_asfalto
            ... )
        """
        if source is None:
            return fallback_factory()
        return pygame.transform.smoothscale(source, (size, size))

    def _escalar_superficie_zoom(self, source, size, fallback_factory, zoom=1.0):
        """Recorta el centro de un tile aplicando zoom y luego lo escala.

        Args:
            source (pygame.Surface | None): Imagen de origen.
            size (int): Tamaño final cuadrado.
            fallback_factory (Callable[[], pygame.Surface]): Creador alterno.
            zoom (float): Factor de acercamiento; 1.0 no recorta.

        Returns:
            pygame.Surface: Tile escalado con el zoom solicitado.

        Example:
            >>> tile = visualizador._escalar_superficie_zoom(  # doctest: +SKIP
            ...     source, 60, visualizador._crear_tile_asfalto, 1.2
            ... )
        """
        if source is None:
            return fallback_factory()
        if zoom <= 1.0:
            return pygame.transform.smoothscale(source, (size, size))

        recorte_ancho = max(1, int(source.get_width() / zoom))
        recorte_alto = max(1, int(source.get_height() / zoom))
        recorte = pygame.Rect(
            (source.get_width() - recorte_ancho) // 2,
            (source.get_height() - recorte_alto) // 2,
            recorte_ancho,
            recorte_alto,
        )
        tile = source.subsurface(recorte).copy()
        return pygame.transform.smoothscale(tile, (size, size))

    def _crear_tile_asfalto(self):
        """Crea un tile vertical de asfalto cuando no hay imagen disponible.

        Returns:
            pygame.Surface: Superficie de tamaño ``tam_celda``.

        Example:
            >>> tile = visualizador._crear_tile_asfalto()  # doctest: +SKIP
            >>> tile.get_width() == visualizador.tam_celda  # doctest: +SKIP
            True
        """
        surface = pygame.Surface((self.tam_celda, self.tam_celda))
        rect = surface.get_rect()
        surface.fill((62, 68, 73))
        pygame.draw.rect(surface, (72, 78, 84), rect, 1, border_radius=max(3, self.tam_celda // 10))

        carril_x = rect.centerx - max(1, self.tam_celda // 18)
        salto = max(8, self.tam_celda // 5)
        largo = max(4, self.tam_celda // 10)
        ancho = max(2, self.tam_celda // 16)
        for top in range(6, rect.height - 6, salto):
            pygame.draw.rect(surface, (228, 228, 222), (carril_x, top, ancho, largo), border_radius=2)

        radio = max(4, self.tam_celda // 10)
        cx, cy = rect.centerx - self.tam_celda // 6, rect.centery - self.tam_celda // 5
        pygame.draw.circle(surface, (82, 87, 92), (cx, cy), radio)
        pygame.draw.circle(surface, (34, 37, 40), (cx, cy), radio, 2)
        drenaje = pygame.Rect(rect.left + max(4, self.tam_celda // 15), rect.bottom - max(18, self.tam_celda // 3), max(6, self.tam_celda // 9), max(12, self.tam_celda // 5))
        pygame.draw.rect(surface, (56, 60, 64), drenaje, border_radius=1)

        return surface

    def _crear_tile_asfalto_plano(self):
        """Crea un tile de asfalto sin marcas de orientación.

        Returns:
            pygame.Surface: Superficie cuadrada de asfalto.

        Example:
            >>> visualizador._crear_tile_asfalto_plano()  # doctest: +SKIP
        """
        surface = pygame.Surface((self.tam_celda, self.tam_celda))
        rect = surface.get_rect()
        surface.fill((61, 66, 71))
        pygame.draw.rect(surface, (71, 76, 81), rect, 1, border_radius=max(3, self.tam_celda // 10))
        radio = max(4, self.tam_celda // 10)
        cx, cy = rect.centerx - self.tam_celda // 7, rect.centery - self.tam_celda // 5
        pygame.draw.circle(surface, (82, 87, 92), (cx, cy), radio)
        pygame.draw.circle(surface, (34, 37, 40), (cx, cy), radio, 2)
        drenaje = pygame.Rect(rect.left + max(4, self.tam_celda // 15), rect.bottom - max(18, self.tam_celda // 3), max(6, self.tam_celda // 9), max(12, self.tam_celda // 5))
        pygame.draw.rect(surface, (56, 60, 64), drenaje, border_radius=1)
        return surface

    def _crear_tile_houses(self):
        """Crea el tile alternativo que representa una celda de muro.

        Returns:
            pygame.Surface: Ilustración cuadrada de un edificio.

        Example:
            >>> visualizador._crear_tile_houses()  # doctest: +SKIP
        """
        surface = pygame.Surface((self.tam_celda, self.tam_celda))
        surface.fill((86, 92, 97))
        offset = max(6, self.tam_celda // 8)
        tam = self.tam_celda - offset * 2
        sombra = pygame.Rect(offset + 3, offset + 3, tam, tam)
        pygame.draw.rect(surface, (45, 49, 54), sombra, border_radius=max(4, self.tam_celda // 10))

        edificio = pygame.Rect(offset, offset, tam, tam)
        pygame.draw.rect(surface, (198, 190, 176), edificio, border_radius=max(4, self.tam_celda // 10))
        pygame.draw.rect(surface, (122, 118, 110), edificio, 2, border_radius=max(4, self.tam_celda // 10))

        techo = edificio.inflate(-max(8, self.tam_celda // 7), -max(8, self.tam_celda // 7))
        pygame.draw.rect(surface, (214, 208, 196), techo, border_radius=max(3, self.tam_celda // 14))
        pygame.draw.rect(surface, (156, 151, 142), techo, 1, border_radius=max(3, self.tam_celda // 14))

        claraboya = pygame.Rect(techo.left + max(4, self.tam_celda // 12), techo.top + max(4, self.tam_celda // 12), max(8, self.tam_celda // 6), max(6, self.tam_celda // 8))
        pygame.draw.rect(surface, (98, 142, 171), claraboya, border_radius=2)
        pygame.draw.rect(surface, (223, 233, 240), claraboya, 1, border_radius=2)

        hvac1 = pygame.Rect(techo.right - max(14, self.tam_celda // 5), techo.top + max(5, self.tam_celda // 12), max(7, self.tam_celda // 8), max(7, self.tam_celda // 8))
        hvac2 = pygame.Rect(techo.right - max(18, self.tam_celda // 4), techo.bottom - max(12, self.tam_celda // 6), max(10, self.tam_celda // 6), max(6, self.tam_celda // 9))
        pygame.draw.rect(surface, (126, 132, 139), hvac1, border_radius=2)
        pygame.draw.rect(surface, (108, 114, 121), hvac2, border_radius=2)

        acceso = pygame.Rect(edificio.centerx - max(6, self.tam_celda // 12), edificio.bottom - max(12, self.tam_celda // 6), max(12, self.tam_celda // 6), max(8, self.tam_celda // 8))
        pygame.draw.rect(surface, (148, 111, 76), acceso, border_radius=2)
        pygame.draw.rect(surface, (96, 71, 46), acceso, 1, border_radius=2)

        for x in (edificio.left + tam // 4, edificio.left + tam // 2, edificio.left + (tam * 3) // 4):
            pygame.draw.line(surface, (173, 167, 155), (x, edificio.top + max(5, self.tam_celda // 12)), (x, edificio.bottom - max(6, self.tam_celda // 10)), 1)

        pygame.draw.rect(surface, (70, 74, 78), surface.get_rect(), 2, border_radius=max(3, self.tam_celda // 10))
        return surface

    def _crear_tile_trafico(self, road_tile=None):
        """Añade señales de tráfico a un tile de carretera.

        Args:
            road_tile (pygame.Surface | None): Carretera base opcional.

        Returns:
            pygame.Surface: Tile de flujo alto con semáforo y advertencia.

        Example:
            >>> visualizador._crear_tile_trafico()  # doctest: +SKIP
        """
        if road_tile is None:
            surface = self._crear_tile_asfalto()
        else:
            surface = road_tile.copy()

        rect = surface.get_rect()
        borde_lateral = max(8, self.tam_celda // 6)
        linea_parada_y = rect.centery - max(6, self.tam_celda // 10)
        linea_parada = pygame.Rect(
            borde_lateral,
            linea_parada_y,
            rect.width - borde_lateral * 2,
            max(3, self.tam_celda // 14),
        )
        pygame.draw.rect(surface, (244, 244, 238), linea_parada, border_radius=2)

        sombra = pygame.Surface((self.tam_celda, self.tam_celda), pygame.SRCALPHA)
        pygame.draw.rect(
            sombra,
            (0, 0, 0, 34),
            (
                max(6, self.tam_celda // 12),
                max(6, self.tam_celda // 12),
                self.tam_celda - max(12, self.tam_celda // 6),
                self.tam_celda - max(12, self.tam_celda // 6),
            ),
            border_radius=max(8, self.tam_celda // 7),
        )
        surface.blit(sombra, (0, 0))

        semaforo_x = rect.right - max(12, self.tam_celda // 6)
        semaforo_y = rect.centery - max(6, self.tam_celda // 12)
        self._dibujar_semaforo(surface, (semaforo_x, semaforo_y))

        advertencia = pygame.Rect(
            rect.left + max(7, self.tam_celda // 10),
            rect.top + max(8, self.tam_celda // 9),
            max(16, self.tam_celda // 3),
            max(8, self.tam_celda // 6),
        )
        pygame.draw.rect(surface, (42, 47, 54), advertencia, border_radius=4)
        pygame.draw.rect(surface, (210, 179, 56), advertencia, 1, border_radius=4)
        pygame.draw.circle(
            surface,
            (226, 68, 66),
            advertencia.center,
            max(2, min(advertencia.width, advertencia.height) // 4),
        )
        return surface

    def _crear_taxi_fallback(self):
        """Dibuja un sprite alternativo para el taxi.

        Returns:
            pygame.Surface: Sprite transparente del vehículo.

        Example:
            >>> visualizador._crear_taxi_fallback()  # doctest: +SKIP
        """
        surface = pygame.Surface((self.taxi_sprite_size, self.taxi_sprite_size), pygame.SRCALPHA)
        rect = surface.get_rect()
        pygame.draw.ellipse(surface, (0, 0, 0, 45), rect.inflate(-8, -6).move(0, 3))
        carro = rect.inflate(-10, -16)
        pygame.draw.rect(surface, (255, 205, 58), carro, border_radius=max(6, self.taxi_sprite_size // 8))
        pygame.draw.rect(surface, (238, 150, 43), carro, 2, border_radius=max(6, self.taxi_sprite_size // 8))
        cabina = pygame.Rect(carro.left + max(6, self.taxi_sprite_size // 10), carro.top + max(6, self.taxi_sprite_size // 10), carro.width - max(12, self.taxi_sprite_size // 5), carro.height - max(12, self.taxi_sprite_size // 5))
        pygame.draw.rect(surface, (98, 203, 255), cabina, border_radius=max(5, self.taxi_sprite_size // 10))
        pygame.draw.rect(surface, (248, 248, 244), (cabina.centerx - max(7, self.taxi_sprite_size // 12), cabina.top + 3, max(14, self.taxi_sprite_size // 6), max(5, self.taxi_sprite_size // 10)), border_radius=2)
        return surface

    def _crear_pasajero_fallback(self):
        """Dibuja un sprite alternativo para los pasajeros.

        Returns:
            pygame.Surface: Sprite transparente de una persona.

        Example:
            >>> visualizador._crear_pasajero_fallback()  # doctest: +SKIP
        """
        surface = pygame.Surface((self.passenger_sprite_size, self.passenger_sprite_size), pygame.SRCALPHA)
        cx = surface.get_width() // 2
        pygame.draw.ellipse(surface, (0, 0, 0, 40), (cx - 12, surface.get_height() - 16, 24, 8))
        pygame.draw.circle(surface, (255, 223, 180), (cx, max(12, self.passenger_sprite_size // 4)), max(7, self.passenger_sprite_size // 7))
        torso = pygame.Rect(cx - max(10, self.passenger_sprite_size // 5), max(20, self.passenger_sprite_size // 3), max(20, self.passenger_sprite_size // 3), max(18, self.passenger_sprite_size // 3))
        pygame.draw.rect(surface, (76, 132, 255), torso, border_radius=max(6, self.passenger_sprite_size // 10))
        pygame.draw.line(surface, (52, 58, 65), (cx - 5, torso.bottom - 1), (cx - 10, surface.get_height() - 10), 3)
        pygame.draw.line(surface, (52, 58, 65), (cx + 5, torso.bottom - 1), (cx + 10, surface.get_height() - 10), 3)
        pygame.draw.line(surface, (52, 58, 65), (cx - 8, torso.top + 5), (cx - 16, torso.centery + 2), 3)
        pygame.draw.line(surface, (52, 58, 65), (cx + 8, torso.top + 5), (cx + 16, torso.centery + 2), 3)
        return surface

    def _dibujar_auto_vertical(self, surface, rect, color):
        """Dibuja un automóvil vertical simplificado.

        Args:
            surface (pygame.Surface): Superficie de destino.
            rect (pygame.Rect): Área ocupada por el automóvil.
            color (tuple[int, int, int]): Color RGB de la carrocería.

        Returns:
            None.

        Example:
            >>> visualizador._dibujar_auto_vertical(  # doctest: +SKIP
            ...     surface, pygame.Rect(0, 0, 20, 40), (255, 0, 0)
            ... )
        """
        pygame.draw.rect(surface, color, rect, border_radius=max(4, rect.width // 4))
        ventana = pygame.Rect(rect.left + 2, rect.top + max(3, rect.height // 8), rect.width - 4, rect.height - max(6, rect.height // 4))
        pygame.draw.rect(surface, (73, 99, 123), ventana, border_radius=max(3, rect.width // 4))
        pygame.draw.rect(surface, (233, 239, 245), ventana, 1, border_radius=max(3, rect.width // 4))
        pygame.draw.line(surface, (31, 36, 41), (rect.centerx, ventana.top + 1), (rect.centerx, ventana.bottom - 1), 1)

    def _dibujar_semaforo(self, surface, centro):
        """Dibuja un semáforo con poste y tres luces.

        Args:
            surface (pygame.Surface): Superficie de destino.
            centro (tuple[int, int]): Centro del cuerpo del semáforo.

        Returns:
            None.

        Example:
            >>> visualizador._dibujar_semaforo(surface, (30, 30))  # doctest: +SKIP
        """
        cuerpo_alto = self.traffic_signal_size
        cuerpo_ancho = max(12, int(cuerpo_alto * 0.44))
        cuerpo = pygame.Rect(0, 0, cuerpo_ancho, cuerpo_alto)
        cuerpo.center = centro

        poste_alto = max(10, self.tam_celda // 5)
        poste_y = min(surface.get_height() - poste_alto, cuerpo.bottom - 2)
        pygame.draw.rect(
            surface,
            (62, 68, 74),
            (cuerpo.centerx - 2, poste_y, 4, poste_alto),
            border_radius=2,
        )
        pygame.draw.rect(
            surface,
            (30, 35, 40),
            cuerpo.inflate(4, 4),
            border_radius=max(4, cuerpo_ancho // 3),
        )
        pygame.draw.rect(
            surface,
            (46, 52, 58),
            cuerpo,
            border_radius=max(4, cuerpo_ancho // 3),
        )
        pygame.draw.rect(
            surface,
            (104, 112, 120),
            cuerpo,
            1,
            border_radius=max(4, cuerpo_ancho // 3),
        )

        radio = max(3, int(cuerpo_ancho * 0.24))
        separacion = max(7, cuerpo_alto // 3)
        colores = ((226, 68, 66), (247, 191, 53), (64, 194, 107))
        for idx, color in enumerate(colores):
            centro_luz = (cuerpo.centerx, cuerpo.top + max(7, self.tam_celda // 9) + idx * separacion)
            brillo = pygame.Surface((radio * 5, radio * 5), pygame.SRCALPHA)
            pygame.draw.circle(brillo, (*color, 36), (brillo.get_width() // 2, brillo.get_height() // 2), radio * 2)
            brillo_rect = brillo.get_rect(center=centro_luz)
            surface.blit(brillo, brillo_rect.topleft)
            pygame.draw.circle(surface, color, centro_luz, radio)
            pygame.draw.circle(surface, (245, 247, 249), centro_luz, max(1, radio // 3))

    def _conexiones_calle(self, fila, columna):
        """Consulta las conexiones transitables de una celda.

        Args:
            fila (int): Fila de la celda.
            columna (int): Columna de la celda.

        Returns:
            dict[str, bool]: Disponibilidad en las cuatro direcciones.

        Example:
            >>> visualizador._conexiones_calle(0, 0)  # doctest: +SKIP
            {'up': False, 'down': False, 'left': False, 'right': True}
        """
        return {
            "up": self.grid.es_transitable(fila - 1, columna),
            "down": self.grid.es_transitable(fila + 1, columna),
            "left": self.grid.es_transitable(fila, columna - 1),
            "right": self.grid.es_transitable(fila, columna + 1),
        }

    def _angulo_calle(self, fila, columna):
        """Determina la orientación visual dominante de una calle.

        Args:
            fila (int): Fila de la celda.
            columna (int): Columna de la celda.

        Returns:
            int | None: 0 para vertical, 90 para horizontal o ``None`` cuando
            no existe una orientación dominante.

        Example:
            >>> visualizador._angulo_calle(0, 0)  # doctest: +SKIP
            90
        """
        conexiones = self._conexiones_calle(fila, columna)
        verticales = int(conexiones["up"]) + int(conexiones["down"])
        horizontales = int(conexiones["left"]) + int(conexiones["right"])

        if horizontales > verticales:
            return 90
        if verticales > horizontales:
            return 0
        if conexiones["left"] and conexiones["right"]:
            return 90
        if conexiones["up"] and conexiones["down"]:
            return 0
        return None

    def _tile_para_celda(self, tipo, fila, columna):
        """Selecciona el tile y su orientación para una celda.

        Args:
            tipo (int): Código de celda definido por ``Grid``.
            fila (int): Fila de la celda.
            columna (int): Columna de la celda.

        Returns:
            pygame.Surface: Tile listo para dibujarse.

        Example:
            >>> tile = visualizador._tile_para_celda(Grid.LIBRE, 0, 0)  # doctest: +SKIP
        """
        if tipo == Grid.MURO:
            return self.tiles["houses"]

        angulo = self._angulo_calle(fila, columna)
        if tipo == Grid.FLUJO_ALTO:
            if angulo is None:
                conexiones = self._conexiones_calle(fila, columna)
                angulo = 90 if conexiones["left"] or conexiones["right"] else 0
            return self.tile_variantes["traffic"][angulo]

        if angulo is None:
            return self.tiles["road_plain"]
        return self.tile_variantes["road"][angulo]

    def _celda_a_pixel(self, fila, columna):
        """Convierte una posición del mapa en coordenadas de pantalla.

        Args:
            fila (int): Fila de la celda.
            columna (int): Columna de la celda.

        Returns:
            tuple[int, int]: Esquina superior izquierda en píxeles.

        Example:
            >>> visualizador._celda_a_pixel(0, 0)  # doctest: +SKIP
            (0, 0)
        """
        return (
            self.map_rect.x + columna * self.tam_celda,
            self.map_rect.y + fila * self.tam_celda,
        )

    def _blit_centrado(self, surface, x, y):
        """Dibuja una superficie centrada dentro de una celda.

        Args:
            surface (pygame.Surface): Imagen que se dibujará.
            x (int): Coordenada horizontal de la celda.
            y (int): Coordenada vertical de la celda.

        Returns:
            None.

        Example:
            >>> visualizador._blit_centrado(sprite, 0, 0)  # doctest: +SKIP
        """
        rect = surface.get_rect(center=(x + self.tam_celda // 2, y + self.tam_celda // 2))
        self.ventana.blit(surface, rect.topleft)

    def _dibujar_sombra_celda(self, rect):
        """Dibuja una sombra translúcida bajo una celda.

        Args:
            rect (pygame.Rect): Rectángulo de la celda.

        Returns:
            None.

        Example:
            >>> visualizador._dibujar_sombra_celda(  # doctest: +SKIP
            ...     pygame.Rect(0, 0, 60, 60)
            ... )
        """
        sombra = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(sombra, COLOR_SOMBRA, sombra.get_rect(), border_radius=max(4, self.tam_celda // 10))
        self.ventana.blit(sombra, (rect.x + 1, rect.y + 2))

    def _dibujar_etiqueta_marcador(self, x, y, texto, color):
        """Dibuja la cápsula de texto de un marcador.

        Args:
            x (int): Coordenada horizontal de la celda.
            y (int): Coordenada vertical de la celda.
            texto (str): Texto del marcador.
            color (tuple[int, int, int]): Color RGB del borde.

        Returns:
            None.

        Example:
            >>> visualizador._dibujar_etiqueta_marcador(  # doctest: +SKIP
            ...     0, 0, "Inicio", COLOR_INICIO
            ... )
        """
        if self.marker_label_font is None:
            return

        label = self.marker_label_font.render(texto, True, (248, 251, 255))
        pad_x = max(5, self.tam_celda // 10)
        pad_y = max(2, self.tam_celda // 14)
        ancho = label.get_width() + pad_x * 2
        alto = label.get_height() + pad_y * 2

        etiqueta = pygame.Rect(0, 0, ancho, alto)
        etiqueta.centerx = x + self.tam_celda // 2
        etiqueta.y = y + max(3, self.tam_celda // 18)

        sombra = pygame.Surface((etiqueta.width + 6, etiqueta.height + 6), pygame.SRCALPHA)
        pygame.draw.rect(sombra, (0, 0, 0, 70), sombra.get_rect(), border_radius=max(7, self.tam_celda // 7))
        self.ventana.blit(sombra, (etiqueta.x - 2, etiqueta.y + 2))

        capsule = pygame.Surface((etiqueta.width, etiqueta.height), pygame.SRCALPHA)
        pygame.draw.rect(capsule, (18, 24, 31, 220), capsule.get_rect(), border_radius=max(7, self.tam_celda // 7))
        pygame.draw.rect(capsule, color, capsule.get_rect(), 2, border_radius=max(7, self.tam_celda // 7))
        self.ventana.blit(capsule, etiqueta.topleft)
        self.ventana.blit(label, (etiqueta.x + pad_x, etiqueta.y + pad_y))

    def _dibujar_marcador_inicio(self, x, y):
        """Dibuja el indicador visual de la celda inicial.

        Args:
            x (int): Coordenada horizontal de la celda.
            y (int): Coordenada vertical de la celda.

        Returns:
            None.

        Example:
            >>> visualizador._dibujar_marcador_inicio(0, 0)  # doctest: +SKIP
        """
        self._dibujar_etiqueta_marcador(x, y, "Inicio", COLOR_INICIO)
        radio = max(8, self.tam_celda // 6)
        centro = (x + radio + 4, y + max(24, self.tam_celda // 2))
        pygame.draw.circle(self.ventana, (10, 15, 20), centro, radio + 5)
        pygame.draw.circle(self.ventana, (255, 255, 255), centro, radio + 2)
        pygame.draw.circle(self.ventana, COLOR_INICIO, centro, radio)
        pygame.draw.polygon(
            self.ventana,
            (255, 255, 255),
            [
                (centro[0] - 2, centro[1] - 4),
                (centro[0] - 2, centro[1] + 4),
                (centro[0] + 5, centro[1]),
            ],
        )

    def _dibujar_marcador_destino(self, x, y):
        """Dibuja el indicador visual de la celda de destino.

        Args:
            x (int): Coordenada horizontal de la celda.
            y (int): Coordenada vertical de la celda.

        Returns:
            None.

        Example:
            >>> visualizador._dibujar_marcador_destino(60, 0)  # doctest: +SKIP
        """
        self._dibujar_etiqueta_marcador(x, y, "Meta", COLOR_DESTINO)
        radio = max(8, self.tam_celda // 6)
        centro = (x + self.tam_celda - radio - 4, y + max(24, self.tam_celda // 2))
        pygame.draw.circle(self.ventana, (10, 15, 20), centro, radio + 5)
        pygame.draw.circle(self.ventana, (255, 255, 255), centro, radio + 2)
        pygame.draw.circle(self.ventana, COLOR_DESTINO, centro, radio)
        estrella = [
            (centro[0], centro[1] - 4),
            (centro[0] + 2, centro[1] - 1),
            (centro[0] + 5, centro[1]),
            (centro[0] + 2, centro[1] + 2),
            (centro[0] + 1, centro[1] + 5),
            (centro[0], centro[1] + 3),
            (centro[0] - 1, centro[1] + 5),
            (centro[0] - 2, centro[1] + 2),
            (centro[0] - 5, centro[1]),
            (centro[0] - 2, centro[1] - 1),
        ]
        pygame.draw.polygon(self.ventana, (116, 73, 12), estrella)

    def _dibujar_camino(self, camino, paso_actual):
        """Resalta el tramo recorrido de una solución.

        Args:
            camino (Sequence[tuple[int, int]] | None): Ruta calculada.
            paso_actual (int): Índice del último paso alcanzado.

        Returns:
            None.

        Example:
            >>> visualizador._dibujar_camino([(0, 0), (0, 1)], 1)  # doctest: +SKIP
        """
        if not camino or paso_actual >= len(camino):
            return

        overlay = pygame.Surface(self.ventana.get_size(), pygame.SRCALPHA)
        puntos = []

        for fila, columna in camino[: paso_actual + 1]:
            x, y = self._celda_a_pixel(fila, columna)
            rect = pygame.Rect(
                x + max(6, self.tam_celda // 7),
                y + max(6, self.tam_celda // 7),
                self.tam_celda - max(12, self.tam_celda // 4),
                self.tam_celda - max(12, self.tam_celda // 4),
            )
            pygame.draw.rect(overlay, COLOR_CAMINO_RELLENO, rect, border_radius=max(10, self.tam_celda // 4))
            puntos.append((x + self.tam_celda // 2, y + self.tam_celda // 2))

        if len(puntos) > 1:
            pygame.draw.lines(overlay, COLOR_CAMINO_LINEA, False, puntos, max(4, self.tam_celda // 9))

        for punto in puntos:
            pygame.draw.circle(overlay, COLOR_CAMINO_PUNTO, punto, max(3, self.tam_celda // 13))

        self.ventana.blit(overlay, (0, 0))

    def _direccion_a_angulo(self, origen, destino):
        """Convierte un movimiento entre celdas en un ángulo de sprite.

        Args:
            origen (tuple[int, int]): Posición de partida.
            destino (tuple[int, int]): Posición contigua de llegada.

        Returns:
            int: Ángulo en grados para orientar el taxi.

        Example:
            >>> visualizador._direccion_a_angulo((0, 0), (0, 1))
            -90
        """
        delta_fila = destino[0] - origen[0]
        delta_columna = destino[1] - origen[1]
        if delta_fila < 0:
            return 0
        if delta_fila > 0:
            return 180
        if delta_columna > 0:
            return -90
        if delta_columna < 0:
            return 90
        return 0

    def _interpolar_angulo(self, origen, destino, progreso):
        """Interpola dos ángulos usando el giro más corto.

        Args:
            origen (float): Ángulo inicial en grados.
            destino (float): Ángulo final en grados.
            progreso (float): Fracción de interpolación.

        Returns:
            float: Ángulo interpolado.

        Example:
            >>> visualizador._interpolar_angulo(0, 90, 0.5)
            45.0
        """
        delta = (destino - origen + 180) % 360 - 180
        return origen + delta * progreso

    def _ease(self, progreso):
        """Aplica una curva suave de aceleración y desaceleración.

        Args:
            progreso (float): Fracción lineal entre 0.0 y 1.0.

        Returns:
            float: Progreso suavizado con una función *smoothstep*.

        Example:
            >>> visualizador._ease(0.5)
            0.5
        """
        return progreso * progreso * (3 - 2 * progreso)

    def _estado_taxi(self, camino, paso_actual, progreso):
        """Calcula la posición y orientación interpoladas del taxi.

        Args:
            camino (Sequence[tuple[int, int]]): Ruta del taxi.
            paso_actual (int): Índice de la celda de origen del tramo.
            progreso (float): Avance del tramo entre 0.0 y 1.0.

        Returns:
            dict[str, tuple[float, float] | float] | None: Centro y ángulo del
            taxi, o ``None`` si no hay camino.

        Example:
            >>> estado = visualizador._estado_taxi(  # doctest: +SKIP
            ...     [(0, 0), (0, 1)], 0, 0.5
            ... )
            >>> "centro" in estado  # doctest: +SKIP
            True
        """
        if not camino:
            return None

        if len(camino) == 1 or paso_actual >= len(camino) - 1:
            fila, columna = camino[-1]
            x, y = self._celda_a_pixel(fila, columna)
            angulo = 0
            if len(camino) > 1:
                angulo = self._direccion_a_angulo(camino[-2], camino[-1])
            return {
                "centro": (x + self.tam_celda / 2, y + self.tam_celda / 2),
                "angulo": angulo,
            }

        origen = camino[paso_actual]
        destino = camino[paso_actual + 1]
        origen_x, origen_y = self._celda_a_pixel(*origen)
        destino_x, destino_y = self._celda_a_pixel(*destino)

        progreso_suave = self._ease(max(0.0, min(1.0, progreso)))
        centro_x = (origen_x + self.tam_celda / 2) + (destino_x - origen_x) * progreso_suave
        centro_y = (origen_y + self.tam_celda / 2) + (destino_y - origen_y) * progreso_suave

        angulo_actual = self._direccion_a_angulo(origen, destino)
        if paso_actual == 0:
            angulo = angulo_actual
        else:
            angulo_previo = self._direccion_a_angulo(camino[paso_actual - 1], origen)
            angulo = self._interpolar_angulo(angulo_previo, angulo_actual, progreso_suave)

        return {
            "centro": (centro_x, centro_y),
            "angulo": angulo,
        }

    def _dibujar_taxi(self, taxi_estado):
        """Dibuja el taxi rotado y su sombra.

        Args:
            taxi_estado (Mapping[str, object]): Centro y ángulo calculados por
                ``_estado_taxi``.

        Returns:
            None.

        Example:
            >>> visualizador._dibujar_taxi({  # doctest: +SKIP
            ...     "centro": (30, 30), "angulo": 0
            ... })
        """
        centro_x, centro_y = taxi_estado["centro"]
        angulo = taxi_estado["angulo"]
        taxi_size = self.img_taxi.get_width()
        sombra = pygame.Surface((taxi_size, taxi_size), pygame.SRCALPHA)
        pygame.draw.ellipse(
            sombra,
            (0, 0, 0, 45),
            (6, taxi_size - 16, taxi_size - 12, 10),
        )
        sombra_rect = sombra.get_rect(center=(centro_x, centro_y + 2))
        self.ventana.blit(sombra, sombra_rect.topleft)
        taxi_rotado = pygame.transform.rotozoom(self.img_taxi, angulo, 1.0)
        taxi_rect = taxi_rotado.get_rect(center=(centro_x, centro_y))
        self.ventana.blit(taxi_rotado, taxi_rect.topleft)

    def dibujar_grid(self, camino=None, paso_actual=0, taxi_progreso=0.0):
        """Dibuja el mapa, los pasajeros, el camino y el taxi.

        Args:
            camino (Sequence[tuple[int, int]] | None): Solución que se resalta.
            paso_actual (int): Última posición alcanzada en la solución.
            taxi_progreso (float): Avance interpolado al siguiente paso.

        Returns:
            None.

        Example:
            >>> visualizador.dibujar_grid([(0, 0), (0, 1)], 0, 0.5)  # doctest: +SKIP
        """
        pygame.draw.rect(self.ventana, COLOR_FONDO, self.viewport, border_radius=24)

        pasajeros_recogidos = set()
        if camino and paso_actual < len(camino):
            for pos in camino[: paso_actual + 1]:
                if pos in self.pasajeros_originales:
                    pasajeros_recogidos.add(pos)

        for fila in range(self.grid.filas):
            for columna in range(self.grid.columnas):
                x, y = self._celda_a_pixel(fila, columna)
                rect = pygame.Rect(x, y, self.tam_celda, self.tam_celda)
                tipo = self.grid.matriz[fila][columna]

                self._dibujar_sombra_celda(rect)
                self.ventana.blit(self._tile_para_celda(tipo, fila, columna), rect.topleft)
                pygame.draw.rect(self.ventana, COLOR_BORDE_CELDA, rect, 2, border_radius=max(4, self.tam_celda // 10))

                if tipo == Grid.INICIO:
                    self._dibujar_marcador_inicio(x, y)
                elif tipo == Grid.DESTINO:
                    self._dibujar_marcador_destino(x, y)

                if tipo == Grid.PASAJERO and (fila, columna) not in pasajeros_recogidos:
                    self._blit_centrado(self.img_pasajero, x, y)

        self._dibujar_camino(camino, paso_actual)

        if camino and paso_actual < len(camino):
            taxi_estado = self._estado_taxi(camino, paso_actual, taxi_progreso)
            if taxi_estado is not None:
                self._dibujar_taxi(taxi_estado)

    def animar_camino(self, camino, resultado, nombre_algoritmo, delay=300):
        """Anima una solución cuando el visualizador controla la ventana.

        Args:
            camino (Sequence[tuple[int, int]]): Ruta que se animará.
            resultado (Mapping[str, object]): Métricas mostradas al finalizar.
            nombre_algoritmo (str): Nombre incluido en el reporte.
            delay (int): Milisegundos de espera entre pasos.

        Returns:
            None.

        Example:
            >>> visualizador.animar_camino(  # doctest: +SKIP
            ...     camino, resultado, "A*", delay=100
            ... )
        """
        if not camino or not self.own_display:
            return

        paso = 0
        ejecutando = True

        while ejecutando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

            self.ventana.fill((24, 28, 34))
            self.dibujar_grid(camino, paso, taxi_progreso=0.0)
            pygame.display.flip()

            if paso < len(camino) - 1:
                paso += 1
                pygame.time.wait(delay)
            else:
                self.mostrar_exito()
                ejecutando = False

        self.mostrar_reporte(resultado, nombre_algoritmo)

    def mostrar_exito(self, duracion=1500):
        """Muestra temporalmente un aviso de llegada a la meta.

        Args:
            duracion (int): Tiempo visible en milisegundos.

        Returns:
            None.

        Example:
            >>> visualizador.mostrar_exito(500)  # doctest: +SKIP
        """
        overlay = pygame.Surface(self.ventana.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        fuente = pygame.font.SysFont("Arial", 36, bold=True)
        texto = fuente.render("¡Llegó a la meta!", True, (255, 255, 255))
        self.ventana.blit(overlay, (0, 0))
        self.ventana.blit(
            texto,
            (
                self.viewport.centerx - texto.get_width() // 2,
                self.viewport.centery - texto.get_height() // 2,
            ),
        )
        pygame.display.flip()
        pygame.time.wait(duracion)

    def mostrar_reporte(self, resultado, nombre_algoritmo):
        """Muestra un modal interactivo con las métricas de búsqueda.

        Args:
            resultado (Mapping[str, object]): Métricas de la solución.
            nombre_algoritmo (str): Nombre del algoritmo ejecutado.

        Returns:
            None.

        Example:
            >>> visualizador.mostrar_reporte(resultado, "A*")  # doctest: +SKIP
        """
        fuente_titulo = pygame.font.SysFont("Arial", 26, bold=True)
        fuente_texto = pygame.font.SysFont("Arial", 20)
        boton = pygame.Rect(self.viewport.centerx - 80, self.viewport.centery + 140, 160, 44)
        tiempo_busqueda_ms = resultado.get("tiempo_busqueda_ms", resultado.get("tiempo", 0))

        while True:
            overlay = pygame.Surface(self.ventana.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.ventana.blit(overlay, (0, 0))

            modal = pygame.Rect(0, 0, min(520, self.viewport.width - 40), 360)
            modal.center = self.viewport.center
            pygame.draw.rect(self.ventana, (29, 34, 40), modal, border_radius=18)
            pygame.draw.rect(self.ventana, (88, 101, 114), modal, 1, border_radius=18)

            titulo = fuente_titulo.render(f"Reporte — {nombre_algoritmo}", True, (255, 255, 255))
            self.ventana.blit(titulo, (modal.centerx - titulo.get_width() // 2, modal.y + 26))

            lineas = [
                f"Nodos expandidos : {resultado['nodos_expandidos']}",
                f"Profundidad      : {resultado['profundidad']}",
                f"Pasos en camino  : {len(resultado['camino'])}",
                f"Costo total      : {resultado['costo']}",
                f"Tiempo de busqueda: {tiempo_busqueda_ms} ms",
            ]
            if "heuristica" in resultado:
                lineas.append(f"Heuristica (h)   : {resultado['heuristica']}")

            for indice, linea in enumerate(lineas):
                texto = fuente_texto.render(linea, True, (210, 216, 224))
                self.ventana.blit(texto, (modal.x + 52, modal.y + 88 + indice * 38))

            pygame.draw.rect(self.ventana, (68, 118, 178), boton, border_radius=12)
            pygame.draw.rect(self.ventana, (120, 164, 220), boton, 1, border_radius=12)
            cerrar = fuente_texto.render("Cerrar", True, (255, 255, 255))
            self.ventana.blit(cerrar, (boton.centerx - cerrar.get_width() // 2, boton.centery - cerrar.get_height() // 2))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    return
                if event.type == pygame.MOUSEBUTTONDOWN and boton.collidepoint(event.pos):
                    return

    def esperar_cierre(self):
        """Mantiene abierta la ventana propia hasta recibir un evento de cierre.

        Returns:
            None.

        Example:
            >>> visualizador.esperar_cierre()  # doctest: +SKIP
        """
        if not self.own_display:
            return

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

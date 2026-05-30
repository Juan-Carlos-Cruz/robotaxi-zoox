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
    def __init__(self, grid, titulo="robotaxi-zoox", surface=None, viewport=None):
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
        self.img_taxi_source = self._cargar_fuente_imagen("imagenes", "robot_taxi.png")
        self.img_pasajero_source = self._cargar_fuente_imagen("imagenes", "pasajero_robot.png")
        self.tile_sources = {
            "road": self._cargar_fuente_imagen("imagenes", "tiles", "road_tile.png"),
            "houses": self._cargar_fuente_imagen("imagenes", "tiles", "houses_tile.png"),
        }

    def _cargar_fuente_imagen(self, *ruta_relativa):
        ruta = os.path.join(ruta_raiz, *ruta_relativa)
        try:
            return pygame.image.load(ruta).convert_alpha()
        except Exception:
            return None

    def set_surface(self, surface, viewport=None):
        nuevo_viewport = pygame.Rect(viewport) if viewport is not None else surface.get_rect()
        if surface is self.ventana and nuevo_viewport == self.viewport:
            return
        self.ventana = surface
        self.viewport = nuevo_viewport
        self._recalcular_layout()

    def set_grid(self, grid):
        self.grid = grid
        self.pasajeros_originales = set(grid.pasajeros)
        self._recalcular_layout()

    def _recalcular_layout(self):
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
        if source is None:
            return fallback_factory()
        return pygame.transform.smoothscale(source, (size, size))

    def _escalar_sprite(self, source, size, fallback_factory):
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
        if source is None:
            return fallback_factory()
        return pygame.transform.smoothscale(source, (size, size))

    def _escalar_superficie_zoom(self, source, size, fallback_factory, zoom=1.0):
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
        pygame.draw.rect(surface, color, rect, border_radius=max(4, rect.width // 4))
        ventana = pygame.Rect(rect.left + 2, rect.top + max(3, rect.height // 8), rect.width - 4, rect.height - max(6, rect.height // 4))
        pygame.draw.rect(surface, (73, 99, 123), ventana, border_radius=max(3, rect.width // 4))
        pygame.draw.rect(surface, (233, 239, 245), ventana, 1, border_radius=max(3, rect.width // 4))
        pygame.draw.line(surface, (31, 36, 41), (rect.centerx, ventana.top + 1), (rect.centerx, ventana.bottom - 1), 1)

    def _dibujar_semaforo(self, surface, centro):
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
        return {
            "up": self.grid.es_transitable(fila - 1, columna),
            "down": self.grid.es_transitable(fila + 1, columna),
            "left": self.grid.es_transitable(fila, columna - 1),
            "right": self.grid.es_transitable(fila, columna + 1),
        }

    def _angulo_calle(self, fila, columna):
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
        return (
            self.map_rect.x + columna * self.tam_celda,
            self.map_rect.y + fila * self.tam_celda,
        )

    def _blit_centrado(self, surface, x, y):
        rect = surface.get_rect(center=(x + self.tam_celda // 2, y + self.tam_celda // 2))
        self.ventana.blit(surface, rect.topleft)

    def _dibujar_sombra_celda(self, rect):
        sombra = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(sombra, COLOR_SOMBRA, sombra.get_rect(), border_radius=max(4, self.tam_celda // 10))
        self.ventana.blit(sombra, (rect.x + 1, rect.y + 2))

    def _dibujar_etiqueta_marcador(self, x, y, texto, color):
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
        delta = (destino - origen + 180) % 360 - 180
        return origen + delta * progreso

    def _ease(self, progreso):
        return progreso * progreso * (3 - 2 * progreso)

    def _estado_taxi(self, camino, paso_actual, progreso):
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
        if not self.own_display:
            return

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

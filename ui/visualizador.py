import sys
import os

ruta_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ruta_raiz)

import pygame

from mundo import Grid


# Colores en formato RGB
COLORES = {
    Grid.LIBRE:      (255, 255, 255),
    Grid.MURO:       (0,   0,   0  ),
    Grid.INICIO:     (0,   0,   255),
    Grid.FLUJO_ALTO: (255, 0,   0  ),
    Grid.PASAJERO:   (0,   255, 0  ),
    Grid.DESTINO:    (255, 255, 0  ),
}
COLOR_CAMINO_RESALTE = (128, 0, 128)
COLOR_FONDO          = (200, 200, 200)

TAM_CELDA = 60
FILAS     = 10
COLUMNAS  = 10

ANCHO = COLUMNAS * TAM_CELDA
ALTO  = FILAS    * TAM_CELDA


class Visualizador:

    def __init__(self, grid, titulo="robotaxi-zoox"):
        self.grid      = grid
        self.tam_celda = TAM_CELDA
        self.ancho     = grid.columnas * self.tam_celda
        self.alto      = grid.filas    * self.tam_celda

        pygame.init()
        self.ventana = pygame.display.set_mode((self.ancho, self.alto))
        pygame.display.set_caption(titulo)
        self.reloj = pygame.time.Clock()

        self.pasajeros_originales = set(grid.pasajeros)

        # Cargar imágenes
        ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_taxi     = pygame.image.load(os.path.join(ruta_base, "imagenes", "robot_taxi.png"))
        img_pasajero = pygame.image.load(os.path.join(ruta_base, "imagenes", "pasajero_robot.png"))

        self.img_taxi     = pygame.transform.scale(img_taxi,     (self.tam_celda, self.tam_celda))
        self.img_pasajero = pygame.transform.scale(img_pasajero, (self.tam_celda, self.tam_celda))


    def dibujar_grid(self, camino=None, paso_actual=0):
        self.ventana.fill(COLOR_FONDO)

        # Pasajeros ya recogidos hasta el paso actual
        pasajeros_recogidos = set()
        if camino and paso_actual < len(camino):
            for k in range(paso_actual + 1):
                pos = camino[k]
                if pos in self.pasajeros_originales:
                    pasajeros_recogidos.add(pos)

        # Dibujar cada celda
        for i in range(self.grid.filas):
            for j in range(self.grid.columnas):
                x    = j * self.tam_celda
                y    = i * self.tam_celda
                rect = pygame.Rect(x, y, self.tam_celda, self.tam_celda)
                tipo = self.grid.matriz[i][j]

                # Si el pasajero ya fue recogido, mostrar celda libre
                if tipo == Grid.PASAJERO and (i, j) in pasajeros_recogidos:
                    color = COLORES[Grid.LIBRE]
                else:
                    color = COLORES.get(tipo, COLORES[Grid.LIBRE])

                pygame.draw.rect(self.ventana, color, rect)
                pygame.draw.rect(self.ventana, (100, 100, 100), rect, 1)

                # Imagen del pasajero si no fue recogido
                if tipo == Grid.PASAJERO and (i, j) not in pasajeros_recogidos:
                    self.ventana.blit(self.img_pasajero, (x, y))

        # Dibujar camino y taxi
        if camino and paso_actual < len(camino):
            for k in range(paso_actual + 1):
                i, j = camino[k]
                x    = j * self.tam_celda
                y    = i * self.tam_celda
                rect = pygame.Rect(x, y, self.tam_celda, self.tam_celda)

                pygame.draw.rect(self.ventana, COLOR_CAMINO_RESALTE, rect, 6)

                # Imagen del taxi en la posición actual
                if k == paso_actual:
                    self.ventana.blit(self.img_taxi, (x, y))

        pygame.display.flip()


    def animar_camino(self, camino, resultado, nombre_algoritmo, delay=300):
        if not camino:
            print("No hay camino para animar")
            return

        ejecutando = True
        paso = 0

        while ejecutando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    ejecutando = False

            self.dibujar_grid(camino, paso)

            if paso < len(camino) - 1:
                paso += 1
                pygame.time.wait(delay)
            else:
                self.mostrar_exito()
                ejecutando = False

        self.mostrar_reporte(resultado, nombre_algoritmo)
        pygame.quit()
        sys.exit()


    def mostrar_exito(self, duracion=2000):
        fuente  = pygame.font.SysFont("Arial", 36, bold=True)
        texto   = fuente.render("¡Llegó a la meta!", True, (255, 255, 255))
        overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))

        self.ventana.blit(overlay, (0, 0))
        x = self.ancho // 2 - texto.get_width()  // 2
        y = self.alto  // 2 - texto.get_height() // 2
        self.ventana.blit(texto, (x, y))

        pygame.display.flip()
        pygame.time.wait(duracion)


    def mostrar_reporte(self, resultado, nombre_algoritmo):
        fuente_titulo = pygame.font.SysFont("Arial", 26, bold=True)
        fuente_texto  = pygame.font.SysFont("Arial", 20)

        ejecutando = True
        while ejecutando:
            self.ventana.fill((30, 30, 30))

            titulo = fuente_titulo.render(f"Reporte — {nombre_algoritmo}", True, (255, 255, 255))
            self.ventana.blit(titulo, (self.ancho // 2 - titulo.get_width() // 2, 60))

            pygame.draw.line(self.ventana, (100, 100, 100), (50, 110), (self.ancho - 50, 110), 1)

            lineas = [
                f"Nodos expandidos : {resultado['nodos_expandidos']}",
                f"Profundidad      : {resultado['profundidad']}",
                f"Pasos en camino  : {len(resultado['camino'])}",
                f"Costo total      : {resultado['costo']}",
                f"Tiempo de computo: {resultado['tiempo']} ms",
            ]

            for i, linea in enumerate(lineas):
                texto = fuente_texto.render(linea, True, (200, 200, 200))
                self.ventana.blit(texto, (100, 160 + i * 50))

            cerrar = fuente_texto.render("Presiona cualquier tecla para cerrar", True, (120, 120, 120))
            self.ventana.blit(cerrar, (self.ancho // 2 - cerrar.get_width() // 2, self.alto - 60))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    ejecutando = False


    def esperar_cierre(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

import pygame

def dibujar_boton(ventana, texto,x,y,ancho,alto,color,color_texto=(0,0,0)):
    """Dibuja un botón rectangular centrando su etiqueta.

    Args:
        ventana (pygame.Surface): Superficie de destino.
        texto (str): Etiqueta visible.
        x (int): Coordenada horizontal.
        y (int): Coordenada vertical.
        ancho (int): Ancho del botón en píxeles.
        alto (int): Alto del botón en píxeles.
        color (tuple[int, int, int]): Color de fondo RGB.
        color_texto (tuple[int, int, int]): Color RGB de la etiqueta.

    Returns:
        pygame.Rect: Rectángulo usado para dibujar y detectar clics.

    Example:
        >>> superficie = pygame.Surface((200, 80))
        >>> dibujar_boton(superficie, "Aceptar", 0, 0, 120, 40, (0, 0, 0))
        <rect(0, 0, 120, 40)>
    """
    rect = pygame.Rect(x,y,ancho,alto)
    pygame.draw.rect(ventana,color,rect,border_radius=8)
    pygame.draw.rect(ventana, (80, 80, 80), rect, 2, border_radius=8)

    fuente = pygame.font.SysFont("Arial", 20)
    label = fuente.render(texto, True, color_texto)

    texto_x = x + (ancho - label.get_width()) // 2
    texto_y = y + (alto - label.get_height()) // 2
    ventana.blit(label, (texto_x, texto_y))
    
    return rect

def mostrar_menu(ventana,ancho,alto):
    """Muestra el menú para elegir una familia de búsqueda.

    Args:
        ventana (pygame.Surface): Superficie principal de la aplicación.
        ancho (int): Ancho disponible en píxeles.
        alto (int): Alto disponible en píxeles.

    Returns:
        str: ``"no_informada"`` o ``"informada"`` según el botón pulsado.

    Example:
        >>> categoria = mostrar_menu(ventana, 800, 600)  # doctest: +SKIP
        >>> categoria in {"no_informada", "informada"}  # doctest: +SKIP
        True
    """
    fuente_titulo = pygame.font.SysFont("Arial",28, bold =True)
    
    ejecutando = True

    while ejecutando:
        ventana.fill((240,240,240)) #fondo gris claro

        #titulo

        titulo = fuente_titulo.render("Selecciona el tipo de búsqueda", True, (30,30,30))

        ventana.blit(titulo,(ancho // 2 - titulo.get_width() // 2, 80))
        
        
        btn_no_inf = dibujar_boton(ventana, "No Informada", (ancho // 2 - 200 // 2),200, 200, 50, (100, 149, 237), (255,255,255))
        btn_inf    = dibujar_boton(ventana, "Informada",  (ancho // 2 - 200 // 2),280 , 200, 50, (60,  179, 113), (255,255,255))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_no_inf.collidepoint(event.pos):
                    return "no_informada"
                if btn_inf.collidepoint(event.pos):
                    return "informada"
def mostrar_submenu(ventana, ancho, alto, categoria):
    """Muestra los algoritmos disponibles para una categoría.

    Args:
        ventana (pygame.Surface): Superficie principal de la aplicación.
        ancho (int): Ancho disponible en píxeles.
        alto (int): Alto disponible en píxeles.
        categoria (str): Familia ``"no_informada"`` o ``"informada"``.

    Returns:
        str: Clave del algoritmo seleccionado.

    Example:
        >>> clave = mostrar_submenu(
        ...     ventana, 800, 600, "informada"
        ... )  # doctest: +SKIP
        >>> clave in {"avara", "a_estrella"}  # doctest: +SKIP
        True
    """
    fuente_titulo = pygame.font.SysFont("Arial", 24, bold=True)

    if categoria == "no_informada":
        opciones = [
            ("Amplitud",   "amplitud"),
            ("Costo Uniforme", "costo"),
            ("Profundidad", "profundidad"),
        ]
    else:
        opciones = [
            ("Avara",  "avara"),
            ("A*",     "a_estrella"),
        ]

    ejecutando = True
    while ejecutando:
        ventana.fill((240, 240, 240))

        titulo = fuente_titulo.render("Selecciona el algoritmo", True, (30, 30, 30))
        ventana.blit(titulo, (ancho // 2 - titulo.get_width() // 2, 80))

        botones = []
        for idx, (texto, clave) in enumerate(opciones):
            btn = dibujar_boton(ventana, texto,
                                ancho // 2 - 100,
                                180 + idx * 80,   # separados 80px entre sí
                                200, 50, (70, 130, 180), (255, 255, 255))
            botones.append((btn, clave))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for btn, clave in botones:
                    if btn.collidepoint(event.pos):
                        return clave

# robotaxi-zoox

Proyecto del curso de Inteligencia Artificial. El problema consiste en mover un robotaxi dentro de una ciudad en cuadricula para recoger todos los pasajeros y luego llegar al destino final usando algoritmos de busqueda no informada e informada.

## Estado actual

La aplicacion ya no funciona como una secuencia de ventanas separadas. Hoy el proyecto ofrece una interfaz persistente:

- selector de mapa al iniciar;
- mapa grande a la izquierda;
- panel de algoritmos a la derecha;
- cambio de mapa sin cerrar la aplicacion;
- modal de resultados al finalizar cada recorrido;
- reporte con tiempo de busqueda separado del tiempo de animacion;
- musica y efectos de sonido integrados.

## Algoritmos incluidos

Busqueda no informada:

- Amplitud (`BFS`)
- Costo uniforme (`UCS`)
- Profundidad evitando ciclos (`DFS`)

Busqueda informada:

- Avara
- A*

### Modelado del estado

El estado de busqueda incluye:

- posicion del taxi;
- conjunto de pasajeros recogidos;
- costo acumulado;
- profundidad;
- heuristica y `f` en los algoritmos informados.

Esto permite evitar ciclos sin impedir que el taxi se devuelva despues de recoger un pasajero, porque el estado cambia cuando cambia el conjunto de pasajeros recogidos.

### Heuristica usada

La heuristica de los algoritmos informados se basa en distancia Manhattan:

- si faltan pasajeros, usa la distancia al pasajero faltante mas cercano;
- si ya estan todos recogidos, usa la distancia al destino.

La explicacion completa y la justificacion de admisibilidad estan en [`docs/informe.tex`](docs/informe.tex) y [`docs/informe.pdf`](docs/informe.pdf).

## Interfaz

Flujo actual de uso:

1. Ejecuta la aplicacion.
2. Selecciona un mapa `.txt`.
3. Elige `No informada` o `Informada`.
4. Selecciona el algoritmo especifico.
5. Observa la animacion del recorrido.
6. Revisa el modal final y prueba otro algoritmo o cambia de mapa.

Controles visibles en la interfaz:

- `Cambiar mapa`
- `Ambiente On / Off` para activar o desactivar solo la musica ambiente
- botones de categoria y subopciones de algoritmos
- cierre de modal sin cerrar el programa

## Reporte de resultados

El modal final muestra:

- nodos expandidos;
- profundidad;
- pasos del camino;
- costo total;
- tiempo de busqueda en milisegundos;
- heuristica final, solo cuando el algoritmo es informado.

Importante: el tiempo mostrado corresponde a la ejecucion del algoritmo de busqueda. La animacion del taxi se mide aparte y no se mezcla con ese valor.

## Audio

La aplicacion incluye:

- musica ambiente de inicio;
- sonido del auto en carretera durante la animacion;
- claxon al recoger pasajero;
- claxon al pasar por trafico alto;
- sonido de clic en botones;
- jingle de finalizacion al abrir el modal de resultado.

Los assets viven en [`audio/`](audio) y pueden regenerarse con:

```bash
python3 scripts/generate_audio_assets.py
```

Si `pygame.mixer` no puede inicializarse en la maquina, la aplicacion sigue funcionando sin audio.

## Render del mapa

El visualizador usa una estetica tipo ciudad:

- carretera para vias libres;
- edificios para muros;
- semaforo para trafico alto;
- taxi y pasajero con sprites propios;
- marcadores claros de `Inicio` y `Meta`;
- orientacion de calles segun conectividad del mapa.

## Ejecucion automatica

### Una sola instruccion

En Unix, Linux, macOS o Git Bash:

```bash
make run
```

Alternativas:

```bash
bash scripts/run.sh
```

En Windows:

```bat
launchers\windows\run.bat
```

En macOS:

```bash
./launchers/macos/run.command
```

## Comandos disponibles

```bash
make doctor
make setup
make run
make test
make clean
```

Tambien existen launchers equivalentes para Windows y macOS dentro de [`launchers/`](launchers).

## Que hace la automatizacion

- detecta una version utilizable de Python;
- crea un entorno virtual por version;
- instala `pygame` si hace falta;
- valida `tkinter` y `pygame`;
- verifica si hay entorno grafico disponible;
- en Linux intenta resolver dependencias del sistema cuando `pip` no basta.

## Requisitos practicos

Para ejecutar la interfaz necesitas:

- Python 3;
- entorno grafico disponible;
- `tkinter`;
- `pygame`.

Si solo quieres validar la logica de busqueda, puedes usar:

```bash
make test
```

## Estructura relevante

```text
robotaxi-zoox/
  README.md
  Makefile
  application/
    audio.py
    carga.py
    config.py
    ejecucion.py
    runner.py
  algoritmosBusqueda/
    informada/
    noinformada/
  audio/
    finish_jingle.wav
    lofi_ambient.wav
    pickup_horn.wav
    road_loop.wav
    traffic_horn.wav
    ui_click.wav
  docs/
    informe.tex
    informe.pdf
  imagenes/
  launchers/
    macos/
    windows/
  mapas/
    test/
  mundo/
    io/
    models/
  scripts/
    bootstrap.py
    doctor.sh
    generate_audio_assets.py
    run.sh
    setup.sh
    test.sh
  tests/
  ui/
    visualizador.py
```

## Documentacion del proyecto

- Informe fuente: [`docs/informe.tex`](docs/informe.tex)
- Informe compilado: [`docs/informe.pdf`](docs/informe.pdf)

## Verificacion

Comando recomendado para validar el proyecto:

```bash
make test
```

Eso compila los modulos relevantes y ejecuta las pruebas incluidas de `Grid`, algoritmos no informados e informados.

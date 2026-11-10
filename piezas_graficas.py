"""Recorta una pose por personaje y crea variantes a color y en escala de grises."""

from pathlib import Path
from collections import deque

from PIL import Image, ImageOps


def recortar_fotograma(
    hoja: Image.Image, columnas: int, filas: int, columna: int = 0, fila: int = 0
) -> Image.Image:
    if columnas < 1 or filas < 1 or not (0 <= columna < columnas and 0 <= fila < filas):
        raise ValueError("La posición del fotograma está fuera de la cuadrícula.")
    ancho, alto = hoja.size
    if ancho < columnas or alto < filas:
        raise ValueError("La hoja es demasiado pequeña para la cuadrícula indicada.")
    cuadro = hoja.crop(
        (
            ancho * columna // columnas,
            alto * fila // filas,
            ancho * (columna + 1) // columnas,
            alto * (fila + 1) // filas,
        )
    ).convert("RGBA")
    contenido = cuadro.getchannel("A").getbbox()
    return cuadro.crop(contenido) if contenido else cuadro


def limpiar_artefactos(imagen: Image.Image) -> Image.Image:
    """Elimina colores de croma y manchas aisladas alrededor del personaje."""
    imagen = imagen.convert("RGBA")
    ancho, alto = imagen.size
    pixeles = imagen.load()
    for y in range(alto):
        for x in range(ancho):
            r, g, b, a = pixeles[x, y]
            # Las hojas originales contienen ruido neón rojo/verde/amarillo
            # y magenta detrás de los sprites, no parte de los personajes.
            ruido = (
                (r > 225 and g < 65 and b < 65)
                or (r > 215 and b > 170 and g < 60)
                or (g > 195 and r < 100 and b < 120)
                or (r > 215 and g > 190 and b < 90)
            )
            if ruido:
                pixeles[x, y] = (0, 0, 0, 0)

    # El cuerpo es el componente conexo de mayor tamaño. Los restos del
    # fondo (incluidas motas blancas/grises) quedan fuera de ese componente.
    visitados = bytearray(ancho * alto)
    mayor = []
    for inicio in range(ancho * alto):
        if visitados[inicio]:
            continue
        x, y = inicio % ancho, inicio // ancho
        if pixeles[x, y][3] < 55:
            continue
        visitados[inicio] = 1
        cola = deque([inicio])
        componente = []
        while cola:
            actual = cola.popleft()
            componente.append(actual)
            cx, cy = actual % ancho, actual // ancho
            for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                if not (0 <= nx < ancho and 0 <= ny < alto):
                    continue
                vecino = ny * ancho + nx
                if not visitados[vecino] and pixeles[nx, ny][3] >= 55:
                    visitados[vecino] = 1
                    cola.append(vecino)
        if len(componente) > len(mayor):
            mayor = componente

    # Se conservan dos píxeles de margen para preservar bordes suavizados.
    conservar = bytearray(ancho * alto)
    for indice in mayor:
        x, y = indice % ancho, indice // ancho
        for ny in range(max(0, y - 2), min(alto, y + 3)):
            for nx in range(max(0, x - 2), min(ancho, x + 3)):
                conservar[ny * ancho + nx] = 1
    for y in range(alto):
        for x in range(ancho):
            if not conservar[y * ancho + x]:
                pixeles[x, y] = (0, 0, 0, 0)
    contenido = imagen.getchannel("A").getbbox()
    return imagen.crop(contenido) if contenido else imagen


def preparar_pieza(imagen: Image.Image, tamano: int, blanco: bool) -> Image.Image:
    """Encaja la pose sin deformarla y conserva su transparencia."""
    imagen = imagen.convert("RGBA")
    if not blanco:
        gris = ImageOps.grayscale(imagen)
        imagen = Image.merge("RGBA", (gris, gris, gris, imagen.getchannel("A")))
    margen = max(3, tamano // 15)
    imagen.thumbnail((tamano - 2 * margen, tamano - 2 * margen), Image.Resampling.LANCZOS)
    lienzo = Image.new("RGBA", (tamano, tamano), (0, 0, 0, 0))
    lienzo.alpha_composite(imagen, ((tamano - imagen.width) // 2, (tamano - imagen.height) // 2))
    return lienzo


def cargar_pieza(
    archivo: Path, tamano: int, columnas: int, filas: int, columna: int, fila: int
) -> tuple[Image.Image, Image.Image]:
    with Image.open(archivo) as hoja:
        pose = recortar_fotograma(hoja, columnas, filas, columna, fila)
    return preparar_pieza(pose, tamano, True), preparar_pieza(pose, tamano, False)

"""Genera una única pose por personaje a partir de las hojas originales."""

from pathlib import Path

from PIL import Image, ImageOps

from piezas_graficas import limpiar_artefactos, recortar_fotograma


BASE = Path(__file__).resolve().parent
ORIGINALES = BASE / "Sprites"
DESTINO = BASE / "assets" / "piezas"

# Las hojas seleccionadas contienen 5 columnas y 4 filas. Se extrae la pose
# frontal de la primera casilla; ninguna imagen original se modifica.
FUENTES = {
    "special_week": ORIGINALES / "Special week" / "Atlas chibi de chica caballo-1.png",
    "silent_suzuka": ORIGINALES / "silent susuka" / "Atlas de sprites de chica caballo chibi-2.png",
    "tokai_teio": ORIGINALES / "tokai teio" / "Atlas de animación_ chica caballo chibi-1.png",
    "haru_urara": ORIGINALES / "Haru urara" / "Atlas de sprites de chica caballo-1.png",
    "oguri_cap": ORIGINALES / "Oguri cap" / "Hoja de sprites chibi ecuestre-1.png",
    "agnes_tachyon": ORIGINALES / "Agnes Tachyon" / "Atlas de sprites chibi_ reposo y caminata-3.png",
}


def generar():
    faltantes = [ruta for ruta in FUENTES.values() if not ruta.is_file()]
    if faltantes:
        raise FileNotFoundError("No se encontraron estas hojas: " + ", ".join(map(str, faltantes)))
    DESTINO.mkdir(parents=True, exist_ok=True)
    for nombre, ruta in FUENTES.items():
        with Image.open(ruta) as hoja:
            color = limpiar_artefactos(recortar_fotograma(hoja, 5, 4))
        gris = ImageOps.grayscale(color)
        negro = Image.merge("RGBA", (gris, gris, gris, color.getchannel("A")))
        color.save(DESTINO / f"{nombre}_blanca.png", optimize=True)
        negro.save(DESTINO / f"{nombre}_negra.png", optimize=True)
        print(f"{nombre}: {color.width}x{color.height}, color y escala de grises")


if __name__ == "__main__":
    generar()

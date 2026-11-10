"""Copia los archivos de la web y las piezas al proyecto estático de Vercel."""

from pathlib import Path
from shutil import copy2, copytree


BASE = Path(__file__).resolve().parent
DESTINO = BASE / "frontend"


def sincronizar():
    (DESTINO / "web").mkdir(parents=True, exist_ok=True)
    for archivo in (BASE / "web").iterdir():
        if archivo.is_file():
            copy2(archivo, DESTINO / "web" / archivo.name)
    copy2(BASE / "web" / "index.html", DESTINO / "index.html")
    copytree(BASE / "assets" / "piezas", DESTINO / "assets" / "piezas", dirs_exist_ok=True)
    print("Frontend sincronizado: HTML, CSS, JS y sprites.")


if __name__ == "__main__":
    sincronizar()

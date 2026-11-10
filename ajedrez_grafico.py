"""Ajedrez gráfico local para dos jugadores; ejecutar con python ajedrez_grafico.py."""

from pathlib import Path

import chess
import pygame

from PIL import Image

from piezas_graficas import preparar_pieza


BASE = Path(__file__).resolve().parent
SPRITES = BASE / "assets" / "piezas"
CASILLA = 80
TABLERO_X, TABLERO_Y = 52, 58
PANEL_X = 726
ANCHO, ALTO = 1020, 754

PERSONAJES = {
    chess.PAWN: "special_week",
    chess.ROOK: "silent_suzuka",
    chess.KNIGHT: "tokai_teio",
    chess.BISHOP: "haru_urara",
    chess.QUEEN: "oguri_cap",
    chess.KING: "agnes_tachyon",
}
NOMBRES = {
    chess.PAWN: "Special Week",
    chess.ROOK: "Silent Suzuka",
    chess.KNIGHT: "Tokai Teio",
    chess.BISHOP: "Haru Urara",
    chess.QUEEN: "Oguri Cap",
    chess.KING: "Agnes Tachyon",
}
TIPOS_CORONACION = (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT)
FONDO = (19, 23, 35)
PANEL = (30, 37, 55)
TEXTO = (235, 238, 247)
SUAVE = (163, 177, 197)
CLARA = (231, 220, 197)
OSCURA = (127, 143, 157)
ACENTO = (244, 192, 111)


def imagen_pygame(imagen):
    return pygame.image.fromstring(imagen.tobytes(), imagen.size, "RGBA").convert_alpha()


def cargar_imagenes():
    imagenes = {}
    pendientes = []
    for tipo, nombre in PERSONAJES.items():
        for color, sufijo in ((chess.WHITE, "blanca"), (chess.BLACK, "negra")):
            ruta = SPRITES / f"{nombre}_{sufijo}.png"
            try:
                with Image.open(ruta) as imagen:
                    imagenes[(tipo, color)] = imagen_pygame(preparar_pieza(imagen, CASILLA, True))
            except (FileNotFoundError, OSError, ValueError) as error:
                pendientes.append(f"{ruta.name}: {error}")
    return imagenes, pendientes


def casilla_en(posicion):
    x, y = posicion
    columna = (x - TABLERO_X) // CASILLA
    fila = (y - TABLERO_Y) // CASILLA
    if 0 <= columna < 8 and 0 <= fila < 8:
        return chess.square(columna, 7 - fila)
    return None


class AjedrezGrafico:
    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Ajedrez Uma Musume")
        self.reloj = pygame.time.Clock()
        self.titulo = pygame.font.SysFont("arial", 26, bold=True)
        self.fuente = pygame.font.SysFont("arial", 19)
        self.pequena = pygame.font.SysFont("arial", 15)
        self.pieza_fallback = pygame.font.SysFont("arial", 34, bold=True)
        self.tablero = chess.Board()
        self.tablas_reclamadas = False
        self.seleccion = None
        self.coronacion = None  # Lista de jugadas de coronación pendientes.
        self.mensaje = "Selecciona una pieza y luego su destino."
        self.imagenes, self.pendientes = cargar_imagenes()
        self.botones = {
            "nueva": pygame.Rect(PANEL_X + 14, 549, 121, 43),
            "deshacer": pygame.Rect(PANEL_X + 144, 549, 121, 43),
            "tablas": pygame.Rect(PANEL_X + 14, 602, 251, 43),
        }

    def texto(self, contenido, x, y, fuente=None, color=TEXTO):
        superficie = (fuente or self.fuente).render(contenido, True, color)
        self.pantalla.blit(superficie, (x, y))

    def pieza(self, tipo, color, rect):
        imagen = self.imagenes.get((tipo, color))
        if imagen is not None:
            self.pantalla.blit(imagen, rect.topleft)
        else:
            # Permite jugar incluso antes de copiar las hojas de sprites.
            simbolo = chess.Piece(tipo, color).symbol().upper()
            tono = (255, 253, 241) if color else (54, 60, 72)
            borde = (55, 60, 71) if color else (224, 229, 236)
            centro = rect.center
            pygame.draw.circle(self.pantalla, borde, centro, 29)
            pygame.draw.circle(self.pantalla, tono, centro, 26)
            letras = self.pieza_fallback.render(simbolo, True, borde)
            self.pantalla.blit(letras, letras.get_rect(center=centro))

    def dibujar_tablero(self):
        ultimos = set()
        if self.tablero.move_stack:
            jugada = self.tablero.peek()
            ultimos = {jugada.from_square, jugada.to_square}
        legales = set()
        if self.seleccion is not None:
            legales = {m.to_square for m in self.tablero.legal_moves if m.from_square == self.seleccion}

        for fila in range(8):
            for columna in range(8):
                casilla = chess.square(columna, 7 - fila)
                rect = pygame.Rect(TABLERO_X + columna * CASILLA, TABLERO_Y + fila * CASILLA, CASILLA, CASILLA)
                color = CLARA if (fila + columna) % 2 == 0 else OSCURA
                pygame.draw.rect(self.pantalla, color, rect)
                if casilla in ultimos:
                    pygame.draw.rect(self.pantalla, (234, 195, 98), rect, 4)
                if casilla == self.seleccion:
                    pygame.draw.rect(self.pantalla, (67, 214, 151), rect, 5)
                pieza = self.tablero.piece_at(casilla)
                if pieza:
                    self.pieza(pieza.piece_type, pieza.color, rect)
                if casilla in legales:
                    if pieza:
                        pygame.draw.circle(self.pantalla, (50, 178, 117), rect.center, 35, 4)
                    else:
                        pygame.draw.circle(self.pantalla, (50, 178, 117), rect.center, 10)

        for indice, letra in enumerate("abcdefgh"):
            self.texto(letra, TABLERO_X + indice * CASILLA + 35, TABLERO_Y + 647, self.pequena, SUAVE)
        for indice in range(8):
            self.texto(str(8 - indice), TABLERO_X - 25, TABLERO_Y + indice * CASILLA + 30, self.pequena, SUAVE)

    def dibujar_panel(self):
        pygame.draw.rect(self.pantalla, PANEL, (PANEL_X, 58, 279, 640), border_radius=15)
        self.texto("UMA CHESS", PANEL_X + 17, 77, self.titulo, ACENTO)
        resultado = self.tablero.outcome()
        if self.tablas_reclamadas:
            estado = "Fin: 1/2-1/2 (tablas)"
        elif resultado:
            estado = f"Fin: {resultado.result()}"
        elif self.tablero.is_check():
            estado = "¡Jaque a las " + ("blancas!" if self.tablero.turn else "negras!")
        else:
            estado = "Turno: " + ("blancas" if self.tablero.turn else "negras")
        self.texto(estado, PANEL_X + 17, 124)
        self.texto("Color: blancas / gris: negras", PANEL_X + 17, 156, self.pequena, SUAVE)
        pygame.draw.line(self.pantalla, (81, 91, 111), (PANEL_X + 17, 185), (PANEL_X + 262, 185))
        self.texto("JUGADAS", PANEL_X + 17, 200, self.pequena, ACENTO)
        copia = chess.Board()
        jugadas = []
        for indice, movimiento in enumerate(self.tablero.move_stack):
            san = copia.san(movimiento)
            if indice % 2 == 0:
                jugadas.append(f"{indice // 2 + 1}.  {san}")
            else:
                jugadas[-1] += f"    {san}"
            copia.push(movimiento)
        for linea, entrada in enumerate(jugadas[-15:]):
            self.texto(entrada, PANEL_X + 20, 229 + linea * 20, self.pequena)

        for clave, boton in self.botones.items():
            pygame.draw.rect(self.pantalla, (68, 82, 110), boton, border_radius=8)
            etiqueta = {"nueva": "Nueva partida", "deshacer": "Deshacer", "tablas": "Reclamar tablas"}[clave]
            rotulo = self.pequena.render(etiqueta, True, TEXTO)
            self.pantalla.blit(rotulo, rotulo.get_rect(center=boton.center))
        self.texto(self.mensaje[:34], PANEL_X + 16, 660, self.pequena, ACENTO)
        if self.pendientes:
            self.texto(f"Sprites sin cargar: {len(self.pendientes)}/12", 52, 22, self.pequena, ACENTO)
        else:
            self.texto("Sprites cargados: 12/12", 52, 22, self.pequena, SUAVE)

    def opciones_coronacion(self):
        return [pygame.Rect(280 + indice * 110, 322, 100, 110) for indice in range(4)]

    def dibujar_coronacion(self):
        capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa.fill((10, 16, 26, 190))
        self.pantalla.blit(capa, (0, 0))
        pygame.draw.rect(self.pantalla, PANEL, (259, 270, 470, 190), border_radius=18)
        self.texto("Elige una pieza para coronar", 296, 290, self.fuente, ACENTO)
        for tipo, rect in zip(TIPOS_CORONACION, self.opciones_coronacion()):
            pygame.draw.rect(self.pantalla, CLARA, rect, border_radius=10)
            self.pieza(tipo, self.tablero.turn, pygame.Rect(rect.x + 10, rect.y, 80, 80))
            nombre = {chess.QUEEN: "Dama", chess.ROOK: "Torre", chess.BISHOP: "Alfil", chess.KNIGHT: "Caballo"}[tipo]
            rotulo = self.pequena.render(nombre, True, FONDO)
            self.pantalla.blit(rotulo, rotulo.get_rect(center=(rect.centerx, rect.bottom - 17)))

    def dibujar(self):
        self.pantalla.fill(FONDO)
        self.dibujar_tablero()
        self.dibujar_panel()
        if self.coronacion:
            self.dibujar_coronacion()
        pygame.display.flip()

    def mover(self, movimiento):
        san = self.tablero.san(movimiento)
        self.tablero.push(movimiento)
        self.mensaje = f"Última jugada: {san}"
        self.seleccion = None
        self.coronacion = None
        if self.tablero.outcome():
            self.mensaje = f"Resultado: {self.tablero.result()}"

    def pulsar(self, posicion):
        if self.coronacion:
            for tipo, rect in zip(TIPOS_CORONACION, self.opciones_coronacion()):
                if rect.collidepoint(posicion):
                    self.mover(next(m for m in self.coronacion if m.promotion == tipo))
                    return
            return

        for clave, rect in self.botones.items():
            if rect.collidepoint(posicion):
                if clave == "nueva":
                    self.tablero.reset()
                    self.seleccion = None
                    self.tablas_reclamadas = False
                    self.mensaje = "Nueva partida. Mueven blancas."
                elif clave == "deshacer":
                    if self.tablero.move_stack:
                        self.tablero.pop()
                        self.seleccion = None
                        self.mensaje = "Última jugada deshecha."
                    else:
                        self.mensaje = "No hay jugadas que deshacer."
                elif self.tablero.can_claim_draw():
                    self.mensaje = "Tablas reclamadas: 1/2-1/2"
                    self.tablas_reclamadas = True
                else:
                    self.mensaje = "Aún no puedes reclamar tablas."
                return

        if self.tablero.outcome() or getattr(self, "tablas_reclamadas", False):
            return
        casilla = casilla_en(posicion)
        if casilla is None:
            return
        pieza = self.tablero.piece_at(casilla)
        if pieza and pieza.color == self.tablero.turn:
            self.seleccion = None if self.seleccion == casilla else casilla
            if self.seleccion is not None:
                self.mensaje = f"{NOMBRES[pieza.piece_type]}: elige destino."
            return
        if self.seleccion is None:
            return
        candidatas = [m for m in self.tablero.legal_moves if m.from_square == self.seleccion and m.to_square == casilla]
        if not candidatas:
            self.mensaje = "Movimiento ilegal; elige otro destino."
        elif len(candidatas) > 1:
            self.coronacion = candidatas
        else:
            self.mover(candidatas[0])

    def ejecutar(self):
        activo = True
        while activo:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    activo = False
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    self.pulsar(evento.pos)
                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        self.coronacion = None
                        self.seleccion = None
                    elif evento.key == pygame.K_z and evento.mod & pygame.KMOD_CTRL:
                        self.pulsar(self.botones["deshacer"].center)
            self.dibujar()
            self.reloj.tick(30)
        pygame.quit()


if __name__ == "__main__":
    AjedrezGrafico().ejecutar()

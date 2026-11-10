"""Pruebas de clics de la interfaz sin abrir una ventana visible."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import pygame

from ajedrez_grafico import AjedrezGrafico, CASILLA, TABLERO_X, TABLERO_Y


def centro(casilla):
    return (
        TABLERO_X + chess.square_file(casilla) * CASILLA + CASILLA // 2,
        TABLERO_Y + (7 - chess.square_rank(casilla)) * CASILLA + CASILLA // 2,
    )


class InterfazTests(unittest.TestCase):
    def setUp(self):
        self.juego = AjedrezGrafico()

    def tearDown(self):
        pygame.quit()

    def test_movimiento_deshacer_y_nueva_partida(self):
        self.assertEqual(len(self.juego.imagenes), 12)
        self.assertEqual(self.juego.pendientes, [])
        self.juego.dibujar()
        self.juego.pulsar(centro(chess.E2))
        self.juego.pulsar(centro(chess.E4))
        self.assertEqual(self.juego.tablero.peek().uci(), "e2e4")
        self.juego.pulsar(self.juego.botones["deshacer"].center)
        self.assertFalse(self.juego.tablero.move_stack)
        self.juego.pulsar(centro(chess.D2))
        self.juego.pulsar(centro(chess.D4))
        self.juego.pulsar(self.juego.botones["nueva"].center)
        self.assertEqual(self.juego.tablero.fen(), chess.STARTING_FEN)

    def test_coronacion_se_elige_con_un_clic(self):
        self.juego.tablero.set_fen("k7/4P3/8/8/8/8/8/K7 w - - 0 1")
        self.juego.pulsar(centro(chess.E7))
        self.juego.pulsar(centro(chess.E8))
        self.assertIsNotNone(self.juego.coronacion)
        self.juego.dibujar()
        self.juego.pulsar(self.juego.opciones_coronacion()[0].center)
        self.assertEqual(self.juego.tablero.piece_at(chess.E8).piece_type, chess.QUEEN)


if __name__ == "__main__":
    unittest.main()

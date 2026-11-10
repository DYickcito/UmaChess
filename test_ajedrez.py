"""Pruebas básicas del juego de terminal."""

import unittest

import chess

from ajedrez import describir_resultado, historial, interpretar_jugada


class AjedrezTests(unittest.TestCase):
    def test_coordenadas_y_san(self):
        tablero = chess.Board()
        tablero.push(interpretar_jugada(tablero, "e2e4"))
        tablero.push(interpretar_jugada(tablero, "e5"))
        tablero.push(interpretar_jugada(tablero, "Nf3"))
        self.assertEqual(historial(tablero), "1. e4 e5  2. Nf3")

    def test_jugada_ilegal(self):
        with self.assertRaises(ValueError):
            interpretar_jugada(chess.Board(), "e2e5")

    def test_jaque_mate(self):
        tablero = chess.Board()
        for texto in ("f3", "e5", "g4", "Qh4#"):
            tablero.push(interpretar_jugada(tablero, texto))
        self.assertIn("0-1 (jaque mate)", describir_resultado(tablero.outcome()))

    def test_coronacion(self):
        tablero = chess.Board("4k3/4P3/8/8/8/8/8/K7 w - - 0 1")
        with self.assertRaises(ValueError):
            interpretar_jugada(tablero, "e7e8q")  # El rey ocupa e8.
        tablero = chess.Board("k7/4P3/8/8/8/8/8/K7 w - - 0 1")
        tablero.push(interpretar_jugada(tablero, "e7e8q"))
        self.assertEqual(tablero.piece_at(chess.E8).piece_type, chess.QUEEN)


if __name__ == "__main__":
    unittest.main()

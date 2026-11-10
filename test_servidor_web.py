"""Partidas online: roles, movimientos y partidas completas."""

import unittest

from fastapi.testclient import TestClient

from servidor_web import app, salas


class ServidorTests(unittest.TestCase):
    def setUp(self):
        self.cliente = TestClient(app)

    def tearDown(self):
        self.cliente.close()
        salas.clear()

    def crear(self):
        datos = self.cliente.post("/api/salas").json()
        self.assertEqual(len(datos["sala"]), 8)
        return datos

    def test_servidor_y_piezas(self):
        self.assertEqual(self.cliente.get("/health").json(), {"ok": True})
        self.assertEqual(self.cliente.get("/").status_code, 200)
        self.assertIn("UMA_BACKEND_URL", self.cliente.get("/config.js").text)
        self.assertEqual(self.cliente.get("/assets/piezas/special_week_blanca.png").status_code, 200)

    def test_turnos_espectador_y_reconexion(self):
        datos = self.crear()
        codigo, clave = datos["sala"], datos["clave"]
        with self.cliente.websocket_connect(f"/ws/{codigo}?clave={clave}") as blancas:
            self.assertEqual(blancas.receive_json()["lado"], "blancas")
            blancas.receive_json()
            with self.cliente.websocket_connect(f"/ws/{codigo}") as negras:
                negra = negras.receive_json()
                self.assertEqual(negra["lado"], "negras")
                blancas.receive_json()
                negras.receive_json()
                with self.cliente.websocket_connect(f"/ws/{codigo}") as espectador:
                    self.assertEqual(espectador.receive_json()["lado"], "espectador")
                    blancas.receive_json()
                    negras.receive_json()
                    espectador.receive_json()
                    espectador.send_json({"tipo": "mover", "uci": "e2e4"})
                    self.assertEqual(espectador.receive_json()["tipo"], "error")
                    negras.send_json({"tipo": "mover", "uci": "e7e5"})
                    self.assertEqual(negras.receive_json()["tipo"], "error")
                    blancas.send_json({"tipo": "mover", "uci": "e2e5"})
                    self.assertEqual(blancas.receive_json()["tipo"], "error")
                    blancas.send_json({"tipo": "mover", "uci": "e2e4"})
                    self.assertEqual(blancas.receive_json()["turno"], "negras")
                    negras.receive_json()
                    espectador.receive_json()
                    negras.send_json({"tipo": "mover", "uci": "e7e5"})
                    blancas.receive_json()
                    self.assertEqual(negras.receive_json()["historial"], ["e4", "e5"])
                    espectador.receive_json()
            blancas.receive_json()
            with self.cliente.websocket_connect(f"/ws/{codigo}?clave={negra['clave']}") as reconectada:
                self.assertEqual(reconectada.receive_json()["lado"], "negras")
                self.assertEqual(reconectada.receive_json()["historial"], ["e4", "e5"])

    def test_rendicion_y_revancha(self):
        datos = self.crear()
        codigo = datos["sala"]
        with self.cliente.websocket_connect(f"/ws/{codigo}?clave={datos['clave']}") as blancas:
            blancas.receive_json()
            blancas.receive_json()
            with self.cliente.websocket_connect(f"/ws/{codigo}") as negras:
                negras.receive_json()
                negras.receive_json()
                blancas.receive_json()
                blancas.send_json({"tipo": "rendirse"})
                self.assertEqual(blancas.receive_json()["fin"]["resultado"], "0-1")
                negras.receive_json()
                blancas.send_json({"tipo": "revancha"})
                blancas.receive_json()
                negras.receive_json()
                negras.send_json({"tipo": "revancha"})
                self.assertIsNone(blancas.receive_json()["fin"])
                self.assertEqual(negras.receive_json()["historial"], [])


if __name__ == "__main__":
    unittest.main()

"""Servidor de ajedrez online de dos jugadores con salas y WebSockets."""

import asyncio
import json
import os
import re
import secrets
import time
from pathlib import Path
from urllib.parse import urlparse

import chess
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware


BASE = Path(__file__).resolve().parent
CADUCIDAD = 6 * 60 * 60
app = FastAPI(title="Uma Chess")
origenes_permitidos = [origen.strip().rstrip("/") for origen in os.environ.get("ALLOWED_ORIGINS", "").split(",") if origen.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origenes_permitidos, allow_methods=["POST"], allow_headers=["Content-Type"])
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")
app.mount("/web", StaticFiles(directory=BASE / "web"), name="web")


class Sala:
    def __init__(self):
        self.tablero = chess.Board()
        self.jugadores = {"blancas": secrets.token_urlsafe(24), "negras": None}
        self.conexiones: dict[str, WebSocket] = {}
        self.votos: set[str] = set()
        self.fin_manual: dict | None = None
        self.actualizada = time.monotonic()
        self.candado = asyncio.Lock()

    def estado(self):
        copia = chess.Board()
        historial = []
        for jugada in self.tablero.move_stack:
            historial.append(copia.san(jugada))
            copia.push(jugada)
        resultado = self.tablero.outcome()
        fin = self.fin_manual or (
            {"resultado": resultado.result(), "motivo": resultado.termination.name.lower()}
            if resultado else None
        )
        return {
            "tipo": "estado", "fen": self.tablero.fen(),
            "turno": "blancas" if self.tablero.turn else "negras",
            "legales": [m.uci() for m in self.tablero.legal_moves] if not fin else [],
            "historial": historial,
            "ultima": self.tablero.peek().uci() if self.tablero.move_stack else None,
            "jaque": self.tablero.is_check(), "fin": fin,
            "conectados": {lado: lado in self.conexiones for lado in self.jugadores},
            "revancha": list(self.votos),
        }

    async def avisar(self):
        estado = self.estado()
        for socket in list(self.conexiones.values()):
            try:
                await socket.send_json(estado)
            except (RuntimeError, WebSocketDisconnect, OSError):
                pass


salas: dict[str, Sala] = {}


@app.get("/")
async def pagina():
    return FileResponse(BASE / "web" / "index.html")


@app.get("/config.js")
async def configuracion():
    return FileResponse(BASE / "config.js", media_type="application/javascript")


@app.get("/health")
async def salud():
    return {"ok": True}


@app.post("/api/salas")
async def crear_sala():
    ahora = time.monotonic()
    for codigo, sala in list(salas.items()):
        if not sala.conexiones and ahora - sala.actualizada > CADUCIDAD:
            del salas[codigo]
    if len(salas) >= 1000:
        raise HTTPException(503, "Demasiadas salas activas")
    codigo = secrets.token_hex(4)
    while codigo in salas:
        codigo = secrets.token_hex(4)
    sala = Sala()
    salas[codigo] = sala
    return {"sala": codigo, "clave": sala.jugadores["blancas"]}


@app.websocket("/ws/{codigo}")
async def jugar(websocket: WebSocket, codigo: str):
    origen = websocket.headers.get("origin")
    if origen and urlparse(origen).netloc != websocket.headers.get("host") and origen.rstrip("/") not in origenes_permitidos:
        await websocket.close(code=1008)
        return
    if not re.fullmatch(r"[0-9a-f]{8}", codigo) or codigo not in salas:
        await websocket.close(code=1008)
        return
    sala = salas[codigo]
    clave = websocket.query_params.get("clave", "")
    async with sala.candado:
        lado = next((lado for lado, token in sala.jugadores.items() if token and secrets.compare_digest(clave, token)), None)
        if lado is None and sala.jugadores["negras"] is None:
            lado = "negras"
            clave = secrets.token_urlsafe(24)
            sala.jugadores[lado] = clave
        anterior = sala.conexiones.get(lado) if lado else None
        await websocket.accept()
        if anterior:
            try:
                await anterior.close(code=1000)
            except (RuntimeError, OSError):
                pass
        if lado:
            sala.conexiones[lado] = websocket
        else:
            # Espectadores reciben los estados pero nunca pueden mover.
            sala.conexiones[f"espectador-{id(websocket)}"] = websocket
        sala.actualizada = time.monotonic()
        await websocket.send_json({"tipo": "bienvenida", "lado": lado or "espectador", "clave": clave if lado else None})
        await sala.avisar()

    try:
        while True:
            texto = await websocket.receive_text()
            if len(texto) > 512:
                await websocket.send_json({"tipo": "error", "mensaje": "Mensaje demasiado largo."})
                continue
            try:
                mensaje = json.loads(texto)
            except (ValueError, TypeError):
                await websocket.send_json({"tipo": "error", "mensaje": "Mensaje inválido."})
                continue
            async with sala.candado:
                if not lado or sala.conexiones.get(lado) is not websocket:
                    await websocket.send_json({"tipo": "error", "mensaje": "Solo los jugadores pueden jugar."})
                    continue
                accion = mensaje.get("tipo") if isinstance(mensaje, dict) else None
                if accion == "mover":
                    if sala.fin_manual or sala.tablero.is_game_over():
                        error = "La partida ha terminado."
                    elif (sala.tablero.turn == chess.WHITE) != (lado == "blancas"):
                        error = "Espera tu turno."
                    else:
                        try:
                            movimiento = chess.Move.from_uci(mensaje.get("uci", ""))
                        except (ValueError, TypeError, AttributeError):
                            movimiento = None
                        error = None if movimiento in sala.tablero.legal_moves else "Movimiento ilegal."
                    if error:
                        await websocket.send_json({"tipo": "error", "mensaje": error})
                        continue
                    sala.tablero.push(movimiento)
                elif accion == "rendirse" and not (sala.fin_manual or sala.tablero.is_game_over()):
                    sala.fin_manual = {"resultado": "0-1" if lado == "blancas" else "1-0", "motivo": "rendición"}
                elif accion == "tablas" and not sala.fin_manual and sala.tablero.can_claim_draw():
                    sala.fin_manual = {"resultado": "1/2-1/2", "motivo": "tablas reclamadas"}
                elif accion == "revancha" and (sala.fin_manual or sala.tablero.is_game_over()):
                    sala.votos.add(lado)
                    if len(sala.votos) == 2:
                        sala.tablero.reset()
                        sala.fin_manual = None
                        sala.votos.clear()
                else:
                    await websocket.send_json({"tipo": "error", "mensaje": "Acción no disponible."})
                    continue
                sala.actualizada = time.monotonic()
                await sala.avisar()
    except WebSocketDisconnect:
        pass
    finally:
        async with sala.candado:
            identificador = lado or f"espectador-{id(websocket)}"
            if sala.conexiones.get(identificador) is websocket:
                del sala.conexiones[identificador]
                sala.actualizada = time.monotonic()
                await sala.avisar()

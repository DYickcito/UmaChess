"""Ajedrez para dos jugadores en la terminal (Python 3.12)."""

import argparse

import chess


AYUDA = """Comandos:
  e2e4, e7e8q       Mover por coordenadas (q=dama, r=torre, b=alfil, n=caballo)
  Nf3, O-O, e8=Q    Mover con notación algebraica estándar (SAN)
  movimientos        Mostrar las jugadas realizadas
  deshacer           Deshacer la última jugada
  tablas             Reclamar tablas si las reglas lo permiten
  rendirse           Abandonar la partida
  ayuda              Mostrar esta ayuda
  salir              Terminar el programa

Las piezas en el tablero son K/Q/R/B/N/P (blancas) y k/q/r/b/n/p (negras).
La notación SAN usa letras inglesas: K rey, Q dama, R torre, B alfil, N caballo.
Para coronar por coordenadas, añade q, r, b o n (por ejemplo, e7e8q)."""


def mostrar_tablero(tablero: chess.Board) -> None:
    print("\n    a b c d e f g h")
    for fila in range(7, -1, -1):
        piezas = []
        for columna in range(8):
            pieza = tablero.piece_at(chess.square(columna, fila))
            piezas.append(pieza.symbol() if pieza else ".")
        print(f" {fila + 1}  {' '.join(piezas)}  {fila + 1}")
    print("    a b c d e f g h\n")


def historial(tablero: chess.Board) -> str:
    copia = chess.Board()
    jugadas = []
    for numero, movimiento in enumerate(tablero.move_stack):
        san = copia.san(movimiento)
        if numero % 2 == 0:
            jugadas.append(f"{numero // 2 + 1}. {san}")
        else:
            jugadas[-1] += f" {san}"
        copia.push(movimiento)
    return "  ".join(jugadas) if jugadas else "Aún no hay jugadas."


def interpretar_jugada(tablero: chess.Board, texto: str) -> chess.Move:
    try:
        jugada = chess.Move.from_uci(texto.lower())
    except ValueError:
        pass
    else:
        if jugada in tablero.legal_moves:
            return jugada
    return tablero.parse_san(texto)


def describir_resultado(resultado: chess.Outcome) -> str:
    motivos = {
        chess.Termination.CHECKMATE: "jaque mate",
        chess.Termination.STALEMATE: "ahogado",
        chess.Termination.INSUFFICIENT_MATERIAL: "material insuficiente",
        chess.Termination.SEVENTYFIVE_MOVES: "regla de las 75 jugadas",
        chess.Termination.FIVEFOLD_REPETITION: "quíntuple repetición",
        chess.Termination.FIFTY_MOVES: "regla de las 50 jugadas",
        chess.Termination.THREEFOLD_REPETITION: "triple repetición",
    }
    return f"Fin de la partida: {resultado.result()} ({motivos.get(resultado.termination, 'partida terminada')})."


def jugar() -> None:
    tablero = chess.Board()
    print("Ajedrez para dos jugadores. Escribe 'ayuda' para ver los comandos.")

    while True:
        mostrar_tablero(tablero)
        resultado = tablero.outcome()
        if resultado is not None:
            print(describir_resultado(resultado))
            print(historial(tablero))
            return

        turno = "blancas" if tablero.turn == chess.WHITE else "negras"
        if tablero.is_check():
            print(f"¡Jaque a las {turno}!")
        try:
            texto = input(f"Turno de las {turno}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nPartida terminada.")
            return

        comando = texto.lower()
        if comando == "salir":
            print("Partida terminada.")
            return
        if comando == "ayuda":
            print(AYUDA)
        elif comando == "movimientos":
            print(historial(tablero))
        elif comando == "deshacer":
            if tablero.move_stack:
                tablero.pop()
                print("Última jugada deshecha.")
            else:
                print("No hay jugadas que deshacer.")
        elif comando == "tablas":
            if tablero.can_claim_draw():
                print(f"Tablas reclamadas: {tablero.outcome(claim_draw=True).result()}.")
                return
            print("Todavía no se pueden reclamar tablas.")
        elif comando == "rendirse":
            ganador = "negras" if tablero.turn == chess.WHITE else "blancas"
            print(f"Las {turno} se rinden. Ganan las {ganador}.")
            return
        elif texto:
            try:
                jugada = interpretar_jugada(tablero, texto)
            except ValueError:
                print("Jugada no válida o ilegal. Escribe 'ayuda' para ver ejemplos.")
                continue
            print(f"Jugada: {tablero.san(jugada)}")
            tablero.push(jugada)
        else:
            print("Introduce una jugada o escribe 'ayuda'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ajedrez para dos jugadores en la terminal")
    parser.parse_args()
    jugar()

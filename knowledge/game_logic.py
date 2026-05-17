"""
Buscaminas - Lógica pura del juego
IC6200-PY-260604_2

Sin dependencias de pygame. Maneja:
  - Estado del tablero
  - Generación de minas
  - Revelar celdas / colocar banderas
  - Detección de victoria y derrota
  - Turno de la IA
"""

import os
import sys
import time

from interface.constants import (
    UNREVEALED, REVEALED, FLAGGED, QUESTION, MINE,
    FACE_NORMAL, FACE_OFACE, FACE_DEAD, FACE_WON,
    MIN_ROWS, MAX_ROWS, MIN_COLS, MAX_COLS,
)
from data.bombas import Bombas
from data.lugares_bomba import LugaresBomba
from utils.utils import revelar_celdas_vacias, ia_movimiento_random
from knowledge.logic_ia import LogicIA

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))
from data.map import NOVATO, AFICIONADO, EXPERIMENTADO

_PRESET_MAPS = {
    "Novato":        NOVATO,
    "Aficionado":    AFICIONADO,
    "Experimentado": EXPERIMENTADO,
}


class GameLogic:
    """
    Toda la lógica del juego, sin pygame.

    Atributos públicos que GameScreen puede leer:
        board            — tablero 2D de dicts {state, value, hit}
        rows, cols, mines, mode
        game_active, game_over, game_won
        face_state       — FACE_NORMAL | FACE_OFACE | FACE_DEAD | FACE_WON
        flags_placed
        elapsed          — segundos transcurridos (int)
        esperando_decision_usuario
        inciertas_ia     — lista de (row, col) inciertas para movimiento aleatorio
    """

    def __init__(self, config: dict):
        self.rows  = config["rows"]
        self.cols  = config["cols"]
        self.mines = config["mines"]
        self.mode  = config["name"]

        self.board            = self._make_board()
        self.game_active      = False
        self.game_over        = False
        self.game_won         = False
        self.face_state       = FACE_NORMAL
        self.flags_placed     = 0
        self._start_time      = None
        self.elapsed          = 0
        self.bombas_generadas = False

        self.ia_auto                    = False
        self._ultimo_mov_ia             = 0
        self.esperando_decision_usuario = False
        self.inciertas_ia               = []

    # ──────────────────────────────────────────────────────────────────────────
    #  Tablero
    # ──────────────────────────────────────────────────────────────────────────

    def _make_board(self):
        preset = _PRESET_MAPS.get(self.mode)
        if preset is not None and len(preset) == self.rows and len(preset[0]) == self.cols:
            return [[{"state": UNREVEALED, "value": preset[r][c], "hit": False}
                     for c in range(self.cols)] for r in range(self.rows)]
        return [[{"state": UNREVEALED, "value": 0, "hit": False}
                 for _ in range(self.cols)] for _ in range(self.rows)]

    def reset(self):
        self.board            = self._make_board()
        self.game_active      = False
        self.game_over        = False
        self.game_won         = False
        self.face_state       = FACE_NORMAL
        self.flags_placed     = 0
        self._start_time      = None
        self.elapsed          = 0
        self.bombas_generadas = False
        self.esperando_decision_usuario = False
        self.inciertas_ia     = []

    # ──────────────────────────────────────────────────────────────────────────
    #  Generación de minas
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_mines(self, safe_cell):
        generador  = Bombas(self.rows, self.cols, self.mines)
        ubicaciones = generador.generar_bombas(safe_cell)
        LugaresBomba.colocar_numeros(self.board, ubicaciones)
        self.bombas_generadas = True

    # ──────────────────────────────────────────────────────────────────────────
    #  Actualización de tiempo
    # ──────────────────────────────────────────────────────────────────────────

    def update(self):
        """Debe llamarse cada frame desde GameScreen."""
        if self.game_active and not self.game_over and not self.game_won:
            if self._start_time is not None:
                self.elapsed = min(999, int(time.time() - self._start_time))

        # El bucle auto-IA lo gestiona GameScreen para capturar el highlight

    # ──────────────────────────────────────────────────────────────────────────
    #  Acciones del jugador
    # ──────────────────────────────────────────────────────────────────────────

    def press_cell(self, row, col):
        """MOUSEBUTTONDOWN sobre una celda: activa FACE_OFACE si está sin revelar."""
        if self.game_over or self.game_won:
            return
        if not self.game_active:
            self.game_active = True
            self._start_time = time.time()
        if not self.bombas_generadas:
            self._generate_mines((row, col))
        c = self.board[row][col]
        if c["state"] == UNREVEALED:
            self.face_state = FACE_OFACE

    def reveal_cell(self, row, col) -> set:
        """
        Revela una celda (clic izquierdo / modo reveal).
        Devuelve set vacío siempre (compatibilidad con ia_last_cells).
        """
        if self.game_over or self.game_won:
            return set()
        c = self.board[row][col]
        if c["state"] != UNREVEALED:
            return set()

        if c["value"] == MINE:
            self.game_over   = True
            self.game_active = False
            self.face_state  = FACE_DEAD
            self._reveal_all_mines(row, col)
        else:
            revelar_celdas_vacias(self.board, row, col, self.rows, self.cols)
            if self._check_win():
                self.game_won    = True
                self.game_active = False
                self.face_state  = FACE_WON

        return set()

    def place_flag(self, row, col):
        """Coloca o quita una bandera (modo flag / clic derecho)."""
        if self.game_over or self.game_won:
            return
        c = self.board[row][col]
        if c["state"] == UNREVEALED:
            c["state"] = FLAGGED
            self.flags_placed += 1
        elif c["state"] == FLAGGED:
            c["state"] = UNREVEALED
            self.flags_placed -= 1

    def cycle_mark(self, row, col):
        """Cicla UNREVEALED → FLAGGED → QUESTION → UNREVEALED (clic derecho clásico)."""
        if self.game_over or self.game_won:
            return
        c = self.board[row][col]
        if c["state"] == UNREVEALED:
            c["state"] = FLAGGED;   self.flags_placed += 1
        elif c["state"] == FLAGGED:
            c["state"] = QUESTION;  self.flags_placed -= 1
        elif c["state"] == QUESTION:
            c["state"] = UNREVEALED

    def release_cell(self):
        """MOUSEBUTTONUP: restaura cara si estaba en OFACE."""
        if self.face_state == FACE_OFACE:
            self.face_state = FACE_NORMAL

    # ──────────────────────────────────────────────────────────────────────────
    #  Victoria / derrota
    # ──────────────────────────────────────────────────────────────────────────

    def _check_win(self) -> bool:
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.board[r][c]
                if cell["value"] != MINE and cell["state"] != REVEALED:
                    return False
        return True

    def _reveal_all_mines(self, hit_row, hit_col):
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.board[r][c]
                if cell["value"] == MINE and cell["state"] != FLAGGED:
                    cell["state"] = REVEALED
                    cell["hit"]   = (r == hit_row and c == hit_col)

    # ──────────────────────────────────────────────────────────────────────────
    #  IA
    # ──────────────────────────────────────────────────────────────────────────

    def jugar_turno_ia(self) -> set:
        """
        Ejecuta un turno de la IA.
        Devuelve el set de celdas (row, col) que la IA tocó,
        para que GameScreen pueda resaltarlas visualmente.
        """
        ia = LogicIA(self.board, self.rows, self.cols)
        tocadas = set()

        # Primer movimiento
        if not self.game_active:
            row, col = ia.primer_movimiento()
            self.game_active = True
            self._start_time = time.time()
            if not self.bombas_generadas:
                self._generate_mines((row, col))
            tocadas.add((row, col))
            revelar_celdas_vacias(self.board, row, col, self.rows, self.cols)
            return tocadas

        resultado = ia.analizar()

        for row, col in resultado["minas"]:
            cell = self.board[row][col]
            if cell["state"] == UNREVEALED:
                cell["state"] = FLAGGED
                self.flags_placed += 1
                tocadas.add((row, col))

        for row, col in resultado["seguras"]:
            cell = self.board[row][col]
            if cell["state"] == UNREVEALED:
                tocadas.add((row, col))
                revelar_celdas_vacias(self.board, row, col, self.rows, self.cols)

        if self._check_win():
            self.game_won    = True
            self.game_active = False
            self.face_state  = FACE_WON
            return tocadas

        if not resultado["minas"] and not resultado["seguras"]:
            print("[IA] No hay movimientos logicos disponibles")
            self.inciertas_ia = [
                (r, c)
                for r in range(self.rows)
                for c in range(self.cols)
                if self.board[r][c]["state"] == UNREVEALED
            ]
            self.esperando_decision_usuario = True

        return tocadas

    def ia_movimiento_aleatorio(self) -> set:
        """Movimiento aleatorio cuando la IA no tiene certeza."""
        tocadas = set()
        if not self.inciertas_ia:
            return tocadas
        import random
        row, col = random.choice(self.inciertas_ia)
        print(f"[IA] Movimiento aleatorio en ({row}, {col})")
        tocadas.add((row, col))
        revelar_celdas_vacias(self.board, row, col, self.rows, self.cols)
        self.esperando_decision_usuario = False
        return tocadas

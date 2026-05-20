import random
from interface.constants import UNREVEALED, REVEALED, FLAGGED


# ══════════════════════════════════════════════════════════════════════════════
#  Restricción
# ══════════════════════════════════════════════════════════════════════════════

class Restriccion:
    """
    Representa: las celdas del conjunto 'cells' contienen exactamente
    'count' minas entre ellas.
    """
    def __init__(self, cells, count):
        self.cells = frozenset(cells)
        self.count = int(count)

    def __eq__(self, other):
        return isinstance(other, Restriccion) and self.cells == other.cells and self.count == other.count

    def __hash__(self):
        return hash((self.cells, self.count))

    def __repr__(self):
        return f"{set(self.cells)} = {self.count}"


# ══════════════════════════════════════════════════════════════════════════════
#  IA
# ══════════════════════════════════════════════════════════════════════════════

class LogicIA:
    def __init__(self, board, rows, cols):
        self.board = board
        self.rows  = rows
        self.cols  = cols

    # ──────────────────────────────────────────────────────────────────────────
    #  Vecinos
    # ──────────────────────────────────────────────────────────────────────────

    def vecinos(self, row, col):
        resultado = []
        for df in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if df == 0 and dc == 0:
                    continue
                nr, nc = row + df, col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    resultado.append((nr, nc))
        return resultado

    # ──────────────────────────────────────────────────────────────────────────
    #  Construcción de restricciones desde el tablero
    # ──────────────────────────────────────────────────────────────────────────

    def _construir_restricciones(self):
        restricciones = set()
        for row in range(self.rows):
            for col in range(self.cols):
                celda = self.board[row][col]
                if celda["state"] != REVEALED or celda["value"] <= 0:
                    continue

                ocultas  = []
                banderas = 0
                for nr, nc in self.vecinos(row, col):
                    v = self.board[nr][nc]
                    if v["state"] == UNREVEALED:
                        ocultas.append((nr, nc))
                    elif v["state"] == FLAGGED:
                        banderas += 1

                minas_restantes = celda["value"] - banderas

                if ocultas and 0 <= minas_restantes <= len(ocultas):
                    restricciones.add(Restriccion(ocultas, minas_restantes))

        return restricciones

    # ──────────────────────────────────────────────────────────────────────────
    #  Propagación de restricciones
    # ──────────────────────────────────────────────────────────────────────────

    def _propagar(self, restricciones):
        """
        Aplica las tres reglas de inferencia en bucle hasta convergencia.

        Regla 1: |celdas| == k  →  todas minas
        Regla 2: k == 0         →  todas seguras
        Regla 3: A ⊆ B          →  nueva restricción (B−A) = (kB − kA)
        """
        minas   = set()
        seguras = set()
        pendientes = set(restricciones)

        cambio = True
        while cambio:
            cambio = False
            nuevas = set()

            for r in list(pendientes):
                # Actualizar restricción con lo ya conocido
                celdas_activas = r.cells - minas - seguras
                k = r.count - len(r.cells & minas)

                if not celdas_activas:
                    continue

                # Regla 1: todas las celdas activas son minas
                if k == len(celdas_activas):
                    for c in celdas_activas:
                        if c not in minas:
                            minas.add(c)
                            cambio = True
                    continue

                # Regla 2: ninguna celda activa es mina
                if k == 0:
                    for c in celdas_activas:
                        if c not in seguras:
                            seguras.add(c)
                            cambio = True
                    continue

                nuevas.add(Restriccion(celdas_activas, k))

            # Regla 3: inferencia por subconjuntos  A ⊆ B → (B−A) = (kB − kA)
            lista = list(nuevas)
            for i in range(len(lista)):
                for j in range(len(lista)):
                    if i == j:
                        continue
                    a, b = lista[i], lista[j]
                    if a.cells and a.cells < b.cells:
                        diff_count = b.count - a.count
                        diff_cells = b.cells - a.cells
                        if 0 <= diff_count <= len(diff_cells):
                            nueva = Restriccion(diff_cells, diff_count)
                            if nueva not in nuevas:
                                nuevas.add(nueva)
                                cambio = True

            pendientes = nuevas

        return minas, seguras

    # ──────────────────────────────────────────────────────────────────────────
    #  API pública
    # ──────────────────────────────────────────────────────────────────────────

    def analizar(self):
        restricciones = self._construir_restricciones()
        minas, seguras = self._propagar(restricciones)

        todas_ocultas = {
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if self.board[r][c]["state"] == UNREVEALED
        }
        inciertas = todas_ocultas - minas - seguras

        print(f"[IA] Seguras: {len(seguras)}  Minas: {len(minas)}  Inciertas: {len(inciertas)}")

        return {
            "seguras":   list(seguras),
            "minas":     list(minas),
            "inciertas": list(inciertas),
            "logs":      [],
        }

    def primer_movimiento(self):
        row = random.randint(0, self.rows - 1)
        col = random.randint(0, self.cols - 1)
        print(f"[IA] Primer movimiento aleatorio en ({row},{col})")
        return (row, col)

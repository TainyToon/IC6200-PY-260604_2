"""
Buscaminas – Pantalla de Configuración Personalizada
IC6200-PY-260604_2

Permite al usuario ajustar filas, columnas y minas dentro de los
límites definidos (Observaciones #3 y #7).
"""

import pygame
from interface.constants import *
from interface.sprites import draw_raised, draw_sunken


class CustomScreen:
    """
    Pantalla con botones +/- para configurar el tablero personalizado.
    Respeta los límites mínimos (9×9, 10 minas) y máximos (16×30, calculado).
    """

    _BG_TOP = ( 18,  52, 120)
    _BG_BOT = (  5,  20,  60)

    _W = 460
    _H = 420

    def __init__(self):
        self.rows  = MIN_ROWS
        self.cols  = MIN_COLS
        self.mines = 10
        self._build()

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────

    def _max_mines(self) -> int:
        """Máximo de minas: deja al menos 9 celdas libres."""
        return max(1, self.rows * self.cols - 9)

    def _clamp(self):
        self.rows  = max(MIN_ROWS, min(MAX_ROWS, self.rows))
        self.cols  = max(MIN_COLS, min(MAX_COLS, self.cols))
        self.mines = max(1,        min(self._max_mines(), self.mines))

    # ──────────────────────────────────────────
    # Construcción de layout
    # ──────────────────────────────────────────

    def _build(self):
        self._font_title = pygame.font.SysFont("Arial", 34, bold=True)
        self._font_label = pygame.font.SysFont("Arial", 19, bold=True)
        self._font_val   = pygame.font.SysFont("Arial", 28, bold=True)
        self._font_btn   = pygame.font.SysFont("Arial", 22, bold=True)
        self._font_sub   = pygame.font.SysFont("Arial", 15)
        self._font_hint  = pygame.font.SysFont("Arial", 13)

        # Botón de inicio y volver
        self._btn_start = pygame.Rect(self._W//2 - 110, self._H - 70, 220, 44)
        self._btn_back  = pygame.Rect(18, 18, 90, 32)

        # Cada fila de ajuste tiene: [label, attr, min, max_fn, btn-, btn+]
        # Se construyen dinámicamente en draw() porque max_mines cambia
        self._hover: str | None = None   # 'rows-', 'rows+', 'cols-', etc.

    # ──────────────────────────────────────────
    # Layout de botones +/-
    # ──────────────────────────────────────────

    def _rows_data(self):
        """Devuelve la configuración de cada fila de ajuste."""
        cx = self._W // 2
        rows_y    = 160
        cols_y    = 240
        mines_y   = 320
        bw = 36         # ancho botón +/-

        def make_row(y, attr, lo, hi):
            val = getattr(self, attr)
            btn_minus = pygame.Rect(cx - 90,      y - bw//2, bw, bw)
            btn_plus  = pygame.Rect(cx + 90 - bw, y - bw//2, bw, bw)
            return {
                "attr": attr, "lo": lo, "hi": hi, "val": val,
                "minus": btn_minus, "plus": btn_plus,
                "cy": y,
            }

        return [
            make_row(rows_y,  "rows",  MIN_ROWS,  MAX_ROWS),
            make_row(cols_y,  "cols",  MIN_COLS,  MAX_COLS),
            make_row(mines_y, "mines", 1,          self._max_mines()),
        ]

    # ──────────────────────────────────────────
    # API pública
    # ──────────────────────────────────────────

    def get_size(self) -> tuple[int, int]:
        return (self._W, self._H)

    def handle_event(self, event) -> tuple | None:
        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            self._hover = None
            for row in self._rows_data():
                if row["minus"].collidepoint(pos):
                    self._hover = f"{row['attr']}-"
                elif row["plus"].collidepoint(pos):
                    self._hover = f"{row['attr']}+"
            if self._btn_start.collidepoint(pos):
                self._hover = "start"
            elif self._btn_back.collidepoint(pos):
                self._hover = "back"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            for row in self._rows_data():
                if row["minus"].collidepoint(pos):
                    setattr(self, row["attr"],
                            max(row["lo"], getattr(self, row["attr"]) - 1))
                    self._clamp()
                    return None
                if row["plus"].collidepoint(pos):
                    setattr(self, row["attr"],
                            min(row["hi"], getattr(self, row["attr"]) + 1))
                    self._clamp()
                    return None

            if self._btn_start.collidepoint(pos):
                return ("start_game", {
                    "name": "Personalizado",
                    "rows": self.rows,
                    "cols": self.cols,
                    "mines": self.mines,
                })
            if self._btn_back.collidepoint(pos):
                return ("menu", None)

        return None

    def update(self):
        pass

    def draw(self, screen: pygame.Surface):
        w, h = self._W, self._H

        # Fondo degradado
        step = max(1, h // 80)
        for y in range(0, h, step):
            t = y / h
            r = int(self._BG_TOP[0] * (1-t) + self._BG_BOT[0] * t)
            g = int(self._BG_TOP[1] * (1-t) + self._BG_BOT[1] * t)
            b = int(self._BG_TOP[2] * (1-t) + self._BG_BOT[2] * t)
            pygame.draw.rect(screen, (r, g, b), (0, y, w, step))

        # Título
        title = self._font_title.render("Configuración Personalizada",
                                        True, (255, 255, 255))
        screen.blit(title, title.get_rect(centerx=w//2, y=20))

        # Botón volver
        bk_clr = (200, 200, 200) if self._hover == "back" else (180, 180, 180)
        pygame.draw.rect(screen, bk_clr, self._btn_back, border_radius=5)
        bk_lbl = self._font_hint.render("◀ Volver", True, (50, 50, 100))
        screen.blit(bk_lbl, bk_lbl.get_rect(center=self._btn_back.center))

        # Línea separadora
        pygame.draw.line(screen, (100, 140, 220), (30, 70), (w-30, 70), 1)

        labels = {"rows": "Filas", "cols": "Columnas", "mines": "Minas"}

        for row in self._rows_data():
            attr = row["attr"]
            cy   = row["cy"]
            cx   = w // 2

            # Etiqueta
            lbl = self._font_label.render(labels[attr], True, (200, 220, 255))
            screen.blit(lbl, lbl.get_rect(centerx=cx, centery=cy - 18))

            # Valor
            val_surf = self._font_val.render(str(row["val"]), True, (255, 255, 200))
            screen.blit(val_surf, val_surf.get_rect(center=(cx, cy + 4)))

            # Límites
            hint = self._font_hint.render(
                f"(mín {row['lo']}  –  máx {row['hi']})",
                True, (140, 170, 220))
            screen.blit(hint, hint.get_rect(centerx=cx, centery=cy + 24))

            # Botones -/+
            for (btn, symbol, hkey) in [
                (row["minus"], "−", f"{attr}-"),
                (row["plus"],  "+", f"{attr}+"),
            ]:
                bg = (230, 230, 250) if self._hover == hkey else (210, 210, 210)
                pygame.draw.rect(screen, bg, btn, border_radius=4)
                pygame.draw.rect(screen, (130, 130, 150), btn, 1, border_radius=4)
                sym = self._font_btn.render(symbol, True, (30, 30, 100))
                screen.blit(sym, sym.get_rect(center=btn.center))

        # Botón INICIAR
        st_clr = (100, 180, 100) if self._hover == "start" else (70, 150, 70)
        pygame.draw.rect(screen, st_clr, self._btn_start, border_radius=8)
        pygame.draw.rect(screen, (40, 100, 40), self._btn_start, 2, border_radius=8)
        st_lbl = self._font_label.render("▶  Iniciar Partida", True, C_WHITE)
        screen.blit(st_lbl, st_lbl.get_rect(center=self._btn_start.center))

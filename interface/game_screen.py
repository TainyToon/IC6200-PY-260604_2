"""
Buscaminas - Pantalla de Juego
IC6200-PY-260604_2

Toolbar estilo Windows 98:
  [zoom+] [zoom-] | [dificultad] | [pista] [bandera] [?] | [check]
  icono dificultad: ^ principiante  ^^ intermedio  * avanzado  gear personalizado
"""

import sys
import os
import pygame
import time
import math
from interface.constants import *
from interface.sprites import (draw_raised, draw_sunken,
                     make_cell_sprites, make_face_sprites,
                     make_lcd_surface)

#Imports de archivos.
from utils.utils import revelar_celdas_vacias
from data.bombas import Bombas
from data.lugares_bomba import LugaresBomba

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "data"))
from data.map import NOVATO, AFICIONADO, EXPERIMENTADO

_PRESET_MAPS = {
    "Novato":        NOVATO,
    "Aficionado":    AFICIONADO,
    "Experimentado": EXPERIMENTADO,
}

_DIFF_IDX = {DIFFICULTIES[k]["name"]: i for i, k in enumerate(DIFF_ORDER)}

_ZOOM_IN  = "zoom_in"
_ZOOM_OUT = "zoom_out"
_DIFF     = "difficulty"
_HINT     = "hint"
_FLAG     = "flag_btn"
_QUES     = "question_btn"
_CHECK    = "check"

_TOOLBAR_SEQ = [
    _ZOOM_IN, _ZOOM_OUT, None,
    _DIFF,    None,
    _HINT, _FLAG, _QUES, None,
    _CHECK,
]

_NUM_DIFFS = 4   # 0=novato 1=aficionado 2=experimentado 3=personalizado


def _open_custom_window():
    """
    Ventana de configuracion personalizada usando tkinter.
    Funciona con cualquier version de pygame; corre en paralelo al juego.
    """
    import tkinter as tk

    result = [None]

    root = tk.Tk()
    root.title("Configuracion personalizada")
    root.configure(bg="#122878")
    root.resizable(False, False)

    W, H = 370, 310
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
    root.lift()
    root.focus_force()

    rows_var  = tk.IntVar(value=MIN_ROWS)
    cols_var  = tk.IntVar(value=MIN_COLS)
    mines_var = tk.IntVar(value=10)

    def max_mines():
        return max(1, rows_var.get() * cols_var.get() - 9)

    def clamp_all():
        rows_var.set(max(MIN_ROWS, min(MAX_ROWS, rows_var.get())))
        cols_var.set(max(MIN_COLS, min(MAX_COLS, cols_var.get())))
        mines_var.set(max(1, min(max_mines(), mines_var.get())))
        lbl_max_mines.config(text=f"max {max_mines()}")

    def adjust(var, lo, hi_fn, delta):
        var.set(max(lo, min(hi_fn(), var.get() + delta)))
        clamp_all()

    BG   = "#122878"
    FG   = "#c8dcff"
    VFG  = "#ffffc8"
    BTN  = "#d2d4e6"
    BTN2 = "#506494"

    # ── Titulo ────────────────────────────────────────────────────────────────
    tk.Label(root, text="Configuracion personalizada",
             bg=BG, fg="white", font=("Arial", 14, "bold")).pack(pady=(14, 0))
    tk.Frame(root, bg="#6488dc", height=1).pack(fill="x", padx=20, pady=8)

    # ── Filas de control ──────────────────────────────────────────────────────
    rows_data = [
        ("Filas",    rows_var,  MIN_ROWS, lambda: MAX_ROWS,    None),
        ("Columnas", cols_var,  MIN_COLS, lambda: MAX_COLS,    None),
        ("Minas",    mines_var, 1,        max_mines,           None),
    ]

    lbl_max_mines = None

    for i, (label, var, lo, hi_fn, _) in enumerate(rows_data):
        frame = tk.Frame(root, bg=BG)
        frame.pack(pady=4)

        tk.Label(frame, text=label, bg=BG, fg=FG,
                 font=("Arial", 11, "bold"), width=8, anchor="e").pack(side="left")

        tk.Button(frame, text="-", width=3, font=("Arial", 11, "bold"),
                  bg=BTN, relief="raised",
                  command=lambda v=var, l=lo, h=hi_fn: adjust(v, l, h, -1)
                  ).pack(side="left", padx=4)

        tk.Label(frame, textvariable=var, bg=BG, fg=VFG,
                 font=("Arial", 14, "bold"), width=4).pack(side="left")

        tk.Button(frame, text="+", width=3, font=("Arial", 11, "bold"),
                  bg=BTN, relief="raised",
                  command=lambda v=var, l=lo, h=hi_fn: adjust(v, l, h, +1)
                  ).pack(side="left", padx=4)

        hi_val = hi_fn() if callable(hi_fn) else hi_fn
        hint_text = f"min {lo}  max {hi_val}"
        hint_lbl = tk.Label(frame, text=hint_text, bg=BG, fg="#8aaada",
                            font=("Arial", 9), width=14, anchor="w")
        hint_lbl.pack(side="left")

        if label == "Minas":
            lbl_max_mines = hint_lbl

    # Actualizar hint de minas cada vez que cambian filas o cols
    def on_change(*_):
        clamp_all()
        if lbl_max_mines:
            lbl_max_mines.config(text=f"min 1  max {max_mines()}")

    rows_var.trace_add("write", on_change)
    cols_var.trace_add("write", on_change)

    tk.Frame(root, bg="#6488dc", height=1).pack(fill="x", padx=20, pady=10)

    # ── Botones Iniciar / Cancelar ────────────────────────────────────────────
    btn_frame = tk.Frame(root, bg=BG)
    btn_frame.pack()

    def on_start():
        clamp_all()
        result[0] = {
            "name":  "Personalizado",
            "rows":  rows_var.get(),
            "cols":  cols_var.get(),
            "mines": mines_var.get(),
        }
        root.destroy()

    def on_cancel():
        root.destroy()

    tk.Button(btn_frame, text="Iniciar", width=12, font=("Arial", 11, "bold"),
              bg="#4a9640", fg="white", relief="raised",
              activebackground="#5ab050",
              command=on_start).pack(side="left", padx=8)

    tk.Button(btn_frame, text="Cancelar", width=12, font=("Arial", 11, "bold"),
              bg="#7a2020", fg="white", relief="raised",
              activebackground="#9a3030",
              command=on_cancel).pack(side="left", padx=8)

    root.bind("<Return>", lambda e: on_start())
    root.bind("<Escape>", lambda e: on_cancel())
    root.protocol("WM_DELETE_WINDOW", on_cancel)

    root.mainloop()
    return result[0]


class GameScreen:
    """Pantalla principal de juego con toolbar estilo Win98."""

    _STATUS_BG  = ( 40,  40,  40)
    _STATUS_TXT = (210, 210, 210)
    _STATUS_H   = 20

    def __init__(self, config: dict):
        self.config = config
        self.rows   = config["rows"]
        self.cols   = config["cols"]
        self.mines  = config["mines"]
        self.mode   = config["name"]
        self.bombas_generadas = False

        self._diff_idx  = _DIFF_IDX.get(self.mode, 3)
        self._cell_size = CELL_SIZE

        self.game_active  = False
        self.game_over    = False
        self.game_won     = False
        self.face_state   = FACE_NORMAL
        self.flags_placed = 0
        self._start_time  = None
        self._elapsed     = 0
        self._board = self._make_board()

        self._mouse_cell = None
        self._left_held  = False

        pygame.font.init()
        self._cell_spr    = make_cell_sprites(self._cell_size)
        self._face_spr    = make_face_sprites(FACE_SIZE)
        self._font_status = pygame.font.SysFont("Arial", 11)
        self._font_q      = pygame.font.SysFont("Arial", 15, bold=True)
        self._font_num    = pygame.font.Font(None, 14)

        self._compute_layout()

    def _compute_layout(self):
        BO = BORDER_OUTER
        BI = BORDER_INNER
        CS = self._cell_size
        TH = TOOLBAR_H
        bpw = self.cols * CS
        bph = self.rows * CS
        self._win_w = BO + BI + bpw + BI + BO
        self._win_h = TH + BO + HEADER_H + BI + bph + BI + BO + self._STATUS_H
        self._toolbar_rect = pygame.Rect(0, 0, self._win_w, TH)
        self._build_toolbar_rects(TH)
        self._header_rect = pygame.Rect(BO, TH+BO, self._win_w-2*BO, HEADER_H)
        self._board_rect  = pygame.Rect(BO, TH+BO+HEADER_H+BI,
                                        self._win_w-2*BO, bph+2*BI)
        self._grid_x = BO + BI
        self._grid_y = TH + BO + HEADER_H + BI + BI
        hx  = self._header_rect.x + 2
        hw  = self._header_rect.w - 4
        hcy = self._header_rect.centery
        lcd_w = LCD_DIGITS*LCD_DIGIT_W + (LCD_DIGITS-1)*LCD_GAP + 2*LCD_PAD
        lcd_h = LCD_DIGIT_H + 2*LCD_PAD
        PAD   = 4
        self._lcd_mines_rect = pygame.Rect(hx+PAD, hcy-lcd_h//2, lcd_w, lcd_h)
        self._lcd_timer_rect = pygame.Rect(hx+hw-PAD-lcd_w, hcy-lcd_h//2, lcd_w, lcd_h)
        self._face_rect = pygame.Rect(self._header_rect.centerx-FACE_SIZE//2,
                                      hcy-FACE_SIZE//2, FACE_SIZE, FACE_SIZE)
        self._status_rect = pygame.Rect(0, self._win_h-self._STATUS_H,
                                        self._win_w, self._STATUS_H)

    def _build_toolbar_rects(self, TH):
        bs=24; py=(TH-bs)//2; x=4; gap=3; sep=9
        self._toolbar_btn_rects  = []
        self._toolbar_btn_ids    = []
        self._toolbar_separators = []
        for item in _TOOLBAR_SEQ:
            if item is None:
                self._toolbar_separators.append(x+1)
                x += sep
            else:
                self._toolbar_btn_rects.append(pygame.Rect(x, py, bs, bs))
                self._toolbar_btn_ids.append(item)
                x += bs + gap

    def _make_board(self):
        preset = _PRESET_MAPS.get(self.mode)
        if preset is not None:
            return [[{"state": UNREVEALED, "value": preset[r][c], "hit": False}
                     for c in range(self.cols)] for r in range(self.rows)]
        return [[{"state": UNREVEALED, "value": 0, "hit": False}
                 for _ in range(self.cols)] for _ in range(self.rows)]

    def reset(self):
        self._board = self._make_board()
        self.game_active = self.game_over = self.game_won = False
        self.face_state   = FACE_NORMAL
        self.flags_placed = 0
        self._start_time  = None
        self._elapsed     = 0
        self._left_held   = False
        self._mouse_cell  = None
        self.bombas_generadas = False

    def _pixel_to_cell(self, px, py):
        cs = self._cell_size
        col = (px - self._grid_x) // cs
        row = (py - self._grid_y) // cs
        if (0 <= row < self.rows and 0 <= col < self.cols
                and self._grid_x <= px < self._grid_x + self.cols*cs
                and self._grid_y <= py < self._grid_y + self.rows*cs):
            return (row, col)
        return None

    def _cell_rect(self, row, col):
        cs = self._cell_size
        return pygame.Rect(self._grid_x+col*cs, self._grid_y+row*cs, cs, cs)

    def _zoom(self, delta):
        new = max(12, min(34, self._cell_size + delta))
        if new != self._cell_size:
            self._cell_size = new
            self._cell_spr  = make_cell_sprites(self._cell_size)
            self._compute_layout()
            return True
        return False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_r):
                self.reset()

        if event.type == pygame.MOUSEMOTION:
            self._mouse_cell = self._pixel_to_cell(*event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for btn_r, btn_id in zip(self._toolbar_btn_rects, self._toolbar_btn_ids):
                if not btn_r.collidepoint(pos):
                    continue
                if btn_id == _ZOOM_IN:
                    if self._zoom(+2): return ("resize", None)
                elif btn_id == _ZOOM_OUT:
                    if self._zoom(-2): return ("resize", None)
                elif btn_id == _DIFF:
                    new_idx = (self._diff_idx + 1) % _NUM_DIFFS
                    self._diff_idx = new_idx
                    if new_idx < 3:
                        return ("start_game", dict(DIFFICULTIES[DIFF_ORDER[new_idx]]))
                    else:
                        cfg = _open_custom_window()
                        if cfg:
                            return ("start_game", cfg)
                        return None
                return None

            if self._face_rect.collidepoint(pos):
                self.reset(); return None

            cell = self._pixel_to_cell(*pos)
            if cell is None: return None
            row, col = cell
            c = self._board[row][col]
            
            if self.game_over or self.game_won: return None

            if not self.game_active: #Inicio de partida.
                self.game_active = True
                self._start_time = time.time()

            self._left_held = True
            if c["state"] == UNREVEALED:
                self.face_state = FACE_OFACE

            if not self.bombas_generadas:
                generador = Bombas(self.rows, self.cols, self.mines)
                ubicaciones = generador.generar_bombas((row, col))
                LugaresBomba.colocar_numeros(self._board, ubicaciones)
                self.bombas_generadas = True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            cell = self._pixel_to_cell(*event.pos)
            if cell and not self.game_over and not self.game_won:
                row, col = cell
                c = self._board[row][col]
                if c["state"] == UNREVEALED:
                    c["state"] = FLAGGED;   self.flags_placed += 1
                elif c["state"] == FLAGGED:
                    c["state"] = QUESTION;  self.flags_placed -= 1
                elif c["state"] == QUESTION:
                    c["state"] = UNREVEALED

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._left_held = False
            if self.face_state == FACE_OFACE:
                self.face_state = FACE_NORMAL
            cell = self._pixel_to_cell(*event.pos)
            if cell and not self.game_over and not self.game_won:
                row, col = cell
                c = self._board[row][col]
                if c["state"] == UNREVEALED:
                    revelar_celdas_vacias(
                        self._board,
                        row,
                        col,
                        self.rows,
                        self.cols
                    )

        return None

    def update(self):
        if self.game_active and not self.game_over and not self.game_won:
            if self._start_time is not None:
                self._elapsed = min(999, int(time.time() - self._start_time))

    def get_size(self):
        return (self._win_w, self._win_h)

    def draw(self, screen):
        screen.fill(C_BG)
        draw_raised(screen, (0, TOOLBAR_H, self._win_w,
                             self._win_h - self._STATUS_H - TOOLBAR_H),
                    w=BORDER_OUTER // 2)
        self._draw_toolbar(screen)
        pygame.draw.rect(screen, C_BG, self._header_rect)
        draw_sunken(screen, self._header_rect, w=2)
        self._draw_lcd(screen, self._lcd_mines_rect, self.mines - self.flags_placed)
        self._draw_face(screen)
        self._draw_lcd(screen, self._lcd_timer_rect, self._elapsed)
        pygame.draw.rect(screen, C_BG, self._board_rect)
        draw_sunken(screen, self._board_rect, w=BORDER_INNER // 2)
        self._draw_board(screen)
        self._draw_status(screen)

    def _draw_toolbar(self, screen):
        TH = TOOLBAR_H
        pygame.draw.rect(screen, C_BG, self._toolbar_rect)
        draw_raised(screen, (0, 0, self._win_w, TH), w=2)
        mpos = pygame.mouse.get_pos()
        mb   = pygame.mouse.get_pressed()
        for btn_r, btn_id in zip(self._toolbar_btn_rects, self._toolbar_btn_ids):
            hover   = btn_r.collidepoint(mpos)
            pressed = hover and mb[0]
            if pressed: draw_sunken(screen, tuple(btn_r), w=2)
            else:       draw_raised(screen, tuple(btn_r), w=2)
            self._draw_icon(screen, btn_r, btn_id, 1 if pressed else 0)
        for sx in self._toolbar_separators:
            pygame.draw.line(screen, C_GRAY_MID, (sx,   5), (sx,   TH-5), 1)
            pygame.draw.line(screen, C_WHITE,    (sx+1, 5), (sx+1, TH-5), 1)

    def _draw_icon(self, screen, btn_r, btn_id, ox):
        cx = btn_r.centerx + ox
        cy = btn_r.centery + ox
        if btn_id == _ZOOM_IN:
            self._ic_magnifier(screen, cx, cy, plus=True)
        elif btn_id == _ZOOM_OUT:
            self._ic_magnifier(screen, cx, cy, plus=False)
        elif btn_id == _DIFF:
            idx = self._diff_idx
            if idx == 0:   self._ic_chevron(screen, cx, cy, double=False)
            elif idx == 1: self._ic_chevron(screen, cx, cy, double=True)
            elif idx == 2: self._ic_star(screen, cx, cy)
            else:          self._ic_gear(screen, cx, cy)
        elif btn_id == _HINT:
            self._ic_bulb(screen, cx, cy)
        elif btn_id == _FLAG:
            self._ic_flag(screen, cx, cy)
        elif btn_id == _QUES:
            t = self._font_q.render("?", True, (40, 40, 160))
            screen.blit(t, t.get_rect(center=(cx, cy)))
        elif btn_id == _CHECK:
            self._ic_check(screen, cx, cy)

    def _ic_magnifier(self, screen, cx, cy, plus=True):
        lx, ly = cx-2, cy-2
        pygame.draw.circle(screen, C_BLACK, (lx, ly), 6, 2)
        dx = int(6*0.65)
        pygame.draw.line(screen, C_BLACK, (lx+dx, ly+dx), (lx+dx+5, ly+dx+5), 2)
        if plus:
            pygame.draw.line(screen, C_BLACK, (lx-3, ly), (lx+3, ly), 2)
            pygame.draw.line(screen, C_BLACK, (lx, ly-3), (lx, ly+3), 2)
        else:
            pygame.draw.line(screen, C_BLACK, (lx-3, ly), (lx+3, ly), 2)

    def _ic_chevron(self, screen, cx, cy, double=False):
        w, h = 8, 5
        col = (20, 70, 200)
        if double:
            for y0 in (cy-5, cy+2):
                pygame.draw.lines(screen, col, False,
                                  [(cx-w, y0+h), (cx, y0), (cx+w, y0+h)], 2)
        else:
            pygame.draw.lines(screen, col, False,
                              [(cx-w, cy+h//2+1), (cx, cy-h//2+1),
                               (cx+w, cy+h//2+1)], 3)

    def _ic_star(self, screen, cx, cy):
        r_out, r_in = 8, 3
        pts = []
        for i in range(10):
            ang = -math.pi/2 + i*math.pi/5
            r   = r_out if i % 2 == 0 else r_in
            pts.append((int(cx + r*math.cos(ang)), int(cy + r*math.sin(ang))))
        pygame.draw.polygon(screen, (200, 160, 0), pts)
        pygame.draw.polygon(screen, (120,  90, 0), pts, 1)

    def _ic_gear(self, screen, cx, cy):
        gc = (55, 55, 75)
        n  = 8; r_body=8; r_tip=11; r_hub=3
        t_angle = math.pi / n * 0.55
        pygame.draw.circle(screen, gc, (cx, cy), r_body)
        for i in range(n):
            base = 2*math.pi*i/n
            pts = [
                (cx + r_body*math.cos(base - t_angle*1.2),
                 cy + r_body*math.sin(base - t_angle*1.2)),
                (cx + r_tip *math.cos(base - t_angle),
                 cy + r_tip *math.sin(base - t_angle)),
                (cx + r_tip *math.cos(base + t_angle),
                 cy + r_tip *math.sin(base + t_angle)),
                (cx + r_body*math.cos(base + t_angle*1.2),
                 cy + r_body*math.sin(base + t_angle*1.2)),
            ]
            pygame.draw.polygon(screen, gc, [(int(p[0]),int(p[1])) for p in pts])
        pygame.draw.circle(screen, C_BG, (cx, cy), r_hub)
        pygame.draw.circle(screen, gc,   (cx, cy), r_hub, 1)

    def _ic_bulb(self, screen, cx, cy):
        pygame.draw.circle(screen, (255, 230, 0), (cx, cy-2), 6)
        pygame.draw.circle(screen, C_BLACK,       (cx, cy-2), 6, 1)
        pygame.draw.rect(screen, (210, 210, 180), (cx-3, cy+3, 6, 5))
        pygame.draw.rect(screen, C_BLACK,         (cx-3, cy+3, 6, 5), 1)
        pygame.draw.line(screen, (255, 255, 150), (cx-2, cy+1), (cx+2, cy-3), 1)

    def _ic_flag(self, screen, cx, cy):
        px, py0, py1 = cx-2, cy-7, cy+7
        pygame.draw.line(screen, C_BLACK, (px, py0), (px, py1), 2)
        pygame.draw.polygon(screen, (220, 20, 20),
                             [(px, py0), (px+7, py0+3), (px, py0+6)])
        t = self._font_num.render("1", True, C_BLACK)
        screen.blit(t, (cx+4, cy))

    def _ic_check(self, screen, cx, cy):
        pygame.draw.lines(screen, (0, 140, 0), False,
                          [(cx-7, cy+1), (cx-2, cy+6), (cx+7, cy-6)], 3)

    def _draw_lcd(self, screen, rect, value):
        lcd = make_lcd_surface(value)
        screen.blit(lcd, (rect.x+(rect.w-lcd.get_width())//2,
                          rect.y+(rect.h-lcd.get_height())//2))

    def _draw_face(self, screen):
        pos     = pygame.mouse.get_pos()
        pressed = self._left_held and self._face_rect.collidepoint(pos)
        key     = f"{self.face_state}_{'pressed' if pressed else 'normal'}"
        spr     = self._face_spr.get(key)
        if spr: screen.blit(spr, self._face_rect.topleft)

    def _draw_board(self, screen):
        hover = self._mouse_cell
        for r in range(self.rows):
            for c in range(self.cols):
                spr = self._sprite_for(self._board[r][c], r, c, hover)
                screen.blit(spr, self._cell_rect(r, c).topleft)

    def _sprite_for(self, cell, row, col, hover):
        s, v = cell["state"], cell["value"]
        if s == FLAGGED:  return self._cell_spr["flag"]
        if s == QUESTION: return self._cell_spr["question"]
        if s == REVEALED:
            if cell["hit"]: return self._cell_spr["mine_hit"]
            if v == MINE:   return self._cell_spr["mine"]
            if v == 0:      return self._cell_spr["revealed"]
            return self._cell_spr[str(v)]
        if self._left_held and hover==(row,col) and not self.game_over and not self.game_won:
            return self._cell_spr["revealed"]
        return self._cell_spr["unrevealed"]

    def _draw_status(self, screen):
        pygame.draw.rect(screen, self._STATUS_BG, self._status_rect)
        fl = self.mines - self.flags_placed
        if self.game_won:
            msg = "Ganaste!  R -> reiniciar"
        elif self.game_over:
            msg = "Perdiste!  R -> reiniciar"
        else:
            msg = (f"{self.mode}  |  {self.cols}x{self.rows}  |  "
                   f"Minas: {self.mines}  Banderas: {self.flags_placed}  "
                   f"Restantes: {fl}  Tiempo: {self._elapsed}s  |  R -> reiniciar")
        txt = self._font_status.render(msg, True, self._STATUS_TXT)
        screen.blit(txt, (5, self._status_rect.y + 4))



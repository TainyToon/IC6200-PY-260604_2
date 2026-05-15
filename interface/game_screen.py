# v1778821685
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
                     make_cell_sprites, make_lcd_surface)

#Imports de archivos.
from utils.utils import revelar_celdas_vacias, ia_movimiento_random
from data.bombas import Bombas
from data.lugares_bomba import LugaresBomba

from knowledge.logic_ia import LogicIA
from utils.utils import revelar_celdas_vacias

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
_FLAG     = "flag_btn"
_QUES     = "question_btn"

_TOOLBAR_SEQ = [
    _QUES, _DIFF, _FLAG, None,
    _ZOOM_IN, _ZOOM_OUT,
]

_NUM_DIFFS = 4   # 0=novato 1=aficionado 2=experimentado 3=personalizado




class GameScreen:
    """Pantalla principal de juego con toolbar estilo Win98."""

    _STATUS_BG  = ( 40,  40,  40)
    _STATUS_TXT = (210, 210, 210)
    _STATUS_H   = 20
    _SB_H       = 42   # altura barra de config personalizada

    def __init__(self, config: dict):
        self.esperando_decision_usuario = False
        self.inciertas_ia = []

        self.config = config
        self.rows   = config["rows"]
        self.cols   = config["cols"]
        self.mines  = config["mines"]
        self.mode   = config["name"]
        self.bombas_generadas = False
        self.ia_auto = False
        self._ultimo_mov_ia = 0

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

        self._mouse_cell  = None
        self._left_held   = False
        self._click_mode  = 'reveal'  # 'reveal' | 'flag'

        # Valores temporales de la barra de config personalizada
        self._sb_rows   = self.rows
        self._sb_cols   = self.cols
        self._sb_mines  = self.mines
        self._sb_focused = None  # indice del campo con foco (0,1,2)
        self._sb_input   = ''    # texto que se esta escribiendo

        pygame.font.init()
        self._cell_spr    = make_cell_sprites(self._cell_size)

        # Imágenes para los botones del toolbar
        _img_dir = os.path.join(os.path.dirname(__file__), '..', 'img')
        def _li(fname, size=32):
            try:
                img = pygame.image.load(os.path.join(_img_dir, fname)).convert_alpha()
                return pygame.transform.smoothscale(img, (size, size))
            except Exception:
                return None

        self._toolbar_imgs = {
            'zoom_in':      _li('mas.png'),
            'zoom_out':     _li('menos.png'),
            'diff_0':       _li('principiante.png'),
            'diff_1':       _li('avanzado.png'),
            'diff_2':       _li('experto.png'),
            'diff_3':       _li('personalizado.png'),
            'flag_btn':     _li('n.png'),
            'flag_btn_on':  _li('bandera.png'),
         
        }

        # Iconos para labels de la barra personalizada
        self._sb_bomba_img = _li('bomba.png',   size=18)
        self._sb_filas_img = _li('fila.png',    size=18)
        self._sb_cols_img  = _li('columna.png', size=18)
        self._sb_check_img = _li('check.png',   size=22)

        # Imagenes de bombas (se recargan en _zoom si cambia el tamaño)
        self._img_bomba      = self._load_cell_img('bomba.png')
        self._img_bomba_roja = self._load_cell_img('bomba-roja.png')

        # Imagenes para las caras
        self._face_img_normal  = _li('reiniciar.png',    size=FACE_SIZE)
        self._face_img_oface   = _li('sorpresa.png', size=FACE_SIZE + 1)
        self._face_img_dead    = _li('perdio.png',       size=FACE_SIZE)
        self._face_img_won     = _li('social.png',       size=FACE_SIZE)

        self._font_status = pygame.font.SysFont("Arial", 11)
        self._font_num    = pygame.font.Font(None, 14)

        self._compute_layout()

    def _load_cell_img(self, fname):
        _img_dir = os.path.join(os.path.dirname(__file__), '..', 'img')
        try:
            img = pygame.image.load(os.path.join(_img_dir, fname)).convert_alpha()
            return pygame.transform.smoothscale(img, (self._cell_size, self._cell_size))
        except Exception:
            return None

    def _make_sb_icon(self, kind, size=18):
        """Icono pixel-art para labels de la barra: 'rows' o 'cols'."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        col  = C_BLACK
        px   = 2          # tamaño de bloque
        bars = 3          # numero de barras
        gap  = 2          # separacion entre barras
        span = 5          # bloques de largo por barra
        total = bars * px + (bars - 1) * gap   # 10 px
        off  = (size - total) // 2

        if kind == 'rows':
            # Barras horizontales
            for b in range(bars):
                y0 = off + b * (px + gap)
                cx = (size - span * px) // 2
                for s in range(span):
                    pygame.draw.rect(surf, col,
                                     (cx + s * px, y0, px, px))
        else:
            # Barras verticales
            for b in range(bars):
                x0 = off + b * (px + gap)
                cy = (size - span * px) // 2
                for s in range(span):
                    pygame.draw.rect(surf, col,
                                     (x0, cy + s * px, px, px))
        return surf

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
        self._sb_rect = None   # controles ahora viven dentro del toolbar
        self._build_sb_rects(TH)
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
        bs=32; py=(TH-bs)//2; x=4; gap=4; sep=11
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

    def _build_sb_rects(self, TH):
        """Construye rects de filas/cols/minas alineados a la derecha del toolbar."""
        self._sb_fields = []
        self._sb_apply  = None
        if self._diff_idx != 3:
            return
        cy   = TH // 2
        bw, bh = 14, 11          # tamaño botones ▲▼
        vw   = 28                # ancho display valor
        ico  = 20                # ancho icono label
        gap  = 8
        fields = [
            ("Minas",    "_sb_mines", 1,        None),
            ("Columnas", "_sb_cols",  MIN_COLS, MAX_COLS),
            ("Filas",    "_sb_rows",  MIN_ROWS, MAX_ROWS),
        ]
        # Construir de derecha a izquierda
        x = self._win_w - 8
        for label, attr, lo, hi in fields:
            r_up  = pygame.Rect(x - bw,      cy - bh, bw, bh)
            r_dn  = pygame.Rect(x - bw,      cy,      bw, bh)
            r_val = pygame.Rect(x - bw - vw - 2, cy - bh, vw, bh * 2)
            r_ico = pygame.Rect(r_val.x - ico - 2, cy - ico // 2, ico, ico)
            self._sb_fields.insert(0, (label, attr, lo, hi, r_up, r_dn, r_val, r_ico))
            x = r_ico.x - gap

    def _make_board(self):
        preset = _PRESET_MAPS.get(self.mode)
        if preset is not None and len(preset) == self.rows and len(preset[0]) == self.cols:
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
        # No se puede reducir por debajo del tamaño inicial
        min_size = CELL_SIZE
        new = max(min_size, min(34, self._cell_size + delta))
        if new != self._cell_size:
            self._cell_size = new
            self._cell_spr       = make_cell_sprites(self._cell_size)
            self._img_bomba      = self._load_cell_img('bomba.png')
            self._img_bomba_roja = self._load_cell_img('bomba-roja.png')
            self._compute_layout()
            return True
        return False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # Escritura en campo de la barra personalizada
            if self._sb_focused is not None:
                if event.key == pygame.K_RETURN:
                    label, attr, lo, hi, r_up, r_dn, r_val, r_ico = self._sb_fields[self._sb_focused]
                    hi_val = hi if hi is not None else max(1, self._sb_rows * self._sb_cols - 9)
                    try:
                        val = max(lo, min(hi_val, int(self._sb_input)))
                        setattr(self, attr, val)
                    except ValueError:
                        pass
                    self._sb_focused = None
                    self._sb_input   = ""
                    return self._apply_sb()
                elif event.key == pygame.K_ESCAPE:
                    self._sb_focused = None
                    self._sb_input   = ""
                elif event.key == pygame.K_BACKSPACE:
                    self._sb_input = self._sb_input[:-1]
                elif event.unicode.isdigit():
                    self._sb_input += event.unicode
                return None
            if event.key in (pygame.K_ESCAPE, pygame.K_r):
                self.reset()
            if event.key == pygame.K_i:
                self.jugar_turno_ia()
            if event.key == pygame.K_a:
                 self.ia_auto = not self.ia_auto
                 print("[IA] Auto:", self.ia_auto)
             #Cuando la IA no sabe que hacer
            if self.esperando_decision_usuario:

                if event.key == pygame.K_y:
                        ia_movimiento_random(
                            self._board,
                            self.inciertas_ia,
                            self.rows,
                            self.cols
                        )
                        self.esperando_decision_usuario = False
                        
                elif event.key == pygame.K_n:
                    print("[IA] Control entregado al usuario.")
                    self.esperando_decision_usuario = False

           


        if event.type == pygame.MOUSEMOTION:
            self._mouse_cell = self._pixel_to_cell(*event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            # Clicks en la barra de config personalizada
            if self._sb_fields and self._toolbar_rect.collidepoint(pos):
                for i, (label, attr, lo, hi, r_up, r_dn, r_val, r_ico) in enumerate(self._sb_fields):
                    hi_val = hi if hi is not None else max(1, self._sb_rows * self._sb_cols - 9)
                    if r_val.collidepoint(pos):
                        self._sb_focused = i
                        self._sb_input   = str(getattr(self, attr))
                        return None
                    if r_up.collidepoint(pos):
                        self._sb_focused = None
                        setattr(self, attr, min(hi_val, getattr(self, attr) + 1))
                        return self._apply_sb()
                    if r_dn.collidepoint(pos):
                        self._sb_focused = None
                        setattr(self, attr, max(lo, getattr(self, attr) - 1))
                        return self._apply_sb()
            for btn_r, btn_id in zip(self._toolbar_btn_rects, self._toolbar_btn_ids):
                if not btn_r.collidepoint(pos):
                    continue
                if btn_id == _ZOOM_IN:
                    if self._zoom(+2): return ("resize", None)
                elif btn_id == _ZOOM_OUT:
                    if self._zoom(-2): return ("resize", None)
                elif btn_id == _FLAG:
                    self._click_mode = 'flag' if self._click_mode == 'reveal' else 'reveal'
                    return None
                elif btn_id == _DIFF:
                    new_idx = (self._diff_idx + 1) % _NUM_DIFFS
                    self._diff_idx = new_idx
                    if new_idx < 3:
                        return ("start_game", dict(DIFFICULTIES[DIFF_ORDER[new_idx]]))
                    else:
                        # Mostrar barra embebida sin abrir ventana externa
                        self._compute_layout()
                        return ("resize", None)
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
                    if self._click_mode == 'flag':
                        # Modo bandera: clic izq coloca/quita bandera
                        c["state"] = FLAGGED
                        self.flags_placed += 1
                    elif c["value"] == MINE:
                        # Pisó una mina → game over
                        self.game_over  = True
                        self.game_active = False
                        self.face_state = FACE_DEAD
                        self._reveal_all_mines(row, col)
                    else:
                        revelar_celdas_vacias(
                            self._board,
                            row,
                            col,
                            self.rows,
                            self.cols
                        )
                        if self._check_win():
                            self.game_won    = True
                            self.game_active = False
                            self.face_state  = FACE_WON
                elif c["state"] == FLAGGED and self._click_mode == 'flag':
                    # Segunda vez: quita la bandera
                    c["state"] = UNREVEALED
                    self.flags_placed -= 1

        return None

    def _reveal_all_mines(self, hit_row, hit_col):
        """Revela todas las minas al perder."""
        for r in range(self.rows):
            for col in range(self.cols):
                cell = self._board[r][col]
                if cell["value"] == MINE and cell["state"] != FLAGGED:
                    cell["state"] = REVEALED
                    cell["hit"]   = (r == hit_row and col == hit_col)

    def update(self):
        if self.game_active and not self.game_over and not self.game_won:
            if self._start_time is not None:
                self._elapsed = min(999, int(time.time() - self._start_time))
        if self.ia_auto and not self.game_over and not self.game_won:
            ahora = time.time()

            if ahora - self._ultimo_mov_ia >= 0.5:
                self.jugar_turno_ia()
                self._ultimo_mov_ia = ahora


    def get_size(self):
        return (self._win_w, self._win_h)

    def draw(self, screen):
        screen.fill(C_BG)
        draw_raised(screen, (0, TOOLBAR_H, self._win_w,
                             self._win_h - self._STATUS_H - TOOLBAR_H),
                    w=BORDER_OUTER // 2)
        self._draw_toolbar(screen)
        self._draw_settings_bar(screen)
        pygame.draw.rect(screen, C_BG, self._header_rect)
        draw_sunken(screen, self._header_rect, w=2)
        self._draw_lcd(screen, self._lcd_mines_rect, self.mines - self.flags_placed)
        self._draw_face(screen)
        self._draw_lcd(screen, self._lcd_timer_rect, self._elapsed)
        pygame.draw.rect(screen, C_BG, self._board_rect)
        draw_sunken(screen, self._board_rect, w=BORDER_INNER // 2)
        self._draw_board(screen)
        self._draw_status(screen)

    def _draw_settings_bar(self, screen):
        pass  # controles personalizados se dibujan dentro del toolbar

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
        self._draw_sb_inline(screen)

    def _draw_sb_inline(self, screen):
        """Dibuja los controles de config personalizada dentro del toolbar."""
        if not self._sb_fields:
            return
        fn_lbl = pygame.font.SysFont("Arial", 9,  bold=True)
        fn_val = pygame.font.SysFont("Arial", 11, bold=True)
        ico_map = {"Filas":    self._sb_filas_img,
                   "Columnas": self._sb_cols_img,
                   "Minas":    self._sb_bomba_img}
        for i, (label, attr, lo, hi, r_up, r_dn, r_val, r_ico) in enumerate(self._sb_fields):
            ico = ico_map.get(label)
            if ico:
                screen.blit(ico, ico.get_rect(center=r_ico.center))
            else:
                tl = fn_lbl.render(label[:3], True, C_BLACK)
                screen.blit(tl, tl.get_rect(center=r_ico.center))
            focused = (self._sb_focused == i)
            bg_col  = C_WHITE if focused else C_REVEALED
            pygame.draw.rect(screen, bg_col, r_val)
            draw_sunken(screen, tuple(r_val), w=1)
            txt = self._sb_input if focused else str(getattr(self, attr))
            if focused: txt += "|"
            tv = fn_val.render(txt, True, C_BLACK)
            screen.blit(tv, tv.get_rect(center=r_val.center))
            for btn_r, symbol in ((r_up, chr(0x25B2)), (r_dn, chr(0x25BC))):
                draw_raised(screen, tuple(btn_r), w=1)
                ts = fn_lbl.render(symbol, True, C_BLACK)
                screen.blit(ts, ts.get_rect(center=btn_r.center))

    def _draw_icon(self, screen, btn_r, btn_id, ox):
        cx = btn_r.centerx + ox
        cy = btn_r.centery + ox

        # Clave de imagen según tipo de botón
        if btn_id == _DIFF:
            img_key = f'diff_{self._diff_idx}'
        else:
            img_key = btn_id

        # Botón de modo: alterna entre n.png y bandera.png
        if btn_id == _FLAG:
            img_key = 'flag_btn_on' if self._click_mode == 'flag' else 'flag_btn'
        
        img = self._toolbar_imgs.get(img_key)
        if img:
            screen.blit(img, img.get_rect(center=(cx, cy)))
            return

        # Fallback procedural si no hay imagen
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
        elif btn_id == _FLAG:
            self._ic_flag(screen, cx, cy)
        elif btn_id == _QUES:
            self._ic_play(screen, cx, cy)

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


    def _ic_flag(self, screen, cx, cy):
        px, py0, py1 = cx-2, cy-7, cy+7
        pygame.draw.line(screen, C_BLACK, (px, py0), (px, py1), 2)
        pygame.draw.polygon(screen, (220, 20, 20),
                             [(px, py0), (px+7, py0+3), (px, py0+6)])
        t = self._font_num.render("1", True, C_BLACK)
        screen.blit(t, (cx+4, cy))

    def _ic_play(self, screen, cx, cy):
        # Triangulo pixeleado apuntando a la derecha (estilo retro)
        px   = 2                          # tamano de cada "pixel"
        rows = [1, 2, 3, 4, 3, 2, 1]     # columnas por fila -> triangulo
        col  = (200, 30, 30)              # rojo play
        total_h = len(rows) * px
        max_w   = max(rows) * px
        ox = cx - max_w // 2
        oy = cy - total_h // 2
        for r, ncols in enumerate(rows):
            for c in range(ncols):
                pygame.draw.rect(screen, col,
                                 (ox + c*px, oy + r*px, px, px))


    def _draw_lcd(self, screen, rect, value):
        lcd = make_lcd_surface(value)
        screen.blit(lcd, (rect.x+(rect.w-lcd.get_width())//2,
                          rect.y+(rect.h-lcd.get_height())//2))

    def _draw_face(self, screen):
        pos     = pygame.mouse.get_pos()
        pressed = self._left_held and self._face_rect.collidepoint(pos)
        # Caras con imagen PNG
        face_img = None
        if self.face_state == FACE_NORMAL and self._face_img_normal:
            face_img = self._face_img_normal
        elif self.face_state == FACE_OFACE and self._face_img_oface:
            face_img = self._face_img_oface
        elif self.face_state == FACE_DEAD and self._face_img_dead:
            face_img = self._face_img_dead
        elif self.face_state == FACE_WON and self._face_img_won:
            face_img = self._face_img_won

        if face_img:
            if pressed:
                draw_sunken(screen, tuple(self._face_rect), w=2)
            else:
                draw_raised(screen, tuple(self._face_rect), w=2)
            off = 1 if pressed else 0
            screen.blit(face_img,
                        (self._face_rect.x + off, self._face_rect.y + off))


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
            if cell["hit"]:
                if self._img_bomba_roja:
                    return self._img_bomba_roja
                return self._cell_spr["mine_hit"]
            if v == MINE:
                if self._img_bomba:
                    return self._img_bomba
                return self._cell_spr["mine"]
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



    def jugar_turno_ia(self):
        ia = LogicIA(self._board, self.rows, self.cols)

        # Si es el primer movimiento, la IA hace click aleatorio
        if not self.game_active:
            row, col = ia.primer_movimiento()

            self.game_active = True
            self._start_time = time.time()

            if not self.bombas_generadas:
                generador = Bombas(self.rows, self.cols, self.mines)
                ubicaciones = generador.generar_bombas((row, col))
                LugaresBomba.colocar_numeros(self._board, ubicaciones)
                self.bombas_generadas = True

            revelar_celdas_vacias(
                self._board,
                row,
                col,
                self.rows,
                self.cols
            )

            return

        resultado = ia.analizar()

        # Primero marca minas seguras
        for row, col in resultado["minas"]:
            celda = self._board[row][col]

            if celda["state"] == UNREVEALED:
                celda["state"] = FLAGGED
                self.flags_placed += 1

        # Luego revela celdas seguras
        for row, col in resultado["seguras"]:
            celda = self._board[row][col]

            if celda["state"] == UNREVEALED:
                revelar_celdas_vacias(
                    self._board,
                    row,
                    col,
                    self.rows,
                    self.cols
                )

        # Verificar victoria
        if self._check_win():
            self.game_won    = True
            self.game_active = False
            self.face_state  = FACE_WON
            return

        # Si no pudo hacer nada logico, danis ka decision
        if not resultado["minas"] and not resultado["seguras"]:
            print("[IA] No hay movimientos logicos disponibles")
            # Obtener celdas inciertas para movimiento aleatorio
            self.inciertas_ia = [
                (r, c)
                for r in range(self.rows)
                for c in range(self.cols)
                if self._board[r][c]["state"] == UNREVEALED
            ]
            self.esperando_decision_usuario = True

    def _apply_sb(self):
        """Aplica la config personalizada inmediatamente."""
        cfg = {
            "name":  "Personalizado",
            "rows":  self._sb_rows,
            "cols":  self._sb_cols,
            "mines": min(self._sb_mines,
                         self._sb_rows * self._sb_cols - 9),
        }
        return ("start_game", cfg)

    def _check_win(self):
        """Verifica si el jugador ha ganado."""
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self._board[r][c]
                if cell["value"] != MINE and cell["state"] != REVEALED:
                    return False
        return True

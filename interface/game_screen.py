import os
import math
import pygame

from interface.constants import *
from interface.sprites import draw_raised, draw_sunken, make_cell_sprites, make_lcd_surface
from knowledge.game_logic import GameLogic

_ZOOM_IN  = "zoom_in"
_ZOOM_OUT = "zoom_out"
_DIFF     = "difficulty"
_FLAG     = "flag_btn"
_QUES     = "question_btn"

_TOOLBAR_SEQ = [_QUES, _DIFF, _FLAG, None, _ZOOM_IN, _ZOOM_OUT]
_NUM_DIFFS   = 4   # 0=novato 1=aficionado 2=experimentado 3=personalizado

_DIFF_IDX = {DIFFICULTIES[k]["name"]: i for i, k in enumerate(DIFF_ORDER)}

class GameScreen:
    """Pantalla de juego: solo rendering, layout y captura de eventos."""

    _STATUS_BG  = ( 40,  40,  40)
    _STATUS_TXT = (210, 210, 210)


    # ──────────────────────────────────────────────────────────────────────────
    #  Inicializacion
    # ──────────────────────────────────────────────────────────────────────────

    def __init__(self, config: dict):
        # Logica pura del juego
        self.logic = GameLogic(config)

        # Estado visual / UI
        self._diff_idx   = _DIFF_IDX.get(config["name"], 3)
        self._cell_size  = CELL_SIZE
        self._click_mode = 'reveal'   # 'reveal' | 'flag'
        self._mouse_cell = None
        self._left_held      = False
        self._ia_last_cells  = set()
        self._ia_manual_mode = False

        # Config personalizada (toolbar inline)
        self._sb_rows    = config["rows"]
        self._sb_cols    = config["cols"]
        self._sb_mines   = config["mines"]
        self._sb_focused = None
        self._sb_input   = ''

        pygame.font.init()

        _img_dir = os.path.join(os.path.dirname(__file__), '..', 'img')
        def _li(fname, size=32):
            try:
                img = pygame.image.load(os.path.join(_img_dir, fname)).convert_alpha()
                return pygame.transform.smoothscale(img, (size, size))
            except Exception:
                return None

        # Imagen de bandera para celdas (se carga una vez, sin escalar aún)
        try:
            self._flag_src = pygame.image.load(
                os.path.join(_img_dir, 'banderin.png')).convert_alpha()
        except Exception:
            self._flag_src = None

        self._cell_spr = make_cell_sprites(self._cell_size, self._flag_src)

        self._toolbar_imgs = {
            'zoom_in':     _li('mas.png'),
            'zoom_out':    _li('menos.png'),
            'diff_0':      _li('principiante.png'),
            'diff_1':      _li('avanzado.png'),
            'diff_2':      _li('experto.png'),
            'diff_3':      _li('personalizado.png'),
            'flag_btn':    _li('n.png'),
            'flag_btn_on': _li('bandera.png'),
        }

        self._sb_bomba_img = _li('bomba.png',   size=30)
        self._sb_bomba_img2 = _li('bomba2.png',   size=30)
        self._sb_filas_img = _li('fila.png',    size=30)
        self._sb_cols_img  = _li('columna.png', size=30)

        self._img_bomba      = self._load_cell_img('bomba.png')
        self._img_bomba_roja = self._load_cell_img('bomba-roja.png')

        self._face_img_normal = _li('reiniciar.png', size=FACE_SIZE)
        self._face_img_oface  = _li('sorpresa.png',  size=FACE_SIZE + 1)
        self._face_img_dead   = _li('perdio.png',    size=FACE_SIZE)
        self._face_img_won    = _li('social.png',    size=FACE_SIZE)

        self._font_status = pygame.font.SysFont("Arial", 11)
        self._font_num    = pygame.font.Font(None, 14)

        # ── Drawer de estadísticas ──────────────────────────────────────────
        self._drawer_open    = False   # abierto / cerrado
        self._DRAWER_W       = 190    # ancho maximo del panel
        self._drawer_visible = 0      # px visibles ahora (0=cerrado, DRAWER_W=abierto)
        self._DRAWER_SPEED   = 18     # px por frame

        self._compute_layout()

    def _load_cell_img(self, fname):
        _img_dir = os.path.join(os.path.dirname(__file__), '..', 'img')
        try:
            img = pygame.image.load(os.path.join(_img_dir, fname)).convert_alpha()
            return pygame.transform.smoothscale(img, (self._cell_size, self._cell_size))
        except Exception:
            return None

    # ──────────────────────────────────────────────────────────────────────────
    #  Layout
    # ──────────────────────────────────────────────────────────────────────────

    _SB_ROW_H = 52   # altura de la segunda fila cuando no caben inline

    def _compute_layout(self):
        lg = self.logic
        BO, BI, CS, TH = BORDER_OUTER, BORDER_INNER, self._cell_size, TOOLBAR_H
        bpw = lg.cols * CS
        bph = lg.rows * CS
        self._win_w = BO + BI + bpw + BI + BO

        # Construir toolbar y decidir si los controles de personalizado
        # caben inline o necesitan una segunda fila
        self._build_toolbar_rects(TH)
        self._build_sb_rects(TH)

        sb_extra = self._SB_ROW_H if self._sb_second_row else 0
        top_h    = TH + sb_extra   # altura total de la zona superior

        self._win_h      = top_h + BO + HEADER_H + BI + bph + BI + BO 
        self._toolbar_rect = pygame.Rect(0, 0, self._win_w, top_h)

        self._header_rect = pygame.Rect(BO, top_h + BO, self._win_w - 2*BO, HEADER_H)
        self._board_rect  = pygame.Rect(BO, top_h + BO + HEADER_H + BI,
                                        self._win_w - 2*BO, bph + 2*BI)
        self._grid_x = BO + BI
        self._grid_y = top_h + BO + HEADER_H + BI + BI
        hx  = self._header_rect.x + 2
        hw  = self._header_rect.w - 4
        hcy = self._header_rect.centery
        lcd_w = LCD_DIGITS*LCD_DIGIT_W + (LCD_DIGITS-1)*LCD_GAP + 2*LCD_PAD
        lcd_h = LCD_DIGIT_H + 2*LCD_PAD
        PAD   = 4
        self._lcd_mines_rect = pygame.Rect(hx + PAD, hcy - lcd_h//2, lcd_w, lcd_h)
        self._lcd_timer_rect = pygame.Rect(hx + hw - PAD - lcd_w, hcy - lcd_h//2, lcd_w, lcd_h)
        self._face_rect = pygame.Rect(self._header_rect.centerx - FACE_SIZE//2,
                                      hcy - FACE_SIZE//2, FACE_SIZE, FACE_SIZE)
        self._status_rect = pygame.Rect(0, self._win_h - 0,
                                        self._win_w, 0)
        self._build_ia_dialog_rects()

        # Botón de toggle del drawer (pestaña lateral derecha del drawer)
        self._drawer_tab_rect = pygame.Rect(
            0, self._win_h // 2 - 36, 16, 72
        )

    def _build_ia_dialog_rects(self):
        dw, dh = 270, 130
        dx = (self._win_w - dw) // 2
        dy = (self._win_h - dh) // 2
        self._ia_dialog_rect = pygame.Rect(dx, dy, dw, dh)
        bw, bh = 112, 26
        gap = 10
        bx = dx + (dw - bw * 2 - gap) // 2
        by = dy + dh - bh - 12
        self._ia_btn_aleatorio = pygame.Rect(bx,            by, bw, bh)
        self._ia_btn_manual    = pygame.Rect(bx + bw + gap, by, bw, bh)

    def _build_toolbar_rects(self, TH):
        bs = 32; py = (TH - bs) // 2; x = 4; gap = 4; sep = 11
        self._toolbar_btn_rects  = []
        self._toolbar_btn_ids    = []
        self._toolbar_separators = []
        for item in _TOOLBAR_SEQ:
            if item is None:
                self._toolbar_separators.append(x + 1)
                x += sep
            else:
                self._toolbar_btn_rects.append(pygame.Rect(x, py, bs, bs))
                self._toolbar_btn_ids.append(item)
                x += bs + gap

    def _build_sb_rects(self, TH):
        """
        Controles de config personalizada.
        Si caben en la misma fila que los botones → inline (derecha del toolbar).
        Si no caben → segunda fila debajo del toolbar, pegados a la izquierda.
        """
        self._sb_fields      = []
        self._sb_second_row  = False
        if self._diff_idx != 3:
            return

        bw, bh = 18, 14
        vw   = 36
        ico  = 32
        gap  = 8
        fields_ltr = [
            ("Filas",    "_sb_rows",  MIN_ROWS, MAX_ROWS),
            ("Columnas", "_sb_cols",  MIN_COLS, MAX_COLS),
            ("Minas",    "_sb_mines", None,     None),   # ← lo=None, hi=None; _mines_limits() los resuelve
        ]

        field_unit = ico + 2 + vw + 2 + bw + gap
        sb_width   = field_unit * 3 - gap

        toolbar_right = (self._toolbar_btn_rects[-1].right
                        if self._toolbar_btn_rects else 0)

        self._sb_second_row = (toolbar_right + 10 + sb_width > self._win_w)

        if self._sb_second_row:
            cy = TH + self._SB_ROW_H // 2
            x  = 8
            for label, attr, lo, hi in fields_ltr:
                r_ico = pygame.Rect(x,               cy - ico//2, ico, ico)
                r_val = pygame.Rect(r_ico.right + 2, cy - bh,     vw,  bh * 2)
                r_up  = pygame.Rect(r_val.right + 2, cy - bh,     bw,  bh)
                r_dn  = pygame.Rect(r_val.right + 2, cy,          bw,  bh)
                self._sb_fields.append((label, attr, lo, hi, r_up, r_dn, r_val, r_ico))
                x = r_up.right + gap
        else:
            cy = TH // 2
            x  = self._win_w - 8
            for label, attr, lo, hi in reversed(fields_ltr):
                r_up  = pygame.Rect(x - bw,            cy - bh,     bw, bh)
                r_dn  = pygame.Rect(x - bw,            cy,          bw, bh)
                r_val = pygame.Rect(x - bw - vw - 2,   cy - bh,     vw, bh * 2)
                r_ico = pygame.Rect(r_val.x - ico - 2, cy - ico//2, ico, ico)
                self._sb_fields.insert(0, (label, attr, lo, hi, r_up, r_dn, r_val, r_ico))
                x = r_ico.x - gap

    def get_size(self):
        current_w = self._win_w + int(self._drawer_visible)
        return (current_w, self._win_h)

    # ──────────────────────────────────────────────────────────────────────────
    #  Helpers UI
    # ──────────────────────────────────────────────────────────────────────────

    def _pixel_to_cell(self, px, py):
        cs  = self._cell_size
        col = (px - self._grid_x) // cs
        row = (py - self._grid_y) // cs
        lg  = self.logic
        if (0 <= row < lg.rows and 0 <= col < lg.cols
                and self._grid_x <= px < self._grid_x + lg.cols * cs
                and self._grid_y <= py < self._grid_y + lg.rows * cs):
            return (row, col)
        return None

    def _cell_rect(self, row, col):
        cs = self._cell_size
        return pygame.Rect(self._grid_x + col*cs, self._grid_y + row*cs, cs, cs)

    def _zoom(self, delta):
        new = max(CELL_SIZE, min(34, self._cell_size + delta))
        if new != self._cell_size:
            self._cell_size      = new
            self._cell_spr       = make_cell_sprites(new, self._flag_src)
            self._img_bomba      = self._load_cell_img('bomba.png')
            self._img_bomba_roja = self._load_cell_img('bomba-roja.png')
            self._compute_layout()
            return True
        return False

    def _apply_sb(self):
        mn, mx = self._mines_limits()
        self._sb_mines = max(mn, min(mx, self._sb_mines))  # clampear antes de aplicar
        cfg = {
            "name":  "Personalizado",
            "rows":  self._sb_rows,
            "cols":  self._sb_cols,
            "mines": self._sb_mines,
        }
        return ("start_game", cfg)
    
    def _mines_limits(self):
        total  = self._sb_rows * self._sb_cols
        minimo = max(1, round(total * 0.10))
        maximo = min(round(total * 0.80), total - 9)
        return minimo, maximo

    def _reset_ui(self):
        self._left_held      = False
        self._mouse_cell     = None
        self._ia_last_cells  = set()
        self._ia_manual_mode = False

    # ──────────────────────────────────────────────────────────────────────────
    #  Eventos
    # ──────────────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        lg = self.logic

        # Dialogo IA: solo responder a los botones del popup
        if lg.esperando_decision_usuario:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if self._ia_btn_aleatorio.collidepoint(pos):
                    self._ia_last_cells = lg.ia_movimiento_aleatorio()
                elif self._ia_btn_manual.collidepoint(pos):
                    lg.esperando_decision_usuario = False
                    self._ia_manual_mode = True
                    lg.ia_auto = False
            return None



        # ── Teclado ──────────────────────────────────────────────────────────
        if event.type == pygame.KEYDOWN:

            # Escritura en campo de config personalizada
            if self._sb_focused is not None:
                if event.key == pygame.K_RETURN:
                    label, attr, lo, hi, *_ = self._sb_fields[self._sb_focused]
                    hi_val = hi if hi is not None else max(1, self._sb_rows * self._sb_cols - 9)
                    try:
                        mn, mx = self._mines_limits()
                        lo_val = mn if label == "Minas" else lo
                        hi_val = mx if label == "Minas" else hi
                        setattr(self, attr, max(lo_val, min(hi_val, int(self._sb_input))))
                    except ValueError:
                        pass
                    self._sb_focused = None
                    self._sb_input   = ''
                    return self._apply_sb()
                elif event.key == pygame.K_ESCAPE:
                    self._sb_focused = None
                    self._sb_input   = ''
                elif event.key == pygame.K_BACKSPACE:
                    self._sb_input = self._sb_input[:-1]
                elif event.unicode.isdigit():
                    self._sb_input += event.unicode
                return None

            if event.key in (pygame.K_ESCAPE, pygame.K_r):
                lg.reset()
                self._reset_ui()

            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                lg.ia_auto = not lg.ia_auto
                print("[IA] Auto:", lg.ia_auto)

        # ── Movimiento raton ──────────────────────────────────────────────────
        if event.type == pygame.MOUSEMOTION:
            self._mouse_cell = self._pixel_to_cell(*event.pos)

        # ── Clic izquierdo DOWN ───────────────────────────────────────────────
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            # Pestaña del drawer de estadísticas
            TAB_W   = 16
            TAB_H   = 72
            tab_x   = self._win_w - TAB_W # pestaña pegada al borde del drawer
            tab_y   = self._win_h // 2 - TAB_H // 2
            tab_hit = pygame.Rect(tab_x, tab_y, TAB_W, TAB_H).collidepoint(pos)
            if tab_hit:
                self._drawer_open = not self._drawer_open
                return None

            # Campos de config personalizada en el toolbar
            if self._sb_fields and self._toolbar_rect.collidepoint(pos):
                for i, (label, attr, lo, hi, r_up, r_dn, r_val, r_ico) in enumerate(self._sb_fields):
                    hi_val = hi if hi is not None else max(1, self._sb_rows * self._sb_cols - 9)
                    if r_val.collidepoint(pos):
                        self._sb_focused = i
                        self._sb_input   = str(getattr(self, attr))
                        return None
                    if r_up.collidepoint(pos):
                        self._sb_focused = None
                        mn, mx = self._mines_limits()
                        lo_val = mn if label == "Minas" else lo
                        hi_val = mx if label == "Minas" else hi
                        setattr(self, attr, min(hi_val, getattr(self, attr) + 1))
                        return self._apply_sb()
                    if r_dn.collidepoint(pos):
                        self._sb_focused = None
                        mn, mx = self._mines_limits()
                        lo_val = mn if label == "Minas" else lo
                        hi_val = mx if label == "Minas" else hi
                        setattr(self, attr, max(lo_val, getattr(self, attr) - 1))
                        return self._apply_sb()

            # Botones del toolbar
            for btn_r, btn_id in zip(self._toolbar_btn_rects, self._toolbar_btn_ids):
                if not btn_r.collidepoint(pos):
                    continue
                if btn_id == _ZOOM_IN:
                    if self._zoom(+2): return ("resize", None)
                elif btn_id == _ZOOM_OUT:
                    if self._zoom(-2): return ("resize", None)
                elif btn_id == _FLAG:
                    self._click_mode = 'flag' if self._click_mode == 'reveal' else 'reveal'
                elif btn_id == _DIFF:
                    new_idx = (self._diff_idx + 1) % _NUM_DIFFS
                    self._diff_idx = new_idx
                    if new_idx < 3:
                        return ("start_game", dict(DIFFICULTIES[DIFF_ORDER[new_idx]]))
                    else:
                        # Precalcular minas máximas al entrar a personalizado
                        _, mx = self._mines_limits()
                        self._sb_mines = mx          
                        self._compute_layout()
                        return ("resize", None)
                elif btn_id == _QUES:
                    lg.ia_auto = not lg.ia_auto
                    print("[IA] Auto:", lg.ia_auto)
                return None

            # Carita -> reiniciar
            if self._face_rect.collidepoint(pos):
                lg.reset()
                self._reset_ui()
                return None

            # Celda del tablero
            cell = self._pixel_to_cell(*pos)
            if cell is None or lg.game_over or lg.game_won:
                return None
            self._left_held = True
            lg.press_cell(*cell)

        # ── Clic derecho DOWN -> ciclar marca ─────────────────────────────────
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            cell = self._pixel_to_cell(*event.pos)
            if cell:
                lg.cycle_mark(*cell)

        # ── Clic izquierdo UP -> accion principal ─────────────────────────────
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_held = self._left_held   # True solo si DOWN fue sobre el tablero
            self._left_held = False
            lg.release_cell()
            cell = self._pixel_to_cell(*event.pos)
            if cell and not lg.game_over and not lg.game_won:
                if self._ia_manual_mode and was_held:
                    # El usuario elige una casilla; despues la IA reintenta
                    import time
                    lg.reveal_cell(*cell)
                    self._ia_manual_mode = False
                    self._ia_last_cells  = set()
                    if not lg.game_over and not lg.game_won:
                        lg.ia_auto = True
                        self._ia_last_cells = lg.jugar_turno_ia()
                        lg._ultimo_mov_ia   = time.time()
                elif not self._ia_manual_mode:
                    if self._click_mode == 'flag':
                        lg.place_flag(*cell)
                    else:
                        lg.reveal_cell(*cell)

        return None

    # ──────────────────────────────────────────────────────────────────────────
    #  Update
    # ──────────────────────────────────────────────────────────────────────────

    def update(self):
        import time

        self.logic.update()
        lg = self.logic

        # ── Animación del drawer ──────────────────────────────────────────────
        target_vis = self._DRAWER_W if self._drawer_open else 0
        if int(self._drawer_visible) != target_vis:
            step = self._DRAWER_SPEED
            if self._drawer_visible < target_vis:
                self._drawer_visible = min(self._drawer_visible + step, target_vis)
            else:
                self._drawer_visible = max(self._drawer_visible - step, target_vis)
            return ('resize', None)   # avisa al main loop para redimensionar

        # Detenemos IA mientras espera respuesta o usuario marca manual
        if lg.esperando_decision_usuario or self._ia_manual_mode:
            return

        if lg.ia_auto and not lg.game_over and not lg.game_won:

            ahora = time.time()

            if ahora - lg._ultimo_mov_ia >= 0.5:
                self._ia_last_cells = lg.jugar_turno_ia()
                lg._ultimo_mov_ia = ahora

    # ──────────────────────────────────────────────────────────────────────────
    #  Dibujo
    # ──────────────────────────────────────────────────────────────────────────

    def draw(self, screen):
        lg  = self.logic
        screen.fill(C_BG)

        # Superficie temporal para el juego (ya no aplicamos offset)
        game_surf = pygame.Surface((self._win_w, self._win_h))
        game_surf.fill(C_BG)
        top_h = self._toolbar_rect.height
        draw_raised(game_surf, (0, top_h, self._win_w,
                                self._win_h - top_h),
                    w=BORDER_OUTER // 2)
        self._draw_toolbar(game_surf)
        pygame.draw.rect(game_surf, C_BG, self._header_rect)
        draw_sunken(game_surf, self._header_rect, w=2)
        self._draw_lcd(game_surf, self._lcd_mines_rect, lg.mines - lg.flags_placed)
        self._draw_face(game_surf)
        self._draw_lcd(game_surf, self._lcd_timer_rect, lg.elapsed)
        pygame.draw.rect(game_surf, C_BG, self._board_rect)
        draw_sunken(game_surf, self._board_rect, w=BORDER_INNER // 2)
        self._draw_board(game_surf)
        if self.logic.esperando_decision_usuario:
            self._draw_ia_dialog(game_surf)
        
        # El tablero SIEMPRE se queda fijo en la esquina superior izquierda
        screen.blit(game_surf, (0, 0))
        
        # El drawer ahora se dibuja después para acoplarse a la derecha
        self._draw_stats_drawer(screen)

    def _draw_toolbar(self, screen):
        TH    = TOOLBAR_H
        top_h = self._toolbar_rect.height   # TH  ó  TH + _SB_ROW_H

        # Fondo y borde 3-D de toda la zona superior
        pygame.draw.rect(screen, C_BG, self._toolbar_rect)
        draw_raised(screen, tuple(self._toolbar_rect), w=2)

        # Separador entre fila 1 y fila 2 cuando los controles van abajo
        if self._sb_second_row:
            pygame.draw.line(screen, C_GRAY_MID, (2, TH-1), (self._win_w-3, TH-1), 1)
            pygame.draw.line(screen, C_WHITE,    (2, TH),   (self._win_w-3, TH),   1)

        # Botones de la fila 1
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

        # Controles de config personalizada (inline o segunda fila)
        self._draw_sb_inline(screen)

    def _draw_sb_inline(self, screen):
        if not self._sb_fields:
            return
        fn_lbl = pygame.font.SysFont("Arial", 9,  bold=True)
        fn_val = pygame.font.SysFont("Arial", 11, bold=True)
        ico_map = {"Filas":    self._sb_filas_img,
                   "Columnas": self._sb_cols_img,
                   "Minas":    self._sb_bomba_img2}
        for i, (label, attr, lo, hi, r_up, r_dn, r_val, r_ico) in enumerate(self._sb_fields):
            ico = ico_map.get(label)
            if ico:
                screen.blit(ico, ico.get_rect(center=r_ico.center))
            else:
                tl = fn_lbl.render(label[:3], True, C_BLACK)
                screen.blit(tl, tl.get_rect(center=r_ico.center))
            focused = (self._sb_focused == i)
            pygame.draw.rect(screen, C_WHITE if focused else C_REVEALED, r_val)
            draw_sunken(screen, tuple(r_val), w=1)
            txt = (self._sb_input + "|") if focused else str(getattr(self, attr))
            tv  = fn_val.render(txt, True, C_BLACK)
            screen.blit(tv, tv.get_rect(center=r_val.center))
            for btn_r, sym in ((r_up, chr(0x25B2)), (r_dn, chr(0x25BC))):
                draw_raised(screen, tuple(btn_r), w=1)
                ts = fn_lbl.render(sym, True, C_BLACK)
                screen.blit(ts, ts.get_rect(center=btn_r.center))

    def _draw_icon(self, screen, btn_r, btn_id, ox):
        cx, cy = btn_r.centerx + ox, btn_r.centery + ox
        if btn_id == _DIFF:
            img_key = f'diff_{self._diff_idx}'
        elif btn_id == _FLAG:
            img_key = 'flag_btn_on' if self._click_mode == 'flag' else 'flag_btn'
        else:
            img_key = btn_id
        img = self._toolbar_imgs.get(img_key)
        if img:
            screen.blit(img, img.get_rect(center=(cx, cy)))
            return
        if btn_id == _ZOOM_IN:    self._ic_magnifier(screen, cx, cy, plus=True)
        elif btn_id == _ZOOM_OUT: self._ic_magnifier(screen, cx, cy, plus=False)
        elif btn_id == _DIFF:
            idx = self._diff_idx
            if idx == 0:   self._ic_chevron(screen, cx, cy, double=False)
            elif idx == 1: self._ic_chevron(screen, cx, cy, double=True)
            elif idx == 2: self._ic_star(screen, cx, cy)
            else:          self._ic_gear(screen, cx, cy)
        elif btn_id == _FLAG: self._ic_flag(screen, cx, cy)
        elif btn_id == _QUES: self._ic_play(screen, cx, cy)

    def _ic_magnifier(self, screen, cx, cy, plus=True):
        lx, ly = cx-2, cy-2
        pygame.draw.circle(screen, C_BLACK, (lx, ly), 6, 2)
        dx = int(6*0.65)
        pygame.draw.line(screen, C_BLACK, (lx+dx, ly+dx), (lx+dx+5, ly+dx+5), 2)
        pygame.draw.line(screen, C_BLACK, (lx-3, ly), (lx+3, ly), 2)
        if plus:
            pygame.draw.line(screen, C_BLACK, (lx, ly-3), (lx, ly+3), 2)

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
        n  = 8; r_body = 8; r_tip = 11; r_hub = 3
        t_angle = math.pi / n * 0.55
        pygame.draw.circle(screen, gc, (cx, cy), r_body)
        for i in range(n):
            base = 2*math.pi*i/n
            pts  = [
                (cx + r_body*math.cos(base - t_angle*1.2),
                 cy + r_body*math.sin(base - t_angle*1.2)),
                (cx + r_tip *math.cos(base - t_angle),
                 cy + r_tip *math.sin(base - t_angle)),
                (cx + r_tip *math.cos(base + t_angle),
                 cy + r_tip *math.sin(base + t_angle)),
                (cx + r_body*math.cos(base + t_angle*1.2),
                 cy + r_body*math.sin(base + t_angle*1.2)),
            ]
            pygame.draw.polygon(screen, gc, [(int(p[0]), int(p[1])) for p in pts])
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
        px = 2
        rows = [1, 2, 3, 4, 3, 2, 1]
        col  = (200, 30, 30)
        ox = cx - max(rows)*px // 2
        oy = cy - len(rows)*px // 2
        for r, ncols in enumerate(rows):
            for c in range(ncols):
                pygame.draw.rect(screen, col, (ox + c*px, oy + r*px, px, px))

    def _draw_lcd(self, screen, rect, value):
        lcd = make_lcd_surface(value)
        screen.blit(lcd, (rect.x + (rect.w - lcd.get_width())  // 2,
                          rect.y + (rect.h - lcd.get_height()) // 2))

    def _draw_face(self, screen):
        pos     = pygame.mouse.get_pos()
        pressed = self._left_held and self._face_rect.collidepoint(pos)
        face_imgs = {
            FACE_NORMAL: self._face_img_normal,
            FACE_OFACE:  self._face_img_oface,
            FACE_DEAD:   self._face_img_dead,
            FACE_WON:    self._face_img_won,
        }
        face_img = face_imgs.get(self.logic.face_state)
        if face_img:
            if pressed: draw_sunken(screen, tuple(self._face_rect), w=2)
            else:       draw_raised(screen, tuple(self._face_rect), w=2)
            off = 1 if pressed else 0
            screen.blit(face_img, (self._face_rect.x + off, self._face_rect.y + off))

    def _draw_board(self, screen):
        hover = self._mouse_cell
        lg    = self.logic
        for r in range(lg.rows):
            for c in range(lg.cols):
                spr  = self._sprite_for(lg.board[r][c], r, c, hover)
                dest = self._cell_rect(r, c)
                screen.blit(spr, dest.topleft)
                if (r, c) in self._ia_last_cells:
                    tint = pygame.Surface((dest.w, dest.h), pygame.SRCALPHA)
                    tint.fill((0, 0, 80, 70))
                    screen.blit(tint, dest.topleft)

    def _sprite_for(self, cell, row, col, hover):
        lg   = self.logic
        s, v = cell["state"], cell["value"]
        if s == FLAGGED:  return self._cell_spr["flag"]
        if s == QUESTION: return self._cell_spr["question"]
        if s == REVEALED:
            if cell["hit"]:
                return self._img_bomba_roja or self._cell_spr.get("mine_hit",
                                                                    self._cell_spr["revealed"])
            if v == MINE:
                return self._img_bomba or self._cell_spr.get("mine",
                                                              self._cell_spr["revealed"])
            if v == 0: return self._cell_spr["revealed"]
            return self._cell_spr[str(v)]
        if self._left_held and hover == (row, col) and not lg.game_over and not lg.game_won:
            return self._cell_spr["revealed"]
        return self._cell_spr["unrevealed"]

    def _draw_ia_dialog(self, screen):
        """Dialogo estilo Windows 98 cuando la IA no tiene movimientos logicos."""
        dr  = self._ia_dialog_rect
        fn_title = pygame.font.SysFont("Arial", 11, bold=True)
        fn_body  = pygame.font.SysFont("Arial", 11)
        fn_btn   = pygame.font.SysFont("Arial", 11)

        # Sombra
        sombra = pygame.Rect(dr.x + 4, dr.y + 4, dr.w, dr.h)
        pygame.draw.rect(screen, (80, 80, 80), sombra)

        # Fondo del dialogo
        pygame.draw.rect(screen, C_BG, dr)
        draw_raised(screen, tuple(dr), w=2)

        # Barra de titulo (azul Windows 98)
        title_h = 20
        title_r = pygame.Rect(dr.x + 2, dr.y + 2, dr.w - 4, title_h)
        pygame.draw.rect(screen, (0, 0, 128), title_r)
        t = fn_title.render("[IA]  Decisión requerida", True, C_WHITE)
        screen.blit(t, (title_r.x + 4, title_r.y + (title_h - t.get_height()) // 2))

        # Mensaje
        msg1 = fn_body.render("No hay movimientos lógicos disponibles.", True, C_BLACK)
        msg2 = fn_body.render("¿Qué deseas hacer?", True, C_BLACK)
        cx   = dr.centerx
        y0   = dr.y + title_h + 14
        screen.blit(msg1, msg1.get_rect(centerx=cx, top=y0))
        screen.blit(msg2, msg2.get_rect(centerx=cx, top=y0 + msg1.get_height() + 4))

        # Botones
        mpos = pygame.mouse.get_pos()
        for btn_r, label in (
            (self._ia_btn_aleatorio, "Mov. aleatorio"),
            (self._ia_btn_manual,    "Marcar casilla"),
        ):
            hover = btn_r.collidepoint(mpos)
            if hover: draw_sunken(screen, tuple(btn_r), w=2)
            else:     draw_raised(screen, tuple(btn_r), w=2)
            pygame.draw.rect(screen, C_BG, btn_r.inflate(-4, -4))
            tb = fn_btn.render(label, True, C_BLACK)
            screen.blit(tb, tb.get_rect(center=btn_r.center))

    def _draw_stats_drawer(self, screen):

        DW    = self._DRAWER_W
        DH    = self._win_h
        vis   = int(self._drawer_visible)   # px visibles ahora
        if vis <= 0:
            # Solo dibujar la pestaña cuando está completamente cerrado
            pass
        stats = self.logic.stats
        lg    = self.logic

        # ── Colores del drawer ────────────────────────────────────────────────
       
        _TEXT      = (34, 39, 49)
        _MUTED     = (86, 94, 110)
        _CARD      = (245, 247, 250)
        _CARD_ALT  = (235, 239, 245)
        _GREEN     = (46, 160, 90)
        _RED       = (220, 75, 75)
        _YELLOW    = (210, 150, 35)


        fn_title  = pygame.font.SysFont("Arial", 12, bold=True)
        fn_label  = pygame.font.SysFont("Arial", 11,bold=True)
        fn_value  = pygame.font.SysFont("Arial", 13, bold=True)
        fn_small  = pygame.font.SysFont("Arial",  12, bold=True)

        # ── Panel principal ───────────────────────────────────────────────────
        panel = pygame.Surface((DW, DH), pygame.SRCALPHA)
        panel.fill(C_BG)
        
        # Cabecera
        pygame.draw.rect(panel, _CARD, (8, 8, DW - 16, 28), border_radius=7)
        t = fn_title.render("ESTADÍSTICAS", True, _TEXT)
        panel.blit(t, (14, 8 + (28 - t.get_height()) // 2))
        y = 42

        def _section(title):
            nonlocal y
            y += 6
            t = fn_small.render(title.upper(), True, _MUTED)
            panel.blit(t, (12, y))
            y += t.get_height() + 6

        def _stat_row(label, value, color=None):
            nonlocal y
            col = color if color else _TEXT
            row_h = 24

            pygame.draw.rect(
                panel,
                _CARD,
                (8, y, DW - 16, row_h),
                border_radius=6
            )

            tl = fn_label.render(label, True, _MUTED)
            tv = fn_value.render(str(value), True, col)

            panel.blit(tl, (14, y + (row_h - tl.get_height()) // 2))
            panel.blit(tv, (DW - tv.get_width() - 14, y + (row_h - tv.get_height()) // 2))

            y += row_h + 5

        def _bar(value, maximum, color):
            nonlocal y
            bw = DW - 24
            bh = 7

            pygame.draw.rect(panel, _CARD_ALT, (12, y, bw, bh), border_radius=4)

            fill = int(bw * min(value, maximum) / max(maximum, 1))
            if fill > 0:
                pygame.draw.rect(panel, color, (12, y, fill, bh), border_radius=4)

            y += bh + 8

        # ── Sección: Partida actual ───────────────────────────────────────────
        _section("Partida actual")

        _stat_row("Banderas", lg.flags_placed,
                  _YELLOW if lg.flags_placed > 0 else _TEXT)

        stats.registrar_minas_correctas(lg.board)
        _stat_row("Minas correctas", stats.minas_marcadas_correctas, _GREEN)
        _stat_row("Restantes", lg.mines - lg.flags_placed, C_BLACK)
        
        revealed = sum(
            1 for fila in lg.board
            for c in fila if c["state"] == REVEALED and c["value"] != MINE
        )
        total_safe = lg.rows * lg.cols - lg.mines
        _stat_row("Celdas reveladas", f"{revealed}/{total_safe}",
                  _GREEN if lg.game_won else _TEXT)
        _bar(revealed, total_safe, _GREEN)
        

        y += 4
        # ── Sección: IA ───────────────────────────────────────────────────────
        _section("Agente")
        _stat_row("Turnos analizados", stats.turnos_ia)
        _stat_row("Seguras inferidas", stats.seguras_identificadas, _GREEN)

        avg_inc = (stats.inciertas_acumuladas // max(stats.turnos_ia, 1))
        _stat_row("Inciertas (promedio)", avg_inc,
                  _RED if avg_inc > 5 else _YELLOW if avg_inc > 0 else _GREEN)

        _stat_row("Mov. aleatorios", stats.movimientos_aleatorios,
                  _RED if stats.movimientos_aleatorios > 0 else _GREEN)

        y += 4


        if vis > 0:
            clip_rect = pygame.Rect(0, 0, vis, DH)
            screen.blit(panel, (self._win_w, 0), clip_rect)

        # ── Pestaña de toggle ─────────────────────────────────────────────────
        TAB_W = 16
        TAB_H = 72
        tab_x = self._win_w - TAB_W   # Siempre fijada al borde derecho del tablero principal
        tab_y = DH // 2 - TAB_H // 2

        tab_surf = pygame.Surface((TAB_W, TAB_H), pygame.SRCALPHA)
        tab_surf.fill(C_GRAY_MID)

        # Flecha indicadora (chevron)
        arrow_pts = []
        if self._drawer_open:
            # apunta a la izquierda (← cerrar panel derecho)
            ax, ay = TAB_W // 2 + 2, TAB_H // 2
            arrow_pts = [
                (ax - 3, ay),
                (ax + 2, ay - 5),
                (ax + 2, ay + 5),
            ]
        else:
            # apunta a la derecha (→ abrir hacia afuera)
            ax, ay = TAB_W // 2 - 2, TAB_H // 2
            arrow_pts = [
                (ax + 3, ay),
                (ax - 2, ay - 5),
                (ax - 2, ay + 5),
            ]
        pygame.draw.polygon(tab_surf, C_BLACK, arrow_pts)
        
        # Dibujar borde de la pestaña
        pygame.draw.rect(tab_surf, C_BLACK, (0, 0, TAB_W, TAB_H), 1)

        screen.blit(tab_surf, (tab_x, tab_y))

"""
Buscaminas – Fábrica de Sprites
IC6200-PY-260604_2

Todos los gráficos se dibujan de forma procedural con pygame.draw.
No se requieren archivos de imagen externos.
"""

import pygame
import math
from interface.constants import *


# ══════════════════════════════════════════════════════════════════════════════
#  Utilidades de borde 3-D  (estilo Windows 98)
# ══════════════════════════════════════════════════════════════════════════════

def draw_raised(surf, rect, w=2):
    """Borde convexo: claro arriba-izquierda, oscuro abajo-derecha."""
    x, y, rw, rh = rect
    light = [C_WHITE, C_BG]
    dark  = [C_BLACK, C_GRAY_MID]
    for i in range(w):
        cl = light[min(i, len(light) - 1)]
        cd = dark [min(i, len(dark)  - 1)]
        pygame.draw.line(surf, cl, (x+i, y+rh-1-i), (x+i,      y+i))
        pygame.draw.line(surf, cl, (x+i, y+i),       (x+rw-1-i, y+i))
        pygame.draw.line(surf, cd, (x+i, y+rh-1-i),  (x+rw-1-i, y+rh-1-i))
        pygame.draw.line(surf, cd, (x+rw-1-i, y+i),  (x+rw-1-i, y+rh-1-i))


def draw_sunken(surf, rect, w=2):
    """Borde concavo: oscuro arriba-izquierda, claro abajo-derecha."""
    x, y, rw, rh = rect
    dark  = [C_BLACK, C_GRAY_MID]
    light = [C_WHITE, C_BG]
    for i in range(w):
        cd = dark [min(i, len(dark)  - 1)]
        cl = light[min(i, len(light) - 1)]
        pygame.draw.line(surf, cd, (x+i, y+rh-1-i), (x+i,      y+i))
        pygame.draw.line(surf, cd, (x+i, y+i),       (x+rw-1-i, y+i))
        pygame.draw.line(surf, cl, (x+i, y+rh-1-i),  (x+rw-1-i, y+rh-1-i))
        pygame.draw.line(surf, cl, (x+rw-1-i, y+i),  (x+rw-1-i, y+rh-1-i))


# ══════════════════════════════════════════════════════════════════════════════
#  Display LCD de 7 segmentos
# ══════════════════════════════════════════════════════════════════════════════

_LCD_SEG = {
    0:   (1,1,1,1,1,1,0),
    1:   (0,1,1,0,0,0,0),
    2:   (1,1,0,1,1,0,1),
    3:   (1,1,1,1,0,0,1),
    4:   (0,1,1,0,0,1,1),
    5:   (1,0,1,1,0,1,1),
    6:   (1,0,1,1,1,1,1),
    7:   (1,1,1,0,0,0,0),
    8:   (1,1,1,1,1,1,1),
    9:   (1,1,1,1,0,1,1),
    "-": (0,0,0,0,0,0,1),
    " ": (0,0,0,0,0,0,0),
}


def _draw_digit(surf, ox, oy, digit, W=LCD_DIGIT_W, H=LCD_DIGIT_H):
    pat = _LCD_SEG.get(digit, _LCD_SEG[" "])
    T   = 2
    M   = 2
    mid = H // 2

    def hbar(y_off, lit):
        c = C_LCD_ON if lit else C_LCD_OFF
        pygame.draw.rect(surf, c, (ox+M+1, oy+y_off, W-2*(M+1), T))

    def vbar(x_off, y_off, lit):
        c = C_LCD_ON if lit else C_LCD_OFF
        pygame.draw.rect(surf, c, (ox+x_off, oy+y_off, T, mid-M-T))

    hbar(0,           pat[0])
    vbar(W-T, M+T,    pat[1])
    vbar(W-T, mid+M,  pat[2])
    hbar(H-T,         pat[3])
    vbar(0,   mid+M,  pat[4])
    vbar(0,   M+T,    pat[5])
    hbar(mid-T//2,    pat[6])


def make_lcd_surface(value, clamp_max=999):
    W, H = LCD_DIGIT_W, LCD_DIGIT_H
    G, P = LCD_GAP, LCD_PAD
    pw = LCD_DIGITS*W + (LCD_DIGITS-1)*G + 2*P
    ph = H + 2*P
    surf = pygame.Surface((pw, ph))
    surf.fill(C_LCD_BG)
    draw_sunken(surf, (0, 0, pw, ph), w=1)
    value = max(-99, min(clamp_max, value))
    neg = value < 0
    av  = abs(value)
    if neg:
        chars = ["-", av//10, av%10]
    else:
        chars = [av//100, (av//10)%10, av%10]
    for i, ch in enumerate(chars):
        _draw_digit(surf, P+i*(W+G), P, ch)
    return surf


# ══════════════════════════════════════════════════════════════════════════════
#  Sprites de celdas
# ══════════════════════════════════════════════════════════════════════════════

def _make_raised_cell(size):
    surf = pygame.Surface((size, size))
    surf.fill(C_BG)
    draw_raised(surf, (0, 0, size, size), w=2)
    return surf


def _make_flat_cell(size, bg=None):
    surf = pygame.Surface((size, size))
    surf.fill(bg if bg else C_REVEALED)
    pygame.draw.rect(surf, C_GRAY_MID, (0, 0, size, size), 1)
    return surf


def _draw_flag_icon(surf, size):
    cx     = size // 2
    pole_x = cx - 1
    py0    = size // 5
    py1    = int(size * 0.78)
    pygame.draw.line(surf, C_BLACK, (pole_x, py0), (pole_x, py1), 2)
    pygame.draw.polygon(surf, (220, 20, 20), [
        (pole_x,              py0),
        (pole_x + size//4,    py0 + size//8),
        (pole_x,              py0 + size//4),
    ])
    bw = size // 3
    pygame.draw.line(surf, C_BLACK, (pole_x-bw//2, py1), (pole_x+bw//2, py1), 2)


def _draw_mine_icon(surf, size, color=C_BLACK):
    cx, cy = size//2, size//2
    r = max(4, size//4)
    for deg in range(0, 360, 45):
        rad = math.radians(deg)
        ex = int(cx + math.cos(rad)*(r + r//2 + 1))
        ey = int(cy + math.sin(rad)*(r + r//2 + 1))
        pygame.draw.line(surf, color, (cx, cy), (ex, ey), 2)
    pygame.draw.circle(surf, color, (cx, cy), r)
    pygame.draw.circle(surf, C_WHITE, (cx-r//3, cy-r//3), max(1, r//4))


def make_cell_sprites(size):
    """
    Claves: 'unrevealed', 'revealed', '1'..'8',
            'flag', 'question', 'mine', 'mine_hit', 'mine_wrong'
    """
    spr = {}
    fn  = pygame.font.SysFont("Arial", size-4, bold=True)
    fq  = pygame.font.SysFont("Arial", size-6, bold=True)

    spr["unrevealed"] = _make_raised_cell(size)
    spr["revealed"]   = _make_flat_cell(size)

    for n in range(1, 9):
        s = _make_flat_cell(size)
        t = fn.render(str(n), True, NUM_COLORS[n])
        s.blit(t, t.get_rect(center=(size//2, size//2)))
        spr[str(n)] = s

    s = _make_raised_cell(size)
    _draw_flag_icon(s, size)
    spr["flag"] = s

    s = _make_raised_cell(size)
    q = fq.render("?", True, C_BLACK)
    s.blit(q, q.get_rect(center=(size//2, size//2)))
    spr["question"] = s

    s = _make_flat_cell(size)
    _draw_mine_icon(s, size)
    spr["mine"] = s

    s = _make_flat_cell(size, bg=C_MINE_HIT)
    _draw_mine_icon(s, size)
    spr["mine_hit"] = s

    s = _make_flat_cell(size)
    _draw_mine_icon(s, size)
    pygame.draw.line(s, (220,20,20), (3,3),       (size-4,size-4), 2)
    pygame.draw.line(s, (220,20,20), (size-4,3),  (3,size-4),      2)
    spr["mine_wrong"] = s

    return spr


# ══════════════════════════════════════════════════════════════════════════════
#  Sprite de carita  (mejorado)
# ══════════════════════════════════════════════════════════════════════════════

def make_face_sprites(size):
    """
    Claves: "{estado}_normal" y "{estado}_pressed"
    estado in {FACE_NORMAL, FACE_OFACE, FACE_WON, FACE_DEAD}
    """
    spr = {}

    for state in (FACE_NORMAL, FACE_OFACE, FACE_WON, FACE_DEAD):
        for pressed in (False, True):
            surf = pygame.Surface((size, size))
            surf.fill(C_BG)
            if pressed:
                draw_sunken(surf, (0,0,size,size), w=2)
            else:
                draw_raised(surf, (0,0,size,size), w=2)

            off = 1 if pressed else 0
            cx  = size//2 + off
            cy  = size//2 + off
            r   = size//2 - 3

            # Cara amarilla
            pygame.draw.circle(surf, (255,220,0), (cx,cy), r)
            pygame.draw.circle(surf, C_BLACK,     (cx,cy), r, 1)

            eye_r  = max(1, r//5)
            eye_y  = cy - r*3//8
            eye_xl = cx - r*3//8
            eye_xr = cx + r*3//8

            sw  = r*3//4
            sh  = max(2, r//3)
            smx = cx - sw//2
            smy = cy + r//5

            if state == FACE_DEAD:
                d = eye_r + 1
                for ex, ey in [(eye_xl, eye_y), (eye_xr, eye_y)]:
                    pygame.draw.line(surf, C_BLACK, (ex-d,ey-d), (ex+d,ey+d), 2)
                    pygame.draw.line(surf, C_BLACK, (ex+d,ey-d), (ex-d,ey+d), 2)
                # boca triste (0..pi = curva hacia abajo en pantalla)
                pygame.draw.arc(surf, C_BLACK,
                                pygame.Rect(smx, smy, sw, sh),
                                0, math.pi, 2)

            elif state == FACE_WON:
                gl_w = eye_r*4
                gl_h = eye_r*3
                for ex in (eye_xl, eye_xr):
                    pygame.draw.rect(surf, C_BLACK,
                                     (ex-gl_w//2, eye_y-gl_h//2, gl_w, gl_h))
                    # reflejo
                    pygame.draw.line(surf, (80,80,80),
                                     (ex-gl_w//2+1, eye_y-gl_h//2+1),
                                     (ex-gl_w//4,   eye_y-gl_h//2+1), 1)
                # puente
                pygame.draw.line(surf, C_BLACK,
                                 (eye_xl+gl_w//2, eye_y),
                                 (eye_xr-gl_w//2, eye_y), 2)
                # sonrisa amplia
                pygame.draw.arc(surf, C_BLACK,
                                pygame.Rect(smx, smy, sw, sh),
                                math.pi, 2*math.pi, 2)

            elif state == FACE_OFACE:
                for ex in (eye_xl, eye_xr):
                    pygame.draw.ellipse(surf, C_BLACK,
                                        pygame.Rect(ex-eye_r-1, eye_y-eye_r,
                                                    (eye_r+1)*2, eye_r*2))
                mouth_r = max(2, r//5)
                pygame.draw.circle(surf, C_BLACK, (cx, cy+r*3//8), mouth_r)

            else:  # FACE_NORMAL
                pygame.draw.circle(surf, C_BLACK, (eye_xl, eye_y), eye_r)
                pygame.draw.circle(surf, C_BLACK, (eye_xr, eye_y), eye_r)
                # sonrisa (pi..2pi = curva hacia abajo en pantalla)
                pygame.draw.arc(surf, C_BLACK,
                                pygame.Rect(smx, smy, sw, sh),
                                math.pi, 2*math.pi, 2)

            key = f"{state}_{'pressed' if pressed else 'normal'}"
            spr[key] = surf

    return spr


# ══════════════════════════════════════════════════════════════════════════════
#  Sprite de rueda dentada  (gear / configuracion)
# ══════════════════════════════════════════════════════════════════════════════

def make_gear_sprite(size, pressed=False):
    """Boton cuadrado con icono de rueda dentada."""
    surf = pygame.Surface((size, size))
    surf.fill(C_BG)
    if pressed:
        draw_sunken(surf, (0,0,size,size), w=2)
    else:
        draw_raised(surf, (0,0,size,size), w=2)

    off     = 1 if pressed else 0
    cx      = size//2 + off
    cy      = size//2 + off
    gc      = (55, 55, 75)
    n       = 8
    r_body  = size//2 - 5
    r_tip   = size//2 - 2
    r_hub   = max(2, size//6)
    t_angle = math.pi / n * 0.55

    pygame.draw.circle(surf, gc, (cx, cy), r_body)

    for i in range(n):
        base = 2*math.pi*i/n
        pts = [
            (cx + r_body*math.cos(base - t_angle*1.25),
             cy + r_body*math.sin(base - t_angle*1.25)),
            (cx + r_tip *math.cos(base - t_angle),
             cy + r_tip *math.sin(base - t_angle)),
            (cx + r_tip *math.cos(base + t_angle),
             cy + r_tip *math.sin(base + t_angle)),
            (cx + r_body*math.cos(base + t_angle*1.25),
             cy + r_body*math.sin(base + t_angle*1.25)),
        ]
        pygame.draw.polygon(surf, gc, [(int(p[0]),int(p[1])) for p in pts])

    pygame.draw.circle(surf, C_BG, (cx, cy), r_hub)
    pygame.draw.circle(surf, gc,   (cx, cy), r_hub, 1)

    return surf

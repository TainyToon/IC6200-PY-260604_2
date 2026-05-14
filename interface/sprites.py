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




def make_cell_sprites(size):
    """
    Claves: 'unrevealed', 'revealed', '1'..'8', 'flag', 'question'
    """
    # ── Patrones pixel-art 3×5 para dígitos 1-8 ──────────────────────────────
    _PX = {
        1: [[0,1,0],[1,1,0],[0,1,0],[0,1,0],[1,1,1]],
        2: [[1,1,0],[0,0,1],[0,1,0],[1,0,0],[1,1,1]],
        3: [[1,1,0],[0,0,1],[0,1,0],[0,0,1],[1,1,0]],
        4: [[1,0,1],[1,0,1],[1,1,1],[0,0,1],[0,0,1]],
        5: [[1,1,1],[1,0,0],[1,1,0],[0,0,1],[1,1,0]],
        6: [[0,1,1],[1,0,0],[1,1,0],[1,0,1],[0,1,0]],
        7: [[1,1,1],[0,0,1],[0,1,0],[0,1,0],[0,1,0]],
        8: [[1,1,1],[1,0,1],[1,1,1],[1,0,1],[1,1,1]],
    }

    def _draw_pixel_digit(surf, n, color, cell_size):
        pattern = _PX[n]
        px = max(2, cell_size // 8)   # tamaño de cada bloque
        gw = 3 * px                    # ancho total del glifo
        gh = 5 * px                    # alto total del glifo
        ox = (cell_size - gw) // 2
        oy = (cell_size - gh) // 2
        for row, bits in enumerate(pattern):
            for col, bit in enumerate(bits):
                if bit:
                    pygame.draw.rect(surf, color,
                                     (ox + col*px, oy + row*px, px, px))

    spr = {}
    fq  = pygame.font.SysFont("Arial", size-6, bold=True)

    spr["unrevealed"] = _make_raised_cell(size)
    spr["revealed"]   = _make_flat_cell(size)

    for n in range(1, 9):
        s = _make_flat_cell(size)
        _draw_pixel_digit(s, n, NUM_COLORS[n], size)
        spr[str(n)] = s

    s = _make_raised_cell(size)
    _draw_flag_icon(s, size)
    spr["flag"] = s

    s = _make_raised_cell(size)
    q = fq.render("?", True, C_BLACK)
    s.blit(q, q.get_rect(center=(size//2, size//2)))
    spr["question"] = s

    return spr

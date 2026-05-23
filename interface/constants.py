from data.map import NOVATO, AFICIONADO, EXPERIMENTADO

# ----------------------------------------------
# Pantalla / ventana
# ----------------------------------------------
FPS   = 60
TITLE = "BUSCAMINAS"

# ----------------------------------------------
# Medidas de layout
# ----------------------------------------------
CELL_SIZE    = 28    # pixeles por celda (inicial; puede cambiar con zoom)
BORDER_OUTER = 14    # borde exterior de la ventana (px)
BORDER_INNER = 8     # separacion entre paneles (px)
HEADER_H     = 54    # altura total de la cabecera
TOOLBAR_H    = 44    # barra de herramientas superior

# Display LCD
LCD_DIGIT_W = 16
LCD_DIGIT_H = 28
LCD_DIGITS  = 3
LCD_GAP     = 2
LCD_PAD     = 4

# Boton de carita
FACE_SIZE = 36

# ----------------------------------------------
# Colores  (paleta Windows 98)
# ----------------------------------------------
C_BG       = (192, 192, 192)
C_WHITE    = (255, 255, 255)
C_GRAY_MID = (128, 128, 128)
C_BLACK    = (  0,   0,   0)
C_REVEALED = (185, 185, 185)

# LCD
C_LCD_BG  = (  0,   0,   0)
C_LCD_ON  = (255,   0,   0)
C_LCD_OFF = ( 80,   0,   0)

# Mina golpeada
C_MINE_HIT = (255,   0,   0)

# Colores de los numeros 1-8
NUM_COLORS = {
    1: (  0,   0, 255),
    2: (  0, 128,   0),
    3: (255,   0,   0),
    4: (  0,   0, 128),
    5: (128,   0,   0),
    6: (  0, 128, 128),
    7: (  0,   0,   0),
    8: (128, 128, 128),
}

# ----------------------------------------------
# Dificultades
# ----------------------------------------------
DIFFICULTIES = {
    "novato":        {"name": "Novato",        "preset": NOVATO,        "rows":  9, "cols": 12, "mines": 10},
    "aficionado":    {"name": "Aficionado",    "preset": AFICIONADO,    "rows": 16, "cols": 16, "mines": 40},
    "experimentado": {"name": "Experimentado", "preset": EXPERIMENTADO, "rows": 16, "cols": 30, "mines": 99},
}
DIFF_ORDER = ["novato", "aficionado", "experimentado"]

MIN_ROWS = 9;  MIN_COLS = 9
MAX_ROWS = 20; MAX_COLS = 40

# ----------------------------------------------
# Estados de celda
# ----------------------------------------------
UNREVEALED = 0
REVEALED   = 1
FLAGGED    = 2
QUESTION   = 3
MINE       = -1

# ----------------------------------------------
# Estados de la carita
# ----------------------------------------------
FACE_NORMAL = 0
FACE_OFACE  = 1
FACE_WON    = 2
FACE_DEAD   = 3

# Pantallas
SCREEN_MENU   = "menu"
SCREEN_GAME   = "game"
SCREEN_CUSTOM = "custom"

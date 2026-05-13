import random
from interface.constants import UNREVEALED, REVEALED


#Permite que las celdas 0 se abran solas si estan proximas
def revelar_celdas_vacias(board, row, col, rows, cols):

    if not (0 <= row < rows and 0 <= col < cols):
        return

    celda = board[row][col]

    if celda["state"] != UNREVEALED:
        return

    celda["state"] = REVEALED

    if celda["value"] != 0:
        return

    for df in [-1, 0, 1]:
        for dc in [-1, 0, 1]:

            if df == 0 and dc == 0:
                continue

            revelar_celdas_vacias(
                board,
                row + df,
                col + dc,
                rows,
                cols
            )



def ia_movimiento_random(board, inciertas, rows, cols):

    if not inciertas:
        return

    row, col = random.choice(inciertas)

    print(f"[IA] Movimiento aleatorio en ({row}, {col})")

    revelar_celdas_vacias(
        board,
        row,
        col,
        rows,
        cols
    )
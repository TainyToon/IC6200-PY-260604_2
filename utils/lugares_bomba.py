from interface.constants import MINE

class LugaresBomba:
    @staticmethod
    def colocar_numeros(tablero, bombas):
        rows = len(tablero)
        cols = len(tablero[0])

        for fila, col in bombas:
            tablero[fila][col]["value"] = MINE

        for fila, col in bombas:
            for df in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if df == 0 and dc == 0:
                        continue

                    nf = fila + df
                    nc = col + dc

                    if 0 <= nf < rows and 0 <= nc < cols:
                        if tablero[nf][nc]["value"] != MINE:
                            tablero[nf][nc]["value"] += 1
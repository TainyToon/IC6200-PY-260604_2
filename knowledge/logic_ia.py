import random
import itertools

from knowledge.logic import Symbol, And, Or, Not, model_check
from interface.constants import UNREVEALED, REVEALED, FLAGGED


class LogicIA:
    def __init__(self, board, rows, cols):
        self.board = board
        self.rows = rows
        self.cols = cols

        self.knowledge = And()
        self.logs = []

        self.celdas_seguras = set()
        self.minas_seguras = set()
        self.celdas_inciertas = set()
    #esto es para printear conocimiento y no estar con puro print
    def log(self, mensaje):
        self.logs.append(mensaje)
        print("[IA]", mensaje)

    def simbolo(self, row, col): #Celdas las contextualizamos como variable logica
        return Symbol(f"M_{row}_{col}") #ejem: La celda en la fila 2, columna 3 es una mina

    '''
        Busca al rededor las celdas de una posicion. 
    '''
    def vecinos(self, row, col):
        resultado = []
      
        '''
            -1  -> una posición arriba / izquierda
            0  -> misma fila o columna
            1  -> una posición abajo / derecha
        '''

        for df in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if df == 0 and dc == 0:
                    continue

                nr = row + df
                nc = col + dc

                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    resultado.append((nr, nc))

        return resultado

        '''
            Es la que me dice cual de todas es una mina si o si, pruebas las cmbinaciones posibles para saberlo.
        '''
    def exactamente_k_minas(self, celdas, k):
        simbolos = [self.simbolo(fila, col) for fila, col in celdas]

        combinaciones_validas = []

        for minas in itertools.combinations(simbolos, k):
            minas = set(minas)
            partes = []

            for simbolo in simbolos:
                if simbolo in minas:
                    partes.append(simbolo)
                else:
                    partes.append(Not(simbolo))

            combinaciones_validas.append(And(*partes))

        if len(combinaciones_validas) == 0:
            return And(*[Not(simbolo) for simbolo in simbolos])

        return Or(*combinaciones_validas)

    #Recorre todo el tablero y si encuentra celda revelada, mira sus vecionos
    def reconstruir_conocimiento(self):
        self.knowledge = And()

        for row in range(self.rows):
            for col in range(self.cols):
                celda = self.board[row][col]

                if celda["state"] == REVEALED and celda["value"] > 0:
                    ocultas = [] #Ocultas
                    banderas = 0 #banderas en juego

                    for nr, nc in self.vecinos(row, col):
                        vecino = self.board[nr][nc]

                        if vecino["state"] == UNREVEALED:
                            ocultas.append((nr, nc))
                        elif vecino["state"] == FLAGGED:
                            banderas += 1

                    minas_restantes = celda["value"] - banderas

                    if ocultas and minas_restantes >= 0:
                        oracion = self.exactamente_k_minas(
                            ocultas,
                            minas_restantes
                        )

                        self.knowledge.add(oracion)

                        self.log(
                            f"Desde ({row},{col})={celda['value']} se crea oración: "
                            f"{ocultas} tienen exactamente {minas_restantes} mina(s)."
                        )
    '''
        Esta es la funcion que tomas las decisiones.

    '''
    def analizar(self):
        self.logs.clear()
        self.celdas_seguras.clear()
        self.minas_seguras.clear()
        self.celdas_inciertas.clear()

        self.reconstruir_conocimiento()

        for row in range(self.rows):
            for col in range(self.cols):
                celda = self.board[row][col]

                if celda["state"] == UNREVEALED:
                    simbolo = self.simbolo(row, col)

                    es_mina = model_check(self.knowledge, simbolo)
                    es_segura = model_check(self.knowledge, Not(simbolo))

                    if es_mina:
                        self.minas_seguras.add((row, col))
                        self.log(f"Se deduce que ({row},{col}) es mina.")

                    elif es_segura:
                        self.celdas_seguras.add((row, col))
                        self.log(f"Se deduce que ({row},{col}) es segura.")

                    else:
                        self.celdas_inciertas.add((row, col))

        self.log(f"Celdas seguras identificadas: {len(self.celdas_seguras)}")
        self.log(f"Minas correctamente marcables: {len(self.minas_seguras)}")
        self.log(f"Celdas inciertas: {len(self.celdas_inciertas)}")

        return {
            "seguras": list(self.celdas_seguras),
            "minas": list(self.minas_seguras),
            "inciertas": list(self.celdas_inciertas),
            "logs": self.logs
        }
    #Entonces escoge una celda aleatoria por que no tiene contexto
    def primer_movimiento(self):
        row = random.randint(0, self.rows - 1)
        col = random.randint(0, self.cols - 1)

        self.log(
            f"Primer movimiento aleatorio en ({row},{col}) "
            f"porque no existe conocimiento inicial."
        )

        return (row, col)
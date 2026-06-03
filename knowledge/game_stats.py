from interface.constants import FLAGGED, MINE


class GameStats:

    def __init__(self):
        self.seguras_identificadas    = 0 
        self.minas_marcadas_correctas = 0   
        self.inciertas_acumuladas     = 0   
        self.turnos_ia                = 0  
        self.movimientos_aleatorios   = 0   
        self.celdas_reveladas         = 0   
        self.tiempo_partida           = 0   

        self.partidas_jugadas = 0
        self.partidas_ganadas = 0
        self.mejor_tiempo     = None   


    def registrar_turno_ia(self, resultado: dict):
        self.turnos_ia            += 1
        self.seguras_identificadas = max(
            self.seguras_identificadas, len(resultado["seguras"])
        )
        self.inciertas_acumuladas += len(resultado["inciertas"])

    def registrar_minas_correctas(self, board):
        total = sum(
            1
            for fila in board
            for c in fila
            if c["state"] == FLAGGED and c["value"] == MINE
        )
        self.minas_marcadas_correctas = total

    def registrar_celda_revelada(self):
        self.celdas_reveladas += 1

    def registrar_movimiento_aleatorio(self):
        self.movimientos_aleatorios += 1

    def cerrar_partida(self, ganada: bool, elapsed: int):
        self.tiempo_partida   = elapsed
        self.partidas_jugadas += 1
        if ganada:
            self.partidas_ganadas += 1
            if self.mejor_tiempo is None or elapsed < self.mejor_tiempo:
                self.mejor_tiempo = elapsed

    def reset_partida(self):
        self.seguras_identificadas    = 0
        self.minas_marcadas_correctas = 0
        self.inciertas_acumuladas     = 0
        self.turnos_ia                = 0
        self.movimientos_aleatorios   = 0
        self.celdas_reveladas         = 0
        self.tiempo_partida           = 0
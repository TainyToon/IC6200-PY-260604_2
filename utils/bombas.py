import random

class Bombas:
    historial_ubicaciones = set()  #Hatsa que se cierre el prhgrama se limpia memoria

    def __init__(self, rows, cols, cantidad):
        self.rows = rows
        self.cols = cols
        self.cantidad = cantidad
        self.ubicaciones = []

    def generar_bombas(self, primer_click):
        fila_click, col_click = primer_click

        posiciones_validas = []

        for fila in range(self.rows):
            for col in range(self.cols):
                posicion = (fila, col)

                if abs(fila - fila_click) <= 1 and abs(col - col_click) <= 1: #Con esto evitamos que haya bombas en la primera celda y en los 8 vecinos, como el juego origi
                    continue

                if posicion in Bombas.historial_ubicaciones:
                    continue

                posiciones_validas.append(posicion)
                

        # Si ya no quedan suficientes posiciones nuevas, reiniciamos historial
        if len(posiciones_validas) < self.cantidad:
            Bombas.historial_ubicaciones.clear()
            return self.generar_bombas(primer_click)

        self.ubicaciones = random.sample(posiciones_validas, self.cantidad)

        for pos in self.ubicaciones:
            Bombas.historial_ubicaciones.add(pos)

        

        print("Bombas: ", self.ubicaciones )
        return self.ubicaciones
import random
from interface.constants import UNREVEALED, REVEALED, FLAGGED

class Sentence:
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = int(count)

    def __eq__(self, other):
        return isinstance(other, Sentence) and \
               self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    """
    ---- Regla 1-----------------------------------------------------------------

    Returns the set of all cells in self.cells known to be mines.
    Example: {A, B, C} = 3  →  {A, B, C}
    """
    def known_mines(self):
        if self.count > 0 and len(self.cells) == self.count:
            return set(self.cells)
        return set()

    """
    ---- Regla 2-----------------------------------------------------------------

    Returns the set of all cells in self.cells known to be safe.
    Example: {A, B, C} = 3  →  {A, B, C}
    """
    def known_safes(self):
       
        if self.count == 0:
            return set(self.cells)
        return set()

    """
    Updates internal knowledge representation given the fact that
    a cell is known to be a mine.
    """
    def mark_mine(self, cell):
        
        if cell in self.cells:
            self.cells.discard(cell)
            self.count -= 1
    """
    Updates internal knowledge representation given the fact that
    a cell is known to be safe.
    """
    def mark_safe(self, cell):
        
        if cell in self.cells:
            self.cells.discard(cell)

class LogicIA:
    """
    Agente jugador de Buscaminas con base de conocimiento proposicional.
    """

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

        self.mines     = set()   # celdas confirmadas como minas
        self.safes     = set()   # celdas confirmadas como seguras
        self.knowledge = []      # base de conocimiento: lista de Sentence

        self._procesadas = set() # celdas ya incorporadas al knowledge base

    def vecinos(self, row, col):
        resultado = []
        for df in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if df == 0 and dc == 0:
                    continue
                nr, nc = row + df, col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    resultado.append((nr, nc))
        return resultado

    """
    Marks a cell as a mine, and updates all knowledge
    to mark that cell as a mine as well.
    """
    def mark_mine(self, cell):
 
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)
    """
    Marks a cell as safe, and updates all knowledge
    to mark that cell as safe as well.
    """
    def mark_safe(self, cell):
   
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    """
    Called when the Minesweeper board tells us, for a given
    safe cell, how many neighboring cells have mines in them.
    """
    def add_knowledge(self, cell, count):

        # 1. Marcar como segura y registrar
        self.mark_safe(cell)
        self._procesadas.add(cell)

        # 2. Construir oración con vecinos ocultos
        row, col = cell
        vecinos_ocultos = []
        minas_conocidas = 0

        for nr, nc in self.vecinos(row, col):
            if (nr, nc) in self.mines:
                minas_conocidas += 1
            elif (nr, nc) not in self.safes:
                vecinos_ocultos.append((nr, nc))

        count_ajustado = count - minas_conocidas

        # 3. Agregar si aporta información nueva
        if vecinos_ocultos and 0 <= count_ajustado <= len(vecinos_ocultos):
            nueva = Sentence(vecinos_ocultos, count_ajustado)
            if nueva not in self.knowledge:
                self.knowledge.append(nueva)

        # 4. Propagar
        self._update_knowledge()

    """
    Aplica las tres reglas de inferencia en bucle hasta convergencia.
    """
    def _update_knowledge(self):
        cambio = True
        while cambio:
            cambio = False

            # Reglas 1 y 2: extraer minas/seguras confirmadas de cada oración
            nuevas_minas   = set()
            nuevas_seguras = set()

            for s in self.knowledge:
                nuevas_minas   |= s.known_mines()
                nuevas_seguras |= s.known_safes()

            for cell in nuevas_minas - self.mines:
                self.mark_mine(cell)
                cambio = True

            for cell in nuevas_seguras - self.safes:
                self.mark_safe(cell)
                cambio = True

            # Regla 3: inferencia por subconjunto  A ⊂ B → (B−A) = (kB − kA)
            activas = [s for s in self.knowledge if s.cells]
            for a in activas:
                for b in activas:
                    if a is b or not a.cells:
                        continue
                    if a.cells < b.cells:           # a es subconjunto propio de b
                        diff_cells = b.cells - a.cells
                        diff_count = b.count - a.count
                        if 0 <= diff_count <= len(diff_cells):
                            nueva = Sentence(diff_cells, diff_count)
                            if nueva not in self.knowledge:
                                self.knowledge.append(nueva)
                                cambio = True

            # Eliminar oraciones vacías (ya resueltas)
            self.knowledge = [s for s in self.knowledge if s.cells]
    """
    Retorna un movimiento aleatorio entre celdas no reveladas y no
    conocidas como minas. Solo se usa cuando no hay inferencias posibles.
    """

    def make_random_move(self, board):
        
        candidatas = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if board[r][c]["state"] == UNREVEALED and (r, c) not in self.mines
        ]
        if candidatas:
            return random.choice(candidatas)
        return None

    """
    Escanea el tablero en busca de celdas recién reveladas, incorpora su
    conocimiento y retorna las conclusiones actuales.
    """
    def analizar(self, board):
        
        # Incorporar celdas reveladas aún no procesadas
        for r in range(self.rows):
            for c in range(self.cols):
                celda = board[r][c]
                if celda["state"] == REVEALED and (r, c) not in self._procesadas:
                    self.add_knowledge((r, c), celda["value"])
                # Sincronizar banderas manuales del jugador
                elif celda["state"] == FLAGGED and (r, c) not in self.mines:
                    self.mark_mine((r, c))

        todas_ocultas = {
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if board[r][c]["state"] == UNREVEALED
        }

        seguras       = todas_ocultas & self.safes
        minas_ocultas = todas_ocultas & self.mines
        inciertas     = todas_ocultas - seguras - minas_ocultas

        print(f"[IA] Knowledge: {len(self.knowledge)} oraciones | "
              f"Seguras: {len(seguras)}  Minas: {len(minas_ocultas)}  "
              f"Inciertas: {len(inciertas)}")

        return {
            "seguras":   list(seguras),
            "minas":     list(minas_ocultas),
            "inciertas": list(inciertas),
            "logs":      [],
        }

    def primer_movimiento(self):
        """Movimiento inicial aleatorio (antes de conocer el tablero)."""
        row = random.randint(0, self.rows - 1)
        col = random.randint(0, self.cols - 1)
        print(f"[IA] Primer movimiento aleatorio en ({row},{col})")
        return (row, col)

    def reset(self):
        """Reinicia la base de conocimiento para una nueva partida."""
        self.mines       = set()
        self.safes       = set()
        self.knowledge   = []
        self._procesadas = set()

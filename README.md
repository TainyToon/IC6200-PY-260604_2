# IC6200-PY-260604_2

Explicacion de por que no podemos usar la clase logic vista en clase del todo, que funciones podemos reciclar y como podemos verlo textualmente.
Primero, sabemos que la inferencia logica mediante proposiciones utiliza:

- Symbol
- And
- Or
- Not
- Implication
- Biconditional
- model_check

Y permiten construir expresiones logicas permitiendo sacar y verificar concluciones a partir de la base de conocimiento, sin embargo, el problema del buscaminas requiere un tipo de razonamiento diferente.

El por que no se puede usar es por que la inferencia normal que conocemos trabaja de forma que cada símbolo representa una afirmación verdadera o falsa.
ejem:
A = “La celda A contiene una mina”

El problema es que Buscaminas no trabaja únicamente con afirmaciones individuales, sino con restricciones numéricas. Por ejemplo, cuando una celda revela el número 1, realmente está indicando:
“Exactamente una de las celdas vecinas contiene una mina”

Al tratar de integrar logic.py en la IA y usar Symbol para representar cada celda, construir una base de conocimiento con And/Or, 
y hacer inferencias con model_check, se da un problema que es una complejidad O(2ⁿ) y congela el juego con tableros medianos. Funcionaría solo en Novato con pocas celdas ocultas.

Y ese tipo de acciones no las tiene nuestro logic.py y se debe implementar funciones nuevas que permitan poder inferir este tipo de concluciones por lo que se creo la clase "LogicIA"

Proposito de logic_ia

La clase LogicIA funciona como un intermeidario entre el tablero del Buscaminas y la logica detras.

Sus responsabilidades deberian ser:

- Leer el estado visible del tablero.
- Identificar vecinos ocultos alrededor de cada número revelado.
- Convertir restricciones numéricas en fórmulas proposicionales.
- Construir una base de conocimiento lógica.
- Consultar mediante model_check si una celda:
  - necesariamente es mina
  - necesariamente es segura
  - y si no permanece incierta

ejemplo:
Celdas desconocidas y un valor conocido. -> [1] [?] [?]
El número 1 indica:
“Exactamente una de las dos celdas ocultas es mina”
En logica proposicional epodemos representarlo como:

---

## | (A ∧ ¬B) ∨ (¬A ∧ B) |

donde:
A = “La primera celda es mina”
B = “La segunda celda es mina”

Y reutilizando funciones logicas de "logic.py" como:

- And
- Or
- Not

Podemos realizar una logica funciona en logicIa

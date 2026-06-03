# IC6200-PY-260604_2 — Buscaminas con Agente de IA

## Aspectos generales del agente

El agente `BuscaminasIA` juega de forma autónoma aplicando lógica proposicional para inferir qué celdas son seguras y cuáles contienen minas. Su comportamiento sigue el siguiente flujo en cada partida:
 
### 1. Primer movimiento: siempre aleatorio
 
Antes de que el tablero genere las minas, el agente no tiene ningún conocimiento sobre el estado del juego. Por eso su primer movimiento se elige al azar entre todas las celdas disponibles. 

### 2. Ciclo de análisis: inferencia lógica
 
A partir del segundo turno, el agente analiza todas las celdas reveladas que aún no han sido procesadas (`analizar()`). Para cada una, construye una oración lógica del tipo `{vecinos_ocultos} = count_ajustado` y la agrega a su base de conocimiento. Luego aplica las tres reglas de inferencia en bucle hasta que no haya más conclusiones nuevas (`_update_knowledge()`):

### 3. Resolución del tablero
 
Con las conclusiones del análisis, el agente actúa:
 
- Coloca una bandera automáticamente sobre cada celda confirmada como mina.
- Revela cada celda confirmada como segura.
- Verifica victoria después de cada acción: si todas las celdas no-mina están reveladas.

### 4. Incertidumbre
 
Cuando el análisis no produce ni minas confirmadas ni celdas seguras, el agente comunica la situación y detiene su ejecución automática. El usuario recibe un diálogo con dos opciones:
 
- **Marcar casilla manualmente:** el usuario elige una celda para revelar y el agente retoma el control automático en base a ese conocimiento.
- **Movimiento aleatorio:** — el agente elige al azar entre las celdas ocultas que no están confirmadas como minas (`make_random_move()`). Esto puede detonar una mina.

## Por qué no se puede usar directamente `logic.py`

El archivo `logic.py` que usamos en clase implementa los operadores logicos proposicional:

- `Symbol` — representa una proposición atómica (verdadera o falsa)
- `And`, `Or`, `Not`, `Implication`, `Biconditional` — conectivos lógicos
- `model_check` — verifica si una consulta se deduce del conocimiento evaluando todos los modelos posibles

Estas herramientas permiten construir expresiones lógicas y verificar conclusiones a partir de una base de conocimiento. Sin embargo, el problema del Buscaminas exige un tipo de solucion diferente a lo visto en clase con las preposiciones ya que un `model_check` no es lo suficientemente "bueno" para realizar este trabajo.

### El problema de las restricciones numéricas

La lógica proposicional trabaja con afirmaciones individuales del tipo:

```
A = "La celda A contiene una mina"   →   verdadero o falso
```

El Buscaminas no trabaja con afirmaciones individuales, sino con **restricciones numéricas**. Cuando una celda revela el número `1`, el tablero comunica:

> *"Exactamente una de las celdas vecinas ocultas contiene una mina."*

Representar eso en lógica proposicional pura requiere expandir todas las combinaciones posibles. Para dos vecinos `A` y `B`:

```
(A ∧ ¬B) ∨ (¬A ∧ B)
```

Para cuatro vecinos `A, B, C, D` con exactamente 2 minas, la expresión crece a 6 disyunciones de 4 conjunciones cada una. Con 8 vecinos y 3 minas son 56 cláusulas. `logic.py` no cuenta con operadores para expresar restricciones numéricas de forma compacta; habría que generarlas manualmente usando `And`, `Or` y `Not` para cada combinación, lo que hace el código inmanejable.

### El problema de escala con `model_check`

`model_check` resuelve por enumeración exhaustiva: prueba todos los posibles valores de verdad para cada símbolo hasta encontrar una conclusión. Para `n` celdas ocultas, evalúa **2ⁿ modelos**.

| Nivel | Celdas totales | Celdas ocultas (turno típico) | Modelos a evaluar |
|---|---|---|---|
| Novato (9×12) | 108 | ~50 | 2⁵⁰ ≈ 10¹⁵ |
| Aficionado (16×16) | 256 | ~120 | 2¹²⁰ ≈ 10³⁶ |
| Experimentado (16×30) | 480 | ~250 | 2²⁵⁰ ≈ 10⁷⁵ |


### Conclusión

Usamos `logic.py` como referencia y en realidad esta fue usada en las primeras versiones del py lo cual nos permitio darnos cuenta de los problemas reales que esta presenta en su uso para este proyecto. La `LogicIA` es la que implementa los mismos principios de inferencia logica pero usando una representacion mas compacta y mejor (usando restricciones numericas) y propagacion directa en lugar de enumeracion de modelos, lo que hace que el agente funcional en los tres niveles requeridos. Con esto dicho, pudimos aprender con base a prueba y error hasta dar con el verdadero problema y de ahi se empezo una investigaciion para una posible solucion a los problemas presentes con `model_check`, lo cual fue asi, permitiendo concretar el proyecto Buscaminas de manera eficiente.

---

## Base conceptual de `BuscaminasIA` — Proyecto Minesweeper de CS50 AI (Harvard)

La estructura de `BuscaminasIA` está inspirada en el proyecto Minesweeper del curso CS50's Introduction to Artificial Intelligence with Python de la Universidad de Harvard. Este curso aborda inteligencia artificial aplicada en Python y dedica su primera semana al tema de **Knowledge**, donde propone construir un agente capaz de jugar Buscaminas usando exactamente las mismas herramientas de lógica proposicional vistas en clase.

El proyecto de CS50 define una clase `Sentence` que encapsula una restricción del tipo `{celdas} = count`, y una clase `MinesweeperAI` que mantiene una **base de conocimiento persistente** compuesta por esas oraciones. A diferencia de reconstruir el conocimiento desde cero en cada turno, el agente acumula información incrementalmente: cada vez que se revela una celda, se agrega una nueva oración y se propagan las inferencias sobre todas las existentes.


La diferencia principal es que nosotros añadimos la **Regla 3 de inferencia por subconjunto** dentro de `_update_knowledge()`. El CS50 la menciona como mejora opcional; en nuestra implementación es esencial para resolver situaciones donde las Reglas 1 y 2 solas no son suficientes:

```
{A, B} = 1          ← una oración
{A, B, C, D} = 2    ← otra oración
─────────────────────────────────────
{C, D} = 1          ← nueva oración derivada (Regla 3: subconjunto)
```

**Referencia oficial del proyecto:**
https://cs50.harvard.edu/ai/2023/projects/1/minesweeper/

**Curso completo:**
https://cs50.harvard.edu/ai/

---

## Lógica de inferencia

Las tres reglas que aplica `_update_knowledge()` en bucle hasta convergencia:

**Regla 1 Resolución unitaria positiva:**
Si el número de celdas ocultas en una oración es igual al conteo de minas, todas son minas.
`{A, B, C} = 3` → A es mina, B es mina, C es mina

**Regla 2 Resolución unitaria negativa:**
Si el conteo de minas es 0, ninguna celda es mina: todas son seguras.
`{A, B, C} = 0` → A es segura, B es segura, C es segura

**Regla 3 Inferencia por subconjunto:**
Si una oración es subconjunto propio de otra, se deriva una nueva oración con las celdas y el conteo restante.
`A ⊂ B` → nueva oración `(B − A) = (kB − kA)`

Cuando ninguna regla produce nuevo conocimiento, las celdas restantes son **lógicamente indeterminadas** y el agente lo comunica al usuario, cumpliendo la Observación #8 (solo actúa cuando está justificado) y la Observación #11 (comunica la incertidumbre).

---

## Análisis PEAS

| Componente | Descripción |
|---|---|
| **Performance** | Completar el tablero sin detonar minas, identificando correctamente celdas seguras y minas en el menor tiempo posible. |
| **Environment** | Tablero de Buscaminas de dimensiones configurables 9×9, 16x16,16×30 y personalizado. El entorno es parcialmente observable, pues solo se ven las celdas reveladas. |
| **Actuators** | Revelar una celda o colocar bandera en una celda. |
| **Sensors** | Valor numérico de cada celda revelada (0–8), estado de celdas vecinas. |

## Task Environment

| Propiedad | Clasificación |
|---|---|
| Observabilidad | Parcialmente observable, el agente no tiene acceso al estado global del entorno, solo conoce las celdas que han sido reveladas. |
| Agentes | Un solo agente, BuscaminasIA|
| Determinismo | Estocástico, pues las minas se colocadan aleatoriamente.|
| Episodicidad | Secuencial, pues las acciones no son independientes, pues revelear una celda o colocar bandera altera el conocimiento del agente.|
| Dinamismo | Estático, el entorno no cambia muestas el agente realiza su próximo movimiento |
| Continuidad | Discreto, pues el entorno está compuesto por una cuadrícula finita de celdas y un conjunto limitado de estados. |

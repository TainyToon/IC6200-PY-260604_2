# IC6200-PY-260604_2 — Buscaminas con Agente de IA

## Por qué no se puede usar directamente `logic.py`

La librería `logic.py` vista en clase implementa los operadores clásicos de la lógica proposicional:

- `Symbol` — representa una proposición atómica (verdadera o falsa)
- `And`, `Or`, `Not`, `Implication`, `Biconditional` — conectivos lógicos
- `model_check` — verifica si una consulta se deduce del conocimiento evaluando todos los modelos posibles

Estas herramientas permiten construir expresiones lógicas y verificar conclusiones a partir de una base de conocimiento. Sin embargo, el problema del Buscaminas exige un tipo de razonamiento que va más allá de lo que `model_check` puede manejar de forma eficiente.

### El problema de las restricciones numéricas

La lógica proposicional clásica trabaja con afirmaciones individuales del tipo:

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

`logic.py` permanece en el repositorio como referencia de la base teórica vista en clase. La clase `LogicIA` implementa los mismos principios de inferencia lógica, pero usando una representación compacta (restricciones numéricas) y propagación directa en lugar de enumeración de modelos, lo que hace el agente funcional en los tres niveles requeridos.

---

## Base conceptual de `LogicIA` — Proyecto Minesweeper de CS50 AI (Harvard)

La estructura de `LogicIA` está inspirada en el proyecto *Minesweeper* del curso **CS50's Introduction to Artificial Intelligence with Python** de la Universidad de Harvard. Este curso aborda inteligencia artificial aplicada en Python y dedica su primera semana al tema de **Knowledge** (conocimiento y razonamiento lógico), donde propone construir un agente capaz de jugar Buscaminas usando exactamente las mismas herramientas de lógica proposicional vistas en clase.

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
| **Performance** | Revelar todas las celdas sin minas sin detonar ninguna. Métricas: celdas seguras identificadas, minas correctamente marcadas, celdas inciertas, tiempo. |
| **Environment** | Tablero de Buscaminas de dimensiones configurables (mínimo 9×9, máximo 16×30). Parcialmente observable: solo se ven las celdas reveladas. |
| **Actuators** | Revelar una celda, colocar bandera en una celda. |
| **Sensors** | Valor numérico de cada celda revelada (0–8), estado de celdas vecinas. |

## Task Environment

| Propiedad | Clasificación |
|---|---|
| Observabilidad | Parcialmente observable |
| Agentes | Un solo agente |
| Determinismo | Estocástico (minas colocadas aleatoriamente) |
| Episodicidad | Secuencial |
| Dinamismo | Estático |
| Continuidad | Discreto |

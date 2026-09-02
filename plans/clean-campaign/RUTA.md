# Ruta de la campaña limpia

Escrito el 2026-09-02, sobre el sustrato que sobrevivió al reinicio de la base.
Este documento es la fuente; la pantalla que lo dibuja lo lee de aquí.

Una regla gobierna todo lo demás: **un nivel se nombra por todos los campos que
varían en él**. El defecto que esta campaña existe para no repetir siempre tuvo
la misma forma — un nombre, dos cantidades.

---

## 0. El sustrato: lo que hay, sin decisiones dentro

| material | cantidad | estado |
|---|---|---|
| secuencias | 528.294 | íntegro |
| embeddings | 6.867.762 = 13 configs x 528.294 | íntegro, cobertura total |
| anotaciones GOA | 21.876.159 en 4 versiones | íntegro |
| ontologías | 9 snapshots, 2024-03 a 2026-01 | íntegro |
| alineamientos | 4.478.115 pares en caché | íntegro, crece bajo demanda |
| metadatos UniProt | 575.503 | íntegro |

Nada de esto hay que recalcularlo. Es exactamente el punto del reinicio.

### 0.1 GOA 220 apunta once meses a su propio futuro

`GOA 220` (publicada 2024-04-16) está enlazada a `releases/2025-03-16`. Ese
snapshot tiene 213 términos que aún no existían y **77.600 relaciones frente a
las 82.461** de `releases/2024-03-28` — un 6 % de diferencia en el grafo por el
que se propaga. Propagar t0 bajo un grafo posterior marca anotaciones
experimentales pre-ventana como conocimiento nuevo. Es el "phantom gap".

**No hay que editar la base.** `generate_evaluation_set` ya acepta
`old_native_snapshot_id` y `new_native_snapshot_id` exactamente para esto: cada
lado se propaga bajo un snapshot explícito sin tocar ni una fila de anotación.
La corrección es un parámetro del payload.

### 0.2 Los nueve snapshots emparejan con nueve versiones GOA


No es casualidad: quien los cargó los eligió así. Cada ventana tiene ya su
pivote inmediatamente anterior.

| GOA | publicada | pivote (última ontología <= publicación) |
|---|---|---|
| 220 | 2024-04-16 | releases/2024-03-28 |
| 221 | 2024-06-14 | releases/2024-06-10 |
| 222 | 2024-08-01 | releases/2024-06-17 |
| 223 | 2024-10-21 | releases/2024-09-08 |
| 224 | 2024-12-21 | releases/2024-09-08 |
| 225 | 2025-03-08 | releases/2025-02-06 |
| 226 | 2025-05-03 | releases/2025-03-16 |
| 227 | 2025-09-04 | releases/2025-07-22 |
| 230 | 2026-03-04 | releases/2026-01-23 |

221 a 225 **no están cargadas**. Las fechas de arriba son reales, leídas de la
cabecera `!date-generated` de cada GAF, no interpoladas.

---

## 1. Las ventanas

**AJUSTE: 220 -> 227**, 2024-04-16 a 2025-09-04, 16,6 meses.
**COMPETICIÓN: 227 -> 230**, 6,0 meses. Sellada, una sola pasada al final.

No hace falta cargar ninguna versión GOA nueva. El coste de simplificar, dicho:
la ventana de ajuste mide 2,8 veces la de competición, así que las
**magnitudes** de los efectos no trasladan directamente. Lo que tiene que
trasladar es el **orden** de los brazos, que es sobre lo que se decide.

### 1.1 Un error mío, y por qué se cuenta aquí

La primera versión de este documento daba 4.487.376 pares nuevos y una cohorte
de 30.074 proteínas. **Estaban mal.** El anti-join emparejaba por
`protein_go_annotation.go_term_id`, y `go_term.id` es **por snapshot**: 432.070
filas para 48.251 accesiones GO repartidas en 9 snapshots. `GO:0005515` tiene
nueve `id` distintos. GOA 220 y GOA 227 cuelgan de snapshots distintos, así que
el anti-join no emparejaba **nunca** y lo que medí fue "anotaciones fechadas
después del corte de 220", no "anotaciones ganadas".

Es exactamente el defecto que este documento dice evitar, cometido dentro del
documento. Se queda escrito por dos razones. La primera es que la guardia de
delta de `go_id` deja de ser hipotética y pasa a estar demostrada. La segunda es
tranquilizadora: **la ruta de producción no tiene el fallo.**
`compute_evaluation_data_reconciled` reconcilia por texto `go_id` a través de
snapshots desiguales, que es justo lo que hay que hacer.

### 1.2 La ganancia real de la ventana, y por qué la verdad es experimental

Emparejando por `go_id`, en 220 -> 227 aparecen **811.440 pares nuevos**
(proteína, término) sobre 367.729 proteínas. Su composición:

| código | pares | % |
|---|---|---|
| IEA | 712.954 | 87,9 |
| IBA (filogenético) | 43.137 | 5,3 |
| ISO | 21.081 | 2,6 |
| IDA | 11.343 | 1,4 |
| IMP | 6.619 | 0,8 |
| resto | 16.306 | 2,0 |

Casi nueve de cada diez anotaciones ganadas son electrónicas. Evaluar contra
ellas mide el acuerdo con la tubería de InterPro, no la predicción de función.

**La verdad de la ventana son los códigos experimentales y de alto rendimiento**
(EXP, IDA, IPI, IMP, IGI, IEP, HTP, HDA, HMP, HGI, HEP, TAS, IC):

| aspecto | pares nuevos | proteínas |
|---|---|---|
| BPO | 14.811 | 8.721 |
| CCO | 6.621 | 4.719 |
| MFO | 5.376 | 4.467 |
| **total** | **26.808** | **14.219 distintas** |

### 1.3 IEA no se tira: entra en tres sitios, y en un cuarto no

1. **El banco.** Los vecinos donan IEA. Es el eje C (`donor_policy`), y quitar
   IEA del banco es una **ablación**, no la norma.
2. **La base de exclusión.** Lo que la proteína ya sabía al inicio incluye sus
   IEA. Si no, un término que ya tenía por IEA contaría como descubrimiento.
3. **Como rasgo.** Y hay evidencia medida de que vale: **5.513 pares sobre
   4.379 proteínas** tenían una IEA previa que un experimento confirmó después.
   IEA es señal parcial y real, no ruido.
4. **En la categorización NK/LK/PK, no.** El código la define sobre anotaciones
   **experimentales** de t0 únicamente (`protea/core/domain/category.py`).
   Comprobado en el código, no supuesto.

Dos filtros por código de evidencia comparten vocabulario y nada más: **la
verdad** (qué cuenta como ganado) y **`donor_policy`** (qué puede donar un
vecino). Confundirlos sería otra vez un nombre para dos cantidades.

## 2. El marco: lo que se mantiene quieto

El sello cubre seis campos (`seal_evaluation_frames._FRAME_FIELDS`):
`evaluation_set_id`, `pivot_snapshot_id`, `information_accretion_set_id`,
`temporal_window`, `max_terms`, `max_distance`.

La campaña declara **una política**, no un marco. La política genera el marco
por ventana:

1. pivote = la ontología en o antes del **inicio** de la ventana
2. IA = calculada sobre el conjunto de anotaciones del inicio, bajo ese pivote
3. verdad = primera aparición dentro de la ventana
4. base de exclusión = lo que la proteína ya sabía al inicio de la ventana
5. `max_terms`, `max_distance` = constantes de campaña, declaradas una vez

Cinco marcos: cuatro de ajuste y uno de competición. Dos números bajo sellos
distintos no se comparan, y el panel se niega a ponerlos en la misma barra.

El preset de scoring **no** está en el marco. Es un nivel. Meterlo daría a cada
nivel su propio marco y el sello dejaría de decir nada.

---

## 3. El ganador se busca en cada estrato

Lo que cambia de un estrato a otro no es **si** se busca el ganador, sino
**cuánto peso aguanta** la afirmación.

### 3.0 Las nueve celdas de decisión están todas potenciadas

Ya no es una estimación. Medido sobre el conjunto de evaluación construido
(`b7cfed9a`, ventana 220->227, modo `reconciled`): **23.736 proteínas delta**,
203.306 anotaciones ganadas tras propagación. Proteínas distintas por celda —
un mismo protein puede aparecer en más de un aspecto, de ahí que 30.433 exceda
las 23.736 distintas:

| aspecto | NK | LK | PK | total |
|---|---|---|---|---|
| BPO | 1.509 | 1.214 | 13.876 | 16.599 |
| CCO | 1.116 | 821 | 4.872 | 6.809 |
| MFO | 1.129 | 943 | 4.953 | 7.025 |
| **total** | **3.754** | **2.978** | **23.701** | **30.433** |

Efecto mínimo detectable, sigma pareada 0,1157:

| aspecto | NK | LK | PK |
|---|---|---|---|
| BPO | 0,0083 | 0,0093 | 0,0028 |
| CCO | 0,0097 | **0,0113** | 0,0046 |
| MFO | 0,0096 | 0,0106 | 0,0046 |

**La celda más pequeña, LK:CCO con 821, resuelve 0,0113.** Las nueve ven por
debajo de 0,012 — seis veces mejor que el 0,02 que la campaña quiere declarar.
Antes sólo PK:BPO llegaba.

Con 30.433 unidades sobre 9.720 estratos completos, la media por celda sigue
siendo **3,1**. Por eso los estratos no se pueden tratar como 9.720
experimentos, y por eso hacen falta los tres mecanismos que siguen — pero el
nivel de decisión sobre el que se apoyan está firme.

### 3.1 Cada estrato nombra un ganador, y lleva su propia fuerza


El grafo ya tiene el vocabulario; sólo hay que aplicarlo por celda en lugar de
por nodo:

| en la celda | fuerza | qué significa |
|---|---|---|
| n >= n_min para el efecto declarado | `measured` | hay ganador y está separado del suelo |
| >= 2 niveles puntuados, n < n_min | `unpowered` | hay líder, no hay separación |
| 1 nivel | `chosen` | no había con quién comparar |
| 0 | `blocked` | la celda está vacía |

Ninguna celda se pinta de verde gratis, y ninguna se esconde.

`n_min` no es un número, es una curva. Con la sigma pareada medida de 0,1157:

| n en la celda | efecto mínimo detectable |
|---|---|
| 25 | 0,065 |
| 50 | 0,046 |
| 100 | 0,032 |
| 263 | 0,020 |
| 500 | 0,015 |
| 1.000 | 0,010 |

Una celda con n=50 no es inútil: ve efectos de 0,046. Lo que no puede es ver
0,02 y decir que lo ha visto.

### 3.2 La estimación es jerárquica, no celda a celda

Un ganador estimado por su cuenta sobre n=8 es ruido con nombre. El efecto de
cada estrato se **encoge** hacia el de su padre (aspecto x categoría), y ése
hacia el global. La cantidad de encogimiento la fija el propio dato: es la
varianza entre estratos frente al ruido dentro de cada uno.

- Si los estratos de verdad difieren, el encogimiento es leve y el ganador
  por estrato se sostiene.
- Si no difieren, todo colapsa al ganador global — y ese colapso **es el
  hallazgo**, no un fracaso del método.

Esto es lo que permite nombrar un ganador en 9.720 celdas sin inventarse 9.720
experimentos independientes.

### 3.3 La política de enrutado se valida cruzada, o no vale

El canalizado gana sobre ruido a menos que la política se ajuste cruzada. Es la
trampa más segura de este diseño: con 9.720 celdas y 30.074 proteínas, elegir
el mejor brazo por celda **siempre** mejora el número si se elige y se mide
sobre el mismo dato.

El protocolo, entonces:

1. Aprender el ganador por estrato en un pliegue.
2. Aplicar esa política a otro pliegue.
3. Medir la ganancia del sistema enrutado frente al **único mejor brazo
   global**, como un solo número sobre las 30.074 proteínas.

Ese número sí está bien potenciado. Si el enrutado es real, aparece ahí. Si no
aparece ahí, los ganadores por estrato eran ruido por bonita que fuese la
tabla.

### 3.4 Lo primero que hay que construir

Las 9.720 celdas **no** están pobladas de forma uniforme: la mayoría de las
proteínas se concentra en unas pocas decenas de combinaciones de
(longitud, homología, taxonomía). Cuántas celdas llegan de verdad a `measured`
es una pregunta empírica con respuesta exacta, y hay que responderla **antes**
de mover ningún eje.

Instrumento: la tabla de ocupación de estratos sobre el conjunto de evaluación
de la ventana de ajuste. Es barata y ordena todo lo que viene después.

## 4. Los ejes, en orden de despacho

El orden no es estético: cada eje depende del anterior y ninguno se mueve
mientras el de arriba está sin fijar.

### A — Sustrato / representación  (tu paso 1)

13 configuraciones, todas con cobertura completa. Pero no son 13 niveles de un
eje, son **tres ejes distintos**:

- **Modelo preentrenado** — esm2 (8M, 650M, 3B), esmc_600m, ankh (base, large),
  prot_t5, prostt5, protst. Nueve niveles.
- **Capa** — `ankh_base` en `layer_indices [0]` frente a `ankh_base@L10` en
  `[10]`. Mismo modelo, misma familia, todo lo demás idéntico. **Un par, un
  eje.**
- **Sustrato aprendido** — rung2-pooled, rung2-dense, rung2-residue. Otro nodo.
  Ponerlos en la misma barra que los preentrenados sin decirlo es el defecto de
  siempre.

**Arreglado el 2026-09-02.** Dos filas no tenían `display_name` ni `family` y
renderizaban como niveles indistinguibles. Resultó que no eran duplicados:

| id | era | ahora | por qué |
|---|---|---|---|
| `b691b1ad` | `ElnaggarLab/ankh-base`, sin nombre | `ankh_base@L10`, familia `ankh` | es la misma ankh-base en **capa [10]**, no un duplicado. El nombre tenía que decir la capa o el eje entero desaparecía del render |
| `a322a00b` | `facebook/esm2_t36_3B_UR50D`, sin nombre | `esm2_3b`, familia `esm2` | `param_count` se deja NULO a propósito: lo llena `count_backend_parameters` cargando el modelo, no una cifra de memoria deducida |

Las 13 tienen ahora nombre y familia.

**Ablación que falta**: `metric` (coseno vs euclídea) y `aspect_separated_knn`
(on/off). Perillas del recuperador que llevan toda la vida en su valor por
defecto sin que nadie las haya medido.

### B — El corte de la lista  (tu paso 2)

El código ya separa tres cantidades que antes se llamaban `depth`: la
**profundidad de recuperación** (`limit_per_entry`) cambia qué candidatos
llegaron a existir y cambiarla es **volver a correr**; los **cortes**
(`max_k_position`, `max_sequence_rank`) truncan una lista ya recuperada y son
**gratis**.

Por eso: recuperar **una vez a K=30** y estudiar cómo se corta esa lista. Eso
responde el eje del corte. No responde el de la recuperación, y decir que sí
sería el mismo error otra vez. **K=1 no va en la escalera**: es un régimen
distinto, un donante por (proteína, aspecto), y se informa aparte.

#### Por qué un `distance_threshold` global no vale

Medido, no supuesto. Distancia coseno media entre pares aleatorios de
proteínas, 2.157 pares por configuración:

| config | dim | media | sd | máx |
|---|---|---|---|---|
| ankh_base@L10 | 768 | **0,0004** | 0,0002 | 0,0010 |
| esm2_3b | 2560 | 0,0532 | 0,0293 | 0,1922 |
| esm2_650m | 1280 | 0,1214 | 0,0786 | 0,5668 |
| esm2_8m | 320 | 0,1271 | 0,0743 | 0,6781 |
| esmc_600m | 1152 | 0,1974 | 0,1035 | 0,7566 |
| prostt5 | 1024 | 0,3215 | 0,1287 | 0,7423 |
| ankh_base | 768 | 0,3748 | 0,1046 | 0,8279 |
| ankh_large | 1536 | 0,4904 | 0,1190 | 0,9102 |
| prot_t5 | 1024 | 0,5779 | 0,1299 | 0,9449 |
| protst | 512 | 0,8268 | 0,1870 | 1,3147 |
| rung2-pooled | 2048 | 0,8843 | 0,0571 | 1,0016 |
| rung2-dense | 2048 | 0,8856 | 0,0697 | 1,0380 |
| rung2-residue | 2048 | 0,9037 | 0,0768 | 0,9958 |

**Factor 2.250 entre los extremos.** Una `d` que deja una vecindad razonable en
`ankh_large` (media 0,49) se queda con **el corpus entero** en `ankh_base@L10`
(máximo 0,0010) y con **nada** en `protst`. Un umbral global no es una perilla
mal calibrada: es una perilla que no puede significar lo mismo en dos sitios.

Y hay un segundo problema que un umbral global tampoco ve: la **densidad local**.
Una familia superpoblada devuelve 200 vecinos bajo la misma `d` con la que una
proteína huérfana devuelve cero.

#### Lo que se ablaciona en su lugar: la REGLA de corte

Cinco niveles, todos truncaciones de la misma lista de 30, todos por tanto
**gratis**:

| nivel | regla | parám. | qué arregla |
|---|---|---|---|
| `rank@k` | los k primeros | k | nada, es la línea base |
| `global-d` | d_i <= d | d | nada — es el **control crudo deliberado**, y está para que la campaña enseñe por qué los otros hacen falta en vez de afirmarlo |
| `ratio` | d_i <= alfa · d_1 | alfa | se adapta por consulta: banda estrecha si hay un vecino muy cercano, ancha si es huérfana |
| `local-scale` | (d_i - d_1)/(d_m - d_1) <= tau | tau, m | quita la escala del **modelo** y la densidad de la **consulta**. Un tau global sí significa lo mismo en las 13 configuraciones |
| `mutual` | j sólo si i está en el top-K de j | — | sin parámetro. Mata los hubs, y sale casi gratis porque el banco es el mismo conjunto que las consultas |

`local-scale` es el principiado: es la misma normalización que usan UMAP y t-SNE
por punto, y es la que convierte el umbral en una cantidad comparable.

#### Un aviso sobre ankh_base@L10

Su distancia media entre pares aleatorios es 0,0004 con sd 0,0002. Los
embeddings se guardan en `halfvec`, con ~11 bits de mantisa. A esa escala la
diferencia entre dos vecinos está cerca del suelo de cuantización. **El ranking
puede seguir siendo correcto** — coseno preserva el orden — pero hay que
comprobarlo: recalcular en float32 sobre una muestra y ver si el top-30
coincide. Es una comprobación barata y hoy nadie la ha hecho.

### C — Banco, donante y auto-donación

`donor_policy`: permisiva vs restringida por códigos de evidencia. Se sabía que
la permisiva ganaba 8 de 8 y costaba catorce veces más en NK que en PK — **de la
campaña borrada, así que no es evidencia sobre nada ahora.** Se vuelve a medir.
`expand_votes_to_ancestors` es otro eje.

**`exclude_self_neighbour` pasa a ser una ablación**, y estaba mal clasificado
en la primera versión de este documento. La razón: la proteína consulta existe
en el banco con sus anotaciones **del inicio de la ventana**, que son
legítimamente conocidas. Que se done a sí misma no es leer el futuro, es una
decisión de modelado — y sólo tiene contenido en LK y PK, porque en NK no hay
nada previo que donar. Interacciona fuerte con el estrato de categoría, que es
exactamente lo que la hace interesante.

**Lo que sí es invariante, y ocupa su sitio**: el banco se construye con el
conjunto de anotaciones del **inicio** de la ventana, nunca con el del final. Si
el banco fuese 227, la auto-donación le entregaría a la proteína sus propias
anotaciones futuras. Ése es el control de fuga; la auto-donación no lo era.

### D — Rasgos  (tu paso 4, la parte de "comprobar que están bien")

21 familias en `feature_schema.FEATURE_FAMILIES`, 10 banderas `compute_*`.
Tu instinto es el correcto y hace falta un instrumento que no existe:

**Censo de rasgos** sobre el parquet exportado. Por familia y por columna:
fracción de nulos, cardinalidad, varianza, correlación con la etiqueta. Una
familia entera en NaN es un defecto. Una familia constante es un defecto. Una
familia con varianza y sin señal es un **hallazgo**, y son cosas distintas que
hoy se ven igual: no se ven.

**Ablación**: dejar-una-familia-fuera sobre las 21. Es barata — reentrenar el
reranker, no volver a recuperar.

### E — Scoring

Las 8 configuraciones las sembraban migraciones de alembic y se fueron con el
borrado. Se reconstruyen **desde los valores por defecto del código**, no
copiando las de antes: las de antes son inspiración, no configuración.

- `formula` ∈ {linear, evidence_weighted}
- `weights` sobre 10 señales
- `params.ia_prior` {enabled, gamma, source ∈ frequency | ia}
- `params.calibration`

**Ablación que falta**: `ia_prior.source` frecuencia vs IA. Los conjuntos de IA
se calculan por marco de todos modos, así que el nivel sale casi gratis.

### F — Reranker  (tus pasos 4 y 5)

`RerankerSpec`: runner, `objective` ∈ {binary, lambdarank},
`enabled_feature_families`, `drop_features`, `seed`.

**Control de fuga, explícito y auditable**: `train_versions` y `test_versions`
del payload de exportación deben terminar **en o antes del inicio** de la
ventana de ajuste. El reranker no puede haber visto la ventana sobre la que se
le evalúa.

**Un booster o tres.** El despacho por categoría (NK/LK/PK) es una decisión de
**enrutado** disfrazada de perilla del reranker. Se mide como tal.

**Ablación que falta**: sensibilidad a la semilla. Cinco semillas. Una ganancia
dentro del ruido de semilla no es una ganancia.

### G — Two towers  (tu paso 6)

Existe `two_tower_classifier.py`, `classifier_producer.py` y la bandera
`compute_classifier`. Pero hay una distinción que tu frase señala y el código
hoy no cubre:

- **como rasgo** — `compute_classifier=True` junto al KNN. Esto es lo que hay.
- **como generador de candidatos** — sustituyendo al KNN. Esto es lo que has
  pedido, y es **otro nodo del grafo**, no otro nivel del mismo.

Generarlo de cero significa además que su conjunto de entrenamiento sale sólo
del conjunto de anotaciones del inicio de la ventana. Mismo control de fuga que
el reranker.

### H — Combinación y enrutado

Los dos nodos que nadie ha movido nunca.

- **combinación**: cómo se funden la puntuación del KNN y la del reranker
  (`reranking/combiners.py`)
- **enrutado**: elegir brazo por aspecto, por categoría, por estrato

Son los últimos porque consumen la salida de todos los anteriores.

---

## 5. La canalización

Por ventana y por brazo:

```
KNN K=30 ──► rasgos ──► scoring ──► predicciones
                                        │
                                        ├─► evaluar en cortes {2,3,5,10,20,30}
                                        ├─► estratificar (7 ejes)
                                        └─► sellar marco + experiment_run
```

En paralelo, la rama del reranker:

```
export_research_dataset (train_versions ⊂ pre-ventana)
        │
        ├─► CENSO DE RASGOS   ← instrumento nuevo, bloquea si una familia está muerta
        │
        └─► ajustar reranker ──► re-predecir ──► re-evaluar ──► re-estratificar
```

### Paso 0 de ejecución: un brazo cronometrado

Antes de comprometer los 13 conjuntos de prediccion de la ventana de ajuste, se
corre **uno solo, de punta a punta, midiendo**. De ahi sale el coste unitario
real. Multiplicar una estimacion por 13 es como se llega a una noche perdida.

---

## 6. Las puertas

Invariantes que se comprueban, no que se suponen. Cada una tiene que poder
fallar; si no puede fallar, no cuenta.

1. Nada lee 227->230 sin el waiver declarado. Guardia ya cableada.
2. Las dos máquinas en la revisión declarada. Código distinto etiqueta mal.
3. Todo brazo tiene `experiment_run` con `graph_node` y `floor` **antes** de
   despachar. El suelo es un nombre de nivel, no un número.
4. Todo resultado sale sellado con `frame_digest`.
5. El banco se construye con las anotaciones del INICIO de la ventana, nunca
   con las del final. Demostrado, no supuesto.
6. KNN en CPU. El "auto" elige GPU y la GPU es la ruta que falla.
7. Un nivel se nombra por todos los campos que varían.
8. Toda métrica almacenada está redondeada a 1e-4: "igual" leído de la base es
   una cota superior, nunca un cero.

---

## 7. Cola de instrumentos que faltan

| instrumento | para qué | bloquea |
|---|---|---|
| censo de rasgos | detectar familias muertas o constantes | paso 4 |
| tabla de celdas de estrato + escritor | describir sin recalcular | paso 3 |
| tabla de aterrizaje de intervalos pareados | potencia por celda | declarar cualquier eje |
| revisión declarada por la API al arrancar | el servidor sirvió 5 días de código viejo | confianza en el panel |
| sexto valor de fuerza: nulo bien potenciado | hoy "no hay efecto" y "no se pudo ver" son el mismo color | lectura del grafo |
|  guardia de delta de `go_id` por ventana **(demostrada, ver 1.1)** | detectar términos que aparecen por cambio de ontología, no por anotación | limpieza de la verdad |

## 8. Deuda menor detectada al escribir esto

- `strata.Stratum` documenta "seis ejes" y tiene siete campos.
- ~~Dos `embedding_config` sin nombre ni familia~~ ARREGLADO 2026-09-02: eran
  ankh-base en dos capas distintas, no un duplicado. Ver eje A.

# El marco declarado de la campaña limpia

Declarado el 2026-09-02, antes de mover ningún eje. Todo número de esta campaña
sale bajo este marco o no se compara con los demás.

## Constantes de campaña

| campo | valor | por qué |
|---|---|---|
| `max_terms` | `None` | paridad con LAFA: no se recorta la lista por proteína y namespace. Un tope sólo cambia la puntuación si una predicción lo supera, y las de tipo KNN nunca lo hacen |
| `max_distance` | `None` | el marco base no corta por distancia. **Todo corte es un nivel del eje B, no parte del marco** — y como `max_distance` sí entra en el sello, dos cortes distintos producen marcos hermanos que el sello mantiene separados. Eso es lo correcto: comparar un brazo cortado con otro sin cortar es comparar dos cosas |
| régimen de evidencia (verdad) | `lafa` | EXP, IDA, IPI, IMP, IGI, IEP, HTP, HDA, HMP, HGI, HEP, IC, TAS. Es lo que LAFA puntúa, así que el ajuste y la competición miden lo mismo |

## Ventana de ajuste 220 -> 227

| campo | valor |
|---|---|
| conjunto viejo | `cbb35a32-44e4-4e39-b524-05b4b7433727` — GOA 220, publicada 2024-04-16 |
| conjunto nuevo | `ec9f5c2c-cc1c-4e22-8cda-d1fe53ca86b3` — GOA 227, publicada 2025-09-04 |
| pivote | `6b78af68-eb01-477e-a599-fcde11ff0135` — `releases/2024-03-28` |
| nativo del viejo | `6b78af68-...` — el mismo. **Corrige el enlace de 220**, que apuntaba a `releases/2025-03-16` |
| nativo del nuevo | `a24e7d91-1236-4a18-a3ac-aadc36222e8b` — `releases/2025-07-22`, el propio de 227 |
| papel | `valid` |
| conjunto de IA | `b5f134b1-8c38-4894-9243-300284703ad9` |

### Por qué el pivote es el de t0

El pivote fija el universo de términos en el que se compara. Un término que no
existía cuando se hizo la predicción no pudo predecirse, así que no puede contar
como ganado. Cada lado se propaga bajo **su propio** DAG nativo (regla del
camino verdadero) y luego se interseca con el universo del pivote; eso es el
protocolo `filter_terms_given_obo`, y es lo que hace
`compute_evaluation_data_reconciled`.

### La corrección de 220, verificada

GOA 220 estaba enlazada a `releases/2025-03-16`, once meses posterior a su
publicación. Propagar t0 bajo un grafo posterior marca anotaciones
experimentales pre-ventana como conocimiento nuevo: el "phantom gap". La
corrección no toca ni una fila de anotación, es el parámetro
`old_native_snapshot_id`.

**Y quedó comprobada al calcular la IA**: `drop_rate_pct = 0.0`. Ni una sola
anotación del corpus 220 tiene un `go_id` ausente de `releases/2024-03-28`.
Corpus y snapshot pertenecen el uno al otro.

## El conjunto de IA, y sus cifras

`compute_information_accretion`, régimen `lafa`, pivote t0, corpus 220:

```
términos            42.312        no nulos    29.780
proteínas            86.068        pares propagados  3.863.889
IA máx              15,9046        IA media    2,7436
raíces  3    ciclos  0    violaciones TPR  0    drop_rate  0,0 %
sha256  15c411c9707b1a06dbf3171f279ed3d3ff712be27e3ba1b8eba8a36fd107ebfd
```

Contraste con la referencia que documenta el propio módulo: `IA_cafa6.tsv` tiene
máx 15,880 y media 2,647. La nuestra cae al lado, que es lo que tiene que pasar.

## Lo que falta para cerrar el sello

El sello (`_FRAME_FIELDS`) cubre seis campos. Cinco están fijados arriba. El
sexto, `evaluation_set_id`, lo produce el trabajo `90d847fc`.

## La ventana de competición

`227 -> 230` no se construye todavía. No hace falta para ajustar, y construirla
es una oportunidad de mirarla. Se construye cuando haya una decisión que
defender, con el waiver declarado, y una sola vez.

---

## El conjunto de evaluación, construido

`evaluation_set` = **`b7cfed9a-ccde-4d11-bd5c-0569618ee8b6`**, modo
`reconciled`. Con esto el sello tiene sus seis campos.

```
ventana        220 -> 227     506 dias     16,6 meses     papel: valid
proteinas delta       23.736
anotaciones ganadas  203.306   (nk 46.081 · lk 37.126 · pk 120.099)
conocido en t0     3.847.723
retiradas            426.385   sobre 47.455 proteinas
verdad         s3://protea/eval_groundtruth/b7cfed9a-.../groundtruth.parquet
```

Las cifras son **posteriores a la propagación a ancestros** (regla del camino
verdadero), por eso son mayores que un recuento de pares directos.

### Las nueve celdas de decisión, medidas

Proteínas distintas por (aspecto, categoría). Un mismo protein puede aparecer
en más de un aspecto, así que la suma 30.433 excede las 23.736 distintas.

| aspecto | NK | LK | PK | total |
|---|---|---|---|---|
| BPO | 1.509 | 1.214 | 13.876 | 16.599 |
| CCO | 1.116 | 821 | 4.872 | 6.809 |
| MFO | 1.129 | 943 | 4.953 | 7.025 |
| **total** | **3.754** | **2.978** | **23.701** | **30.433** |

Efecto mínimo detectable con sigma pareada 0,1157:

| aspecto | NK | LK | PK |
|---|---|---|---|
| BPO | 0,0083 | 0,0093 | 0,0028 |
| CCO | 0,0097 | 0,0113 | 0,0046 |
| MFO | 0,0096 | 0,0106 | 0,0046 |

**La celda más pequeña, LK:CCO con 821, resuelve 0,0113.** Las nueve celdas de
decisión ven por debajo de 0,012, que es seis veces mejor que el efecto de 0,02
que la campaña quiere declarar.

### Una observación que hay que mirar antes de fiarse

**426.385 anotaciones retiradas sobre 47.455 proteínas**, el doble de proteínas
que las que ganan. Son experimentales y propagadas, así que un solo cambio en
una hoja arrastra sus ancestros, y la reestructuración del grafo entre los dos
DAG nativos también retira ancestros. Puede ser todo eso y ser normal. Pero es
una cifra grande y **nadie la ha mirado**: merece un desglose por causa
(término obsoleto, cambio de relación, retirada real) antes de que la ventana
sostenga una decisión.

---

## El desglose de las retiradas, y lo que destapó

### Las retiradas no se puntúan

Primero lo tranquilizador. `_classify_protein_deltas` lo dice en su docstring:
*"`removed` holds terms present at the start of the window and absent at its
end. It is reported rather than scored."* No entra en la puntuación. Y `known`
—la base de exclusión— se toma de `old_by_ns` **incluyendo** lo que después se
retiró, que es lo correcto: la base es lo que la proteína sabía al empezar.

### Por causa

De las 426.385 retiradas:

| causa | pares | proteínas | % |
|---|---|---|---|
| C · sólo era **ancestro**, se pierde al cambiar el grafo | 404.972 | 46.690 | 95,0 |
| B · era anotación **directa** en 220 y ya no en 227 | 16.220 | 9.620 | 3,8 |
| A · la proteína pierde **toda** anotación experimental | 5.193 | 199 | 1,2 |

Noventa y cinco por ciento es el grafo, no la biología. Y eso obligaba a hacer
la pregunta espejo, que sí toca lo que se puntúa.

### La pregunta espejo: cuánta GANANCIA es cambio de grafo

Un par (p, T) ganado es un artefacto si p ya tenía en 220 una anotación directa
L tal que T es ancestro de L **bajo el DAG nuevo**. La proteína ya tenía la
hoja; lo único que cambió fue el grafo que la propaga.

| bucket | pares | artefactos | % |
|---|---|---|---|
| nk | 46.081 | 0 | 0,00 |
| lk | 37.126 | 0 | 0,00 |
| **pk** | **120.099** | **25.231** | **21,01** |
| total | 203.306 | 25.231 | 12,41 |

Los ceros exactos en NK y LK no son suerte: en NK no hay hoja previa que pueda
implicar nada, y en LK la ganancia está en otro aspecto, que es un subgrafo
disjunto. Que salgan cero es la comprobación de que la cuenta está bien hecha.

Está concentrado: **592 términos distintos**, y los doce primeros son el 51,8 %.

```
2.717  GO:0009987  cellular process
1.957  GO:0032774  RNA biosynthetic process
1.952  GO:0034654  nucleobase-containing compound biosynthetic process
1.934  GO:0141187  nucleic acid biosynthetic process
1.104  GO:1901652  response to peptide
  564  GO:0043232  intracellular non-membrane-bounded organelle
```

`GO:0141187` es un identificador nuevo insertado en la rama de biosíntesis de
ácidos nucleicos. Es reconexión de aristas, no anotación.

### Las dos variantes, medidas

Mismo par de conjuntos, misma verdad experimental, sólo cambia bajo qué grafo se
propaga cada lado:

| | A · cada lado bajo su nativo | B · ambos bajo el pivote t0 | cambio |
|---|---|---|---|
| proteínas NK | 2.413 | 2.404 | −9 |
| proteínas LK | 2.585 | 2.564 | −21 |
| **proteínas PK** | **19.836** | **9.768** | **−51 %** |
| delta proteínas | 23.736 | 13.753 | −42 % |
| anotaciones NK | 46.081 | 49.732 | +3.651 |
| anotaciones LK | 37.126 | 40.987 | +3.861 |
| anotaciones PK | 120.099 | 101.007 | −19.092 |
| ganado total | 203.306 | 191.726 | −5,7 % |
| retiradas | 426.385 | 115.436 | **−73 %** |
| conocido en t0 | 3.847.723 | 3.847.723 | idéntico |

Diez mil proteínas entraban en PK sólo por reconexión del grafo. NK y LK ganan
anotaciones porque el grafo de 2024 tiene **más** relaciones que el de 2025
(82.461 frente a 77.600), así que su cierre de ancestros es mayor.

### El defecto que esto destapa

`generate_evaluation_set` **se niega a construir la variante B**: el par
`(old, new)` es único. Es decir, **la clave de identidad no incluye los grafos
de propagación** — y acabamos de medir que cambiarlos mueve la verdad de PK un
21 % y el reparto de proteínas un 51 %.

Es el defecto recurrente del proyecto, una vez más: un nivel nombrado por menos
campos de los que varía. Dos conjuntos que miden cosas distintas comparten
nombre, y sólo cabe uno.

**Propuesta**: meter `old_native_snapshot_id` y `new_native_snapshot_id` en la
clave, construir las dos, y **exigir que la decisión se sostenga bajo las dos**
— exactamente la misma lógica que exigir que se sostenga en varias ventanas. El
grafo de propagación pasa a ser un eje más que la decisión tiene que sobrevivir,
en vez de un supuesto invisible.

No lo cambio sin que lo decidas: altera lo que la campaña mide, y la variante A
es la que presumiblemente usa LAFA.

---

## Las dos variantes, construidas (2026-09-02)

La clave de identidad se ensanchó (PROTEA#933) y las dos conviven:

| id | modo | nativos viejo / nuevo | NK | LK | PK | delta | retiradas |
|---|---|---|---|---|---|---|---|
| `b7cfed9a` | reconciled | 2024-03-28 / 2025-07-22 | 2.413 | 2.585 | 19.836 | 23.736 | 426.385 |
| `b7452c0e` | reconciled | 2024-03-28 / 2024-03-28 | 2.404 | 2.564 | 9.768 | 13.753 | 115.436 |

**A** es cada lado bajo su DAG nativo. **B** es el delta en un solo grafo, ambos
lados bajo el pivote t0. Una decisión de esta campaña tiene que sostenerse bajo
las dos; el grafo de propagación es un eje más que hay que sobrevivir, no un
supuesto invisible.

B reproduce exactamente el cálculo que se hizo fuera del sistema antes de tocar
el código, lo que es la comprobación de que la operación hace lo que se creía.

### Un defecto que sólo apareció al construirla

El primer intento de B guardó un conjunto **vacío**: nk 0, lk 0, pk 0, delta 0,
modo `same_snapshot`. Sin error.

`generate_evaluation_set` elegía entre sus dos caminos con
`same_snapshot = old_native == new_native == pivot_id`, que es una propiedad de
los **argumentos**. El camino rápido resuelve por `go_term.id`, columna
**scoped al snapshot**, así que sólo es correcto si los **conjuntos** están
enlazados al grafo en uso. Las dos pruebas coinciden mientras no haya override
y divergen exactamente cuando lo hay.

Medido: de las **11.197.453** anotaciones experimentales de los dos corpus,
**cero** resuelven bajo el pivote. Todas descartadas sin comentario por
`_load_experimental_annotations_by_ns`.

PROTEA#934 lo arregla por los dos lados: el modo se decide sobre el enlace
propio de los conjuntos, y un delta vacío sobre corpus no vacíos se **rechaza**
en vez de guardarse. Esa segunda mitad importa tanto como la primera: el fallo
no lanzaba, y aguas abajo nada podía distinguir un ground truth vacío de uno
real.

### Estado del sello

Los seis campos del marco están fijados para las dos variantes. Falta el query
set y el primer brazo para que `frame.declared` pase a verdadero: se cierra
cuando el primer resultado lo selle.

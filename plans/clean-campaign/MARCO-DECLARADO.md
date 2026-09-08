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

**Y confirmada por la cabecera del propio GAF (2026-09-04).** Cada fichero GOA
declara contra qué ontología se generó, lo que sustituye la heurística de
cercanía por un hecho leído:

| GAF | `!go-version` | publicada más reciente ≤ | enlazada | |
|---|---|---|---|---|
| 220 | `releases/2024-04-13` | `releases/2024-03-28` | `releases/2025-03-16` | ✗ |
| 226 | `releases/2025-04-27` | `releases/2025-03-16` | `releases/2025-03-16` | ✓ |
| 227 | `releases/2025-08-31` | `releases/2025-07-22` | `releases/2025-07-22` | ✓ |
| 230 | `releases/2026-03-01` | `releases/2026-01-23` | `releases/2026-01-23` | ✓ |

Las cuatro versiones declaradas son builds de `go-plus` que GO no archiva como
release pública. La regla es entonces *la publicada más reciente igual o anterior
a la declarada*, y bajo ella el pivote `releases/2024-03-28` no es una elección
cómoda: lo obliga la cabecera de GAF 220. El enlace de 227 también sale correcto,
así que el marco declarado aguanta sin cargar ninguna ontología nueva.

**Corregido el 2026-09-04.** `GOA 220` está ahora enlazada a
`releases/2024-03-28` y sus 5.317.051 anotaciones re-expresadas en ese snapshot,
cero fuera, verificado dentro de la transacción. La IA `b5f134b1`, las dos
evaluaciones y los tres encoders rung2 quedaron sin cambio — que era la
predicción, porque todo lo derivado ya leía 220 bajo esa ontología. El guardia
que impide que se repita está en `protea/core/operations/_gaf_header.py`.

**Lo que el parámetro no alcanzaba.** `old_native_snapshot_id` corrige la
evaluación, pero no la predicción: cada término predicho sale de una anotación
del donante, así que el `go_term_id` guardado *es* la identidad del candidato y
no hay parámetro que lo traduzca. Por eso 220 necesita además el remapeo de sus
`go_term_id`, que no cambia ninguna cifra ya medida — sólo hace que los ids
vivan en el snapshot que el resto del marco ya usa.

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

### La tabla de efecto mínimo detectable, retirada el 2026-09-07

Aquí había una tabla de MDE por celda con `2,8016·σ/√n` y σ = 0,1157, y la frase
*«las nueve celdas ven por debajo de 0,012»*. **Se retira entera y se deja dicho
por qué, en vez de borrarla**, porque el número circuló. El razonamiento está en
`PLAN-EXPERIMENTAL.md`: la fórmula no la admite el estadístico, y la σ era la
más apretada de nueve.

**Ninguna celda está declarada potenciada mientras no tenga su intervalo**, y el
intervalo lo da el bootstrap pareado a nivel de proteína.

### Una observación que hay que mirar antes de fiarse

**426.385 anotaciones retiradas sobre 47.455 proteínas**, el doble de proteínas
que las que ganan. Son experimentales y propagadas, así que un solo cambio en
una hoja arrastra sus ancestros, y la reestructuración del grafo entre los dos
DAG nativos también retira ancestros. Puede ser todo eso y ser normal. Pero es
una cifra grande y **nadie la ha mirado**: merece un desglose por causa
(término obsoleto, cambio de relación, retirada real) antes de que la ventana
sostenga una decisión.

---

## El eje C, medido y cerrado (2026-09-08)

El eje C pregunta por la **política de vecindario**: dos perillas de recuperación,
`exclude_self_neighbour` y `aspect_separated_knn`, sobre el haz de tres sustratos
que dejó el eje A. Se midió el 2×2 completo, en los tres sustratos y en las **dos
variantes de propagación**, con el bootstrap pareado a nivel de proteína
(`compare_paired_panels`: `f_micro_w`, 2000 remuestreos, BCa, τ reelegido dentro
de cada remuestreo, ponderación por IA, poblaciones intersectadas) y con
`effect_of_interest = 0,02` declarado.

Ese 0,02 no es nuevo: es **el efecto que la campaña ya decía querer declarar**,
en el texto que acompañaba a la tabla de MDE retirada. Lo que se retiró fue la
fórmula y la σ, no el objetivo.

### Excluir la propia proteína: 54 paneles de 54

`exclude_self_neighbour=true` contra `false`, con `aspect_separated_knn=false`
en los dos lados. Deltas de `f_micro_w`, variante B:

| panel | ankh_large | protst | prot_t5 |
|---|---|---|---|
| LK:BPO | −0,0446 | −0,0419 | −0,0672 |
| LK:CCO | −0,0617 | −0,0661 | −0,0874 |
| LK:MFO | −0,0469 | −0,0412 | −0,0652 |
| NK:BPO | −0,0302 | −0,0316 | −0,0477 |
| NK:CCO | −0,0435 | −0,0418 | −0,0515 |
| NK:MFO | −0,0497 | −0,0537 | −0,0850 |
| PK:BPO | −0,0065 | −0,0072 | −0,0117 |
| PK:CCO | −0,0277 | −0,0272 | −0,0372 |
| PK:MFO | −0,0206 | −0,0192 | −0,0326 |

**Los 54 paneles resuelven** —27 por variante— **ninguno es positivo, y ninguno
queda como nulo**: los 54 salen con estado `ok`. Las dos variantes coinciden
hasta la cuarta cifra.

**Y esto no es un veredicto de rendimiento.** El número baja porque estaba
inflado. Medido el 2026-08-28 y registrado en el docstring de
`_self_neighbour`: con auto-recuperación permitida, **el vecino más cercano es la
propia proteína en el 95,0 % de las filas candidatas a profundidad 1**, y el
**81,8 %** de las 14.032 consultas no tiene ningún otro vecino a esa profundidad.
Un vecindario de uno, donde el uno eres tú, no es una transferencia.

Así que **el coste de excluir ES la medida de esa inflación**, por sustrato. La
lectura correcta es al revés de como se lee sola: el número que sube es el que no
se puede usar.

### Separar por aspecto: nada, y medido donde podía moverse

`aspect_separated_knn=true` contra `false`, con `exclude_self_neighbour=true` en
los dos lados —es decir, **dentro del régimen limpio**—, en las dos variantes:

| sustrato | variante | resuelven | positivos | rango de delta |
|---|---|---|---|---|
| ankh_large | A | 7/9 | 0 | −0,0030 … −0,0002 |
| ankh_large | B | 7/9 | 0 | −0,0030 … −0,0003 |
| protst | A | 5/9 | 0 | −0,0010 … −0,0002 |
| protst | B | 4/9 | 0 | −0,0009 … −0,0002 |
| prot_t5 | A | 4/9 | 0 | −0,0027 … −0,0001 |
| prot_t5 | B | 4/9 | 0 | −0,0027 … −0,0001 |

**31 de 54 resuelven, ninguno positivo, y los 23 restantes son
`null_with_power`, no `null_unread`.** Esa distinción es todo el resultado: un
panel cuyo intervalo cruza el cero **y que tenía potencia frente a 0,02** dice
que ahí no hay nada de ese tamaño, no dice que no se sepa. Es el sexto valor de
fuerza que la campaña llevaba anotado como pendiente, y no hizo falta
construirlo: hacía falta declarar el número.

### La medición retirada, registrada y no borrada

La separación por aspecto se midió antes con `exclude_self_neighbour=false` y se
reportó como veredicto. **Se retiró el mismo día**, por dos defectos del par
comparado: sus dos lados corrieron en revisiones distintas —`8699bfd` con época
de caché 2 contra `5674c933` con época 3— y, decisivo, **la medida entera estaba
dentro del régimen que el otro sub-eje acababa de mostrar dominado por
auto-recuperación**. Era como mucho un techo.

La re-corrida limpia coincide con ella. **Eso es un hecho sobre este caso y no
una licencia para saltarse la comprobación**: la medida vieja era igual de
consistente con «el eje no importa» que con «el eje no se pudo mover», y no las
distinguía.

### La preinscripción, y el desenlace que refutó su mecanismo

El 2026-09-08 a las 10:37, con los brazos a 0/24, se registraron cuatro
desenlaces en `PREINSCRIPCION-2026-09-08-ASPECTO.md`. La predicción era que el
efecto de la separación por aspecto sería **mayor** en el régimen limpio, porque
el pool de donantes dejaría de ser las anotaciones de la propia proteína.

Salió **(D): menor**, en los tres sustratos. Y (D) estaba nombrado de antemano
como *«refuta el mecanismo entero: si el pool propio explicaba el cero, quitarlo
no puede reducir el efecto»*.

Así que el mecanismo del pool compartido **queda refutado por su propio
criterio**, y sólo se puede decir porque estaba escrito antes. Lo que queda del
mecanismo es una explicación estructuralmente fundada de por qué el efecto es
pequeño —las vistas por aspecto son índices sobre un pool unificado— **no una
predicción confirmada**, y no debe leerse como tal.

### El veredicto

    exclude_self_neighbour = true     por correccion, no por puntuacion
    aspect_separated_knn   = false    sin efecto de tamaño util, en los dos
                                      regimenes y las dos variantes

Y un hallazgo lateral que nadie predijo: **las dos perillas no interactúan.** La
contaminación por auto-recuperación vale hasta 0,087 y quitarla no libera ningún
efecto de aspecto.

### Lo que hubo que arreglar para poder medirlo

- **PROTEA #943.** El camino unificado pedía `k+1` y descartaba la propia
  proteína **por accession**, mientras el método descarta **por secuencia**, así
  que alcanzaba posiciones que el pre-search había recortado. Todos los brazos
  `exclude_self_neighbour=true` morían con `SequenceIdentityMissingError`.
- **El marco, declarado en el despacho.** `compare_paired_panels` rehúsa comparar
  filas que no declaren `frame` y `temporal_window`, y ninguna de las 110
  evaluaciones de la campaña los llevaba: son campos de payload que nadie pasaba.
  Las doce del eje C se re-evaluaron con `frame=internal` y
  `temporal_window=SELECT_220_227`.
- **La revisión, emparejada por medición.** La comparación de auto-exclusión era
  cruzada en revisión, porque el brazo `selfx=true` no podía existir en
  `5674c933` —ahí estaba roto—. Se re-predijo la celda base sobre `087fefeb` y se
  comprobó que reproduce: **117 de 117 métricas idénticas** en los tres sustratos
  y las dos variantes.


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

---

# El eje A, medido y leído (2026-09-07)

Trece sustratos × nueve celdas de decisión × dos variantes de propagación, 26
evaluaciones. Recuperación a K=200, coseno, numpy en CPU, auto-donación excluida
por identidad de secuencia; sin alineamientos, sin rasgos de reranker, sin
taxonomía. `experiment_run` **`70b1dec8`**, que supersede al voraz `f2a10398`.

## El resultado, en una frase

**El eje A separa dos grupos y no ordena dentro de ellos.** Nueve sustratos son
mutuamente indistinguibles; cuatro quedan por debajo con márgenes que superan a
los del grupo de cabeza en **dos órdenes de magnitud**.

## La medida que decide, y por qué no es `fmax_w`

`fmax_w` **no tiene error estándar definido**: es 2·pr·rc/(pr+rc) sobre dos
promedios calculados por separado y maximizado sobre τ, no una media de
puntuaciones por proteína. La fórmula `MDE = 2,8016·σ/√n` que el plan declara
(`RUTA.md:175`) no le aplica, ni siquiera con la σ correcta.

Y la σ declarada era la equivocada. **0,1157 es la más apretada de las nueve
medidas**, no la típica: la mediana es 0,2528 y el máximo 0,4051. El plan la cita
como «la sigma pareada medida», en singular. Con la dispersión que el propio
registro mide, **ninguna de las nueve celdas resuelve**, no dos.

La medida que sí decide es el **bootstrap pareado a nivel de proteína**
(`scripts/bootstrap_fmax_ci.py`): mejor F1 de cada proteína, índices emparejados
entre los dos brazos, remuestreo sobre las mismas proteínas. Tiene error
estándar porque es una media de algo.

## Lo que dice el bootstrap pareado (variante A, 200 remuestreos)

```
                                   NK                        LK                        PK
ankh_large vs protst    -0.0033 [-0.0048,-0.0015]  -0.0032 [-0.0045,-0.0016]  -0.0015 [-0.0018,-0.0013]
ankh_large vs prot_t5   -0.0017 [-0.0033,-0.0001]  -0.0012 [-0.0028,+0.0003]  -0.0010 [-0.0013,-0.0008]
protst     vs prot_t5   +0.0016 [-0.0003,+0.0032]  +0.0020 [+0.0004,+0.0037]  +0.0005 [+0.0003,+0.0008]
protst     vs rung2-dense +0.0006 [-0.0010,+0.0021]                           +0.0014 [+0.0011,+0.0017]
rung2-residue vs esm2_650m +0.0710 [+0.0678,+0.0740]                          +0.0182 [+0.0176,+0.0188]
ankh_large vs esm2_8m   +0.0749 [+0.0718,+0.0781]
```

Orden transitivo y coherente: **`protst` > `prot_t5` > `ankh_large`**, los tres
indistinguibles de `rung2-dense`, y todos ellos muy por encima de la cola.

**Y ahí está la escala del asunto**: los deltas del grupo de cabeza van de 0,0005
a 0,0033; el salto a la cola es **+0,0710**. Ciento cuarenta veces mayor.

## La advertencia metodológica, que vale para todos los ejes

**El orden del grupo de cabeza depende de qué estadístico se elija.** Con
`fmax_w`, `ankh_large` encabeza siete de nueve celdas. Con el mejor F1 pareado
por proteína, `protst` lo bate en las tres categorías con el intervalo excluyendo
el cero.

Los dos **coinciden donde hay señal** —la cola se separa igual bajo ambos— y
**discrepan donde no la hay**, que es justo donde el eje pretendía decidir. Una
configuración puede ganar la curva agregada y perder proteína a proteína: pasa
cuando acierta muy bien en unas pocas y algo peor en muchas.

Elegir estadístico es, por tanto, un campo del marco que nadie declaró. Va al
sello.

## Cuatro afirmaciones que se publicaron mal y quedan retiradas

1. **«Las dos variantes dan orden idéntico, B uniformemente +0,02».** Falsa en
   sus dos mitades. NK+LK se mueve **+0,00039** de media (rango −0,0026 a
   +0,0024) y PK **+0,05067** (rango +0,0106 a +0,0705): un factor **130** entre
   estratos, no un desplazamiento uniforme. **25 de 117 celdas bajan** en B,
   todas en NK/LK. Y el orden es idéntico en **3 de 9 celdas**, no en nueve.
   La causa está en `variantes.txt`: la cohorte de PK cae de 19.836 a 9.768
   proteínas, **−50,8 %**, contra −0,4 % en NK y −0,8 % en LK. **A y B no miden
   la misma cantidad en PK**, así que el «+0,02» es un cambio de denominador
   presentado como robustez.
2. **«`protst` queda por debajo del líder en 2 de 9 celdas».** Son **3 de 9**, y
   `prot_t5` también 3. El orden 0/2/3 colapsa a 0/3/3: no son separables.
3. **«La familia esm2 está invertida por tamaño».** No lo está: 8M → 650M sube
   **+0,0288 con el tamaño**, y sólo el 3B rompe. La forma es no monótona con
   pico en 650M.
4. **«La posición ordena, casi exacto».** Pearson +0,747 pero **Spearman +0,599
   y 22 de 78 pares invertidos**. Y la prueba directa: elegir por máxima
   distancia da `rung2-residue`, que pierde contra el líder de cada celda por
   0,0086 a 0,0404 — **de forma resoluble en 9 de 9 celdas**, más de las que el
   eje entero consigue decidir. Lo único que la geometría sostiene es un umbral
   en d ≈ 0,20 que parte los trece sin error, y está confundido con familia.

## Lo que sí se sostiene

- `ankh_base@d79` es el suelo con **0,0784** frente a **0,2864** de su propia
  capa final: caída de **0,2080**, el coste medido del colapso direccional.
- La familia esm2 se separa del grupo de cabeza en **36 de 36 huecos** por
  encima del MDE, en las dos variantes.
- El líder se separa del suelo declarado (`esm2_8m`) por encima del MDE en
  **9 de 9 celdas**, y el bootstrap lo confirma: **+0,0749 [+0,0718, +0,0781]**.

## El veredicto, bajo la regla del propio plan

`PLAN-EXPERIMENTAL.md` § 5: sella si un nivel gana en mayoría de las nueve celdas
con fuerza `measured`. **No ocurre. El eje A queda ABIERTO: no sella y no se
convierte en suelo.**

Y eso contesta qué se arrastra al eje B: **ni uno ni nueve.** El eje A no ha
elegido representación, ha descartado cuatro. Se lleva un **haz de tres**
—`protst`, `prot_t5`, `ankh_large`— que son los que el pareado sitúa arriba, y
el eje B decide entre ellos si puede.

## Lo que el eje A no dice

Nada sobre profundidad, regla de corte, política de donante, métrica ni
agregación de votos: todo eso quedó quieto. El tensor a K=200 está materializado
y **el censo del libro mayor da cobertura 100 %** (10.423.562 de 10.423.562 con
`sequence_rank` y `donor_count` en `ankh_large`), así que `_depth_unit_guard` no
bloqueará y los cortes del eje B salen de él sin recuperar de nuevo.

---

# El eje B, medido: dos monotonías hacia bordes opuestos (2026-09-07)

Haz de tres —`protst`, `prot_t5`, `ankh_large`— por siete profundidades
{1,2,3,5,10,20,30,200} por dos variantes. Los cortes salen del tensor a K=200 sin
recuperar de nuevo, así que **las siete profundidades se comparan sobre
exactamente la misma población**. `experiment_run` **`bbb96a35`**.

## Con `fmax_w`: menos es mejor, monótono, sin óptimo interior

```
sustrato        K=2      K=3      K=5      K=10     K=20     K=30     K=200
ankh_large    0.3800   0.3680   0.3523   0.3358   0.3249   0.3198   0.2953
prot_t5       0.3791   0.3676   0.3526   0.3347   0.3224   0.3158   0.2892
protst        0.3818   0.3701   0.3527   0.3378   0.3250   0.3180   0.2909
```

Y **no es el artefacto de «predice menos»**, que era la sospecha obvia. Si lo
fuera, la profundidad corta tendría más precisión y menos recall. Ocurre lo
contrario: K=2 gana **en las dos**.

```
K      cobertura   precision_w   recall_w   cob_en_tau     tau
2       0.9337       0.2319       0.4376      0.9101      0.833
30      0.9968       0.1783       0.3112      0.7639      0.971
200     0.9994       0.1619       0.2568      0.7714      0.970
```

Añadir vecinos **empeora el recall**, y `tau` sube de 0,833 a 0,970: con 200
donantes hay que subir el listón de confianza para filtrar ruido, y aun así se
pierde. La cobertura baja un 6 % en K=2, en contra del resultado y no a favor.

## Con el bootstrap pareado: más es mejor, monótono, sin óptimo interior

El estadístico que decide (§ regla corregida en `PLAN-EXPERIMENTAL.md`) dice lo
contrario, y con los cinco intervalos excluyendo el cero:

```
protst, NK               Δ = A − B         IC 95%
  K1  vs K2            -0.0123   [-0.0136, -0.0106]      K2  mejor
  K2  vs K3            -0.0063   [-0.0076, -0.0051]      K3  mejor
  K3  vs K5            -0.0069   [-0.0080, -0.0059]      K5  mejor
  K20 vs K30           -0.0019   [-0.0025, -0.0012]      K30 mejor
  K30 vs K200          -0.0033   [-0.0039, -0.0027]      K200 mejor
```

Idéntico signo en PK. Los tamaños decrecen —0,0123 → 0,0063 → 0,0069 → 0,0019 →
0,0033— así que **hay saturación pero no reversión**: cada vecino sigue ayudando,
cada vez menos, y **la curva no se dobla dentro del rango medido**.

## El mecanismo, que explica la discrepancia y una nota vieja del registro

`fmax_w` maximiza una **curva agregada** sobre un umbral: con pocos vecinos las
predicciones son escasas y confiadas, y la curva sale favorecida. El pareado da a
cada proteína **su propio mejor F1**: más vecinos son más oportunidades de que
los términos verdaderos de esa proteína concreta estén presentes.

**`fmax_w` premia predecir poco y seguro; el pareado premia cubrir a cada
proteína.** No son dos formas de medir lo mismo.

Y explica de golpe la nota `protea-depth-is-monotone` del registro —«deeper is
worse en 70 de 72 series, el ganador siempre en el borde»—: **eso era `fmax_w`,
no la profundidad.** No había óptimo porque no se estaba midiendo lo que se creía.

## El K=30 por defecto no lo sostiene ninguno de los dos

Es peor que K=2 bajo `fmax_w` y peor que K=200 bajo el pareado. **Tierra de
nadie**, probablemente heredado de la convención CAFA sin que nadie lo midiera en
este marco. El tensor materializado a K=200 por eficiencia resulta ser, bajo el
estadístico que decide, **el mejor punto medido**.

---

# El hallazgo que abarca a los dos ejes

**La campaña ha medido dos ejes y en los dos el resultado ha dependido de una
elección de métrica que el marco no declaraba.**

```
eje A    fmax_w pone a ankh_large primero;  el pareado pone a protst
         y lo invierte en las tres categorías con el cero fuera del intervalo
eje B    fmax_w gana en K=2;  el pareado gana en K=200
         monotonías completas hacia bordes OPUESTOS
```

Los dos estadísticos **coinciden donde hay señal grande** —la cola del eje A se
separa igual bajo ambos, +0,0710— y **discrepan donde las diferencias son
pequeñas**, que es exactamente donde los ejes pretendían decidir.

Y sólo uno de los dos tiene error estándar: `fmax_w` no es una media de nada.

**Lo que esto fuerza, y es una decisión del investigador y no del dato: declarar
qué optimiza esta tesis.** Si el objetivo es la métrica agregada de CAFA, K bajo
y `ankh_large`. Si es acertar por proteína, K alto y `protst`. **No se pueden
tener las dos**, y hasta ahora el marco no obligaba a elegir.

Ese campo —el estadístico de decisión— entra en el sello, junto a los seis que ya
estaban. Dos números no son comparables si difieren en él, igual que si difieren
en el pivote o en la ventana.

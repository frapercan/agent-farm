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

> **Los UUID de esta tabla son pre-borrado y ya no existen.** La campaña se borró
> el 2026-09-14 y se recargó; los seis identificadores de esta sección y de las dos
> siguientes apuntan a filas que no están. Lo que *declaran* — pivote t0, nativo del
> viejo corregido, nativo del nuevo propio de 227, papel `valid` — sigue vigente y es
> lo que se ha vuelto a construir. Los identificadores vivos están en
> «La ventana reconstruida (2026-10-04)», al final.

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


### El determinismo entre máquinas: medido, arreglado y NO desplegado (2026-09-08)

El mismo brazo, la misma configuración y el mismo código, predicho dos veces,
dio **82 y −73 filas de diferencia sobre diez millones**. La causa no era el
código: cada trabajo reparte sus lotes entre las dos máquinas, OpenBLAS se
compila `DYNAMIC_ARCH` y elige micro-kernel y partición de hilos según la CPU,
así que `1 − Q@Rᵀ` reduce en otro orden en cada host. **838.885 filas llevaban
el mismo donante con distinta distancia**, cada delta un múltiplo exacto de
2⁻²⁴, hasta 13 ulps. Donde el corte de K cae en un empate, un ulp decide quién
entra.

**Impacto medido sobre el eje C: cero.** 117 de 117 métricas reproducen en los
tres sustratos y las dos variantes. La razón es aritmética y no estadística: las
filas que bailan están a distancia ≥ 0,100, o sea puntuación ≤ 0,95, y los
puntos de operación son τ = 0,98 y 0,99, que admiten distancia ≤ 0,04. Ninguna
entra en la matriz de confusión.

**Mitigado**: las dos máquinas fijan `OPENBLAS_CORETYPE=HASWELL` y 8 hilos, con
el techo escrito junto al pin — el valor debe ser ≤ el mínimo de CPUs lógicas de
las dos, hoy 12, porque `OPENBLAS_NUM_THREADS` es una petición que se recorta y
pedir 16 da 16 aquí y 12 allí. Medido: a 16 hilos las huellas difieren, a 1, 4 y
8 son idénticas byte a byte, y **con versiones distintas de numpy en cada
máquina**, lo que descarta la versión como causa.

**Arreglado de verdad** en `protea-method#64`: acumular el producto escalar en
`float64` por bloques de referencia. Da los mismos bytes en cuatro particiones de
hilos y dos CPUs. No es una reducción de probabilidad —que es lo que era el
redondeo a una rejilla, descartado con datos: el ruido llega a 7,75e-7 y un
bucket de 1e-6 es 1,29 veces eso— sino invariancia: la dispersión del `float64`
queda muy por debajo de la resolución del `float32`.

**Y NO está desplegado, por su coste, medido sobre un lote real:**

| sustrato | dim | recuperación antes | después | factor |
|---|---|---|---|---|
| protst | 512 | 9,2 s | 16,3 s | ×1,8 |
| prot_t5 | 1024 | 14,0 s | 33,1 s | ×2,4 |
| ankh_large | 1536 | 20,1 s | 67,4 s | ×3,4 |

Sobre un lote de 67,7 s, en `ankh_large` la recuperación pasa del 30 % al 100 %:
**el lote se iría a unos 115 s, un +70 %**. El factor crece con la dimensión,
coherente con una penalización de ancho de banda.

**La decisión, y su condición de revisión.** Queda en `develop`, medido y
disponible, sin desplegar. Se despliega **si y sólo si** un eje mide donde el
ruido puede entrar: fracción de votos, un τ por debajo de 0,95, o cualquier cosa
que consuma identidad de donante — el reranker, señaladamente, porque
`neighbor_min_distance` es igual a `distance` por construcción y hereda el mismo
ruido. Mientras los puntos de operación sigan en 0,98 y 0,99, el `float32` basta
y el 70 % no se paga.

**Lo que queda abierto y no se resuelve aquí.** El arreglo cubre sólo el backend
`numpy`. Las 53 predicciones almacenadas lo usan, pero `search_backend` viene por
defecto a `faiss` en cinco payloads de exportación y entrenamiento, así que una
exportación de dataset o una corrida de reranker cae en el camino no cubierto sin
que nadie lo elija. Por eso el arreglo avisa una vez por proceso en vez de
callarse. Y para `torch` no existe hoy una declaración a la que alinearse: el
lock declara `2.10.0+cpu`, las dos máquinas corren ruedas de GPU distintas
—`2.11.0+cu128` aquí, `2.12.0+cu130` en el nodo— y alinearse al lock sería
quedarse sin tarjeta. No es una divergencia que arreglar: falta la declaración.


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

---

## La ventana reconstruida (2026-10-04)

El borrado del 2026-09-14 se llevó las dos variantes. Reconstruidas por la
plataforma (`POST /v1/jobs`, `generate_evaluation_set`), con la declaración de
arriba intacta y los identificadores de la campaña limpia:

| campo | valor vivo |
|---|---|
| conjunto viejo | `ba9f57f7-daaf-4ade-9966-0c7b95bb9c2d` — GOA 220 |
| conjunto nuevo | `b16ce3db-39c3-4b81-99dd-560a0f337ba6` — GOA 227 |
| pivote y nativo del viejo | `ac200ce9-21dd-4aab-92ec-f2309785161a` — `releases/2024-03-28` |
| nativo del nuevo (A) | `66a3dec2-bdd3-4dff-b20b-0ecc61e725ec` — `releases/2025-07-22` |
| conjunto de IA | `4346e676-0010-45a7-b994-d5f15ac156c0` |
| variante A | `fd0314d8` — job `49bddc8c` |
| variante B | `43b6b9e7` — job `11b084d8` |

**Los dos enlaces de ontología salieron ya correctos de la recarga**: 220 apunta a
`releases/2024-03-28` y 227 a `releases/2025-07-22`. La corrección del phantom gap no
hubo que repetirla.

### Reproduce el marco

| | declarado | reconstruido | diferencia |
|---|---|---|---|
| **A** proteínas NK / LK / PK | 2.413 / 2.585 / 19.836 | 2.415 / 2.585 / 19.837 | +2 / 0 / +1 |
| **A** delta proteínas | 23.736 | 23.739 | +3 |
| **A** retiradas | 426.385 | 426.443 | +58 |
| **B** proteínas NK / LK / PK | 2.404 / 2.564 / 9.768 | 2.406 / 2.564 / 9.768 | +2 / 0 / 0 |
| **B** delta proteínas | 13.753 | 13.755 | +2 |
| **B** retiradas | 115.436 | 115.443 | +7 |
| conocido en t0 (las dos) | 3.847.723 | 3.848.104 | +381 |

Las diferencias son de partes por diez mil y van todas en el mismo sentido: la
recarga trajo unas pocas filas más (el corpus 220 tiene ahora 5.317.938 anotaciones
frente a las 5.317.051 que registraba el marco). El invariante que el marco predecía
—`conocido en t0` **idéntico entre las dos variantes**— se cumple exactamente.

Las dos salen en modo `reconciled`. El defecto del primer intento de B, que guardó un
conjunto vacío con modo `same_snapshot` y sin error, no ha reaparecido.

### Qué sigue sin construirse

La ventana de competición `227 -> 230` continúa sin construir, por la misma razón de
antes: se construye cuando haya una decisión que defender, con el waiver declarado, y
una sola vez.

---

# El tercer reinicio, y la regla que lo evita la próxima vez (2026-10-05)

## La regla

**Los conjuntos se declaran después de extraer y comprobar, nunca antes.**

Esta campaña ha reiniciado tres veces. Las dos primeras por datos corruptos. La
tercera por algo peor: el corpus estaba bien cargado y era el **alcance** lo que
estaba mal, y lo estaba desde el primer día sin que nada lo dijera.

## Qué pasó

El universo de proteínas de toda la campaña limpia salió de un
`"search_criteria": "reviewed:true"` dentro de un payload de `insert_proteins`
del 2026-09-15. Eso no es una declaración: es un campo de un payload. No estaba
en este fichero, ni en un ADR, ni en el informe.

`load_goa_annotations` guarda una anotación solo si su accesión ya está en
`protein` —`protein_go_annotation.protein_accession` es una FOREIGN KEY— y
descarta el resto en silencio. Así que ese campo, sin discutirse, decidió el
alcance de todo.

Medido el 2026-10-05 contra UniProtKB con los trece códigos de lafa:

    reviewed    93.526
    total      149.774

Unas **56.000 proteínas con etiquetas experimentales curadas** fuera del corpus.
Salió a la luz al comparar con la tabla publicada de FANTASIA: 127.546 donde
nosotros decíamos 88.205.

## Por qué la regla es ésta y no "revisar mejor los payloads"

Porque el defecto no fue un descuido al escribir el payload. Fue **declarar el
conjunto antes de haber mirado los datos**. En septiembre no sabíamos que la
serie tiene 75 ficheros y no 71, ni que empieza en la 156 y no en la 160, ni que
la unión de accesiones fiables sobre tres releases ya supera en 46.390 a la
consulta de hoy. Ninguna de esas tres cosas se puede saber sin leer los GAF.

Un conjunto declarado antes de la extracción es una hipótesis disfrazada de
constante. El orden correcto es: extraer todo, comprobar todo, y entonces
declarar — y lo declarado queda aquí, no en un payload.

## El universo, ahora declarado

**Tres niveles de admisión sobre la serie entera, de cualquier taxonomía.**
Enumerados, nunca un complemento. La versión vigente es la de abajo, «El
criterio son cuatro niveles (2026-10-06)», que es también ADR-D49 en PROTEA;
aquí queda lo que no cambia con el nivel:

- **El criterio de la VERDAD es uno solo y no se toca**: los trece códigos de
  lafa, el nivel `truth`. Una proteína se puntúa contra su verdad.
- **El principio que ordena los niveles**: se admite una proteína por evidencia
  que sea una medición sobre esa proteína, o porque una base curada diga que
  revisó la entrada. Todo lo excluido falla las dos cosas.
- El banco de donantes **no queda fijado por esto**:
  `donor_policy.evidence_codes` es una lista arbitraria que se filtra en la
  consulta del banco, así que el nivel se elige al analizar. El **coste de
  embedding no es recuperable así**: toda proteína admitida con secuencia se
  embebe una vez.
- Las filas `NOT` cuentan. Un NOT es conocimiento curado y escaso, y
  `_reconcile_not_side` ya lo propaga y lo resta. Una proteína cuya única
  anotación fiable es un NOT pertenece al universo.
- Las isoformas no se colapsan.
- El universo sale **de cada GAF**, no de una consulta a UniProt. Una consulta
  describe hoy; la campaña va de 2016 a 2026. Medido sobre tres releases (160,
  194, 235): la unión son **196.164** accesiones, **46.390 más** que la consulta
  de hoy, y la curva seguía subiendo.

Lo construye `extract_goa_universe` (PROTEA#989; antes `ensure_goa_universe`,
PROTEA#978). **Las 75 pasadas de universo van antes de la primera carga de
anotaciones**: intercalar por release truncaría la historia de toda proteína
admitida tarde.

### RETIRADA. El criterio pasó de fiable a curado (2026-10-05), y volvió el 2026-10-06

> Esta sección se conserva porque describe una decisión que se tomó, se ejecutó
> sobre 13 releases y se revirtió. Lo que afirma sobre el reparto por código
> sigue siendo medición válida; lo que propone como criterio, no. La reversión y
> sus razones están justo debajo.

La declaración anterior admitía al universo sólo las proteínas con alguna de las
trece evidencias de lafa. Eso mezclaba dos papeles que quieren criterios
opuestos:

- **Los objetivos** de evaluación quieren el criterio estricto. Una proteína se
  puntúa contra su verdad, y la verdad es `lafa`. Eso no se toca.
- **El banco** de donantes quiere el criterio amplio. Un donante no se puntúa:
  aporta vecindad. Excluirlo por tener «sólo» una evidencia curada de otro tipo
  no protege ninguna medición, nada más empobrece el banco.

La salida no es elegir uno. Es **admitir ancho y guardar `evidence_code` en cada
fila**, de modo que el nivel se escoge al analizar y no al cargar. Una proteína
admitida con `ISS` puede ser donante sin ser nunca objetivo, y la consulta que
construye los objetivos sigue filtrando por los trece.

Lo que cuesta, medido sobre la release 156 cacheada:

| criterio | proteínas en la 156 | unión con las reviewed de hoy |
|---|---|---|
| fiable (los 13) | 117.136 | 620.439 |
| curado (no IEA) | 554.328 | **1.002.048** |

El cambio de criterio añade **381.609 proteínas a la unión, sólo con la 156**.
Desglose de qué aporta cada código, contado en proteínas que no cubren ya los
trece:

| código | filas en la 156 | proteínas nuevas |
|---|---|---|
| `IBA` | 1.258.697 | 304.066 |
| `ND` | 229.481 | 93.835 |
| `ISS` | 267.549 | 36.035 |
| `ISM` | 27.267 | 11.509 |
| `ISO` | 93.721 | 5.117 |
| `ISA` | 13.181 | 4.330 |
| `RCA` | 6.254 | 3.347 |
| `NAS` | 27.196 | 1.746 |
| resto (`IGC`, `IKR`, `IRD`) | 845 | 279 |

Esa columna **no suma** el total: cada código se contó por separado frente a los
trece, así que una proteína que tiene `IBA` e `ISS` y nada más aparece en las dos
filas. Suma 460.264 contra las 437.192 reales de diferencia en la 156; el exceso
de 23.072 es el solape entre códigos. Las cifras que se comparan son las de la
tabla anterior, no las de esta.

**`IBA` entra, y es una decisión consciente**, no un descuido. Es el 80% de lo
que añade el cambio, y es el caso más débil: viene de PAINT, donde la curación
está en un nodo ancestral del árbol y la propagación al descendiente es
mecánica. Recomendé excluirlo. El investigador decidió admitirlo el 2026-10-05
(«está bien que dupliquemos el corpus»), y la razón que lo sostiene es la de
arriba: un donante no se puntúa, así que una evidencia propagada que resulte
pobre degrada la vecindad pero no contamina ninguna verdad. El coste real cae en
los embeddings, que se calculan por secuencia y se multiplican por las ocho
configuraciones de la etapa 1.

Queda **declarado y medible**: como `evidence_code` está en cada fila, la
pregunta «¿cambia algo si se quita `IBA`?» se responde después con una consulta,
sin recargar nada. Si alguna vez se responde, el resultado va aquí.

El campo que lo fija es `evidence_scope` de `ensure_goa_universe`, con dos
niveles: `curated` (el declarado) y `reliable` (los trece). **Por defecto vale
`curated`**, así que el valor declarado es el que sale sin pedirlo.

### La reversión de `curated` a `reliable` (2026-10-06)

El criterio vuelve a los **trece de lafa**. Lo que lo decidió no fue el coste:
fue que `curated` admite proteínas que no deberían entrar.

**El defecto del criterio.** `curated` admite por la **existencia** de una fila
no-`IEA`, nunca por si esa fila lleva información. Y resultó que la mayoría no la
lleva. Medido sobre la release 231, contra un universo de 2.055.075 proteínas:

| por qué estaba en el corpus | proteínas | % |
|---|---|---|
| Swiss-Prot (reviewed) | 621.257 | 30% |
| TrEMBL con evidencia curada real | ~157.889 | **8%** |
| TrEMBL **sólo por `IBA`** | 1.192.444 | **58%** |
| TrEMBL sólo por `ND` o `IBA`+`ND` | ~83.485 | 4% |

**Sólo el 8% era aquello para lo que se amplió.** El `IBA` sale de PAINT, donde
el curador anota un nodo ancestral y la anotación baja por el árbol
mecánicamente; su cuota sobre lo curado pasó del 52% en la 156 al **83% en la
231** en diez años.

**El caso que cerró la discusión fue `ND`.** Lo encontró el investigador, mirando
`A0A021WW64`: una proteína de *Drosophila* en el corpus con, literalmente,
**ninguna anotación**. Sus tres únicas filas en la release 156:

```
A0A021WW64  GO:0003674  GO_REF:0000015  ND  F   <- raíz de MFO
A0A021WW64  GO:0005575  GO_REF:0000015  ND  C   <- raíz de CCO
A0A021WW64  GO:0008150  GO_REF:0000015  ND  P   <- raíz de BPO
```

`ND` es cómo GO registra la **ausencia** de conocimiento, y sus filas están sobre
los tres términos **raíz**. La Information Accretion de una raíz es **cero por
construcción** —IA(t) = −log P(t | padres), y para una raíz P = 1—, así que un
donante sólo-`ND`:

- no aporta nada a una métrica pesada por IA, ni al numerador ni al denominador;
- pero **ocupa un hueco entre los k vecinos**.

Eso no es inerte: es dañino. El `IBA` al menos transfiere una etiqueta real
aunque redundante; el `ND` transfiere una tautología.

**El error, y de quién fue.** La anchura se justificó en
`_universe_sources.py` con esta frase:

> *«`ND` records that a curator looked and found nothing. **Both are curated
> information** and neither is a measurement on the protein in question, so they
> qualify a protein for the retrieval bank but never as evaluation truth.»*

«Both are curated information» es un **error de categoría**, y fue del asistente.
`ND` no es información curada sobre la proteína: es el registro formal de su
ausencia. Un curador la produjo, pero lo que produjo es un negativo.

El mismo comentario remata con *«the tier is a choice made at analysis time»*. Eso
es cierto para las **anotaciones** y para la composición del banco —
`donor_policy.evidence_codes` acepta una lista arbitraria de códigos y filtra en
la consulta — y **falso para el coste de los embeddings**: una secuencia admitida
se embebe se use o no. La anchura se justificó con una recuperabilidad que sólo
valía para la mitad de la cuestión.

Y la fila `| ND | 229.481 | 93.835 |` estaba en la tabla por código de la sección
retirada, o sea delante del investigador cuando aprobó `curated`. Pero se
presentó con el foco en `IBA`, con una recomendación de excluir `IBA`, y **sin
ningún aviso sobre `ND`** — ni que significa «sin conocimiento», ni que sus
anotaciones son raíces, ni que la IA de una raíz es cero.

**Lo que arrastra la vuelta a los trece**, además de `IBA` y `ND`. En la 156,
proteínas que entraban sólo por cada código: `ISS` 36.035, `ISM` 11.509, `ISO`
5.117, `ISA` 4.330, `RCA` 3.347, `NAS` 1.746, `IGC` 172, `IKR` 97, `IRD` 10 —
**62.363 en total**. Caen por el mismo argumento de independencia: `ISS`, `ISO`,
`ISA` e `ISM` *son* inferencias por similitud, así que transferirlas por
similitud de embedding compone la misma señal consigo misma; `RCA` es análisis
computacional y `NAS` una afirmación no trazable.

**Lo que cuesta y lo que ahorra:**

| | `curated` | `reliable` |
|---|---|---|
| unión en la 156 | 1.002.048 | 620.439 |
| corpus final estimado | ~2,5 M secuencias | ~0,7-0,8 M |
| embeddings | 13-23 días de GPU | **5-9 días** |

**Y hubo que vaciar y rehacer.** Las 13 pasadas de 235 a 222 ya habían admitido
1,43 M de proteínas bajo `curated`. Seguir con el criterio nuevo habría dejado
235→222 definidas por una regla y 221→156 por otra, que es la forma exacta del
defecto de «la comparación de un solo campo que no lo era»: el universo dejaría
de estar definido por una regla. Así que `protein` y `sequence` se vaciaron y la
fase 1 se rehizo desde cero. Las mediciones de esas 13 pasadas se conservan en
`registro/pasadas-curated-2026-10-06.txt`, porque la curva de accesiones
irrecuperables por release —de 0,00% en la 235 a 112.360 filas en la 222— es
evidencia sobre GOA que sobrevive al cambio de criterio.

### El orden pasa a ascendente (2026-10-06)

La fase 1 recorre **156 → 235**, no al contrario.

La unión es la misma en cualquier orden, así que esto no es sobre qué acaba en el
corpus. Es sobre qué **significa** la pasada que admite. Ascendiendo, la pasada
que admite una proteína es la **primera release de la serie en que tuvo evidencia
fiable** — que es la cantidad de la que va el corpus, «las entradas que alguna
vez tuvieron anotaciones fiables», y que `date_created` **no** puede dar, porque
la fecha de creación de la entrada en UniProt no es cuándo se anotó. Descendiendo,
esa pasada era 235 para casi todo y por tanto no decía nada.

Y alinea el orden de construcción con la definición de verdad del proyecto, que
es **primera aparición** y no diferencia por pares.

**Lo que cuesta, declarado y no descubierto después.** Una ejecución parcial deja
de ser útil: la ventana de evaluación es 220→227, en el extremo nuevo, así que un
ascendente interrumpido deja 2016-2019 hecho y la ventana sin tocar. El
descendente la cubría en sus primeras quince pasadas. Se acepta porque `reliable`
abarata mucho una pasada —trae una fracción de las accesiones que traía
`curated`— y se espera cerrar la fase 1 de una vez.

También se pierde una alineación de caché: el descendente **terminaba** en los
ficheros con los que la fase 2 **empieza**, lo que dejaba un arranque gratis sobre
la mesa. Ahora las dos fases ascienden y no comparten frontera.

**Y nota sobre `first_release`:** sigue sin ser columna. Bajo descendente su
ausencia estaba justificada porque el valor habría sido inútil; esa justificación
ya no existe, y el valor queda sólo implícito en `created_at` contra las ventanas
de los jobs. Recuperable pero frágil. Añadir la columna es una decisión aparte.

### De dónde salen las reviewed, y cómo quedan fijadas (2026-10-05)

El paso de las reviewed actuales dejó de ser un recorrido por cursor contra la
API de UniProt. Lo es ahora una lectura de los ficheros planos del directorio de
release, y el motivo es que el recorrido no terminaba: UniProt lo estrangula de
forma creciente. Medido sobre el job que corría, 66 registros/s en las primeras
50 páginas, 17 en las 30 siguientes y unos 4 hacia la página 80, lo que dejaba el
recorrido completo entre 10 y 44 horas. Se canceló por la plataforma.

Los dos ficheros son la misma consulta materializada, y eso está **comprobado,
no supuesto**: `uniprot_sprot.fasta.gz` trae 575.748 entradas canónicas, que es
exactamente el recuento de `reviewed:true` medido por separado contra la API.
Con su compañero `_varsplic` son 617.103 registros (575.748 canónicas más 41.355
isoformas) en 22,5 segundos y dos peticiones HTTP.

| fichero | registros | md5 |
|---|---|---|
| `uniprot_sprot.fasta.gz` | 575.748 | `bc9d398533e6df582b563c6c03093bd0` |
| `uniprot_sprot_varsplic.fasta.gz` | 41.355 | `89523edbab859c132949bb25dd91b4eb` |

Los dos md5 coinciden con los publicados en el `RELEASE.metalink` del
directorio, y **van al log del job**. Hacen falta ahí porque
`previous_releases` no publica la release vigente (comprobado: 404 para
`release-2026_03`), así que hoy `current_release` es la única ruta y una URL que
se mueve no fija los bytes. La release leída es **2026_03**.

Lo trae `insert_proteins` con `release_fasta_urls` (PROTEA#986,
protea-sources#36).

### La serie son 802 GB, no 247, y eso decide el cache (2026-10-05)

La fase 1 guardaba los 75 GAF para que la fase 2 los reusara, apoyándose en una
cifra escrita en el driver: «the whole series is 247 GB against 654 GB free».
**Esa cifra está mal por 3,2x.** Medido con `HEAD` sobre las 75 releases:

| | |
|---|---|
| serie completa | **802,1 GB** |
| release más pequeña | 156, con 3,3 GB |
| release más grande | **202, con 24,28 GB** |
| libre en el disco | **661,9 GB** |
| ya en caché | 40,8 GB |
| disponible contando el caché liberable | 702,7 GB |
| **faltan** | **99,4 GB** |

Guardándolas todas, el disco se llena **bajando la release 182, la pasada 49 de
las 75**, unas **2,6 días** después de arrancar al ritmo medido de 9,6 MB/s. Y no
es una parada limpia: Postgres vive en el mismo sistema de ficheros, así que
llegar a cero es un PANIC de WAL en la base de la propia campaña.

Así que cada GAF se borra tras su pasada, igual que hace la fase 2. El pico de
disco de la fase 1 pasa a ser **una** release; el de la fase 2 es **44,8 GB**,
porque allí `MAX_IN_FLIGHT = 2` y el peor par adyacente es 225+226.

Consecuencia aceptada: cada release se baja **dos veces** entre las dos fases. Es
el suelo del diseño de dos fases, no un desperdicio.

#### El crecimiento de la base no es la restricción, medido

El cálculo original de disco ignoró la base de datos entera. Se midió contra
`protea_old`, que tiene las anotaciones de la campaña anterior: **379.462.116
filas en 120,1 GB = 316,6 B/fila** (147,2 de tabla, 169,3 de índices, TOAST
vacío). La clave única nueva de seis columnas es ~30 B/fila más ancha y además
deja sobrevivir más filas, así que 316,6 es cota baja.

Y una premisa del cálculo era falsa: **las filas por release no crecen con el
tamaño del fichero.** Medido en la campaña anterior, entre 4,74 M y 6,15 M por
release (media 5,34 M) mientras el GAF pasaba de 3,7 a 11,7 GB. El GAF crece por
especies que no están en el universo.

Proyección para `protein_go_annotation`: entre **180 GB** (600 M filas) y
**399 GB** (1.050 M filas). Es mucho, pero con el GAF borrándose sobra margen:
**+219 GB en el caso alto**. No hace falta soltar `protea_old`; soltarlo tampoco
permitiría guardar la serie entera, porque 802 + 180 + el resto se va de los
1.005,9 GB del disco.

#### Por qué un caché filtrado no sirve, medido

La idea obvia es guardar un filtrado en vez del bruto. No funciona, y queda
medido para que no se reintente.

El filtro a evaluar es el **útil**, no el ingenuo: el reviewed se conoce antes de
arrancar, así que durante la pasada se puede aplicar
`F = reviewed ∪ {curadas en esta release}`. Medido sobre la 156 con dos pasadas
por el fichero, contra un universo de 1.639.103 miembros:

| | filas |
|---|---|
| del universo en la 156 | 10.411.162 |
| cubiertas por el reviewed | 7.442.575 (71,5%) |
| cubiertas por las curadas de la 156 | 1.146.797 (11,0%) |
| **perdidas** | **1.821.790 (17,5%)**, en 305.949 accesiones |

El fichero filtrado serían 11.443.265 filas, el **4,07%** del original.

Así que la pérdida es **17,5%**, no los dos tercios que dijo una primera medición
mal planteada —ésa evaluó «curado en esta release» a secas, olvidando que el
reviewed ya se conoce—. Pero 17,5% no es 0, y aquí hace falta 0.

La razón de que haga falta 0: **la fase 2 no filtra por evidencia.** El predicado
`accept` del plugin sólo se pasa en la fase 1 (`ensure_goa_universe.py:434`),
nunca en `load_goa_annotations.py:648`. Los únicos filtros de la fase 2 son que
el accession esté en `protein` y que el GO esté en el snapshot. Así que toda fila
IEA de un miembro del universo se guarda, y el filtro las tiraría.

Y el 17,5% es un **suelo**: se midió con una sola release procesada, y a medias.
El universo es una unión sobre las 75 y sólo crece, así que cada accession que
entre después añade filas perdidas. Como la fase 1 desciende, las primeras
pasadas son las que se filtrarían con el universo más vacío, y son justo la
ventana 220→227.

El filtro **seguro** —accession en el universo completo— sí deja poco, unos 23 GB
para la serie entera. Pero sólo se conoce cuando la fase 1 termina, y releer cada
bruto para aplicarlo ya es la segunda descarga: no ahorra nada frente a borrar.

#### Lo que queda sobre la mesa, y a propósito sin hacer

La fase 1 desciende (235→156) y la fase 2 asciende (156→235, `pending` conserva
el orden de `parse_plan`). O sea que **la fase 1 termina justo en los ficheros
con los que la fase 2 empieza.** Conservar los más viejos en vez de borrarlos le
daría a la fase 2 un arranque gratis, y es seguro porque los viejos son los
pequeños (3,3 GB la 156) y a esas alturas el disco de la fase 1 está vacío.

Se deja fuera a propósito: el ahorro es una fracción de la descarga de la fase 2,
el umbral hay que calcularlo contra los 180–400 GB que se llevará
`protein_go_annotation`, y equivocarse en esa aritmética llena el disco, que es
justo el fallo que se está arreglando. Se añade con su propia medición antes de
que empiece la fase 2, no de propina.

## Qué lleva de verdad la base nueva

La campaña anterior se guardó como `protea_old` (120 GB) y se puso una `protea`
nueva en producción con el mismo nombre. **No es una base vacía.** Medido:

| tabla | filas | qué es |
|---|---|---|
| `go_term` | 3.029.397 | de los 64 snapshots, reales y reaprovechables |
| `protein` | 617.103 | el universo reviewed, **copiado** de `protea_old` |
| `sequence` | 528.600 | sus secuencias |
| `annotation_set` | 71 | **cascarones vacíos**, releases 160–235 |
| `ontology_snapshot` | 64 | reales |
| `embedding_config` | 8 | las ocho de la etapa 1 |
| `job` | **0** | nada de lo anterior tiene job detrás |

El md5 del conjunto de accesiones de `protein` es **idéntico** al de
`protea_old`, y su `created_at` es el del `insert_proteins` del 2026-09-15.

**Esas filas se vacían, y la razón es la regla de esta sección.** La redacción
anterior de este párrafo decía que arrancar con las reviewed «es lo declarado
arriba». Era un error de lectura: la declaración describe la **composición** del
universo, y eso no es permiso para heredar filas que casualmente coinciden. La
procedencia forma parte de la declaración. Con 617.103 filas copiadas y sin job,
la pregunta «¿cuál era el corpus en la release 156?» no tiene respuesta —no se
puede decir cuándo entró cada proteína— y entonces ningún número se puede leer
frente a los leakages.

Así que el orden es:

1. `protein` y `sequence` vacías. Sus dependientes
   (`protein_go_annotation`, `interpro_annotation`, `sequence_embedding`,
   `query_set_entry`) están todos a cero, de modo que el borrado no arrastra nada.
2. Las 75 pasadas de `ensure_goa_universe` construyen el universo desde los GAF.
   **Cada proteína entra con un job que dice qué release la admitió**, y eso es lo
   que hace legible cualquier corte temporal posterior.
3. Las reviewed actuales, si se quieren, son **un paso declarado aparte y
   posterior**, con su propio job. No una herencia.

Consecuencia inmediata para las cifras del dry run de la 156: `already_present`
pasa de 72.445 a 0 y `missing` de 44.691 a 117.136, que es el conjunto fiable
completo de esa release.

**Y el denominador queda resuelto**: 617.103 total = 575.748 canónicas + 41.355
isoformas. Son las dos cifras que se venían usando sin distinguir, y el informe
publicado usa la primera donde debía usar la segunda.

## La ventana reconstruida el 2026-10-04 también está muerta

Se reconstruyó un día antes del reinicio. De sus identificadores:

| objeto | estado |
|---|---|
| snapshots `ac200ce9`, `66a3dec2` | **vivos**, mismos ids, con sus términos |
| conjuntos de anotación `ba9f57f7` (220), `b16ce3db` (227) | **cascarones**, 0 filas |
| conjunto de IA `4346e676` | **no está** |
| variantes `fd0314d8` (A) y `43b6b9e7` (B) | **no están** |

Así que la tabla «La ventana reconstruida (2026-10-04)» de más arriba describe
objetos que ya no existen, igual que le pasó a la tabla de la ventana original.
Lo que esas tablas **declaran** sigue vigente; sus identificadores, no.

Hay además una razón independiente para rehacer las dos variantes: PROTEA#976
cambió la verdad de MFO (la regla del binding), así que las cuentas de las
variantes de antes ya no reproducían de todos modos.

## Lo que estuvo bloqueado por las claves, y ya no (resuelto 2026-10-05)

La base nueva tiene **0 claves de API**; `protea_old` tiene las dos. Las rutas
con `require_role(ROLE_OPERATOR)` —entre ellas `POST /v1/annotations/sets/load-goa`
y el borrado de conjuntos— responden 401. Hasta que las dos claves vuelvan a
existir en `protea`, la plataforma no puede despachar nada, y por tanto la fase 1
no puede empezar. Las dos plantillas siguen en `~/.secrets/`, así que restaurar
las filas conserva también la clave que ya tiene el sobremesa.

**Resuelto el 2026-10-05**: las dos filas de `api_key` se restauraron desde
`protea_old` y la plataforma despacha. La clave del sobremesa se conservó, así
que el nodo sigue uniéndose a la cola sin tocarlo.

# El criterio son cuatro niveles, y las secuencias llegan al final (2026-10-06)

Esto **sustituye** a `evidence_scope: "reliable"` y a la reversión que lo
instauró ese mismo día. El registro de decisión es **ADR-D49** en PROTEA
(`docs/source/adr/D49-corpus-is-four-tiers-of-the-gaf-series.rst`), que lleva
todas las mediciones; aquí queda lo que el driver declara y lo que hay que hacer
antes de arrancar.

## Por qué `reliable` no bastaba, aunque fuera más estrecho que `curated`

`reliable` era **un complemento**: todo lo que no es IEA. Un complemento admite
lo que GO invente después sin que nadie lo decida, y ya había admitido dos
familias que nadie eligió:

- **`IBA` / `IBD`** vienen de PAINT: un curador anota un nodo ancestral y la
  anotación se propaga mecánicamente. Hay persona, pero no mirando a esta
  proteína, y la etiqueta es por construcción el consenso de su familia. **58%**
  del universo entraba sólo por `IBA`, y su parte de la anotación curada subió
  del 52% en la GOA 156 al 83% en la 231. Es justo la cantidad contra la que un
  método de vecinos debería evaluarse, no de la que debería aprender.
- **`ND`** es cómo GO registra que un curador miró y no encontró nada. Sus filas
  están sobre los tres términos **raíz**, y IA(v) = −log2 P(v | padres(v)) hace
  que la Information Accretion de una raíz sea **cero por construcción**. Medido
  sobre la 156: **83.950** accesiones llevan sólo `ND`, y 83.949 de ellas tienen
  todas sus filas no-IEA sobre un término raíz. Como donante no aporta nada y
  ocupa un hueco entre los k vecinos: no es inerte, es dañino.

## Los niveles

| nivel | códigos | qué admite | medido en la GOA 156 |
|---|---|---|---|
| `truth` | los trece de lafa | una medición sobre ESTA proteína; el único nivel que la hace objetivo | **117.136** accesiones (69.927 Swiss-Prot, 47.209 TrEMBL) |
| `curated_inference` | `ISS ISO ISA ISM IGC RCA NAS IKR IRD` | el juicio de un curador sobre ESTA proteína, nunca verdad | **62.363** proteínas entran por éstos y por nada más |
| `swissprot_of_release` | ninguno; se lee del nombre de entrada | la entrada estaba revisada EN ESA RELEASE | **527.149** accesiones |
| *excluidos* | `IEA`, `IBA`, `IBD`, `ND` | cada uno por su razón, y no son intercambiables | |

La partición es **exacta**: 13 + 9 + 4 = 26, que son todos los códigos que conoce
el mapeo ECO. Así que un código desconocido es un código que GO añadió después de
escribir esto: se **cuenta y se rechaza**, y aparece en el resultado del job bajo
`codigos_desconocidos`.

**La familia `ISS` entra**, y no por engordar el corpus. Son inferencias de
ALINEAMIENTO revisadas por un curador, así que comparar una predicción por
vecindad de embeddings contra ellas prueba si una vecindad de embeddings captura
lo que captura el alineamiento curado, sin tocar la verdad que se puntúa.

## Swiss-Prot por release sale del propio GAF

UniProt nombra una entrada de TrEMBL `<accesión>_<ORGANISMO>` y una de Swiss-Prot
`<mnemónico>_<ORGANISMO>`, y la columna DB Object Synonym del GAF lleva el nombre
de entrada **de su propia release**. Así que `P12345_HUMAN` es TrEMBL y
`HLA_A_HUMAN` está revisada, y las dos formas son disjuntas por construcción.

Medido sobre la 156 (2016-11-01): la regla nombra **527.149** accesiones como
revisadas, contra **551.705** entradas en el tarball de Swiss-Prot 2016_07, un
déficit de 24.556 (**−4,45%**) que son entradas sin ninguna fila de anotación en
esa release. El déficit va en la dirección segura: la pertenencia no se inventa.

Esto elimina una descarga de 40 GB por release y el problema de emparejar
releases, para una columna que el fichero ya traía.

**Y mata el filtro por `reviewed` de hoy**: de la Swiss-Prot actual, **24.854
entradas (4,3%)** no estaban en Swiss-Prot en 2016. Filtrar una ventana temporal
por el estado de revisión de hoy las inyecta en el pasado.

## Las secuencias llegan al final, y por eso hay tres fases

Las anotaciones son **históricas** y hay que cargarlas release a release. Una
secuencia es una **propiedad de la proteína** y sólo la tiene el UniProt de hoy.
`protein.sequence_id` es nullable, así que una accesión puede ser miembro del
corpus antes de tener cadena, y `load_goa_annotations` filtra con
`select(Protein.accession)` a secas: no necesita ni una secuencia.

| fase | operación | qué hace |
|---|---|---|
| `--phase 1` | `extract_goa_universe` | 75 pasadas ascendentes, filas de sólo accesión, ninguna red más que el fichero |
| `--phase 2` | `load_goa_annotations` | las anotaciones de cada release contra su snapshot |
| `--phase 3` | `resolve_protein_sequences` | **un** job: secuencias, fechas de auditoría y fusiones, sobre toda fila sin secuencia |

Hacerlo por release le preguntaba a UniProt lo mismo hasta 75 veces y preguntaba
una y otra vez por accesiones que no sirve en absoluto: **34% de las peticiones**
en las diez pasadas que corrieron así.

Las anotaciones de una proteína cuya secuencia nunca llega **se quedan**: la
proteína participó en los deltas. Las consultas que necesitan cadena filtran por
`sequence_id IS NOT NULL`. Y lo que no se puede rescatar es ahora una **lista de
nombres** (`sin_resolver.txt` en el almacén de artefactos) y no un número: de 25
muestreadas, 25 son `entryType: "Inactive"` sin secuencia.

## La columna que el orden ascendente hace posible

`protein.first_admitted_release` (migración `f2a8c41d9e37`) guarda la release más
baja que admitió la accesión. **No** es el `first_release` que la migración
`e4b7a19c0f83` rechazó un día antes: aquél significaba *la release más antigua
que existía una vez existía la entrada*, es derivable de `date_created` contra
`annotation_set.source_published_at`, y sigue sin almacenarse.

Éste es el evento de **ganancia de conocimiento**, que es lo que mide la campaña.
Una proteína puede existir en UniProt desde 1998 y haber conseguido su primera
anotación experimental en 2019; `date_created` dice 1998 y no puede decir 2019. Y
para una proteína admitida **sólo** como entrada revisada de su release no es
derivable de nada: recuperarla costaría releer los 802 GB.

Se escribe como **mínimo** (`IS NULL OR > N`), así que el valor es la release más
temprana de verdad aunque la serie se procese desordenada, y una pasada repetida
no lo sube.

## Lo que hay que hacer ANTES de arrancar la fase 1

**Truncar `protein` y `sequence`.** Las 108.532 proteínas que hay ahora entraron
con una pasada de la release 156 bajo `reliable`, que admitía `IBA` y `ND`. Son un
superconjunto en la dirección equivocada: si se deja, el criterio declarado y el
corpus no coinciden, y la diferencia no la señala nada.

El resume de la fase 1 **no** se deja engañar por eso: `universe_done` sólo cuenta
pasadas de `extract_goa_universe` cuyo conjunto de niveles sea exactamente el
declarado, y ninguna pasada vieja lo es. La comparación es de **conjuntos** y se
hace en Python a propósito, porque `payload->'admit' = '[...]'::jsonb` es igualdad
ordenada de arrays y diría que los mismos tres niveles en otro orden son otro
criterio.

## Lo que esto no resuelve

- **La guarda del holdout.** Cargar las 75 releases disuelve la protección física
  que daba «la GOA 230 no está en la base». Los roles de ventana de ADR-D40 son la
  protección lógica; una guarda que se niegue a leer un conjunto de anotación del
  lado TEST no existe todavía.
- **`RELEASES` en `split_registry.py`** no lista estas releases, así que TRAIN no
  se puede nombrar hasta que las liste.
- **`embedding_config` está vacía** tras el reinicio: las ocho recetas de ADR-D48
  hay que volver a declararlas antes de calcular un solo embedding.
- **Los metadatos y la IA.** `fetch_uniprot_metadata` una vez, y
  `compute_information_accretion` con régimen `lafa` sobre el conjunto de
  anotación que se declare cuando la ventana esté construida. La IA es
  **invariante** a los niveles 2 y 3 justamente porque su `evidence_regime` es
  `lafa` por defecto.

## El censo de los 75 tamaños, medido (2026-10-06)

Hasta hoy estaban registrados el total y los dos extremos, pero no la tabla. Sin
ella no se puede calcular ninguna decisión de caché sin volver a preguntar a EBI.
Medido con `HEAD` sobre las 75, **75 de 75 sin un solo error**, y el total sale
**802,1 GB**: clava la cifra del 2026-10-05 medida por separado, así que las dos
mediciones se confirman entre ellas.

GB por release, en grupos de cinco:

| 156: 3.33 | 157: 3.42 | 158: 3.46 | 159: 3.53 | 160: 3.66 |
| 161: 3.76 | 162: 3.88 | 163: 4.06 | 164: 4.24 | 165: 4.47 |
| 166: 4.53 | 167: 4.65 | 168: 4.68 | 169: 4.80 | 170: 4.86 |
| 171: 5.04 | 172: 5.34 | 173: 5.53 | 174: 5.81 | 175: 5.94 |
| 176: 6.02 | 177: 6.16 | 178: 6.50 | 179: 6.34 | 180: 6.25 |
| 181: 6.41 | 182: 6.53 | 183: 6.75 | 184: 6.99 | 185: 7.12 |
| 186: 7.41 | 187: 7.26 | 188: 7.82 | 189: 7.94 | 190: 8.29 |
| 191: 8.16 | 192: 8.85 | 193: 8.85 | 194: 8.88 | 195: 8.83 |
| 196: 9.08 | 197: 9.08 | 198: 9.33 | 199: 9.99 | 200: 12.36 |
| 201: 13.28 | 202: 24.28 | 203: 13.75 | 204: 14.56 | 205: 16.59 |
| 211: 16.55 | 212: 16.66 | 213: 16.83 | 214: 17.39 | 215: 17.90 |
| 216: 17.86 | 217: 17.72 | 218: 18.06 | 219: 21.99 | 220: 20.44 |
| 221: 18.68 | 222: 20.27 | 223: 20.61 | 224: 20.96 | 225: 22.15 |
| 226: 22.65 | 227: 15.66 | 228: 16.93 | 229: 17.72 | 230: 15.44 |
| 231: 15.39 | 232: 10.83 | 233: 11.35 | 234: 11.66 | 235: 11.67 |

Lo que la tabla permite decidir sin volver a medir: con el suelo de 230 GB y 632
libres, la caché retiene ~435 GB, y **qué releases concretas se guarden es
irrelevante para el total** — los bytes ahorrados son exactamente los bytes
cacheados. Eso descarta cualquier política de evicción "más lista" (guardar las
grandes en vez de las pequeñas no ahorra ni un byte más) y descartó también una
run limpia desde la 156: simulada con estos tamaños, da 366 GB de re-descarga
contra 368 de seguir como estábamos, dos GB de diferencia, y cuesta re-escanear
ocho pasadas ya hechas.

## Corrección: dos afirmaciones mías sobre el coste de las dos fases (2026-10-06)

Las dejé escritas en el repositorio y las dos eran falsas.

**«Intercalar perdería el sujeto del experimento.»** Falso, y lo contrario es
demostrable. Bajo orden ascendente, si una proteína se admite en la release N es
porque en 156..N−1 no tenía **ninguna** evidencia admisible: ni código de verdad,
ni `curated_inference`, ni era Swiss-Prot. Si hubiera tenido un IDA en la 160 se
habría admitido en la 160. Luego las filas que intercalar perdería son
**exclusivamente IEA, IBA, IBD y ND**, y ni la evaluación (`_EXP_CODES` en
`protea/core/evaluation.py`) ni la IA (régimen `lafa`) las leen.

El argumento correcto para mantener las dos fases es otro, y es el que el
investigador señaló: mi demostración dice que la **evaluación** está a salvo, no
que el **corpus** esté completo, y el corpus es el activo. Intercalando,
`annotation_set(156)` deja de ser «GOA 156 restringido al corpus» y pasa a ser
«GOA 156 restringido al corpus conocido en 156»: un objeto distinto, incompleto
por el lado antiguo, y **no reparable sin volver a bajar los 802 GB**, porque la
información necesaria para filtrar la 156 correctamente no existe hasta haber
leído la 235.

**«Guardar los GAF ahorra 12,5 h.»** Falso. Ahorra 368 GB de tráfico y casi nada
de reloj: la segunda descarga se esconde detrás de las cargas de la fase 2, que
son 35 min por release contra 7 de descarga, y la fase 2 ya hace prefetch dentro
de su bucle. Sigue valiendo la pena por el ancho de banda y porque nos cubre un
día en que EBI vaya lento, pero no por el tiempo.

**Dónde sí había horas:** la fase 1 bajaba y escaneaba EN SERIE, 423 s + 390 s por
release cuando pueden solaparse. Son ~7,2 h sobre las 67 que quedan, y es el
mismo ahorro que prometía la pasada única, sin tocar la completitud de nada.

# El nivel Swiss-Prot sólo es derivable del GAF hasta la 178 (2026-10-06)

Esto **enmienda el alcance** del tercer nivel declarado en «El criterio son cuatro
niveles», y la enmienda la forzó un defecto, no una revisión.

## Lo que pasó

La release 179 estuvo **tres horas** en RUNNING cuando sus cuatro predecesoras
tardaron once minutos, con el worker en **7,3 GB** de RSS. Su evento `scanned`:

| | la 179 | las anteriores |
|---|---|---|
| filas leídas | 534.813.197 | ~280–300 M |
| **accesiones admisibles** | **7.639.329** | **~600.000** |

Doce veces de más. Llevaba 4 h 37 min en la fase de lectura y lo siguiente era
insertarlas. **Se paró sin escribir nada**: 0 filas con
`first_admitted_release=179`, 0 eventos de inserción.

## La causa, que es de GOA y no nuestra

GOA dejó de poner el nombre de entrada de UniProtKB primero en la columna DB
Object Synonym a partir de la release 179, y puso el **símbolo del gen**. La misma
fila, la misma proteína:

```
178:  A0A021WW32_DROME|vtd|80Fh|CG40222|DRAD21|...
179:  vtd|vtd|80Fh|CG40222|DRAD21|...
```

Y `A0A021WW32_DROME` **no aparece en ninguna otra columna** de esa fila:
desapareció del registro.

**Medido** sobre las releases en caché, fracción de filas con nombre de entrada
legible:

| releases | con nombre |
|---|---|
| 164–178 | **100%** |
| **179** | **0%** |
| **180** | **0%** |
| **231** | **5%** |

Son **52 de las 75** releases de la serie, **incluida la ventana de evaluación
220–227**.

## Por qué no se vio antes, que es la parte que hay que aprender

Dos cosas, y las dos son del mismo tipo:

1. **La regla concluía de una ausencia.** `not (nombre.startswith(accesión) ...)`:
   sin nombre de entrada, `'vtd'.startswith('A0A021WW32')` es falso y devolvía
   True para toda fila. Una regla que infiere de una ausencia **falla abierto**, y
   fallar abierto en el nivel que define el corpus es la peor dirección posible.
2. **La medición que lo justificó se tomó sobre la release 156** — 527.149
   revisadas, cero falsos positivos — que está en la mitad buena. La validación
   del dry run antes de arrancar, también sobre la 156, la única que había en
   caché. Se validó el camino feliz del extremo antiguo y se declaró general.

## La decisión: A + B

**A. Fallar cerrado donde el dato no existe.** `is_swissprot_entry` exige ahora
evidencia **positiva**: un nombre de entrada de UniProtKB es
`<MNEMÓNICO>_<ORGANISMO>`, lleva `_` y después del último va un código de
organismo en mayúsculas de tres o más. `moeA5`, `vtd` y `GA0070216_102329` —un
locus tag de la 231— no lo son. Si no tiene esa forma, la pregunta **no se puede
contestar** desde esa fila y la respuesta es «no», dejando la fila a su código de
evidencia.

Y se **declara por release**: `rows_entry_name_unreadable` entra en el informe del
job, y si pasa de la mitad de las filas la operación emite
`extract_goa_universe.swissprot_tier_unavailable` en warning. Sin eso el único
síntoma de una release sin nivel sería un recuento de admisibles más bajo de lo
esperado, que es exactamente lo que nadie mira. PROTEA#994.

**B. La Swiss-Prot actual como tercera fuente de admisión, declarada.** Para
156–178 el nivel sigue saliendo del GAF, fechado. Para 179–235 el hueco se cubre
sembrando la Swiss-Prot de hoy con `insert_proteins` sobre los ficheros planos de
release (22,5 s medidos, ver «UniProt: ficheros de release, no cursor»).

Lo que esto **no** es: un filtro de ventana. Sigue prohibido filtrar un corpus
temporal por el `reviewed` de hoy. Aquí se usa sólo para **admitir** al corpus, y
las anotaciones siguen fechadas por release, así que ninguna ventana se contamina.
Lo que se pierde es que **la pertenencia deja de estar fechada** en esa mitad: una
proteína sembrada por esta vía queda con `first_admitted_release` a NULL, que es
precisamente lo que significa «admitida por la fuente del presente y por ninguna
release».

**Por qué B y no la Swiss-Prot histórica:** ya está medido que los conjuntos
históricos aportan **cientos** sobre `reviewed de hoy ∪ la unión fiable`, a cambio
de ~90 GB y cuatro horas. Ver «`reviewed` es una instantánea de 2026».

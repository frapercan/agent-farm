# Plan de experimentación

Un folio. `RUTA.md` explica **por qué** cada decisión está donde está;
`MARCO-DECLARADO.md` guarda **las cifras ya medidas**. Esto es sólo el orden en
que se hacen las cosas, y la regla que se repite en cada paso.

La idea entera cabe en dos frases. **Un eje cada vez, sobre un marco que no se
mueve, leído en cada estrato.** El ganador de un eje se convierte en el suelo
del siguiente, y nada baja al holdout hasta el final.

---

## 1. Lo que está quieto

Seis campos sellan el marco. Dos números se comparan si y sólo si su digest
coincide; cualquier cambio en uno de estos seis crea un marco hermano, no una
fila más de la misma tabla.

| campo | valor |
|---|---|
| `temporal_window` | 220 → 227  (`2024-03-28` → `2025-07-22`) |
| `pivot_snapshot_id` | `6b78af68` — `releases/2024-03-28`, el grafo de t0 |
| `information_accretion_set_id` | `b5f134b1` — régimen `lafa`, 42.312 términos, `drop_rate 0.0` |
| `evaluation_set_id` | `b7cfed9a` (A, nativo por lado) y `b7452c0e` (B, grafo único) |
| `max_terms` | `None` |
| `max_distance` | `None` |

Población de consulta: `4951cdda` — **23.737 proteínas**, unión de las dos
variantes, sha256 `065aa458…f6f77fcc`.

Verdad = **anotaciones experimentales ganadas en la ventana**. IEA entra como
entrada (banco de donantes, rasgos, recuperación), nunca como verdad.

Y quieto también, porque no se ablaciona en esta campaña: `evidence_regime =
lafa`, `search_backend = numpy(CPU)`.

---

## 2. El bucle

Cada eje se ejecuta con los mismos cinco pasos. Sin excepciones: la disciplina
está en que el procedimiento no cambie de un eje a otro.

**1 · Declarar.** Antes de despachar nada, se escribe en `experiment_run.config`
el suelo que hereda, los niveles que van a variar, la **lista de lo que se queda
quieto**, y una hipótesis falsable en una frase. Lo que no está en la lista de
`held_still` es lo que se está midiendo; si algo se mueve sin estar declarado, el
eje no se puede leer.

**2 · Un brazo cronometrado.** Un solo nivel, entero, medido. Da el coste
unitario antes de comprometer los trece. Si el coste sale fuera de lo que cabe
en la máquina, el eje se replantea aquí y no después de tres días de cola.

**3 · Despachar el resto.** Todos los niveles, mismo marco, misma población.

**4 · Leer por estrato.** Sección 4.

**5 · Sellar.** El ganador pasa a ser el suelo del eje siguiente y se escribe en
`MARCO-DECLARADO.md` con su fuerza. Un eje que no sella no bloquea al siguiente:
se hereda el suelo anterior y se anota que ese eje quedó abierto.

---

## 3. Los ejes, en orden

El orden no es estético: cada eje hereda el suelo del anterior.

| # | Eje | Qué varía | Qué decide |
|---|---|---|---|
| **A** | Sustrato | 9 modelos preentrenados · el par de capas `ankh_base` [0] vs [10] · 3 sustratos aprendidos rung2. **Tres ejes, no trece niveles** | qué representación |
| **B** | Corte de la lista | profundidad {2,3,5,10,20,30} y la **regla** de corte | cuántos vecinos, y por qué criterio |
| **C** | Banco y donante | auto-donación on/off · `metric` coseno vs euclídea · `aspect_separated_knn` on/off | cómo se recupera |
| **D** | Rasgos | censo y corrección de lo que exporta el dataset | qué entra al reranker |
| **E** | Scoring | agregación de votos a puntuación | cómo un vecino se vuelve número |
| **F** | Reranker | modelo y rasgos | si reordenar gana |
| **G** | Two towers | generador de candidatos entrenado de cero | si un generador aprendido bate al KNN |
| **H** | Combinación y enrutado | política por estrato, validada cruzada | qué sistema para cada estrato |

**Suelo de arranque:** `esm2_8m`, K=30, cortes {2,3,5,10,20,30}, `held_still` =
`donor_policy=permissive`, `exclude_self_neighbour=true`,
`expand_votes_to_ancestors=false`, `aspect_separated_knn=true`, `metric=cosine`.
Ya escrito en `experiment_run` **`f2a10398`**, nodo `substrate`.

**Sobre B, que es el eje más interesante y el más fácil de estropear.** Un
`distance_threshold` global no vale, y está medido por qué: la escala de
distancia va de **0,0004** (`ankh_base@L10`) a **0,9037** (rung2-residue), un
factor de 2.250. Un mismo número corta trece cosas distintas. Lo que se
ablaciona en su lugar es la **regla**: cuantil de la propia distribución de cada
configuración, o corte relativo al primer vecino. La regla es comparable entre
configuraciones; el umbral absoluto no lo es.

---

## 4. Cómo se lee un resultado

**El ganador se busca en cada estrato.** No hay una tabla global con una fila
por nivel; hay un veredicto por celda, y cada veredicto lleva su propia fuerza.

Las **nueve celdas de decisión** (3 aspectos × 3 categorías CAFA) están todas
potenciadas. σ pareada medida = **0,1157**; MDE = 2,8016·σ/√n. La celda más
pequeña es CCO/LK con 821 proteínas y resuelve **Δ = 0,0113**; las nueve están
por debajo de 0,012. Es decir: una diferencia de 0,02 se ve en las nueve.

Tres mecanismos, en este orden:

1. **Veredicto por celda**, con su fuerza en la escala de siempre —
   `blocked → chosen/inherited → unpowered → chosen → measured`. Una celda sin
   potencia dice `unpowered`, no dice "empate".
2. **Encogimiento jerárquico.** Las celdas no se leen aisladas: una celda con
   pocos datos se estima hacia la media del aspecto. Evita que el ruido de una
   celda pequeña se lea como una preferencia.
3. **Enrutado validado cruzado.** Si el resultado es "cada estrato prefiere una
   cosa distinta", eso es una **política**, y una política ajustada y evaluada
   sobre la misma partición no vale. Se valida cruzada o no se declara. Es el
   fallo que ya vimos en la cascada de supervivientes: la canalización gana sobre
   ruido si la política no se cruza.

Y una advertencia que arrastramos: lo que se lee de la base está **redondeado a
1e-4**. "Idéntico" leído en base de datos es una cota superior, no un cero.

---

## 5. Cuándo se cierra un eje

- **Sella** si un nivel gana en mayoría de las nueve celdas con fuerza
  `measured`. Pasa a suelo.
- **Nulo declarado** si el panel está bien potenciado y no hay separación. Hoy no
  se puede escribir: falta el sexto valor de fuerza para un nulo con potencia.
  Instrumento pendiente.
- **Abierto** en cualquier otro caso: se anota `unpowered`, no sella, no se
  convierte en suelo, y el eje siguiente hereda el suelo anterior.

Nada se cierra por haberse quedado sin cola.

---

## 6. El holdout

**227 → 230 no se mira hasta el final** — y desde el 2026-09-04 eso no depende de
que nos aguantemos: **GOA 230 no está en la base.** Se borró teniendo cero
dependientes. Si el dato no está, no se puede mirar por accidente, ni por un
`select` distraído, ni por un job mal parametrizado.

Se recarga una sola vez, al final, con el sistema ya enrutado y con el suelo, para
dar la cifra que se publica. La receta, para que no haya que reconstruirla de
memoria:

| campo | valor |
|---|---|
| `gaf_url` | `https://ftp.ebi.ac.uk/pub/databases/GO/goa/old/UNIPROT/goa_uniprot_all.gaf.230.gz` (14,4 GB) |
| `source_version` | `230` |
| publicada | 2026-03-04 |
| `!go-version` del GAF | `releases/2026-03-01` |
| `ontology_snapshot_id` | `8924aec0` — `releases/2026-01-23`, la publicada más reciente ≤ la declarada |

No se usa para elegir nada, no se usa para diagnosticar. Volver a cargarla antes
de tiempo es la única forma de romper esta campaña, y ahora cuesta un acto
deliberado de 14,4 GB en vez de un descuido.

## 7. Lo único que bloquea hoy

GOA 220 (`cbb35a32`) está enlazada a `releases/2025-03-16`, once meses después de
su propia publicación. En evaluación se esquiva —el reconcile traduce por `go_id`
de texto— pero en predicción no: cada término predicho **sale** de una anotación
del donante, así que el grafo del banco es el grafo de los candidatos, y
`predict_go_terms` se niega. Correctamente.

### El criterio, leído del fichero

Cada GAF declara en su cabecera contra qué ontología se generó. Eso es un hecho,
no una estimación por cercanía de fechas:

| GAF | `!go-version` | publicada más reciente ≤ | enlazada hoy | |
|---|---|---|---|---|
| 220 | `releases/2024-04-13` | **`releases/2024-03-28`** | `releases/2025-03-16` | ✗ |
| 226 | `releases/2025-04-27` | `releases/2025-03-16` | `releases/2025-03-16` | ✓ |
| 227 | `releases/2025-08-31` | `releases/2025-07-22` | `releases/2025-07-22` | ✓ |
| 230 | `releases/2026-03-01` | `releases/2026-01-23` | `releases/2026-01-23` | ✓ |

Las cuatro versiones declaradas son builds de `go-plus` que GO **no archiva**
como release pública (`2024-04-13` y `2025-08-31` dan 404 en
`release.geneontology.org` y en el purl). De ahí la regla operativa: *la release
publicada más reciente igual o anterior a la que el GAF declara.*

Tres de cuatro ya la cumplen. **El pivote `2024-03-28` queda confirmado por la
vía buena** —lo obliga la cabecera de GAF 220, no una heurística— así que no hay
que cargar ninguna ontología nueva ni mover el marco.

### Por qué el contenido de 220 está bien y sólo la etiqueta está mal

Tres vías independientes:

1. 29.028/29.028 términos distintos de 220 existen en `releases/2024-03-28`.
2. **0** términos de `2024-03-28` faltan en `2025-03-16`: superconjunto estricto,
   así que la carga no pudo descartar nada. Importa porque el cargador **descarta
   en silencio** lo que no resuelve (`load_goa_annotations.py:442`).
3. El conjunto de IA `b5f134b1` ya está calculado **bajo `2024-03-28`** sobre el
   corpus 220, con `drop_rate_pct 0.0`. Y las dos evaluaciones se construyeron con
   `old_native_snapshot_id = 6b78af68`. Todo lo derivado ya lee 220 en la
   ontología correcta; sólo la columna `annotation_set.ontology_snapshot_id`
   discrepa.

Ambas rutas trabajan en espacio de `go_id` de texto y por eso cruzaron el
desajuste sin enterarse.

### Hecho el 2026-09-04

Las dos mitades están aplicadas.

`GOA 220` está enlazada a `releases/2024-03-28` y sus 5.317.051 anotaciones
re-expresadas en ese snapshot, cero fuera. Verificado dentro de la transacción, y
antes en un ensayo completo con rollback. **Ninguna cifra medida se movió**, que
era la predicción:

| | antes | después |
|---|---|---|
| IA `b5f134b1` | `drop_rate 0.0`, 30.533 términos con proteínas | idéntico |
| eval `b7cfed9a` | reconciled · 23.736 · 2.413/2.585/19.836 | idéntico |
| eval `b7452c0e` | reconciled · 13.753 · 2.404/2.564/9.768 | idéntico |
| encoders rung2 | 3 configs, 1.584.822 vectores | intactos |

El guardia vive en `protea/core/operations/_gaf_header.py`, integrado en
`load_goa_annotations`: lee `!go-version` con una petición `Range` de 64 KiB
antes de tocar la base, y rechaza una ontología posterior a la declarada. Se
niega también cuando la cabecera no se puede leer, salvo que el payload declare
`allow_unverified_ontology` — un guardia que pasa en silencio cuando no puede
comprobar no es un guardia. Verificado contra el fichero real: lee `2024-04-13`
de GAF 220 y rechaza `releases/2025-03-16`. También rechaza `2024-04-18`, que es
*más cercano en fecha* pero posterior: la cercanía no es la regla.

### La corrección, en dos mitades

**No es una operación registrada.** Corre una vez, sobre una fila, en esta
máquina: pagaría el coste entero del catálogo sin cobrar reintento, reparto ni
progreso. `scripts/` ya tiene seis `backfill_*` que son exactamente esta forma.

- `scripts/remap_annotation_set_ontology.py` — traduce `go_term_id` por `go_id`,
  reenlaza el conjunto, y verifica dentro de la transacción que el recuento sigue
  en 5.317.051 y que cero anotaciones apuntan fuera. Se niega si algún `go_id` no
  mapea, y se niega si el destino es posterior a lo que declara el GAF.
- **El guardia en `load_goa_annotations`** — esto sí es producto y es lo único
  que impide que se repita: leer `!go-version` de la cabecera del GAF y rechazar
  una ontología posterior a la declarada.

Reversible desde `backups/protea-20260902T122325-antes-del-reinicio.dump`.

Recargar 220 no es la alternativa limpia: no mejora la procedencia —el cargador
no escribe `job_id` en el `annotation_set`, los cuatro GOA lo tienen NULL— y
`RESTRICT` obliga a destruir antes los tres sustratos rung2, el conjunto de IA y
las dos variantes de evaluación, para corregir una etiqueta de una fila cuyo
contenido ya es correcto.

---

## 8. Sustrato retirado

Dos conjuntos borrados el **2026-09-04**, los dos con cero dependientes
`RESTRICT` y los dos presentes intactos en
`backups/protea-20260902T122325-antes-del-reinicio.dump`.

| GOA | anotaciones | por qué se va |
|---|---|---|
| 226 (`86e5de3e`) | 5.907.336 | no es extremo de ninguna ventana; sólo valdría para una comprobación de monotonía 220→226→227 que no está en el plan |
| 230 (`9a14f9cc`) | 4.771.370 | es el holdout: fuera de la base no se puede mirar (§ 6) |

`protein_go_annotation` pasa de 21.876.159 a **11.197.453** filas, que son
exactamente las dos que el plan usa:

| GAF | anotaciones | papel |
|---|---|---|
| 220 | 5.317.051 | inicio de la ventana de ajuste |
| 227 | 5.880.402 | fin de la ventana de ajuste |

**Lo que NO se borra, y por qué.** Recargar 220 y 227 desde cero se consideró y se
descartó con las cifras delante. 220 tiene tres encoders aprendidos rung2
entrenados sobre ella —que es el diseño correcto: el banco es el del inicio de
ventana— con **1.584.822 vectores** calculados en la GPU del nodo. `RESTRICT`
obliga a destruirlos antes. Y la recarga compra **cero corrección**: está probado
por tres vías que el contenido de 220 ya es idéntico al que produciría una carga
correcta (§ 7). El enlace de 227 ya es el que impone su cabecera. El margen de
error real no estaba en los datos sino en el cargador, que acepta cualquier
ontología sin comprobar nada — y eso se cierra con el guardia, no con 33,6 GB de
descarga.

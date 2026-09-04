# Auditoría del estado, y la nomenclatura que hace falta

Hecha el 2026-09-04, de lectura, contra la base viva y el árbol de PROTEA en
`fb9f766`. Ordenada por lo que cambia el trabajo, no por lo que impresiona.

---

## 1. Lo que se persiguió y resultó estar bien

Se anota porque un hallazgo descartado también es un resultado, y porque el coste
de volver a perseguirlo dentro de tres meses es el mismo.

**Isoformas inflando votos — no ocurre.** Hay 41.343 filas de isoforma con
embedding propio, y 22.777 accesiones con hasta **37 secuencias distintas**.
Parecía que un donante podía ocupar 37 huecos del top-K votando lo mismo. Pero
**cero anotaciones cuelgan de accesiones no canónicas**, y el banco se construye
desde `ref_data_by_aspect[aspect]["accessions"]`, que sale del conjunto de
anotaciones. Las isoformas no entran. Cero entradas del query set son isoformas.

**`exclude_self_neighbour` excluyendo de menos — no, y está mejor resuelto de lo
que parecía.** 1.702 proteínas de consulta (7,2%) tienen secuencia gemela bajo
otra accesión: donantes a distancia exactamente 0. La ruta viva usa
`protea_method._self_by_sequence.without_own_sequence`, que excluye **por
identidad de secuencia**, y `extra_neighbours_for` pide profundidad extra al
índice para que `limit_per_entry` siga significando donantes reales. El helper
`_self_neighbour.without_self`, que descarta por accesión, no es el camino que
corre.

---

## 2. `layer_indices` cuenta hacia atrás

`compute_embeddings.py:162` — **`[0]` es la ÚLTIMA capa, `[1]` la penúltima.**

De donde:

| nombre actual | `layer_indices` | lo que es de verdad |
|---|---|---|
| `ankh_base` | `[0]` | capa **final** de 48 |
| `ankh_base@L10` | `[10]` | **décima desde el final** — la 38 de 48 |

El segundo nombre lo puse en esta campaña y **dice lo contrario de lo que
significa**: se lee "capa 10" contando desde la entrada. El primero esconde la
capa entera. Un nivel nombra el eje y el otro lo invierte.

---

## 3. Los demás defectos de nomenclatura

- **`family` mezcla dos clases.** `ankh`/`esm2`/`esmc`/`t5`/`protst` son linajes
  de modelo; `learned-code`/`residue-sparse` son arquitecturas. Una columna, dos
  significados: hace falta separar `family` de `kind`.
- **`prot_t5` y `prostt5` comparten `family = t5`.** Eso es una afirmación
  —objetivos de entrenamiento distintos—, no un hecho. Si se agrupan, se agrupan
  diciéndolo.
- **Los rung2 llevan cinco hechos en el nombre**, incluido el hash `0868f1ff` del
  config padre, y `model_name` duplica `display_name` en vez de llevar el id del
  modelo.
- **`param_count` es NULO en 7 de 13.**
- **`esm2_3b` no está en la caché local de modelos**, lo que explica su
  `param_count` nulo: `count_backend_parameters` carga el modelo para contarlo.

---

## 4. El esquema de nombres

La regla es la de siempre: **un nivel se nombra por todos los campos en que
varía**, y el nombre lleva lo que es *comparable*, no lo que es mecánico.

```
<kind>/<family>/<modelo>@<profundidad>:<pooling>
```

La profundidad se escribe **relativa**, porque es lo comparable entre redes de
distinto tamaño:

```
@d100   salida final                 layer_indices [0]
@d67    dos tercios de profundidad   [N/3]   desde el final
@d33    un tercio                    [2N/3]
@d0     salida de la capa de embedding [N]
```

Dos modelos en `@d67` tienen `layer_indices` distintos —`[11]` en esm2_650m de 33
capas, `[16]` en ankh_base de 48— y eso es correcto: **el nombre dice el nivel
del eje, el campo dice el índice.** Poner `[11]` y `[16]` en la misma barra sin
traducirlos es comparar dos cosas distintas; ponerlos como `@d67` es comparar la
misma.

N se lee del modelo en extracción, no se escribe en ninguna tabla:
`_validate_layers` ya conoce `len(hidden_states) - 1`, y `esmc_600m` ni siquiera
declara su profundidad en `config.json`. Empotrar la cifra sería inventar un
segundo lugar donde vive la verdad.

Ejemplos:

```
pretrained/esm2/esm2_650m@d100:mean
pretrained/ankh/ankh_base@d67:mean
learned/rung2/dense@ankh_base_d100:mean:jaccard220
```

---

## 5. El eje de capa, medido en vez de anecdótico

Hoy el eje existe para **un** modelo: un par sobre `ankh_base`. Eso no es un eje.

Rejilla **4 modelos × 4 profundidades**, en posiciones relativas fijas, cubriendo
cuatro linajes distintos:

|  | `@d0` | `@d33` | `@d67` | `@d100` |
|---|---|---|---|---|
| `esm2_650m` (33 capas) | `[33]` | `[22]` | `[11]` | `[0]` |
| `ankh_base` (48) | `[48]` | `[32]` | `[16]` | `[0]` |
| `prot_t5` (24) | `[24]` | `[16]` | `[8]` | `[0]` |
| `esmc_600m` (N) | `[N]` | `[2N/3]` | `[N/3]` | `[0]` |

16 configuraciones donde hoy hay 5. Convierte *dónde vive la señal en la red* en
una pregunta medida y comparable entre familias.

El `[10]` actual de `ankh_base` no cae en la rejilla (es `@d79`). Se conserva o se
retira, pero no se renombra a un punto de rejilla que no es.

---

## 5-bis. Aplicado el 2026-09-04

El esquema está en la base. PROTEA#936 lleva las dos migraciones —`kind` separado
de `family`, y `derived_from_embedding_config_id` para el padre que sólo vivía en
el hash— y `scripts/rename_embedding_configs.py`, que **tira un segmento sólo
después de comprobarlo contra la columna que ahora lo guarda**. Lo que no
coincide se conserva en vez de adivinarse, y por eso sobreviven `cosine-jaccard`
y `k4:d2048:s128`: son los únicos hechos que siguen sin casa.

| antes | ahora |
|---|---|
| `ankh_base` | `ankh_base@d100:mean` |
| `ankh_base@L10` | `ankh_base@d79:mean` |
| `esm2_650m` | `esm2_650m@d100:mean` |
| `rung2-dense:mean:cosine-jaccard-220:0868f1ff` | `rung2-dense:cosine-jaccard` |
| `rung2-residue:k4:d2048:s128:0868f1ff` | `rung2-residue:k4:d2048:s128` |

Ningún id se movió —`display_name`, `family` y `param_count` no están en
`IDENTITY_FIELDS`— así que los 6.867.762 vectores siguen enganchados, y los tres
enlaces de padre resuelven a `ankh_base`.

## 5-ter. Lo que la normalización destapa

Las **diez configuraciones preentrenadas tienen `normalize = true`**. Sobre
vectores L2-normalizados ‖a−b‖² = 2 − 2·cos(a,b): monótona, **mismo ranking
exacto**. El eje `metric` sobre ellas no mediría nada, y sólo tiene sentido en las
tres rung2, que son las únicas sin normalizar.

Eso reinterpreta la escala de distancias. El 0,0004 de `ankh_base@d79` no es un
problema de escala —está normalizado— sino **colapso direccional**: a esa
profundidad el modelo da casi la misma dirección a todas las proteínas. Que es
justamente lo que la rejilla `@d` está para medir.

## 6. El estado que hay que limpiar

`experiment_run f2a10398` codifica el plan **voraz**: suelo `esm2_8m`, K=30,
cortes {2,3,5,10,20,30}, un eje cada vez. Bajo el diseño factorial —tensor de
recuperación profundo a K=200, y todo el grupo de puntuación como relectura— eso
no es un punto de partida sino un artefacto de un plan anterior. **Retirado el
2026-09-04**: `status = abandoned` con el motivo en `findings`, no borrado.
Editarlo habría dejado una fila cuyo `graph_node` dice una cosa y cuya historia
dice otra.

## 7. Lo que la auditoría NO cambia

La ventana sigue siendo **220 → 227**, con 227 → 230 sellado y fuera de la base.
GOA hacia atrás llega a 212 y las ontologías a 2022, así que alargar la ventana
era posible; se decidió no hacerlo. El marco declarado —pivote
`releases/2024-03-28`, IA `b5f134b1`, evaluaciones `b7cfed9a` y `b7452c0e`,
población de 23.737— queda intacto y verificado.

Nada de lo anterior toca `n`. CCO/LK sigue en 821 proteínas y su MDE en 0,0113.

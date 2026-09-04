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
problema de escala —está normalizado, norma L2 exactamente 1,0000— sino
**colapso direccional**: a esa profundidad el modelo da casi la misma dirección
a todas las proteínas.

### Posición y dispersión, que no son lo mismo (2026-09-04)

Medido sobre 1.500 vectores por configuración, muestra determinista:

| | dist. media | p99/p50 | 1er vecino |
|---|---|---|---|
| `prot_t5@d100` | 0,5992 | 1,5× | 0,1667 |
| `ankh_base@d100` | 0,4023 | 1,7× | 0,0964 |
| `esmc_600m@d100` | 0,2444 | 3,5× | 0,0522 |
| `esm2_650m@d100` | 0,1408 | 5,4× | 0,0281 |
| `ankh_base@d79` | **0,0004** | **2,6×** | 0,00006 |

**Una corrección, señalada por el nodo de cómputo.** La primera versión de esta
tabla traía además una columna de *anisotropía* —norma del centroide de los
vectores unitarios— presentada como segunda evidencia. No lo es. Para vectores
unitarios `|centroide|² = 1/n + (n−1)/n · cos_medio`, y la distancia coseno media
es `1 − cos_medio`; luego **anisotropía y distancia media son la misma cantidad**.
Verificado contra las cinco filas: discrepancia máxima 4·10⁻⁵. Citarlas como dos
mediciones concurrentes era contar un hecho dos veces.

Lo que queda, ya sin duplicar:

- **La posición** —la distancia media— varía por un factor de **1.500** entre
  configuraciones. Es lo que hace imposible un `distance_threshold` global: no
  porque las magnitudes difieran (todas son norma 1), sino porque el umbral cae
  en un sitio distinto de cada distribución.
- **La dispersión** —`p99/p50`— varía sólo por **3,6×**, y es la columna
  independiente. `@d79` tiene 2,6×, **más** que `ankh_base@d100` con 1,7×.

Y de ahí sale por qué el colapso no cuesta lo que parecería: el ranking coseno es
invariante de escala, así que un cono mil veces más estrecho conserva el orden
mientras la dispersión relativa aguante. La medición previa del nodo penalizaba
esa profundidad en sólo −0,0076, y esto lo explica sin contradicción.

**La distancia media no predice calidad.** `esm2_650m@d100` está entre las
mejores y su distancia media es 0,1408, cerca del extremo colapsado.

### El truncamiento no es un detalle de coste, es un confundido de estrato

`max_length` es **1022** y `use_chunking` está en `false` en las trece
configuraciones, así que toda secuencia más larga se corta. Medido sobre el
corpus vivo:

| banda | secuencias | residuos | % procesado | % de secuencias cortadas |
|---|---|---|---|---|
| `<=512` | 412.915 | 109.032.448 | **100,0** | 0,0 |
| `512-1024` | 92.109 | 63.281.004 | **100,0** | 0,1 |
| `1024-2048` | 19.299 | 25.825.275 | **76,4** | **100,0** |
| `>2048` | 3.971 | 12.561.129 | **32,3** | **100,0** |

En agregado son 14.604.680 de 210.699.856 residuos, un 6,93%. Pero el agregado
esconde el reparto: **en `>2048` el modelo ve un tercio de la proteína**, y en
`1024-2048` se corta el **100%** de las secuencias.

**Y la banda que se llama `TRUNCATED` no es donde empieza el truncamiento.**
`strata.py` nombra así a `>2048`, pero el corte lo fija `max_length` en 1022, dos
bandas antes. El nombre marca un umbral que no es el que opera — la misma clase
de defecto que el resto de esta auditoría.

**Lo que esto cambia.** La banda larga ya estaba identificada como muro por
potencia: 347 proteínas, 1,8% del corpus, por debajo del suelo en seis de siete
paneles. Ahora tiene una segunda razón, y **son muros distintos**:

- *No hay suficientes proteínas* se arregla con más datos.
- *No hemos mirado la proteína entera* no se arregla con más datos. Se arregla
  con `use_chunking` o con un `max_length` mayor, y las dos están en
  `IDENTITY_FIELDS`, así que cada una crea configuraciones distintas y es
  ablacionable.

Mientras el truncamiento no se mida por banda, cualquier conclusión sobre
longitud en las dos bandas altas **mide truncamiento y no biología**. El campo
`residues_truncated` de `compute_embeddings_batch.done` (PROTEA#938) es lo que
permite separarlas, y hay que leerlo **por banda**, no agregado.

Hallazgo del nodo de cómputo, que vio que el 6,93% se perdía en el 4,4% de las
secuencias y preguntó cómo quedaba el reparto.

### Lo que la rejilla tiene que registrar

Si posición y anisotropía son una sola cantidad, entonces *dónde empieza el
colapso* y *cómo cae la distancia media con la profundidad* son **una sola
curva**, y medir las dos no añade nada.

La información que nadie tiene es **la dispersión por profundidad**. Registrar
`p99/p50` —o mejor el rango relativo p1→p99— **por configuración y por barra de
la rejilla**, no sólo la media. Doce configuraciones por cuatro profundidades dan
una curva de dispersión que es la que predice si el ranking sobrevive al colapso;
la de la media queda determinada en cuanto se conoce un punto.

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

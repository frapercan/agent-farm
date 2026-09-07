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

**La distancia media no predice calidad** — dentro del grupo de cabeza.
`esm2_650m@d100` está entre las mejores con distancia media 0,1408, cerca del
extremo colapsado. **Cuidado con generalizar esto**: ver la sección siguiente,
donde con Fmax medido resulta falso a lo largo del rango completo.

### El truncamiento: una medición, dos poblaciones

`use_chunking` está en `false` en las veinticinco configuraciones, pero
**`max_length` NO es uno solo**:

| `max_length` | configuraciones |
|---|---|
| **2048** | las 22 preentrenadas, incluidas las 12 de la rejilla |
| **1022** | las 3 aprendidas rung2 |

La primera versión de esta sección midió el corpus entero a 1022 —el valor de las
rung2— y aplicó la conclusión a la rejilla, que corre a 2048. Correcta sobre tres
configuraciones, falsa sobre veintidós. Es exactamente el defecto que esta
campaña persigue: la misma medición correcta sobre dos poblaciones distintas.
Corregido por el nodo de cómputo.

**A 2048, que es el valor de la rejilla:**

| banda | secuencias | residuos | % procesado | % de secuencias cortadas |
|---|---|---|---|---|
| `<=512` | 412.915 | 109.032.448 | 100,0 | 0,0 |
| `512-1024` | 92.109 | 63.281.004 | 100,0 | 0,0 |
| `1024-2048` | 19.299 | 25.825.275 | 100,0 | 0,0 |
| `>2048` | 3.971 | 12.561.129 | **64,7** | **100,0** |

**2,10% del corpus**, una sola banda. Y `strata.py` marca el umbral **correcto**:
`TRUNCATED` es `>2048` y el límite de las preentrenadas es 2048. El nombre está
bien puesto — para las veintidós. Para las tres rung2 el corte cae en 1022 y
entonces sí llega dos bandas antes.

A 1022, para las rung2: 6,93% del corpus, `1024-2048` al 76,4% y `>2048` al
32,3%, con el 100% de las secuencias cortadas en ambas.

### La ventana de entrenamiento, que no es el truncamiento

El backend de ESM pasa `max_length` directo al tokenizador con `truncation=True`
(`protea_backends/esm/__init__.py:236-241`). Con 2048 emite hasta 2048 tokens. La
pregunta que abre eso es si los cuatro linajes de la rejilla pueden con ello:

| linaje | posiciones | mecanismo |
|---|---|---|
| `esm2` (8M, 650M, 3B) | `max_position_embeddings` **1026** | rotatorio |
| `ankh` (base, large) | — | sesgo relativo, **64** cubos |
| `prot_t5`, `prostt5` | — | sesgo relativo, **32** cubos |
| `esmc_600m` | — | no declarado |

Ninguno falla a 2048. El rotatorio no tiene tope de array, y el sesgo relativo
satura en el último cubo. Pero **esm2 se entrenó a 1024 y extrapola a partir de
ahí**, mientras la familia T5 degrada saturando. Y el `model_max_length` del
tokenizador de esm2 es el centinela (10³⁰), así que no impone nada: manda
`config.max_length`.

**La consecuencia importa para el instrumento.** `residues_processed` será
**idéntico** en los cuatro linajes, porque la tokenización corta en el mismo
sitio. Así que comparar ese campo entre linajes **no detecta esto**: la
diferencia no está en cuánta proteína ve cada modelo, sino en si lo que ve más
allá de su ventana de entrenamiento significa algo.

La población afectada son las dos bandas altas —`1024-2048` y `>2048`, **23.270
secuencias, 4,4% del corpus**— donde esm2 opera fuera de su ventana y las T5 no.
Ahí la comparación **entre barras del mismo eje** queda contaminada, y eso no se
arregla estratificando.

### Longitud y truncamiento son colineales

A `max_length` fijo el truncamiento es una función determinista de la longitud:
el borde de la banda **es** el umbral. Ninguna estratificación puede separarlos.
La única identificación posible es **variar `max_length` o `use_chunking`**, que
están los dos en `IDENTITY_FIELDS` y por tanto crean configuraciones distintas.

Eso asciende la ablación del chunking de "convendría" a **la única estrategia de
identificación disponible** para cualquier afirmación sobre longitud. Hallazgo
del nodo de cómputo.

### Con Fmax medido, la posición ordena y la dispersión no (2026-09-06)

La sección anterior concluía que la distancia media no predice calidad y que la
dispersión es la columna informativa. Con trece sustratos ya evaluados sobre las
nueve celdas, **las dos afirmaciones se caen**:

```
                          dist. media   p99/p50   fmax_w
ankh_large@d100              0.5652      1.47     0.2953
protst@d100                  0.8769      1.36     0.2909
prot_t5@d100                 0.6305      1.42     0.2892
ankh_base@d100               0.4381      1.65     0.2864
esmc_600m@d100               0.2645      3.10     0.2850
rung2-residue                0.9132      1.06     0.2712
esm2_650m@d100               0.1489      3.69     0.2045
esm2_8m@d100                 0.1569      4.29     0.1757
esm2_3b@d100                 0.0648      2.88     0.1070
ankh_base@d79                0.0004      2.51     0.0784

correlacion  distancia media  vs  fmax_w :  +0,747
correlacion  dispersion       vs  fmax_w :  -0,594
```

**La posición predice; la dispersión predice al revés.** `esm2_8m` tiene la mayor
dispersión de todas, 4,29, y es de las peores.

El error fue generalizar desde un tramo plano. Dentro del grupo de cabeza la
media efectivamente no discrimina —que es lo único que yo había mirado— pero a lo
largo del rango completo, de 0,9132 a 0,0004, ordena casi exacto.

**Se registran las dos columnas. La que ordena es la posición.**

Dos cosas que esto no toca. El colapso de `ankh_base@d79` es real y ahora está
cuantificado: **0,0784 frente a 0,2864** de su propia capa final, una caída de
0,208, donde el prior traído de otro marco lo ponía en −0,0076. El signo era
correcto y la magnitud no era transferible, exactamente como el nodo de cómputo
advirtió al darlo. Y `esmc_600m` es la excepción que hay que perseguir: distancia
media 0,2645, de las más bajas, y aun así en el grupo de cabeza.

**Y absuelve a `esm2_3b`.** En la tabla de cabecera el modelo de 3.000 millones
pierde contra el de 8 millones de su propia familia, lo que parecía defecto
bloqueante. No lo es: dimensión correcta (2560), cobertura completa (528.294), y
una capa final **cuatro veces más colapsada** que la de sus hermanos pequeños.
Escalar dentro de la familia empeoró la última capa para recuperación. Es el
resultado, y es justo lo que la rejilla de capas existe para contestar.

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

## 8. Los instrumentos, auditados con el mismo criterio que los números (2026-09-07)

El eje C se bloqueó porque `ref_data_by_aspect` tiene dos formas y el mapa de
secuencias leía sólo una. Arreglado en PROTEA #941, y **confirmado en
producción**: la tanda anterior murió entera en el camino
`aspect_separated_knn=false`; la de hoy escribe predicciones en los seis brazos.
Lo que sigue es lo que salió al auditar, con el mismo criterio, los instrumentos
que debían haberlo detectado.

### El consumidor ocioso no oía SIGTERM, y su prueba estaba verde

`OperationConsumer._handle_stop` ponía la bandera y volvía. `_on_message` es su
único lector, así que se consulta **exactamente cuando llega un mensaje**: un
consumidor con la cola vacía queda dentro de `start_consuming` y la señal no
tiene ningún efecto. El que se cuelga es el **ocioso**, y por eso esto se leía
como drenaje lento y no como fallo al parar. `_OPERATION_QUEUES` cubre todas las
colas de cómputo, así que ninguna podía pararse limpiamente. Coste el 2026-09-07:
cuatro muertes duras en el nodo y una aquí, cada una pagando su timeout entero.
PROTEA #942.

**Y la prueba de este incidente ya existía.** `test_worker_honours_sigterm.py`
nombra el suceso en su docstring —*once de doce workers ignoraron SIGTERM*— y lo
que fija es que ambas clases heredan de `Stoppable`. Las dos lo cumplían durante
todo el apagón. El incidente correcto, el invariante equivocado, verde todo el
tiempo. La prueba nueva está parametrizada sobre las dos clases: sin el arreglo
fallan los siete casos `[operation]` y pasan los siete `[queue]`, de modo que
**demuestra** la asimetría en vez de afirmarla.

### El latido de cola tiene la misma forma, resuelta con una constante

`queue_heartbeat.py` no mira el log, mira la tasa de acks. No es mejor: un
consumidor dentro de una carga de referencias no acka durante minutos igual que
no escribe. La gracia se puso a 5400 s en las colas de lote **para que
"trabajando despacio" se despeje solo**, o sea que tampoco distingue atascado de
trabajando: espera lo bastante para que la diferencia deje de importar. El
precio es simétrico y está sin pagar: un atasco real en una cola de lote tarda
hora y media en ser nombrado. El discriminador que sí separa los dos casos es el
contador de CPU del proceso —dos lecturas de `/proc/<pid>/stat`, más `send-q`—,
no el silencio. `pcpu` de `ps` no sirve: es la media sobre la vida del proceso.

### Esta máquina no tiene slot de despliegue

Los workers sirven desde `~/Thesis-laptop/PROTEA`, que es el checkout principal.
La autoría sí está aislada —cada PR se escribe en un worktree aparte— pero
**mover la revisión desplegada obliga a hacer `checkout` en el árbol que está
sirviendo**. Las tres violaciones de la regla "no se edita el árbol mientras hay
trabajo" no fueron tres descuidos: aquí desplegar y servir son la misma operación
sobre el mismo directorio, así que la regla no es aplicable, sólo memorizable. El
nodo tiene `worktrees/protea-deploy` separado. Decisión abierta.

### `farm.env` no existe en esta máquina

El `CLAUDE.md` de la raíz avisa de que sin él todo guion de la granja cae a los
defaults `~/Thesis2/...`. **`~/Thesis2` existe entero**, con su PROTEA, su
agent-farm y sus backups. Así que un guion de granja no falla aquí: acierta sobre
el árbol equivocado, y un guardia que lea la declaración desde ahí compararía
contra una copia congelada y aprobaría. Decisión abierta, junto con dónde debe
vivir ese fichero y si debe estar versionado.

### Y ocurrió otra vez, midiendo el reparto entre las dos máquinas (mismo día)

Para repartir los 144 lotes hacían falta los ritmos de las dos máquinas. El
nodo informó de mediana 36,0 s sobre 109 lotes de su propio log; este equipo
había citado 0,93 min/lote. De ahí salía un 1,55x a favor del nodo y un reparto
proporcional 88/56.

**Las dos cifras estaban mal, y de la misma forma.** La de aquí no era un tiempo
por lote sino el **espaciado de reloj entre eventos consecutivos de las dos
máquinas juntas**, que incluye el tiempo del otro consumidor; el tiempo real
por lote medido en `elapsed_seconds` es 49,2 s. La del nodo era una mediana
sobre una población distinta —lotes de otros ejes, con otros sustratos, y la
dimensión del embedding cambia el coste del KNN—. Comparadas, no eran dos
medidas de la misma cosa ni sobre el mismo conjunto.

Sobre los seis brazos de hoy, que es la única comparación de un solo campo
disponible, `child.predict_go_terms_batch.done` da mediana 48,5 s aquí (n=19) y
45,1 s en el nodo (n=2): **indistinguibles, y n=2 no sostiene ninguna
afirmación**. En todo el histórico se invierte: 38,4 s aquí sobre 720 lotes
frente a 51,6 s en el nodo sobre 177.

El reparto propuesto era además inaplicable: los dos consumidores tiran de una
sola cola, así que el reparto ya se autoequilibra por consumo y no hay nada que
asignar. La cifra era descriptiva presentada como accionable.

### `SUCCEEDED` es una afirmación sobre la recuperación, no sobre los datos

El primer brazo redespachado del eje C dio `SUCCEEDED` 24/24. Leída entonces, su
cobertura era **20.776 proteínas frente a las 23.737 de los brazos
`aspect_separated_knn=true`**: una brecha del 12,5% y, de haberse creído, un
hallazgo mayor —dos brazos puntuando poblaciones distintas no son una
comparación de un solo campo—.

Es falso. Tres lecturas consecutivas del mismo conjunto dieron 8.236.157,
8.266.157 y 8.296.157 mientras `protea.predictions.write` retenía 71 mensajes.
Con la cola a cero y dos lecturas idénticas, la cifra real es **23.737 proteínas
en los dos brazos**: misma población, ninguna brecha.

La causa estaba anotada y sin arreglar: `progress_total` cuenta **lotes** y
`progress_current` avanza con los mensajes de **escritura**, así que el estado
terminal llega cuando la recuperación acaba, no cuando los datos están. El
número intermedio es plausible y no deja rastro de estar incompleto.

**Regla operativa: ningún brazo se lee ni se evalúa por el estado del job, sino
con su cola de escritura a cero y dos conteos iguales seguidos.** Con eso, la
comparación limpia sobre `protst@d100:mean` es 9.449.890 predicciones con
separación por aspecto frente a 8.886.453 sin ella, sobre las mismas 23.737
proteínas.

Es el caso más agudo de la lista porque la conclusión equivocada **ya estaba
formada** y sólo la deshizo comprobar el instrumento antes de creerle.

### Lo que une a los seis

Un observable barato sustituyendo a la propiedad cara, con la sustitución nunca
comprobada: `is-active` por *ejecuta este código*, tasa de acks por *el proceso
avanza*, `issubclass(Stoppable)` por *la señal llega al bucle*, un default que
resuelve por *el objeto correcto*, un estado terminal por *los datos están*. y un tiempo de reloj por *un tiempo de proceso*. La regla operativa que lo
cubre es que **un guardia o una prueba tiene que demostrar que puede rehusar**: no "¿pasa?", sino
"¿puede fallar?". Es lo que separa un instrumento de una decoración, y es lo
único que distingue los seis casos de arriba de sus versiones sanas.

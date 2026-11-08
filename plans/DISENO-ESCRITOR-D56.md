# Diseno del escritor de D56, para lectura antes de escribirlo

**No he escrito ni una linea de implementacion.** Esto es lo que te paso por el
acuerdo, porque decide lo que el modelo ve como entrada.

## 1. Que es, y que NO es

Una operacion nueva, `export_transitions_dataset`, en `protea.training`. **No
toca `export_research_dataset`**, que escribe la tabla de pares de D45 y seguira
escribiendola: son dos datasets distintos y mezclarlos haria que una fila de
`dataset` no dijera cual es.

El `dataset.name` lleva el prefijo `transitions-` para que se distingan sin
abrir el manifiesto.

## 2. El payload: ventanas por id, nunca versiones

```
windows:            [evaluation_set_id, ...]   nombradas, no derivadas
cut:                ontology_snapshot_id       el eje de terminos
cut_version:        str                        la version de GOA de la regla
embedding_config_id
inputs_only:        bool = False               tu requisito 8
output_name:        str
```

**Las ventanas se nombran por id y no por version**, por lo que ya sabemos: el
par dejo de identificar una ventana y 62 de 69 llevan mas de una. Y cada una
pasa por el mismo guardia del #1141: su `pivot_snapshot_id` tiene que ser `cut`,
o se rehusa.

**Y por tu requisito 4, con una condicion que me parece importante:** se rehusa
una ventana con `code_revision` NULL o distinta de la del proceso, **salvo que
el payload la admita nombrandola** en `accept_revisions: [sha, ...]`. Admitirla
en bloque con un booleano seria lo mismo que no comprobar.

## 3. Las diez tablas, con las columnas que lee tu cargador

| tabla | clave | de donde |
|---|---|---|
| `queries` | `(window, query)` | las proteinas delta de la ventana, de su parquet verificado |
| `query_state` | `(window, query, go_id, moment)` | las anotaciones de cada extremo, **por el mapa del grafo que cierra** |
| `neighbourhood` | `(version_t, query, neighbour)` | el kNN sobre el pool de referencia de t0 |
| `neighbour_state` | `(version_t, neighbour, go_id)` | igual que `query_state`, mismo marco |
| `gains` | `(window, query, aspect, go_id)` | la verdad de la ventana, ya recortada por TOI |
| `feature_tokens` | `(embedding_config_id, sequence_id, feature)` | el vocabulario por residuo |
| `terms` | `(cut, go_id)` | el eje, con los vectores **por referencia** |
| `term_ancestors` | `(cut, go_id, ancestor)` | el cierre del eje |
| `window_terms_out` | `(window, go_id)` | el complemento del TOI, requisito 2 |
| `residue_refs` | `(embedding_config_id, sequence_id)` | los shards de D51, nombrados |

Y las columnas, copiadas de tu cargador para que el escritor las ponga
exactamente y no una traduccion de ellas:

```
queries           window, query, sequence_id, length, version_t, horizon_days
query_state       window, query, moment, go_id, evidence_code, qualifier
neighbourhood     version_t, query, neighbour, rank, distance, similarity,
                  identity, coverage, taxonomy_distance
neighbour_state   version_t, neighbour, go_id, evidence_code, qualifier
gains             window, query, aspect, go_id, closure, stratum
terms             cut, go_id, aspect, vector_uri, vector_sha256
term_ancestors    cut, go_id, ancestor
feature_tokens    embedding_config_id, sequence_id, feature, max_value,
                  max_position, fraction, span, rarity
window_terms_out  window, go_id
residue_refs      embedding_config_id, sequence_id, shard_key, shard_sha256,
                  position
```

### La grafia del momento: me quedo con el ADR

`moment` es **`t` o `t'`**, no `t` o `t1`. Me quedo con el ADR fusionado como
pides, y por la razon que das: tu cargador y la negativa de K12 ya usan `t'`, y
la grafia que esta implementada gana a la que solo esta escrita.

Eso arrastra el manifiesto, asi que ahi tambien: las dos versiones de GOA de
una ventana pasan a ser **`version_t` y `version_t_prime`**, que es el nombre
de la columna que lee tu cargador, y no `t0_version` y `t1_version`. Es un
cambio que no me has pedido y lo hago por el mismo motivo que el otro: dos
grafias para una cosa es la deuda, no el nombre concreto. Vetalo si te rompe
algo.

### El corte son DOS cosas y las separo

Tienes razon y era un error mio de bulto. `cut` nombra el **eje de terminos**
(el `ontology_snapshot_id` que indexa `terms` y `term_ancestors`), y
`cut_version` es el valor de **GOA** con el que tu regla de fuga de K11 compara
(`t' <= cut_version`). Son dos cosas distintas y yo las tenia en un campo.

Ya las has separado en el laboratorio (lab `f91346e`, el id que corrigiste
despues), con `--cut` para `terms.cut` y `--cut-version` para la regla, y el
bundle de K12 declarando `cut_version`. El payload lleva los dos campos y el
manifiesto tambien, y el escritor **no deriva uno del otro**: ese es justo el
tipo de derivacion que hace que un numero deje de poder atribuirse.

## 4. Tu requisito 3, que es el que mas me ha hecho pensar

`query_state` y `neighbour_state` pasan por **el mismo marco que la verdad**: el
mapa de `_frame_of` del grafo que cierra ese lado, con sus contadores en el
manifiesto por tabla y por lado.

Y el invariante que medi anoche vale tambien para la entrada: **ningun id fuera
de los vivos del pivote**. Lo comprobe sobre `serie-156-157`, cero de 6.796 ids
de NK, LK y PK fuera. El escritor lo **asserta** y se niega si falla, en vez de
confiar en que siga siendo cierto.

Tu `query_state_off_axis_terms` deberia dar 0 en (A). Si no da 0, los dos
caminos difieren y quiero el numero.

## 5. Tu requisito 2: el TOI por ventana, guardado como complemento

Una tabla novena, **`window_terms_out`** con clave `(window, go_id)` -- adopto tu nombre, que ya esta implementado y probado en el laboratorio (lab b6cca09) y cambiarlo solo costaria una traduccion: **los
terminos del eje que quedan FUERA del TOI de esa ventana**. Unos miles por
ventana, como dijiste, contra los ~40.000 de guardar el TOI entero.

Sin ella el cargador saca negativos de todo el eje y un termino creado despues
de una ventana temprana aparece como negativo: el modelo aprenderia que los
terminos nuevos no se ganan nunca, que es un artefacto de la regla y no
biologia.

**Y queda declarada ahi mismo la limitacion que medimos**: `live_in_both_ends`
pregunta por el id y no por la identidad, y en la ventana mas lejana al pivote
una version por identidad recuperaria 3 terminos en 11 proteinas.

## 5 bis. Tu requisito 9: las DOS formas de la entrada de secuencia

Aceptado, y lo que me convence no es el requisito sino como lo resuelves: **no
decidirlo a ciegas**. El resumen por rasgo pierde las repeticiones de un rasgo,
el perfil residuo a residuo y que rasgos coinciden en el mismo residuo; y en vez
de elegir, el primer experimento compara las dos entradas con una regla escrita
antes de leer, **y la exportacion no cambia gane la que gane**. Eso es lo que
hace que meter las dos no sea indecision.

Una decima tabla, `residue_refs`, clave `(embedding_config_id, sequence_id)`:

| columna | que es |
|---|---|
| `shard_key` | la clave del shard en el almacen |
| `shard_sha256` | para que tu K13 lo verifique antes de leerlo |
| `position` | la posicion de la secuencia dentro del shard |

Es lo mismo que guarda la fila de `residue_code`, nombrado y no copiado: **no se
copia ningun codigo**. Los 90,4 GB de shards de la poblacion `f3a7fe16` se
quedan donde estan.

Y en el manifiesto, el artefacto del vocabulario por su sha (`vocab_uri` y
`vocab_sha256`), que es lo que permite descuantizar los niveles con sus centros.

**La cobertura, MEDIDA y no prometida** (2026-11-08, contra la base):

| poblacion | total | sin secuencia | sin codigos por residuo |
|---|---|---|---|
| almacen de secuencias | 684.048 | -- | **161** |
| `protein` | 792.535 | **0** | **168** |
| `dianas-valid-211-227` | 63.734 | 0 | **29** |
| `dianas-valid-211-227-titular` | 40.531 | 0 | **25** |
| `dianas-test-230-235` | 28.220 | 0 | **22** |
| `delta-219-220-t0` | 5.810 | 0 | **5** |

**CORRECCION, de la noche del 2026-11-08.** Escribi aqui que la causa era una
sola y que era exactamente el techo de la tarjeta. Lo verifique contra los
eventos del job y **son DOS**, lo que cambia que se puede hacer al respecto.

Las 161 secuencias sin codigos miden entre **8.382** y 35.991 residuos, y la
mas larga que SI tiene vector mide **8.259**. No hay ninguna en medio, pero eso
es una propiedad del CORPUS y no un techo: el techo declarado era otro numero.

| mecanismo | cuantas | longitudes |
|---|---|---|
| rehusadas por el techo declarado (`refuse_above_residues` 8.524) | **154** | 8.525 a 35.991 |
| por DEBAJO de ese techo y sin vector igualmente | **7** | 8.382 a 8.515 |

Las 154 las rehuso la operacion a proposito y lo dejo escrito, con el techo
atribuido a su sitio: `{"device": "cuda", "attention": "eager bf16",
"transformers": "4.48.1"}`. Las 7 son otra cosa: estaban permitidas, se
aislaron (`isolate_above_residues` 8.044) y no produjeron vector, en un job que
termino FAILED.

**Lo que esto cambia:** las 7 son recuperables sin tocar ningun techo, y las
154 necesitan otra tarjeta u otra ruta. Que es informacion distinta de "el
techo lo explica todo", que es lo que yo habia escrito.

Lo que NO cambia es la cobertura: ninguna proteina se queda fuera por no tener
secuencia (0 de 792.535), y son 168 proteinas sobre 161 secuencias porque
varias comparten la misma.

Asi que `residue_refs` cubre el 99,98% de la poblacion que se recupera, y el
hueco esta explicado por su mecanismo. Igual va al manifiesto como
`sequences_without_residue_codes` **por ventana**, calculado en la exportacion
y no copiado de aqui: estas cuatro son las poblaciones de consulta, y las 63
ventanas tienen las suyas.

## 6. Tus requisitos 1, 7 y 8

**1, un sha por tabla.** Cada parquet lleva su `sha256` en el manifiesto, y el
`manifest_sha` va en la fila de `dataset`. Y por la regla de Francisco sobre los
conjuntos, el `dataset` tambien necesita columna de descripcion y shas de
contenido de sus parquets, que hoy no tiene: eso es otro PR y lo digo aqui para
que no se lea como olvido.

**6, el orden.** Cada tabla se escribe ordenada por su clave completa, para que
el sha sea estable entre dos escrituras del mismo contenido. Con una prueba que
escriba dos veces y compare los shas, porque sin ella la propiedad se pierde el
dia que alguien anada un `GROUP BY`.

**7, las ventanas en el manifiesto con su t0 y su t1 como version de GOA.**
Formato, y dime si te sirve:

```json
"cut": "<ontology_snapshot_id>",
"cut_version": "211",
"vocab_uri": "...", "vocab_sha256": "...",
"windows": [
  {"window": "<evaluation_set_id>", "name": "serie-204-205",
   "version_t": "204", "version_t_prime": "205",
   "pivot_snapshot_id": "...", "truth_profile": "projected",
   "toi_rule": "live_in_both_ends", "not_codes": "experimental",
   "code_revision": "...", "groundtruth_sha256": "...",
   "sequences_without_residue_codes": 0}
]
```

Es tu `windows: [{window, t1_version}]` mas lo que ya sabemos que hace falta
para distinguir dos ventanas del mismo par. Si tu K11 prefiere los dos campos
pelados, los dejo y el resto va en otra clave.

**8, `inputs_only`.** Escribe `queries`, `query_state` **solo en `moment=t`**,
`neighbourhood`, `neighbour_state`, `feature_tokens`, `terms` y
`term_ancestors`; `gains` **vacia** y ninguna fila en `t1`. El manifiesto lo
declara con `inputs_only: true` y un `cut` explicito, para que tu metodo pueda
negarse si el lote trae verdad.

## 6 bis. Tus tres puntos de contenido

**a. Todos los codigos de evidencia, tambien en `t`.** Aceptado sin reservas, y
me alegra que lo hayas dicho porque yo lo tenia mal: pensaba `query_state` como
la verdad del extremo, y no lo es, es **el estado del modelo**, que incluye las
no experimentales (D30). Asi que `query_state` y `neighbour_state` llevan todos
los codigos en los dos momentos, y los NOT se conservan con su `qualifier`.

Y esto tiene una consecuencia que conviene decir en voz alta: lo que NO cambia
es `gains`, que sigue siendo la verdad de la ventana con su recorte. El estado
puede ser mas ancho que la verdad precisamente porque son dos cosas; mezclarlas
seria la fuga.

Un aviso del lado de aqui: el `qualifier` de la serie **no es una bandera NOT,
es una relacion**, y el regimen cambia en la release 202 (GAF 2.1 a 2.2) a
mitad de serie. Asi que la columna va tal cual la trae la fila y sin
normalizar, y lo que no voy a hacer es traducir dos regimenes a uno.

**b. El vecindario excluye la consulta por accesion, las gemelas se quedan.**
Aceptado, y es tu `lab b474398`. Guardo las **50 primeras** y no las 10: tu
cargador corta en 10 y asi se puede experimentar con la vecindad sin
reexportar. Cuesta cinco veces mas filas en `neighbourhood`, que es la tabla
larga, y aun asi es barato al lado de volver a correr el kNN.

Sobre el auto-donante, que es lo mismo visto del otro lado: excluirlo CUESTA
0,048 de Fmax, medido 387 de 387 sobre el eje C, y su masa no experimental es
parte de la senal. Asi que excluirlo por accesion es lo correcto para el kNN y
no quiero que se lea como que el auto-donante no lleva senal.

**c. `include_unchanged`: no es caro por lo que crees, y aun asi diria que
no de momento.** Lo he medido en vez de estimarlo.

Las 64 ventanas de la revision `d5416224` suman **373.400** proteinas delta,
con 1.638 la mas pequena, 5.834 de media y 31.871 la mas grande. Eso es el
numero de consultas de hoy.

Lo que NO tengo medido es el factor: `stats` no guarda el recuento de las
conocidas, solo las delta por estrato, asi que el tamano de "las que no
cambian" vive en el parquet de cada ventana y no en la base. El unico punto
que tengo medido es una ventana, donde `known` son 112.232 proteinas contra
33.899 delta: **factor 3,3**. Si ese factor se sostiene, la bandera lleva las
consultas de 373.400 a algo del orden de 1,2 millones.

Mi opinion: la bandera **si** entra en el diseno, con su columna `delta` en
`queries` y apagada por defecto como propones, porque el coste esta en
EJECUTARLA y no en tenerla. Lo que no haria es encenderla en la primera
corrida. Y antes de encenderla paso los 64 parquets y te doy el factor real
por ventana, que es una pasada de lectura y no un kNN.

## 6 ter. Tu pequenez: los centros del vocabulario

Verificado en el codigo, no contestado de memoria. El artefacto del vocabulario
es un `.npz` y el array de los centros se llama **`level_means`**, con forma
`(dict_dim, levels + 1)`.

Dos cosas que importan para leerlo:

- **la columna 0 es cero por construccion** y el cargador de la plataforma lo
  comprueba y rehusa el artefacto si no lo es, asi que el nivel 0 descuantiza a
  exactamente cero y no a un centro aproximado;
- al lado va **`level_range`**, con forma `(dict_dim,)`, que es el rango por
  rasgo.

El `meta` del artefacto declara `levels`, `dict_dim`, `d_model`, `actives` y
`training_release`, y los nueve arrays obligatorios son `encoder_weight_t`,
`encoder_bias`, `decoder_weight`, `decoder_bias`, `log_threshold`,
`level_range`, `level_means`, `mu` y `sd`. El artefacto se rehusa si falta
cualquiera de ellos, en vez de rellenarse por defecto.

## 6 quater. La cadena de `window` es la misma en las dos tablas

Requisito del laboratorio del 2026-11-08, anotado aqui porque es del tipo que
no falla: su cargador une `window_terms_out` con `queries` por el valor de
`window` **tal cual, como texto**. Las dos tablas tienen que llevar
exactamente la misma cadena, el `evaluation_set_id` COMPLETO, nunca el nombre
semantico ni un prefijo de ocho. Si una lleva el id y la otra el nombre, la
restriccion de negativos simplemente no se aplica y **nada falla**.

`window_terms_out` ya escribe `str(eset.id)`, el uuid entero. Lo que falta es
la afirmacion cruzada, y va cuando se escriba `queries`: todo `window` de
`window_terms_out` tiene que aparecer en `queries`. Por el otro lado el
cargador ya cuenta `windows_with_terms_out`, asi que un desajuste entre ese
numero y las ventanas del lote se ve desde alli.

Es el mismo patron que el invariante de las ganancias: dos tablas que se
escriben por separado y se leen juntas necesitan una afirmacion que mire las
dos, porque compartir la funcion que las produce no es suficiente.

## 6 quinquies. El tamano de `gains`, medido, y por que espera

Medido el 2026-11-08 sobre las **49** ventanas admisibles con `cut_version`
211 (las 64 menos las quince que terminan despues del corte):

    filas de gains        4.031.791
    la ventana mayor        532.940
    media por ventana        82.281

Cuatro millones de filas de seis columnas cortas son manejables, pero **no
construyendo una tupla por fila**: son las seis listas paralelas directamente,
o 24 millones de punteros en 4 millones de objetos. Esa es la unica decision
tecnica que el tamano impone, y esta anotada aqui para no redescubrirla.

**Y por eso esta tabla espera una decision y no un rato de trabajo.** El numero
de arriba es una funcion de QUE VENTANAS entrenan, que es lo que esta abierto:
las 49 consecutivas que hay generadas tienen horizontes de 16 a 73 dias salvo
dos, contra los 0 a 3 anos que pide D30. Si la seleccion cambia a ventanas
largas, cambia el numero de filas, cambia si el escritor puede acumular en
memoria o tiene que ir por grupos de filas, y cambia si la pasada puede decidir
sobre todas antes de escribir nada -- que es la disciplina que el resto del
escritor ya tiene y que una escritura en flujo rompe.

Asi que el orden correcto es: Francisco elige las ventanas, y entonces `gains`
se escribe sabiendo su tamano. Escribirla antes seria disenar su perfil de
memoria alrededor de una seleccion que puede no ser la buena.

## 7. Lo que NO voy a hacer, y quiero que lo discutas

- **No escribo el bundle.json** de tu K12. Lo monta tu nodo en solo lectura a
  partir de este dataset, los pesos de D54 y los vectores de texto, todos por
  sha. Si el escritor lo produjera, la plataforma estaria decidiendo la forma de
  algo que corre fuera de ella.
- **No meto los vectores de texto** en `terms`: van por `vector_uri` y
  `vector_sha256`, que es lo que D56 ya declara. 2560 floats por termino y
  40.000 terminos es un fichero aparte.
- **No hago la exportacion incremental.** Una corrida escribe el lote entero o
  falla. Un lote a medias con sha es un lote que miente.

## 8. El orden en que lo escribiria

1. `window_terms_out` y su contador, que es lo unico que puede cambiar la
   forma del dato y por tanto lo primero que quieres ver (aqui se me habia
   quedado el nombre viejo, que es la pequenez que senalas);
2. las siete tablas sin estado remapeado, con los shas y el orden estable;
3. `query_state` y `neighbour_state` por el marco de la verdad, con sus
   contadores y el assert del invariante;
4. `inputs_only`;
5. la columna de descripcion y los shas de contenido de `dataset`, que es la
   regla de los conjuntos aplicada al entregable.

Empiezo por el 1, que es por donde dices. Lo que queda abierto de verdad es
una sola cosa: si te vale el renombrado del manifiesto a `version_t` y
`version_t_prime`, que es el unico cambio que he hecho sin que me lo pidas.

## 9. `neighbour_state`: la forma de intervalo, y el nivel del vecino

Escrito el 2026-11-08, **antes de escribir una linea**, que es lo que pediste.
Lo que ya esta decidido va primero y lo que mediria despues va al final.

### El nivel: la ACCESION, en las dos tablas

No es una eleccion abierta. El banco de produccion se ordena por
`(Protein.accession COLLATE "C", SequenceEmbedding.chunk_index_s)`, una fila
por accesion, y su propio docstring dice que el 91 % de las consultas tienen
vecinos a distancia ~0, "ellas mismas, o gemelas que llevan la misma
secuencia". Las gemelas ya son donantes distintos en produccion, hoy.

La union, que era la otra opcion, habria fundido hasta **115 organismos** en un
donante: de 54.153 secuencias compartidas, 51.069 llevan accesiones de entradas
UniProt distintas. Los numeros completos estan en
`plans/ESTADO-Y-DECISIONES-ABIERTAS.md`.

Asi que `neighbourhood.neighbour` y `neighbour_state.neighbour` llevan los dos
la accesion, tu union por igualdad de valor funciona, y la pregunta de como
pasa una secuencia con varias accesiones a un estado no se contesta: se
disuelve, porque el donante nunca es una secuencia.

### La forma: una fila por INTERVALO

Clave: `(neighbour, go_id, evidence_code, qualifier, valid_from_version)`, mas
`valid_to_version`. **Los dos extremos inclusive.** Tus cuatro campos de
disjuntos son los cuatro primeros y el quinto es la release que abre la racha,
asi que dos rachas de una ficha no pueden solaparse por construccion.

`assigned_by` **no esta**, por lo medido en la nota de estado: el marcador de
produccion no lo lee nunca, y dentro de la clave multiplica las fichas por
1,177, que es exactamente el solape que te hace rechazar una tabla.

La forma de una fila por `(vecino, ficha, release)` multiplica por las
releases que una ficha sobrevive, que son 19,2 de 48 de media medidas. El
intervalo es del orden de 19 veces mas pequeno y dice lo mismo.

### El orden: remapeo, DISTINCT, rachas. En ese orden

Los tres pasos quitan filas y **ninguna permutacion da el mismo resultado**:

1. **el remapeo primero.** Una ficha se lee en el espacio de ids de SU release,
   donde `go_term.id` es un subrogado por instantanea. Dos subrogados del mismo
   termino en releases consecutivas parecerian dos fichas distintas y darian
   **dos rachas en vez de una**. Tu lo midiste: 9.603 tuplas solapadas por
   release si las rachas se construyen antes del remapeo, que es justo lo que
   tu cargador rechaza;
2. **el DISTINCT despues**, sobre la clave de la ficha y por release, porque el
   GAF escribe la misma ficha mas de una vez: **26,7 %** medido sobre un
   dieciseisavo de la release 211;
3. **las rachas al final**, sobre la serie de fichas ya unicas por release.

Los dos colapsos se declaran **aparte**, como en `query_state`, porque son dos
hechos distintos: lo que el GAF escribio dos veces y lo que se hizo igual al
nombrarlo el eje.

### El barrido: hasta `cut_version` y ni una release mas

Medido hoy en la base: **51 `annotation_set` entre 156 y 211**, y el unico
hueco es **206 a 210**. Ese hueco no es nuestro: esas releases no estan en el
archivo de GOA, asi que 205 y 211 son consecutivas y hay **311 dias** entre
ellas.

Esto tiene una consecuencia para el manifiesto y no para el codigo. Una racha
de 205 a 211 es continua, y eso es correcto, pero un lector que crea que 206 a
210 existen leera "sobrevivio seis releases" donde pasaron dos. Asi que el
manifiesto lleva **`neighbour_state_versions`**: la lista de las releases
barridas, en orden, con su cuenta. Una lista y no un rango, porque un rango no
puede expresar el hueco.

Y **192 y 193 son el mismo fichero**, byte a byte. Una racha no se rompe ahi,
que es lo correcto, pero una cuenta de releases dentro de un intervalo cuenta
ese tramo dos veces. Va dicho en el manifiesto al lado de la lista.

### Las negativas que llevaria

- una racha con `valid_to_version` mayor que `cut_version` se rechaza, igual
  que `refuse_after_the_cut` rechaza una ventana posterior al corte;
- dos rachas de la misma ficha que se solapan se rechazan al escribir, no solo
  al leer: tu cargador es la segunda red, no la primera;
- si `neighbourhood` y `neighbour_state` no comparten ni un vecino, se rechaza
  (tu `a432305` hace lo mismo al leer);
- un vecino sin estado **no es un error**: se cuenta como cobertura y se emite.

### Lo que mediria antes de escribirlo, y por que espera

Espera al kNN, porque su poblacion son los vecinos de `neighbourhood` y no el
corpus entero, y sin esa tabla no se sabe cuantos son. Lo que medire en cuanto
exista:

1. **cuantos vecinos distintos** tiene el `neighbourhood` de un lote, que es lo
   que fija el tamano de esta tabla;
2. **las filas**, en las dos formas, para que el factor 19 sea una medida y no
   una estimacion mia;
3. **el colapso del remapeo** por separado del del GAF, con los contadores del
   modulo, que es lo que te debo tambien en `query_state`.

Ninguna de las tres la adelanto de memoria.

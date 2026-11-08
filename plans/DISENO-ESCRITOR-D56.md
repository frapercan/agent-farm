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

## 3. Las ocho tablas, y de donde sale cada una

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

`moment` es `t` o `t1`, que es lo que hace que `query_state` pueda estar en los
dos extremos sin dos tablas.

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

Y **la causa es una sola**, que es lo que hace que esto sea una nota y no una
conversacion: las 161 secuencias sin codigos miden entre **8.382** y 35.991
residuos, y la mas larga que SI cupo mide **8.259**. No hay ninguna en medio.
Es exactamente el techo de la tarjeta que ya teniamos medido, y no un fallo de
cobertura: ninguna proteina se queda fuera por no tener secuencia (0 de
792.535). Son 168 proteinas sobre 161 secuencias porque varias comparten la
misma.

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
"windows": [
  {"window": "<evaluation_set_id>", "name": "serie-204-205",
   "t0_version": "204", "t1_version": "205",
   "pivot_snapshot_id": "...", "truth_profile": "projected",
   "toi_rule": "live_in_both_ends", "not_codes": "experimental",
   "code_revision": "...", "groundtruth_sha256": "..."}
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

1. `window_terms_excluded` y su contador, que es lo unico que puede cambiar la
   forma del dato y por tanto lo primero que quieres ver;
2. las siete tablas sin estado remapeado, con los shas y el orden estable;
3. `query_state` y `neighbour_state` por el marco de la verdad, con sus
   contadores y el assert del invariante;
4. `inputs_only`;
5. la columna de descripcion y los shas de contenido de `dataset`, que es la
   regla de los conjuntos aplicada al entregable.

Dime donde discrepas antes de que empiece por el 1.

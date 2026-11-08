# El estado, y las cinco decisiones, ya resueltas

Escrito el 2026-11-08 por la sesion del portatil. **Sustituye a
`REVISION-PENDIENTE-PROTEA-1139.md`**, que describia el #1139 como borrador
cuando ya iban trece PRs por delante: una nota de traspaso envejece antes de
que la lean, asi que esta dice solo lo que caduca despacio y apunta a donde
vive lo que caduca rapido.

## De donde viene lo que dice esta nota

Las cinco decisiones se tomaron el **2026-11-08**. Francisco dijo que si a los
cinco puntos en la sesion del sobremesa, a las 12:19 CET, y quedan en el
laboratorio como **D34** (`decisiones.md`, `1212e23`).

**Dos de las cinco las confirmo ademas en la sesion del portatil**, preguntado
directamente: la retirada real y el paso de ADR-D54 a `Accepted`. Esa
distincion esta aqui a proposito y no por formalismo: el relevo de una sesion a
otra es informacion y no su permiso, asi que **las dos acciones que escriben se
hicieron solo con lo confirmado aqui**, y las otras tres no requerian que esta
sesion escribiese nada.

**Cuidado con la numeracion.** Los cinco puntos de D34 no son los cinco de la
version anterior de esta nota. Coinciden cuatro: la retirada, las 161 largas,
`protea.training` y los vectores de texto. El quinto de D34 es el vocabulario.
Y **que ventanas entrenan el modelo minimo, que era el punto 4 de esta nota, NO
esta entre lo decidido**: sigue abierto, mas abajo, y nadie lo ha cerrado.

## Donde vive lo que caduca rapido

- **que revision sirve**: `curl -s http://127.0.0.1:8000/health`, que dice la
  servida, la declarada y si coinciden. No preguntes a un proceso ni a un
  arbol.
- **que es cada ventana**: `plans/INVENTARIO-VENTANAS.md`, con el nombre
  semantico al lado del id. Se regenera desde la base, no se escribe a mano.
- **el diseno del escritor de D56**: `plans/DISENO-ESCRITOR-D56.md`, ya
  acordado con el laboratorio, con los nombres, las diez tablas y las columnas
  que lee su cargador.
- **las decisiones de arquitectura**: los ADR del repositorio, en particular
  D56, que lleva la regla de fuga aplicada al construir y que el `window` es la
  clave de union y es el id completo.

## Las cinco de D34, y lo que queda de cada una

**1. La retirada de las ventanas del marco superado. HECHA.** Job
`b489e06b-6d66-44c6-ae2c-fe61b4ed55df`, `asked: 124`, `retired: 124`,
`originals_left_behind: 0`. **Comprobado contra el almacen y la base, no contra
su propio resumen**: `retired/` tiene 124 objetos y 1,40 GB, `eval_groundtruth`
baja de 293 objetos a 169, y la base baja de 211 ventanas a 87.

Sobreviven **cuatro** del marco superado, y sobreviven por la razon correcta:
`ea94e57e` y `7aa37929` (papel `valid`), `cb46395a` (papel `test`, el holdout,
con CERO resultados) y `c35ee267`, que la operacion rechazo porque tiene tres
resultados apuntandola. El holdout se salvo por su PAPEL y no por su recuento,
que es justo el argumento del inventario: un filtro de "sin resultados" lo
habria borrado.

Los **82 parquets de verdad huerfanos** siguen intactos, y la cuenta cuadra
sola: 169 objetos menos los 87 que una ventana nombra son esos 82. No se tocan
sin palabra de Francisco.

**2. Las 161 secuencias largas. Hay un paso previo que no estaba escrito.**
**2.429.553 residuos**, por ExactAnkh (`embed_batch_per_layer`,
protea-backends #47), en el nodo con tarjeta. Pendiente desde el 2026-11-04.

Lo que faltaba: **no se puede hacer la pasada de codigos sin que entren antes
en el banco**. `_pending_sequence_ids`, en `encode_residue_vocabulary.py`,
filtra por `SequenceEmbedding.embedding_config_id == source_id`, asi que una
secuencia sin vector en el banco fuente no falla: es invisible. Medido el
2026-11-08 sobre `f3a7fe16`:

    con vector      683.887
    sin vector          161
    de esas, con longitud > 8.259 residuos   161 de 161
    de esas, con longitud <= 8.259             0

O sea que el techo de la ruta es la unica causa y no falta ninguna por otro
motivo. El orden es: **#47 primero** (sigue en BORRADOR, y sacarlo de ahi es de
Francisco, porque el clasificador se lo niega a la sesion del nodo), despues
`compute_embeddings` con `skip_existing`, y la pasada de codigos detras, en la
tarjeta del nodo. Tambien es suya la otra pregunta que #47 deja escrita: **si
la ruta de atencion entra en la identidad del vector.**

Cuando #47 entre son del portatil el pin, la declaracion, el
`compute_embeddings` de las 161 y el nombre del banco extendido, poblacion con
su sha. **La tarjeta no se pide sin que lo diga Francisco.**

**3. `protea.training` vive en el sobremesa. Decidido.** El trabajador esta
activo alli. El arranque automatico al encender lo tiene que activar Francisco,
porque el clasificador se lo niega a esa sesion; hasta entonces, si el
sobremesa se reinicia, esa sesion lo arranca a mano antes de que se encole
nada. En el portatil **no hay consumidor y es a proposito**: esa cola sirve
tambien `export_research_dataset`, que es calculo sostenido, y eso esta
prohibido aqui. **Un job encolado ahi sin consumidor se queda QUEUED sin
error**, asi que si algo no consume, esto es lo primero que mirar.

**4. Los vectores de texto del eje. La ruta elegida, y el registro ya
aceptado.** El artefacto vive en el almacen del LABORATORIO y no en el de la
plataforma: `text-qwen3-embedding-4b.npz`, **224.759.782 bytes**, sha
`e32e15907aab0ec7637b6431164b28bf2dad50968ecb226480fcde563d82cbef`. Comprobado
el 2026-11-08 que no esta aqui: 6.445 objetos en trece prefijos y nada que
case. Hasta que este, la tabla `terms` **se niega**, que es lo correcto:
escribir el sha de un mensaje seria un localizador de bytes que nadie de este
lado puede comprobar.

**Los sube el sobremesa por la API**, que es la ruta que eligio Francisco, con
la subida por partes (`POST /model-weights/uploads`, `PUT .../{n}`,
`POST .../complete`) y el `kind` propio `term_text_vectors`, que entro en
PROTEA #1157. **Falta solo la credencial con rol OPERATOR**, que es de
Francisco dejar y todavia no esta. El cliente del nodo esta escrito y probado
en seco.

Y el registro **deja de ser un borrador**: ADR-D54 pasa a `Status: Accepted` en
PROTEA #1159, con dos cosas que no estaban dichas. La **excepcion del job**
queda escrita en el propio ADR: las dos escrituras del registro, la subida por
partes y el registro por referencia, no pasan por `POST /v1/jobs`, y eso es una
excepcion a la regla del proyecto. Su razon es mecanica (el mensaje de una
operacion esta acotado en dos veces 600 s y nada bombea el latido, asi que un
fichero de cientos de megas no viaja por el broker), lo que la sustituye esta
en el servidor y no en quien llama (clave por contenido, 409 con el id
existente, y el registro por referencia lee el objeto y rechaza la fila si el
hash no cuadra), y su limite es lo que la hace una excepcion y no una grieta:
**cubre escribir el registro y nada mas**, que toda operacion que LEE un peso
sigue saliendo por `POST /v1/jobs`.

**5. El vocabulario se queda en el primero (`43193409`)**, para el primer
conjunto de datos y para el experimento de las dos formas de entrada. La
corrida larga queda en reserva, con su copia de reanudacion en Picasso. **No
cambia nada en los escritores de D56**: `codes_config_id` sigue siendo un
parametro del payload, y `residue_refs` ya esta publicado contra ese
vocabulario.

## Lo que sigue abierto, y no lo cerro D34

**Que ventanas entrenan el modelo minimo.** La que mas cambia lo demas, y la
que **no** esta entre los cinco puntos decididos. Medido el 2026-11-08 sobre la
base, despues de la retirada: el marco vivo tiene **83** ventanas, de las que
**66 terminan en la release 211 o antes** y **17 terminan despues**. Esas 17
caen dentro del tramo 211->227 que puntua la ventana de validacion larga, asi
que `refuse_after_the_cut` las rechaza.

**La tanda publicada llevo 65 y no 66**, y la que falta tiene nombre:
`e84dfec8`, la gemela de **construccion (B)** de 160->177, la unica (B) del
marco vivo. Mismo pivote que las demas, pero sus nativas son la era de cada
extremo (`c15c24bb` y `2d2ca421`) en vez de las tres iguales al pivote, asi que
no es una ventana olvidada: es el otro cierre del mismo tramo, y su gemela (A)
`d3c8cd2e` si entro.

| opcion | ventanas | horizontes |
|---|---|---|
| lo publicado, construccion (A) | 65 | 16 a 1.144 dias |
| todo lo admisible por el corte | 66 | lo mismo, mas la (B) de 160->177 |
| el diseno del laboratorio | 53 | de 6 meses a 3 anos, con una primera tanda de ~16 |

D30 pide horizonte variable de 0 a 3 anos y la lectura de supervivencia tiene
tramos de hasta 1.096 dias. **Nadie sabe como salio la lista de pares que se
uso**, asi que no se puede confirmar ni desmentir que fuera el diseno de 53.

## Lo que esta hecho y no hay que repetir

- De las 87 ventanas que quedan, **86 llevan sha de verdad y los 86 son
  distintos**: ninguna comparte bytes con otra. Una no lo lleva, y 81 de las 87
  llevan `code_revision`, sobre cuatro revisiones distintas.
- `query_set` declara su poblacion y el esquema lo exige. Los cuatro conjuntos
  derivados tienen su ventana, su sha y su job, **verificados por bytes** y no
  leidos de su descripcion; el quinto se queda `legacy_undeclared` porque no
  hay nada registrado sobre su origen, y eso es la respuesta correcta.
  `code_revision` es NULL en los cuatro porque ningun job de exportacion
  registro ese campo, medido.
- `dianas-valid-211-227` y `dianas-valid-211-227-titular` vienen de ventanas
  **distintas**: `ea94e57e` con 63.734 dianas y `ea0f4334` con 40.531. La
  titular es la que reproduce el contrato del laboratorio al bit. Para
  `validacion-larga` se usa solo la titular.
- De las diez tablas de D56 estan escritas **cuatro**, y son estas cuatro y no
  otras, listadas desde el almacen el 2026-11-08:

  | tabla | clave del prefijo | sha | filas |
  |---|---|---|---|
  | `window_terms_out` | `transiciones-65-cut211` | `259ed608ec58` | 91.175 |
  | `queries` | `transiciones-65-cut211` | `7b43f018f2d9` | 674.327 |
  | `term_ancestors` | `eje-releases-2022-07-01` | `3a2aeca8588b` | 595.072 |
  | `residue_refs` | `banco-f3a7fe16` | `c4cf94b9c11b` | 683.887 |

  **`terms` NO esta escrita**, y una version anterior de esta nota decia que si:
  es la que espera los vectores. Las tres indexadas por el eje o por el banco no
  dependen de que ventanas se elijan. El cierre de `term_ancestors` sigue `is_a`
  y `part_of` **compartiendo la funcion** que cerro las ganancias, no
  coincidiendo en una lista.
- Las 683.887 filas de `residue_refs` son exactamente las secuencias con vector
  en el banco: una referencia por secuencia codificada, ni una mas.
- El vocabulario de residuos **SI tiene fila** en `model_weights`:
  `vocabulary-v1-06fed75ca76d17be`, sha `06fed75ca76d`, 260.233.730 bytes,
  `created_by = sobremesa-embeddings-2026-10`, con descripcion. Se dijo lo
  contrario en una conversacion y era falso: el precedente de importar un
  artefacto del laboratorio existe y se siguio.

## Dos niveles que se decidieron midiendo, no discutiendo

Las dos tablas que faltan por escribir tenian un nivel sin nombrar, y el
laboratorio lo pregunto antes de que se escribieran. Queda aqui porque dentro
de un mes parecera una eleccion de estilo y no lo es.

**El vecino es la ACCESION, en `neighbourhood` y en `neighbour_state`.** No es
una eleccion abierta: el banco de produccion se ordena por
`(Protein.accession COLLATE "C", SequenceEmbedding.chunk_index_s)`, una fila por
accesion, y su docstring ya dice que el 91 % de las consultas tienen vecinos a
distancia ~0, "ellas mismas, o gemelas que llevan la misma secuencia". Las
gemelas ya son donantes distintos. Y la union, que era la alternativa, habria
sido mala:

    secuencias con una sola accesion                     629.895
    secuencias con mas de una                             54.153  (162.640 accesiones)
    de las compartidas, isoformas de una sola entrada      3.084
    de las compartidas, con VARIAS entradas UniProt       51.069
    de las compartidas, con VARIOS organismos             39.301
    maximo de taxones sobre una secuencia                    115

En la release 211, 41.571 de las compartidas tienen anotaciones en **mas de
una** accesion. La union habria fundido hasta 115 organismos en un donante.

**`assigned_by` queda FUERA de las dos tablas.** Lo decide el marcador de
produccion: `_pin_annotation_order` ordena las anotaciones de cada donante por
`(go_term_id, evidence_code, qualifier)` y toma el codigo de evidencia "de la
primera fila que casa", asi que la fuente no se lee nunca. Medido sobre 1/16 de
la release 211 (605.508 filas, 42.982 proteinas): 443.920 fichas distintas,
**26,7 % de colapso**, y con `assigned_by` dentro de la clave 522.478, un factor
1,177 que son exactamente las rachas solapadas que harian rechazar la tabla. Se
queda en la base, recuperable por su clave, asi que no se pierde nada. El
cargador del laboratorio ya lo quito de `DECLARED_UNUSED` (`0fbbc0c`) y anadio
dos negativas: fichas repetidas en `query_state`, y ningun vecino en comun
entre `neighbourhood` y `neighbour_state` (`a432305`).

## Un artefacto que NO se usa

`s3://protea/transitions/transitions-serie-156-220/15f002ea/window_terms_out-f2a32e45e0b0.parquet`,
sha `f2a32e45...`, **queda superado**. Declaraba `cut_version` 211 sobre las 64
ventanas, incluidas las quince posteriores al corte. Lleva terminos de la
ontologia y no anotaciones, asi que no filtro nada, pero declaraba un alcance
que no era el suyo. Nada en la base apunta a ese objeto: queda huerfano en el
almacen y se dice aqui porque es donde se mira.

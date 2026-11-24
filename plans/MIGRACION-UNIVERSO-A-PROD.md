# La migracion del universo del sobremesa a produccion, y como se comprueba

Escrito el 2026-11-23 por la sesion del portatil. Recoge los criterios con los
que se acepta o se rechaza la carga, las cifras que hacen de contrato y lo que
ya esta verificado de la entrega de manifiestos de esa misma noche. No describe
el codigo: eso lo declara `plans/DECLARED-REVISION.txt`, y la entrada de
7edfb68f remite aqui.

## De donde viene cada cifra

Tres procedencias distintas, y la nota las separa a proposito porque no valen
lo mismo:

- **Medido aqui**, contra esta base con `scripts/db-query.sh` en solo lectura,
  o contra el codigo de la rama leyendo el blob del commit. Es lo unico que
  esta nota afirma por su cuenta.
- **Leido del fichero**, con una peticion por rango al archivo de EBI. Cuesta
  unos kilobytes sobre un fichero de decenas de gigas y resuelve de una vez lo
  que dos informes contaban distinto.
- **Relatado por el sobremesa**, en sus manifiestos sellados o por mensaje. La
  entrega esta verificada por digesto y por consistencia interna, pero el
  contenido describe un universo que esta base todavia no tiene.

El autor decidio el 2026-11-23, en la sesion del portatil y no por relevo, que
**esta maquina es el entorno de produccion**, que se sube lo que hay, que se
actualiza cada noche y que se migran tambien los datos: *"olvidate de lo que
haya aqui, hemos avanzado mucho mas en sobremesa"*. Queda abierta una sola
decision de las dos que habia: que se hace con los 69 conjuntos GOA que el
universo nuevo no usa.

## El orden de la secuencia, y por que el orden importa

1. La release de codigo, verificada por el `commit_id` de cada
   `direct_url.json`, NO por la salida de pip. Seis de los siete hermanos se
   mueven.
2. `protein` y `sequence`.
3. `protein_uniprot_metadata`.
4. Las anotaciones de los seis cortes.
5. Las seis fotos de corte.
6. Las cuatro ventanas LAFA y sus tablas de IA.
7. Los bancos, como ficheros (46 GB), cargados por operacion. Nada se
   recalcula aqui: la tarjeta de esta maquina no se toca.
8. Al final, y solo al final, la comparacion de digestos.

El orden no es gusto. La clave ajena de `protein_go_annotation` hacia `protein`
decide cuantas filas sobreviven a la carga. Los seis cortes ya existian aqui
con 54.336.735 filas sobre un corpus de 792.058 proteinas; el sobremesa declara
113.487.299 sobre 2,76 M de proteinas, 2,09 veces mas. Cargar los cortes antes
que el corpus reproduce los 54 M y el digesto falla por un motivo que no tiene
nada que ver con el codigo.

## Los digestos no son comparables a traves de la release

Los manifiestos de foto llevan dentro la tabla de canales y las revisiones de
las fuentes. La migracion que crea esas tablas,
`f0e6749f94cb_evidence_channel_tables`, va DENTRO de la release y es ancestro
del head que corre el sobremesa (`5d2e8c1b4a73`), asi que sus digestos se
calcularon ya con ellas. Antes de la release esta produccion no tiene la tabla
de canales y no puede producir un manifiesto comparable.

Corolario para el hito: la condicion de "reconstruido dos veces con los mismos
digestos" se evalua DENTRO de una revision, nunca a traves del limite de la
release. La seccion de la cabecera de los GAF da un segundo ejemplo concreto de
por que.

## Dos cuentas, dos contratos

El manifiesto cuenta **cada linea GAF** de sus miembros y su `rows.parquet` las
guarda todas. La tabla guarda **una fila por identidad** bajo
`uq_pga_annotation_identity`, que es (conjunto, proteina, termino,
COALESCE(evidencia), COALESCE(calificador), COALESCE(referencia)). Las lineas
que solo difieren en `with_from`, `assigned_by` o fecha colapsan en una.

| corte | manifiesto | tabla | colapsado | % |
|---|---|---|---|---|
| 160 | 15.127.014 | 14.698.123 | 428.891 | 2,84 |
| 177 | 15.223.386 | 14.728.210 | 495.176 | 3,25 |
| 194 | 20.495.791 | 19.844.139 | 651.652 | 3,18 |
| 205 | 9.607.172 | 9.124.036 | 483.136 | 5,03 |
| 211 | 23.600.054 | 22.496.815 | 1.103.239 | 4,67 |
| 227 | 33.707.963 | 32.595.976 | 1.111.987 | 3,30 |
| **total** | **117.761.380** | **113.487.299** | **4.274.081** | **3,63** |

**El contrato de la carga de `protein_go_annotation` son las cuentas de la
columna "tabla".** Las del manifiesto son el contrato de la foto: sus miembros
y las filas de su `rows.parquet`. El 113,5 M que circulaba antes era
`reltuples`, una estimacion del planificador; queda corregido a 113.487.299.

El colapso esta repartido en los seis, no concentrado en uno.

## CARGADO Y VERIFICADO: las seis fotos, el 2026-11-24 a las 01:36

Las seis estan dentro de `protea_universo`, cargadas por los trabajadores del
sobremesa contra la API de pruebas de esta maquina, y **cada cifra comparada con
la que se escribio ANTES de cargar**. Los dos totales del contrato salen
identicos: **113.487.299 filas** en `protein_go_annotation` y **7.830.125**
miembros en `cut_photo_member`.

Y la diferencia entre lineas y filas guardadas queda **partida en sus dos causas
reales**, que el cargador cuenta por separado (`rows_already_present` y
`rows_with_unknown_term`). Esto corrige la tabla de mas arriba, que llamaba
"colapsado" a la suma de las dos:

| corte | lineas | guardadas | colapsadas | rechazadas | suma |
|---|---|---|---|---|---|
| 160 | 15.127.014 | 14.698.123 | 428.891 | 0 | cierra |
| 177 | 15.223.386 | 14.728.210 | 495.176 | 0 | cierra |
| 194 | 20.495.791 | 19.844.139 | 651.652 | 0 | cierra |
| 205 | 9.607.172 | 9.124.036 | 483.124 | 12 | cierra |
| 211 | 23.600.054 | 22.496.815 | 1.102.171 | 1.068 | cierra |
| 227 | 33.707.963 | 32.595.976 | 1.111.784 | 203 | cierra |
| **total** | **117.761.380** | **113.487.299** | **4.272.798** | **1.283** | **cierra** |

Las **1.283 rechazadas** son filas cuyo termino GO no esta en el grafo de su
corte, y el mecanismo esta probado, no supuesto: `GO:0140718`, el unico termino
que rechaza el 205, **no existe en `releases/2021-10-26` y si existe en
`releases/2022-07-01` y en `releases/2025-07-22`**. Nacio entre la fecha del
grafo (2021-10-26) y la del fichero (2021-11-09). Se rechazan y se cuentan;
nunca se tiran en silencio.

**Dos contadores que se parecen y no son el mismo**, y confundirlos paro dos
veces el conductor del sobremesa:
- `unknown_evidence_keys` / `unknown_evidence_rows` viven en el **manifiesto**,
  son una propiedad del fichero contra la tabla de canales declarada, y dan
  **0 en los seis**;
- `unknown_terms` / `rows_with_unknown_term` los devuelve el **trabajo de
  carga**, dependen del grafo de la base que recibe y por eso no pueden estar en
  el manifiesto. Hoy: 0 en 160, 177 y 194; 1 termino en 205; 19 en 211; 10 en
  227. Coinciden con dev termino a termino.

**Las seis dicen `go_release_rule: declared`**, incluidos los tres GAF 2.1, asi
que el arreglo de la cabecera esta verificado de punta a punta sobre datos
reales y el grafo elegido sigue siendo el mismo que se midio de antemano.

Estado del corpus al cerrar esta fase: 2.758.480 proteinas, 2.523.987
secuencias, 6 conjuntos de anotacion, 7.699.626 miembros con taxon de 7.830.125,
base en 40 GB y 428 G libres en disco.

## La cuenta almacenada es funcion de (fichero, snapshot)

Consecuencia que el contrato no nombraba: el colapso bajo esa identidad y las
filas que se caen por termino ausente **dependen de la ontologia de cada
corte**, porque los `alt_id` que resuelven al mismo termino canonico colapsan y
los terminos que el snapshot no tiene no entran. Asi que las cuentas de arriba
no son una propiedad del `rows.parquet`. Reproducirlas aqui exige el mismo
snapshot por corte, y eso se comprueba por `obo_sha256`.

Los seis que hay en esta base, los seis sellados:

| corte | ontologia | obo_sha256 |
|---|---|---|
| 160 | releases/2016-09-30 | 7dc28e412128bea4f824493e02fa2db7862aef38d0d2df194f4c5e7d47b9f324 |
| 177 | releases/2018-04-02 | 9e429f39ccd1a380bb1af491611c5a0c6908ecd7c50f49fc8cb7072d8dfb3d00 |
| 194 | releases/2019-11-02 | f6a1a4cbafe7d1198704f6c1f86e49d5d804773fe8df6ed03ce6f4d5a4ce0fbf |
| 205 | releases/2021-10-26 | 6d1d1a24fcc179fdaf40353d83568e33690eabaa9a24c6c8003aacc155f8c331 |
| 211 | releases/2022-07-01 | 91eae63f06163aea5072d1d7c8d34a1f0cdf6295b23b527297bce4ac89dd022a |
| 227 | releases/2025-07-22 | d9a5670865816dd63dcdd49f76864d3a621990d8bcbb6b758e4cdfbfdb9f2982 |

Cinco coinciden sello a sello con los del sobremesa. El 160 no: aqui esta
emparejado con `releases/2016-09-30` y el sobremesa lo tiene con
`releases/2016-10-29` (`1d2761644f7a56b4...`), que **ya esta cargada aqui**
desde el 2026-10-08, el mismo dia que la que esta en uso. No hay que descargar
nada, y el 160 lo decide ADR-D60: *"Cut 160 takes the ontology its pairing rule
gives (2016-10-29)"*. No fue un defecto de carga sino un cambio de regla: el
modulo `cut_photo` entero nace con la release, y el 160 de aqui lo empareja el
cargador antiguo.

Coste de recargar el 160 bajo la regla nueva: **ninguna evidencia medida**.
Cuatro de las 87 ventanas referencian ese conjunto, pero no queda ni un
`evaluation_result` vivo, asi que son declaraciones sin resultados y nada
publicado se apoya en el emparejamiento viejo.

## sha256 de los manifiestos: los de la entrega y los de la reconstruccion

Los de la izquierda son los de la entrega del 2026-11-23, construidos a
4a052d2. Los de la derecha, las mismas fotos reconstruidas a 798210f2: mismos
datos byte a byte, manifiesto distinto.

| corte | entrega (4a052d2) | reconstruida (798210f2) |
|---|---|---|
| 160 | 0313f1d3fcc5 | 4fcb367044b6 |
| 177 | 30681e0deee1 | c5edf9ac4e1c |
| 194 | 16b768310221 | 937687865cac |
| 205 | 352bc18d5d69 | 7e5ed25b3273 |
| 211 | 377675277753 | 0683600e745e |
| 227 | 65710a9f9e26 | b3a8cad144f7 |

**Los que valen para la base limpia son los de la derecha**, porque son los de
las fotos que se cargan. Los de la izquierda quedan como lo que eran: el
contrato de una entrega ya verificada.

## sha256 de los manifiestos entregados, completos

| corte | tipo | sha256 |
|---|---|---|
| 160 | full | 0313f1d3fcc54a9b2368742b72938862634a6e153a956ac566edd911687b4a55 |
| 177 | full | 30681e0deee13cc43d2df9ca15a7e7607d14a427939963eeb83bec19c1a8f0d3 |
| 194 | full | 16b768310221134e174cdd26abce4f9c72fd07bd15037384db4b9a94e3eb965d |
| 205 | truth_only | 352bc18d5d69004e3f1f22f4f5d4f88eff80680da8bf873f9649b7995f5d5926 |
| 211 | full | 37767527775310437598fe460fa14c433d23ff053302ad727b024af56e33140b |
| 227 | full | 65710a9f9e26d2de5a39f464ea25ff76cd4d1e78ef16ccea9057784b88983fb0 |

## Las cuentas de miembros, que cierran

| corte | tipo | miembros | Swiss-Prot | vecinos | no revisadas | filas (manifiesto) |
|---|---|---|---|---|---|---|
| 160 | full | 1.131.551 | 552.259 | 507.840 | 71.452 | 15.127.014 |
| 177 | full | 1.186.657 | 557.012 | 555.133 | 74.512 | 15.223.386 |
| 194 | full | 1.479.088 | 561.176 | 831.006 | 86.906 | 20.495.791 |
| 205 | truth_only | 651.760 | 565.254 | 0 | 86.506 | 9.607.172 |
| 211 | full | 1.530.992 | 568.002 | 868.800 | 94.190 | 23.600.054 |
| 227 | full | 1.850.077 | 573.661 | 1.195.703 | 80.713 | 33.707.963 |

Comprobado aqui: **las seis sumas cierran exactas** (Swiss-Prot + vecinos + no
revisadas = miembros). Los vecinos de 205 son 0 por diseno, porque ese corte
solo cierra la ventana 177->205. Y el total, 7.830.125 miembros, cuadra con el
`cut_photo_member` de 7,84 M del inventario.

## El residuo de 205, que cierra al digito

12 tuplas de identidad con un unico termino, `GO:0140718`, que el snapshot de
205 (GO 2021-10-26) no tiene: se rechazan, no se tiran. Ningun colapso por
`alt_id` y ninguna fila en termino obsoleto. 9.607.172 lineas, menos 483.124
colapsadas son 9.124.048 distintas, menos 12 por termino ausente son
9.124.036, que es exactamente lo almacenado. El mecanismo es que la GAF de 205
es del 2021-11-09 y su grafo del 2021-10-26: un termino creado entre las dos
fechas aparece en la GAF y no en el grafo.

## La cabecera de los GAF: dos lectores en el mismo repositorio, uno ciego

Leido el 2026-11-23 de los seis ficheros del archivo de EBI, por rango:

| corte | gaf-version | fecha | clave de version | declara |
|---|---|---|---|---|
| 160 | 2.1 | `!Generated: 2016-10-31` | `!GO-version` | releases/2016-10-29 |
| 177 | 2.1 | `!Generated: 2018-04-23` | `!GO-version` | releases/2018-04-20 |
| 194 | 2.1 | `!Generated: 2019-11-12` | `!GO-version` | releases/2019-11-09 |
| 205 | 2.2 | `!date-generated: 2021-11-09` | `!go-version` | releases/2021-11-06 |
| 211 | 2.2 | `!date-generated: 2022-09-16` | `!go-version` | releases/2022-09-12 |
| 227 | 2.2 | `!date-generated: 2025-09-04` | `!go-version` | releases/2025-08-31 |

Los GAF 2.1 escriben la clave con mayusculas y los 2.2 en minuscula. El
repositorio lee esa cabecera en dos sitios y solo uno lo hace bien:

- `protea/core/operations/_gaf_header.py` compara con `line.lower()`, asi que
  el cargador de anotaciones **si** ve lo declarado y su guarda
  `assert_not_newer_than_declared` sigue viva;
- `protea/core/cut_photo/photo_io.py` usa `_HEADER_FIELD = ^!([a-z][a-z-]*):`,
  que no captura `!GO-version` ni `!Generated`, de modo que `go_release_rule`
  cae a la rama `cut_date` para 160, 177 y 194.

Se ve en la entrega: los manifiestos de los tres cortes 2.1 llevan
`date_generated`, `go_version` y `declared_go_release` vacios y
`go_release_rule` en `cut_date`; los tres 2.2 los llevan completos y la regla
en `declared`.

**Lo que el defecto no cambia.** Medido contra las ontologias cargadas aqui:
con la cota declarada y con la fecha de corte, el grafo elegido es el mismo en
los seis, porque **no hay ninguna ontologia cargada entre el grafo y la cota en
ninguna de las doce ventanas** (cero en las doce). `check_graph` de
`load_cut_photo` acepta las seis fotos bajo las dos reglas.

**Lo que si cambia. Escribi tres y son los seis, por un motivo que no habia
contado.** El arreglo rellena esos cuatro campos y mueve el JSON de 160, 177 y
194; pero el manifiesto guarda tambien **la revision que lo construyo**
(`build.manifest_pass`), asi que reconstruir con otra revision mueve los seis
digestos aunque los datos no cambien. Medido el 2026-11-23 sobre las seis fotos
reconstruidas a 798210f2: **todos los ficheros de datos son identicos byte a
byte** --members, rows, sequences, unreviewed_sequences, unknown_evidence y el
md5 del flujo de la knowledgebase-- y de `photo.json` solo cambian la revision
en los seis y, ademas, la cabecera GOA en los tres GAF 2.1. Cero diferencias
inesperadas en las seis.

Corolario, mas fuerte que el aviso original: **el sha256 de una foto es una
propiedad de (datos, revision), no de los datos.** Dos fotos con digesto
distinto pueden tener los mismos bytes de datos, y eso se comprueba salida a
salida, no por el manifiesto.

**Y una condicion, no una prohibicion.** Volver a medir las doce ventanas si se
carga cualquier ontologia nueva dentro de ellas; la de 211 abarca dos meses y
medio. Dentro de una de esas ventanas, `cut_date` elegiria un grafo mas nuevo
que el declarado y la guarda de la foto no lo veria.

`plans/GOA-ONTOLOGY-PAIRING.md` tenia razon y queda resuelto a su favor: GOA
160 declara `releases/2016-10-29`. Su fila marcada con (*) ya explicaba por que
esta base emparejo el 160 con 2016-09-30 -- el grafo declarado esta archivado
bajo la etiqueta de carpeta 2016-11-01 y la campana comparaba etiquetas --, y
`goa_campaign_driver.parse_plan` sigue leyendo una tabla correcta.

## Lo verificado de la entrega de manifiestos del 2026-11-23

Es una verificacion de lectura: nada de esa carpeta se ha ejecutado y nada se
ha cargado.

- **Digestos: 8 de 8.** `sha256sum -c SHA256SUMS` sale con codigo 0 sobre los
  seis manifiestos, `corpus-by-cut.json` y `LEEME.md`. El unico fichero no
  cubierto es `READY`, y eso es correcto por construccion: se escribe despues
  de los sellos. Su marca es 2026-11-23T02:00:26Z.
- **Los seis sellos de foto son los acordados: 6 de 6**, comparados
  mecanicamente contra la tabla de arriba.
- **Consistencia interna: 48 de 48.** Por corte: `members == superset +
  outside_superset`; los **siete canales de fila suman exactamente
  `member_rows`**; el `manifest_sha256` que declara `corpus-by-cut.json`
  coincide con el digesto real del `photo-<corte>.json`; y las cinco cifras que
  el sobremesa paso por mensaje coinciden con el JSON una por una.
- **Procedencia completa: 96 de 96 campos.** El `corpus-by-cut.json` que va a
  la documentacion no esta transcrito, esta **derivado**: sus 16 campos por
  corte coinciden uno a uno con los contadores de los manifiestos sellados. La
  cadena es auditable de punta a punta: manifiesto sellado -> corpus-by-cut
  -> tabla del PR de documentacion.
- **`unknown_evidence_keys: 0` y `unknown_evidence_rows: 0` en los seis.**
  Ningun codigo de evidencia cayo fuera de la tabla de canales declarada: los
  siete canales no son solo exhaustivos por aritmetica, lo son por declaracion.
- **Una sola tabla de canales en los seis cortes**, el mismo sello
  `ce0089ab6d08...`. Esto es lo que licencia comparar canales ENTRE cortes: si
  un corte usara otra tabla, una serie sobre cortes compararia dos
  definiciones distintas y pareceria un efecto.
- **Un contraste entre maquinas que no estaba pedido: las seis fechas de corte
  coinciden con el `source_published_at` de esta base.** 160 el 2016-11-01, 177
  el 2018-04-24, 194 el 2019-11-12, 205 el 2021-11-09, 211 el 2022-09-16 y 227
  el 2025-09-04.

### Una trampa de lectura en el JSON, que conviene documentar

`by_truth` y `by_curated_only` **no son una particion** del resto no
Swiss-Prot. En 160 suman 165.800 mientras que los no revisados con verdad o
curados son 71.452, y sumar `superset + by_truth + by_curated_only +
by_neighbour` da 1.225.899 frente a los 1.131.551 miembros reales: sobran
94.348. Son contadores de **motivo de admision**, y un miembro puede cumplir
mas de uno. La identidad que si cierra es `members = superset +
outside_superset`. Si esa cifra va a la documentacion, la frase tiene que decir
que son motivos y no clases, o alguien los sumara.

### Lo que NO esta verificado

- Que el contenido de los manifiestos describa el universo que dicen
  describir: esta base no tiene todavia la tabla de canales ni el modulo de
  fotos, que nacen con la release.
- Las cuentas de la columna "tabla" contra esta base: no son comparables
  todavia, porque el corpus de aqui es 792.058 proteinas frente a 2,76 M y los
  seis cortes de aqui suman 54.336.735 filas frente a 113.487.299. Eso esta
  medido y explicado, no es un fallo.

## El espacio

Medido el 2026-11-23, tras borrar los 28 conjuntos de prediccion antiguos: la
base esta en 242 GB y el disco en 537 G libres de 937. La carga completa crece
unos 85 GB en base mas unos 75 GB de ficheros en transito, y deja el pico sobre
377 G libres. Si se sustituyen los 69 conjuntos GOA que el universo nuevo no
usa, se liberan unos 193 GB de los 211 de `protein_go_annotation` y el disco
acaba con mas sitio que ahora.

## Lo que queda abierto

1. **Los 69 conjuntos GOA** que el universo nuevo no usa: conservarlos o
   sustituirlos. Son ~193 GB y los referencian las ventanas de la campana
   vieja. Decision del autor, no tecnica.
2. **El arreglo de `_HEADER_FIELD`**, que cuando entre movera tres de los seis
   sha256 de foto. Conviene que entre antes de que esos digestos se citen en
   ningun sitio como permanentes.
3. **Los 14,6 GB de indice redundante**, que necesitan una migracion.

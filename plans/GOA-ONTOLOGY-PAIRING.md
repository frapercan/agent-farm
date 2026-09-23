# GOA release -> OntologySnapshot: la eleccion, escrita

Medido el 2026-09-15 contra el archivo de EBI y el indice de releases publicadas
de GO. Esta tabla NO la deriva el codigo: `_gaf_header.assert_not_newer_than_declared`
solo RECHAZA un snapshot mas nuevo que el que el GAF declara; cual usar lo elige
una persona. Con 71 releases y una mediana de 18 dias de desfase, esa eleccion
repetida a ojo es donde se cuela el defecto que esta campaña ya pago una vez:
GOA 220 cargada contra una ontologia once meses posterior a su propia publicacion.

## La regla

Para cada release, el snapshot es **la release de GO publicada mas reciente en o
antes del build que el GAF declara en su cabecera**.

Hacia atras y no hacia adelante, y el motivo no es de gusto. El build exacto que
GOA uso YA NO EXISTE: `purl.obolibrary.org/obo/go/releases/<fecha>/go.owl`,
`go-basic.obo` y hasta el directorio del release devuelven 404 para las fechas
antiguas (comprobado sobre 2016-10-29 y 2018-07-15). NINGUNA de las 71 fechas
declaradas coincide con un grafo publicado. La release 168 parecia la excepcion
-- declara 2017-07-01 y existe un directorio 2017-07-01 -- pero el OBO que ese
directorio sirve lleva dentro `data-version: releases/2017-06-29`, dos dias
antes. Coincidia el nombre del directorio, no el grafo.

Ir hacia adelante daria un grafo que contiene todo lo que GOA uso, pero seria un
grafo que no existia cuando esas anotaciones se hicieron, y la guarda lo rechaza.
Ir hacia atras pierde los terminos creados en el hueco. La diferencia que decide:
**perder es contable e inventar no**. `load_goa_annotations` descuenta cada
go_id que no resuelve en `annotations_skipped`; un grafo posterior no deja rastro.

## Lo que cuesta el hueco, medido

Sobre GOA 160, que declara 2016-10-29 y recibe el snapshot 2016-10-01:

    snapshot elegido    2016-10-01    45.433 terminos
    siguiente publicado 2016-11-01    45.656 terminos
    añadidos en el mes que contiene el build declarado: 239 (0,52% del vocabulario)
    retirados: 16

Es cota superior por dos motivos: son los terminos del mes entero, y una release
solo referencia un termino nuevo si algo se anoto contra el en esos dias.
LEER `annotations_skipped` DE CADA CARGA: es el numero real, y ya existe.

## La tabla

Cuatro fechas por fila, porque tres de ellas se han confundido entre si alguna
vez. `declara` es el `!go-version` de la cabecera del GAF. `directorio` es el
segmento de `release.geneontology.org/<fecha>/` desde donde se descarga el OBO,
y es lo unico que esta tabla elige. `grafo` es el `data-version` que el propio
fichero lleva DENTRO, que es lo que la base guarda en
`ontology_snapshot.obo_version` y lo unico que
`assert_not_newer_than_declared` compara. `deriva` es lo que el directorio se
separa de su grafo; `desfase` va de `declara` a `grafo`, no al directorio.

El orden de las columnas no es libre: `goa_campaign_driver.parse_plan` lee la
tercera fecha de cada fila como el directorio y exige un `N d` detras. `grafo`
y `deriva` van despues por eso.

    GOA   declara      directorio   desfase  grafo        deriva
    160   2016-10-29   2016-10-01     29 d  2016-09-30   +1 d
    161   2016-11-26   2016-11-01     28 d  2016-10-29   +3 d
    162   2017-01-14   2017-01-01     21 d  2016-12-24   +8 d
    163   2017-02-11   2017-02-01     11 d  2017-01-31   +1 d
    164   2017-03-11   2017-03-01     11 d  2017-02-28   +1 d
    165   2017-04-07   2017-04-01      7 d  2017-03-31   +1 d
    166   2017-05-04   2017-05-01      6 d  2017-04-28   +3 d
    167   2017-06-02   2017-06-01      3 d  2017-05-30   +2 d
    168   2017-07-01   2017-07-01      2 d  2017-06-29   +2 d
    169   2017-08-23   2017-08-01     23 d  2017-07-31   +1 d
    170   2017-09-23   2017-09-01     23 d  2017-08-31   +1 d
    171   2017-10-21   2017-10-01     21 d  2017-09-30   +1 d
    172   2017-11-18   2017-11-01     18 d  2017-10-31   +1 d
    173   2017-12-12   2017-12-01     12 d  2017-11-30   +1 d
    174   2018-01-25   2018-01-01     27 d  2017-12-29   +3 d
    175   2018-02-20   2018-02-01     19 d  2018-02-01
    176   2018-03-22   2018-03-10     12 d  2018-03-10
    177   2018-04-20   2018-04-02     18 d  2018-04-02
    178   2018-05-14   2018-04-02     42 d  2018-04-02
    179   2018-06-19   2018-06-01     18 d  2018-06-01
    180   2018-07-15   2018-07-02     13 d  2018-07-02
    181   2018-09-07   2018-09-05      2 d  2018-09-05
    182   2018-10-07   2018-10-01      6 d  2018-10-01
    183   2018-10-30   2018-10-08     22 d  2018-10-08
    184   2018-11-30   2018-11-15     15 d  2018-11-15
    185   2019-01-11   2019-01-01     10 d  2019-01-01
    186   2019-02-07   2019-02-01      6 d  2019-02-01
    187   2019-03-29   2019-03-18     10 d  2019-03-19   -1 d
    188   2019-05-04   2019-04-17     17 d  2019-04-17
    189   2019-06-02   2019-06-01      1 d  2019-06-01
    190   2019-06-28   2019-06-09     18 d  2019-06-10   -1 d
    191   2019-07-17   2019-07-01     16 d  2019-07-01
    192   2019-10-03   2019-07-01     94 d  2019-07-01
    193   2019-10-03   2019-07-01     94 d  2019-07-01
    194   2019-11-09   2019-11-01      7 d  2019-11-02   -1 d
    195   2019-12-14   2019-12-09      5 d  2019-12-09
    196   2020-02-20   2020-01-01     50 d  2020-01-01
    197   2020-04-18   2020-03-25     26 d  2020-03-23   +2 d
    198   2020-06-12   2020-06-01     11 d  2020-06-01
    199   2020-08-04   2020-07-16     19 d  2020-07-16
    200   2020-09-30   2020-09-10     20 d  2020-09-10
    201   2020-11-28   2020-11-17     10 d  2020-11-18   -1 d
    202   2021-02-08   2021-02-01      7 d  2021-02-01
    203   2021-04-02   2021-02-01     60 d  2021-02-01
    204   2021-06-06   2021-05-01     36 d  2021-05-01
    205   2021-11-06   2021-10-26     11 d  2021-10-26
    211   2022-09-12   2022-07-01     73 d  2022-07-01
    212   2022-11-12   2022-11-03      9 d  2022-11-03
    213   2023-01-30   2023-01-01     29 d  2023-01-01
    214   2023-03-12   2023-03-06      6 d  2023-03-06
    215   2023-05-12   2023-05-10      2 d  2023-05-10
    216   2023-07-10   2023-06-11     29 d  2023-06-11
    217   2023-09-10   2023-07-27     45 d  2023-07-27
    218   2023-11-06   2023-10-09     28 d  2023-10-09
    219   2024-01-28   2024-01-17     11 d  2024-01-17
    220   2024-04-13   2024-03-28     16 d  2024-03-28
    221   2024-06-13   2024-06-10      3 d  2024-06-10
    222   2024-07-27   2024-06-17     40 d  2024-06-17
    223   2024-10-11   2024-09-08     33 d  2024-09-08
    224   2024-12-15   2024-11-03     49 d  2024-10-27   +7 d
    225   2025-03-07   2025-02-06     29 d  2025-02-06
    226   2025-04-27   2025-03-16     42 d  2025-03-16
    227   2025-08-31   2025-07-22     40 d  2025-07-22
    228   2025-11-06   2025-10-10     27 d  2025-10-10
    229   2025-11-30   2025-10-10     51 d  2025-10-10
    230   2026-03-01   2026-01-23     37 d  2026-01-23
    231   2026-04-06   2026-03-25     12 d  2026-03-25
    232   2026-04-27   2026-03-25     33 d  2026-03-25
    233   2026-05-31   2026-05-19     12 d  2026-05-19
    234   2026-06-15   2026-05-19     27 d  2026-05-19
    235   2026-07-05   2026-06-19     20 d  2026-06-15   +4 d

## Resumen

    releases                    71   (160..235; 206-210 no existen en el archivo)
    snapshots distintos          64
    coinciden exactamente         0   (ninguna; ver "La regla")
    directorio != grafo          22 de 71   (deriva de -1 a +8 dias)
    desfase mediana              18 d      minimo 1 d (GOA 189)   maximo 94 d
    peso de los GAF          734,2 GiB comprimidos
    span              2016-10-29 .. 2026-07-05

Muestreados 6 de los 64 snapshots repartidos en ocho anos: los seis responden 206
en release.geneontology.org. Ninguna release necesita `allow_unverified_ontology`.

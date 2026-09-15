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
antiguas (comprobado sobre 2016-10-29 y 2018-07-15). Solo 1 de las 70 fechas
declaradas coincide con un build publicado: la release 168, que declara
2017-07-01.

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

    GOA   declara      snapshot     desfase
    160   2016-10-29   2016-10-01    28 d
    161   2016-11-26   2016-11-01    25 d
    162   2017-01-14   2017-01-01    13 d
    163   2017-02-11   2017-02-01    10 d
    164   2017-03-11   2017-03-01    10 d
    165   2017-04-07   2017-04-01     6 d
    166   2017-05-04   2017-05-01     3 d
    167   2017-06-02   2017-06-01     1 d
    168   2017-07-01   2017-07-01     0 d   <- unico exacto
    169   2017-08-23   2017-08-01    22 d
    170   2017-09-23   2017-09-01    22 d
    171   2017-10-21   2017-10-01    20 d
    172   2017-11-18   2017-11-01    17 d
    173   2017-12-12   2017-12-01    11 d
    174   2018-01-25   2018-01-01    24 d
    175   2018-02-20   2018-02-01    19 d
    176   2018-03-22   2018-03-10    12 d
    177   2018-04-20   2018-04-02    18 d
    178   2018-05-14   2018-04-02    42 d
    179   2018-06-19   2018-06-01    18 d
    180   2018-07-15   2018-07-02    13 d
    181   2018-09-07   2018-09-05     2 d
    182   2018-10-07   2018-10-01     6 d
    183   2018-10-30   2018-10-08    22 d
    184   2018-11-30   2018-11-15    15 d
    185   2019-01-11   2019-01-01    10 d
    186   2019-02-07   2019-02-01     6 d
    187   2019-03-29   2019-03-18    11 d
    188   2019-05-04   2019-04-17    17 d
    189   2019-06-02   2019-06-01     1 d
    190   2019-06-28   2019-06-09    19 d
    191   2019-07-17   2019-07-01    16 d
    192   2019-10-03   2019-07-01    94 d
    193   2019-10-03   2019-07-01    94 d
    194   2019-11-09   2019-11-01     8 d
    195   2019-12-14   2019-12-09     5 d
    196   2020-02-20   2020-01-01    50 d
    197   2020-04-18   2020-03-25    24 d
    198   2020-06-12   2020-06-01    11 d
    199   2020-08-04   2020-07-16    19 d
    200   2020-09-30   2020-09-10    20 d
    201   2020-11-28   2020-11-17    11 d
    202   2021-02-08   2021-02-01     7 d
    203   2021-04-02   2021-02-01    60 d
    204   2021-06-06   2021-05-01    36 d
    205   2021-11-06   2021-10-26    11 d
    211   2022-09-12   2022-07-01    73 d
    212   2022-11-12   2022-11-03     9 d
    213   2023-01-30   2023-01-01    29 d
    214   2023-03-12   2023-03-06     6 d
    215   2023-05-12   2023-05-10     2 d
    216   2023-07-10   2023-06-11    29 d
    217   2023-09-10   2023-07-27    45 d
    218   2023-11-06   2023-10-09    28 d
    219   2024-01-28   2024-01-17    11 d
    220   2024-04-13   2024-03-28    16 d
    221   2024-06-13   2024-06-10     3 d
    222   2024-07-27   2024-06-17    40 d
    223   2024-10-11   2024-09-08    33 d
    224   2024-12-15   2024-11-03    42 d
    225   2025-03-07   2025-02-06    29 d
    226   2025-04-27   2025-03-16    42 d
    227   2025-08-31   2025-07-22    40 d
    228   2025-11-06   2025-10-10    27 d
    229   2025-11-30   2025-10-10    51 d
    230   2026-03-01   2026-01-23    37 d
    231   2026-04-06   2026-03-25    12 d
    232   2026-04-27   2026-03-25    33 d
    233   2026-05-31   2026-05-19    12 d
    234   2026-06-15   2026-05-19    27 d
    235   2026-07-05   2026-06-19    16 d
## Resumen

    releases                    71   (160..235; 206-210 no existen en el archivo)
    snapshots distintos          64
    coinciden exactamente         1   (GOA 168)
    desfase mediana              18 d      maximo 94 d
    peso de los GAF          734,2 GiB comprimidos
    span              2016-10-29 .. 2026-07-05

Muestreados 6 de los 64 snapshots repartidos en ocho anos: los seis responden 206
en release.geneontology.org. Ninguna release necesita `allow_unverified_ontology`.

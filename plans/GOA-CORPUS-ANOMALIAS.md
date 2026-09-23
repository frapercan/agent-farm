# Anomalias del corpus GOA, medidas

Hechos sobre el archivo de GOA que no se deducen del codigo ni de la base, y que
cambian como se lee una serie. Cada entrada dice como se midio.

## GOA 192 y 193 son el mismo fichero

`goa_uniprot_all.gaf.192.gz` y `goa_uniprot_all.gaf.193.gz` son el mismo
contenido publicado dos veces bajo dos numeros de release.

Medido por dos vias independientes.

**Aguas arriba**, contra el indice de directorios de EBI: mismo tamano, mismo
`Last-Modified` al segundo, mismo sha256 de los primeros 16 KiB, y el mismo
`!Generated:` en la cabecera.

**Aguas abajo**, contra lo que la plataforma cargo:

    release   anotaciones   !go-version declarado
    191        5.380.135    releases/2019-07-17
    192        5.493.899    releases/2019-10-03
    193        5.493.899    releases/2019-10-03
    194        5.514.248    releases/2019-11-09

Las dos cifras del medio coinciden hasta la unidad y declaran el mismo build,
mientras sus vecinas difieren en cientos de miles. Dos cargas independientes,
por caminos distintos, del mismo fichero.

### Que rompe

Cualquier lectura de las releases como serie temporal. El intervalo 192 -> 193
aporta un delta de CERO que no es una observacion: es el mismo dia contado dos
veces. En un analisis de tasas normalizadas por dia, ademas, ese tramo tiene
denominador no nulo y numerador nulo, asi que no se cancela solo -- hunde la
tasa del tramo y desplaza cualquier ranking de "el evento mas violento".

### Que NO rompe

Nada en la carga. Son dos `annotation_set` legitimos con distinto
`source_version`, cada uno completo y atado a su ontologia. La identidad de
`_existing_annotation_set` es (source, source_version, ontology_snapshot_id),
asi que no colisionan ni se reusan el uno al otro. El corpus esta bien; lo que
esta mal es tratarlos como dos puntos de una serie.

### Como usarlo

Al construir cualquier serie sobre releases, descartar una de las dos. Da igual
cual: son identicas. Descartar 193 mantiene la numeracion de los cortes que ya
se citan.

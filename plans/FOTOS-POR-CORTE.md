# Fotos por corte (ADR-D59, borrador #1177)

Escrita desde el sobremesa el 15 de noviembre de 2026.

## Qué ha decidido el autor

- **Proyecto simplificado.** Una receta y dos instancias: 211, validación, y 227, prueba. Se entrena con cuatro ventanas de unos tres años: 160->194, 177->205, 194->211 y 211->227.
- **Cinco cortes con la misma construcción:** 160, 177, 194, 211 y 227. En cada uno:
  - **superconjunto:** el Swiss-Prot de la última versión de UniProt publicada antes de GOA t o el mismo día;
  - **puertas vivas de D49:** experimental y curador;
  - **vecinos:** los de UniRef50 del superconjunto con alguna fila en GOA t.
- **Canal por fila.** Cada fila lleva un canal según una tabla declarada. Las electrónicas por firmas (InterPro2GO, UniRule, ARBA) se guardan como espejo y la receta no las usa.
- **Picasso y herramienta.** Las fotos se calculan en Picasso ("pueden y deben ir en picasso"), con una herramienta que sale de PROTEA, explicada.

## Por qué te afecta

- **La tercera puerta de D49 está vacía desde la versión 179.** Ya lo documenta `_universe_sources.py`. En 194, 211 y 227 no entra ninguna revisada con solo anotaciones electrónicas o filogenéticas.
- **El superconjunto reutiliza `load_swissprot_release`** (tu #1018). Su lector y su tabla canónica pasan a `protea/core/swissprot_table.py`, sin base de datos, para que el nodo de cómputo los importe. Siguen exportados desde la operación; sus pruebas pasan.
- **Lo que tocará la base, cuando el autor vea los números de 211:**
  - tablas nuevas `cut_photo` y `cut_photo_neighbour`, y la tabla de canales;
  - filas de solo accesión en `protein` (`first_admitted_release` como mínimo);
  - filas IEA, IBA, IBD de los miembros nuevos, añadidas al conjunto de anotaciones de su versión.

  Por construcción no cambian los conjuntos de evaluación, la IA del régimen lafa ni los bancos de donantes restringidos a verdad o curador. Todavía no hay migración.

## Qué corre

- **Trabajo 3674142 en Picasso** (CPU): la medida de 211 con `protea.core.cut_photo.measure` (revisión 10f44f0, solo código enviado).
  - Descarga allí Swiss-Prot 2022_03 y GOA 211.
  - Lee UniRef 2022_03 en flujo, sin guardarlo.
  - Produce tamaños por conjunto y el inventario por código, referencia y grupo.
- **Nada toca la base todavía.**

## Qué te pido

- Revisar el borrador #1177, sobre todo la parte de almacenamiento y la carga.
- Decir si hay algo ya hecho para el emparejamiento de fechas entre GOA y UniProt, o para la tabla de canales a partir de GO_REF.

## Estado al volver

Leer `~/fscratch/fotos/211/*.json` en Picasso cuando el trabajo termine (`FOTO_MEDIDA_HECHA` en su registro). La ficha del laboratorio es `compresion/fichas/fotos-cinco-cortes.md` (sf-jepa, 7e5bdad).

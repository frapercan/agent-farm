# Los exámenes del vocabulario, dentro de la plataforma

Escrito el 2026-11-08 por la sesión del sobremesa, **antes de escribir una línea
de código**, para que la sesión del portátil lo lea y lo convierta en un ADR y
una operación. Es una especificación y no un diseño cerrado. Las tres
preguntas que eran del autor están respondidas al final, en "Lo que decidió el
autor".

## Por qué

El autor, 2026-11-08: ningún examen fuera de la plataforma; solo el
entrenamiento. Hoy los cuatro exámenes del vocabulario existen solo en el
laboratorio, y para decidir los vocabularios de D35 a D38 hizo falta una
excepción puntual (laboratorio D37, ampliada en D38). Para cerrar el
componente del vocabulario, el que se adopte se examina aquí, y cada candidato
futuro también. En la plataforma no hay ninguna operación de examen: lo
comprobé en `develop` el 2026-11-08.

## Qué miden los cuatro exámenes

El código de referencia está en el laboratorio, rama `compresion`,
`compresion/scripts/`. Lo que sigue resume sus docstrings, que son la
especificación.

1. **Dominios** (`step11_dominios.py`). Para cada concepto de tipo dominio
   (DOMAIN, REPEAT, ZN_FING, DNA_BIND de Swiss-Prot 2022_03, por nombre) y cada
   rasgo del vocabulario, se ordenan los residuos por la activación del rasgo.
   Cuenta la **AP por residuo**. El rasgo se elige en una mitad de las proteínas
   y se mide en la otra, en los dos sentidos, y se promedia. La media se toma
   sobre los conceptos leídos. Informa también F1 por instancia, detección,
   cobertura y bordes, pero la regla usa la AP.
2. **Sitios** (`step7_localization.py`, examen v2). Funciona igual, sobre los
   conceptos de sitio: sitios activos, de unión (también por ligando
   frecuente), residuos catalíticos y el resto de tipos de rasgo de Swiss-Prot
   2022_03 que marcan residuos, separados por clase de evidencia. La AP se
   calcula con histogramas de 256 niveles del máximo de cada rasgo en el
   examen; los residuos donde el rasgo no está activo comparten el último
   puesto.
3. **Dominios en grupo** (`step22_dominios_grupo.py`, n = 10). En la mitad de
   selección se eligen los n rasgos con mayor diferencia entre su activación
   media dentro y fuera del concepto. Se ajusta una regresión logística sobre
   ellos (estandarizada, L2 1e-4, L-BFGS) y se mide la AP por residuo de su
   puntuación en la otra mitad, con los empates juntos.
4. **Sitios en grupo** (`step23_sitios_grupo.py`). Igual, pero como curva sobre
   n = 1, 2, 5, 10, 20 y 50 (los tamaños de SAEBench). Se informa sin regla.

**Comparación emparejada** (`step38_remuestreo_examenes.py`, con los volcados de
`volcado_examen.py`). Se remuestrean proteínas con reemplazo dentro de cada
mitad, 1.000 veces, con las mismas extracciones para todos los vocabularios. En
cada extracción se recalcula la AP como lo hace el examen, con las elecciones de
rasgo de las mitades completas. El resultado es la media de cada vocabulario, su
error, y la diferencia con un vocabulario de referencia con su intervalo del
95 %. La regla de D37 se lee sobre esto.

## Los datos de examen

Hay dos poblaciones, construidas una vez y congeladas. Tienen que entrar en la
plataforma como conjuntos declarados con su huella, por la regla de 2026-11-08
de conjuntos declarados y descritos.

| examen | construido por | proteínas | otros ficheros (sha256, 16 primeros) |
|---|---|---|---|
| sitios v2 | `step10_exam_v2.py` | 3.335 (`split.parquet` 0e7d127f64e23749) | `sites.parquet` a9b06c7be70d4f0f, 1.986.242 filas; `concepts.json` |
| dominios | `step11_exam_dominios.py` | 4.227 (`proteins.parquet` 9f16e891b6c15226; `split.parquet` d08b23f957641c1e) | `instances.parquet` 6039e18e3ca1dd18, 10.070 instancias; `concepts.json` |

En el sobremesa están en `Thesis2/storage/sf-jepa/runs-world/subset-rapido/exam/{v2,dominios}`.

- **Dos cortes de mitades, y no hay que confundirlos.** El primero aparta un
  conjunto de confirmación: las proteínas con `sha256(accesion + ':confirm')`
  impar, y en dominios además un tercio de los conceptos. Ese conjunto **no se
  ha leído nunca**. El segundo, dentro del conjunto de selección, decide qué
  mitad elige el rasgo y cuál lo mide: la paridad de `sha256(accesion)`. Todas
  las lecturas de hoy son de la selección (`--half selection`). Contados el
  2026-11-08 en `split.parquet` y `concepts.json`, solo la pertenencia y sin
  leer ninguna etiqueta:

  | | sitios v2 | dominios |
  |---|---|---|
  | proteínas | 3.335 | 4.227 |
  | conjunto de selección | 1.662 (1.294 sin las de la escala de 20k: 627 y 667) | 2.128 (1.717 sin las de 20k: 882 y 835) |
  | conjunto de confirmación | 1.673 | 2.099 |
  | conceptos de selección | 79 | 71 |
  | conceptos reservados, nunca leídos | 42 (de 23 familias reservadas) | 40 |
  | conceptos pequeños, sin leer | 47, y 1 solo para informar | 9 |

  En sitios, dos familias se miraron antes de congelar el examen
  (`read_before`: sitio activo y unión, experimentales).
- **Independencia del entrenamiento.** Los exámenes quitan las proteínas que
  usaron los diccionarios, por accesión y por secuencia idéntica.
  `--out-of-sample 20k` informa sin las de la escala de 20k, de la que salió
  v1. `step11_homologia_examenes.py` mide además los homólogos al 30 % con 80 %
  de cobertura frente a cada escala de entrenamiento. En la plataforma, cada
  vocabulario tendría que declarar su población de entrenamiento, para que el
  examen sepa qué excluir. Hoy `model_weights` no la lleva.

## Qué necesita la plataforma

- **Entradas:**
  - un vocabulario registrado (`model_weights`, kind `residue_vocabulary`);
  - las dos poblaciones de examen con sus conceptos;
  - el vocabulario de referencia contra el que se compara.
- **Los códigos de las proteínas de examen.** Medido el 2026-11-08 desde el
  sobremesa, con una consulta de solo lectura por accesión:

  | examen | proteínas | en `protein` | con vector en `f3a7fe16` | con códigos de v1 (`43193409`) | secuencia de hoy distinta de la del examen |
  |---|---|---|---|---|---|
  | sitios v2 | 3.335 | 3.335 | 3.335 | 3.335 | **10** (0,30 %) |
  | dominios | 4.227 | 4.227 | 4.227 | 4.227 | **40** (0,95 %) |

  - **Examinar v1 no necesita ninguna pasada:** sus códigos existen para las
    7.562. La pasada restringida solo hará falta para un vocabulario futuro que
    no cubra el corpus, y entonces sobre proteínas que ya estén en el banco.
  - **Las 50 de secuencia distinta son un problema de posiciones, no de
    cobertura.** Los conceptos de examen son posiciones en la secuencia de
    Swiss-Prot 2022_03 (`proteins.parquet` lleva esa secuencia). La plataforma
    guarda la de hoy (`resolve_protein_sequences`), y sus códigos están
    calculados sobre ella; hay casos de 377 residuos frente a 1.751. En esas 50,
    un concepto apuntaría a residuos que no son. La población de examen debe
    declararse como pares (accesión, md5 de la secuencia del examen). El examen
    solo usa las proteínas cuya secuencia en la plataforma coincide, y cuenta y
    nombra las demás.
  - **Por eso la aceptación no puede ser contra los números de D37 tal cual,**
    que incluyen las 50. Habrá que hacerla contra el examen del laboratorio
    corrido sin ellas, con las mismas elecciones de rasgo calculadas sin
    ellas.
- **Salidas:**
  - una fila por (vocabulario, examen, concepto) y otra por medias;
  - los volcados para el remuestreo emparejado;
  - las diferencias frente a la referencia con su intervalo;
  - todo con su job, su revisión y las huellas de las poblaciones.
- **Aceptación, exacta y sobre los códigos cuantizados (decisión 1):** en el
  conjunto de selección y sin las 50 proteínas de secuencia distinta, el examen
  portado debe dar la misma AP, concepto a concepto, que los scripts del
  laboratorio corridos sobre los mismos códigos cuantizados de v1.
  - Los códigos cuantizados de la plataforma y los del codificador de
    referencia del laboratorio son idénticos bit a bit
    (`compresion/vocabulario-v1/compara-plataforma.json` y `puerta3.json`: 0 de
    309.370.880 entradas distintas). Así que cualquier diferencia vendrá del
    examen, no del código.
  - El sobremesa aporta esos vectores de prueba: v1 cuantizado y sin cuantizar,
    los dos sin las 50. Es la única corrida de examen que queda en el
    laboratorio. Sirve para aceptar el examen portado, no para elegir nada.
  - Las corridas de D37 y D38 en Picasso
    (`vocabulario-final/examenes/{dominios,sitios,grupo,sitios-grupo}-d37-*`, con
    sus volcados) incluyen las 50 y están sin cuantizar, así que no valen tal
    cual como aceptación.
- **Lo que cuesta cuantizar, medido una vez:** la diferencia entre esas dos
  corridas de v1, sobre las mismas proteínas. Enlaza los números de hoy, que son
  continuos, con los de la plataforma. En reconstrucción, v1 pasa de R2 0,7592 a
  0,7534 (`meta_json` del artefacto 06fed75c). Los exámenes ya agrupan las
  activaciones en histogramas (256 niveles del máximo de cada rasgo en sitios),
  así que se espera poco.

## Lo que decidió el autor (2026-11-08, hacia las 21:00)

Las tres preguntas eran: códigos cuantizados o continuos, si se usa una vez el
conjunto de confirmación y si se mantienen las poblaciones. A las dos primeras
respondió con otras ("¿Qué es mejor?", "Háblame en conjuntos... ¿cuál?"). A la
tercera: "Quiero ser fiel a nuestro estado del arte curado... utiliza el más
apropiado. El objetivo es lo que sea... al final tenerlo a la vista y depositado
en la plataforma para la tesis". A la propuesta que sigue: "Ok".

1. **Se examinan los códigos cuantizados que guarda la plataforma,** los que lee
   el modelo. Así el examen certifica lo depositado.
   - Los rasgos activos son los mismos que sin cuantizar; solo su valor se
     redondea a 256 niveles.
   - Cada candidato se registra con su tabla de niveles, como v1, antes de
     examinarse.
   - Lo que cuesta cuantizar se mide una vez, en v1 (ver la aceptación).
2. **El conjunto de confirmación se usa una sola vez, al final, por la
   plataforma,** con los candidatos y la regla escritos antes (laboratorio D39).
   - El rasgo de cada concepto se elige en todo el conjunto de selección y se
     mide en las proteínas de confirmación.
   - Los conceptos reservados, nunca leídos, dan además una lectura aparte, de
     conceptos nuevos.
   - Ese es el número de la tesis. Hasta entonces todo se lee en el conjunto de
     selección.
   - En sitios, las dos familias que se miraron antes de congelar el examen se
     informan aparte.
3. **Las poblaciones se quedan como están:** las anotaciones curadas de
   Swiss-Prot 2022_03, la misma versión que la UniRef50 del entrenamiento. Todo
   lo leído hasta hoy está sobre ellas.
   - Entran como conjuntos declarados, por la regla de 2026-11-08: pares
     (accesión, md5 de la secuencia del examen), con la huella de cada fichero,
     su descripción, su derivación (script y commit) y la partición en
     selección y confirmación.
   - Las 50 proteínas cuya secuencia de hoy difiere (10 de sitios y 40 de
     dominios) quedan fuera y se nombran.
   - El fin: que las poblaciones, los vocabularios, los resultados por concepto
     y la lectura final queden depositados y a la vista en la plataforma.

## Reparto que propongo

- **El sobremesa** especifica (este documento), aporta los vectores de prueba y
  revisa antes de que nada corra.
- **El portátil** escribe el ADR, registra las poblaciones como conjuntos
  declarados y escribe la operación.

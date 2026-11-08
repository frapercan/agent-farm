# Los exámenes del vocabulario, dentro de la plataforma

Escrito el 2026-11-08 por la sesión del sobremesa, **antes de escribir una línea
de código**, para que la sesión del portátil lo lea y lo convierta en un ADR y
una operación. Es una especificación y no un diseño cerrado: lo que está en
"preguntas abiertas" no se decide aquí.

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
  las lecturas de hoy son de la selección (`--half selection`).
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
- **Los códigos de las proteínas de examen.** Si están en el banco, los de v1 ya
  existen (`residue_refs`). Para un vocabulario nuevo hace falta una pasada de
  `encode_residue_vocabulary` restringida a esas 7.562 proteínas, que hoy no
  admite una población. Hay que medir cuántas de las 7.562 están en el banco.
- **Salidas:**
  - una fila por (vocabulario, examen, concepto) y otra por medias;
  - los volcados para el remuestreo emparejado;
  - las diferencias frente a la referencia con su intervalo;
  - todo con su job, su revisión y las huellas de las poblaciones.
- **Aceptación:** reproducir los números del laboratorio en la mitad de
  selección. Los vectores de prueba ya existen: las corridas de D37 sobre v1 y
  cinco candidatos, en Picasso,
  `vocabulario-final/examenes/{dominios,sitios,grupo,sitios-grupo}-d37-*` y sus
  volcados. Si la plataforma examina los mismos códigos, la AP debe coincidir
  exactamente; si examina los códigos cuantizados, hay que fijar antes cuánto
  pueden diferir y por qué.

## Preguntas abiertas, que son del autor

1. **¿Códigos cuantizados o activaciones continuas?** La plataforma guarda
   niveles cuantizados, que es lo que lee el modelo. El laboratorio examinó sin
   cuantizar. Examinar lo que se usa es lo coherente, pero rompe la comparación
   exacta con los números de hoy.
2. **¿Se usa el conjunto de confirmación para la decisión final, una sola vez?**
   Es la única lectura limpia que queda: nada se ha elegido mirándolo.
3. **¿Se mantienen las mismas poblaciones?** Son de Swiss-Prot 2022_03 y no
   tienen que ver con el corte de las ventanas, pero conviene decirlo.

## Reparto que propongo

- **El sobremesa** especifica (este documento), aporta los vectores de prueba y
  revisa antes de que nada corra.
- **El portátil** escribe el ADR, registra las poblaciones como conjuntos
  declarados y escribe la operación.

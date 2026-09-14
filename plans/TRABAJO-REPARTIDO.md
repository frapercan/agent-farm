# El trabajo repartido entre las dos máquinas

Objetivo declarado por el autor el 2026-09-14: **dejar el código en condiciones de
correr la campaña limpia.** No es una lista de mejoras, es la lista de lo que hoy
impide o estropea una ejecución.

## La única regla

**Nadie empieza un punto que no lleve su nombre.** Si hace falta cambiar de dueño
se cambia aquí primero y se trabaja después.

Existe porque un mensaje no sirve: se pierde, y ninguna de las dos máquinas ve lo
que la otra empezó hace diez minutos. Este fichero está en el repositorio que las
dos leen, que es lo que el CLAUDE.md de la raíz pide para cualquier cosa en la que
las dos deban coincidir.

**La columna de ficheros no es decoración.** El 2026-09-14 se lanzaron cuatro
cambios en ramas paralelas desde la misma base; tres reestructuraban el mismo
mecanismo y ninguno veía a los otros. El resultado fueron veinte bloques de
conflicto y un fichero que, resuelto ingenuamente, habría compilado con una
función definida dos veces y llamadores usando dos firmas. Verde a la vista y roto
de verdad. La columna existe para que eso se vea antes.

## Lo que bloquea una corrida, por lo que corrompería

El orden no es por esfuerzo. Es que **peor que no poder despachar es despachar y
publicar mal**: una corrida parada se ve, una atribución corrompida se publica.

| | Qué | Dueño | Ficheros | Estado |
|---|---|---|---|---|
| B1 | El disparo automático de conjuntos de evaluación comprueba la existencia sobre dos columnas mientras la restricción tiene cinco, así que el primero de una pareja bloquea permanentemente su propio reemplazo, y lo hace emitiendo que ya existe | portátil | `core/operations/load_goa_annotations.py` | pendiente |
| B3 | La operación de predicción llega a terminada con sus trabajos de almacén todavía vivos, y el mensaje del guardia receta esperar a ese estado, que es justo el que llega antes que los datos | portátil | `core/operations/predict_go_terms/`, `core/operations/_run_cafa_data_helpers.py` | pendiente |
| B4 | El sello del método no cubre el lado de evaluación. El corte está **activo**: 84 filas en siete valores, y el docstring del guardia que no lo cubre registra que ya se publicó un error por esta causa | portátil | `core/method_seal.py`, `core/operations/compare_paired_panels.py` | pendiente |
| B2 | La tabla de conjuntos de anotación no tiene marca de completitud, así que uno a medio cargar es indistinguible de uno terminado | portátil | `infrastructure/orm/models/annotation/annotation_set.py` y su cargador | pendiente |
| B5 | La superficie del grafo compara nombres de nivel renderizados, y su vocabulario de campos no incluye el banco, la ontología ni dos de los interruptores del recuperador. Dos brazos que difieren en el banco siguen renderizando bajo un solo nombre | portátil | `api/routers/_graph_panels.py`, el router | **bloqueado**: espera a que aterricen los dos rediseños del grafo |

B4 va por delante de B2 a propósito: B2 deja un conjunto malo que se nota al
mirarlo, B4 deja un veredicto que parece bueno.

## Instrumentación, sin la cual una corrida es ilegible

| | Qué | Dueño | Ficheros | Estado |
|---|---|---|---|---|
| I2 | El cierre de la conexión de mensajería durante un trabajo largo emite cuatro líneas de error esperadas por carga. Doce cargas son cuarenta y ocho, y así es como una real pasa desapercibida | portátil | `infrastructure/queue/consumer.py` | pendiente |
| I4 | El presupuesto de residuos informa de que procesó todo lo disponible cuando el troceado está activo, sobre la premisa de que trocear evita truncar | nodo | `core/operations/compute_embeddings.py` | pendiente |
| I3 | El contador de anotaciones cuenta candidatos construidos y no filas escritas. Medido: exceso del 0,004 % y del 0,33 % en dos cargas | portátil | `core/operations/load_goa_annotations.py` | baja |

## Camino de cómputo

| | Qué | Dueño | Ficheros | Estado |
|---|---|---|---|---|
| C1 | Presupuesto en residuos en el camino de lotes rellenados. **Prerrequisito de C3**: sin él, seiscientas secuencias piden 19,28 GiB y revientan antes de que la pregunta de la invariancia se pueda plantear | nodo | `protea_backends/t5/`, `protea_backends/ankh/` | pendiente |
| C2 | Pasada compartida para el codificador cuya invariancia a la composición del lote ya está medida en cero exacto, así que entra sin trabajo previo | nodo | `protea_backends/esm3c/` | pendiente |
| C3 | Pasada compartida para los dos que procesan en lotes rellenados | nodo | `protea_backends/t5/`, `protea_backends/ankh/` | **bloqueado por C1** |
| C4 | El guardia de colapso, implementado. Hoy sólo existe medido: hueco entre el vecino primero y el trigésimo contra el suelo de reproducibilidad, sobre diecisiete configuraciones, con separación de 115 veces entre sanas y ruido | nodo | por decidir, candidato `core/operations/compute_embeddings.py` | pendiente |
| C5 | Subir el pin del paquete de codificadores. El código de la pasada compartida está fusionado y **la flota no lo usa** | portátil escribe, nodo verifica | `poetry.lock` | **en espera**: no mientras se reconstruyen los dos rediseños del grafo |

C5 es el único punto de dos dueños y es deliberado: el código es del portátil, la
tarjeta es del nodo, y ninguno lo cierra solo. El portátil sube el pin y abre en
borrador; el nodo corre el primer lote real y confirma o corrige el ahorro
proyectado antes de que entre.

## Arreglado en el tronco y ausente de la flota

Esta categoría no estaba en el primer inventario y es la que más pesa sobre el
objetivo, porque **un arreglo que nadie ejecuta no es un arreglo para la corrida.**

    revision declarada    2026-09-07
    tronco                2026-09-14
    diferencia            15 commits, una semana

Todo lo que se fusionó anoche vive ahí: el sello del método, el disparador de
integración del tronco, el suelo retirado, la negativa visible, y el registro del
camino de éxito que hace que doce cargas dejen constancia de lo que hicieron.

| | Qué | Dueño | Estado |
|---|---|---|---|
| D1 | Mover la revisión declarada al tronco, con el reinicio verificado por lo que cada worker autoinforma | portátil declara, nodo verifica | **pendiente, y hace reales todos los demás** |

La cabecera del fichero de declaración fija la condición: no se mueve con una
campaña viva. Hoy no la hay, así que la ventana está abierta y no volverá a
estarlo una vez empiece.

## Lo que no es trabajo nuestro

Son decisiones del autor. Ninguna de las dos máquinas las toca.

| Qué | Por qué es suya |
|---|---|
| Cargar o no las diez entregas restantes | 22 horas y unos 65 gigas. La escalera como comparación está cerrada; como corpus de entrenamiento sigue abierta y es la misma carga |
| Cuáles de los once bancos igualar | Siete sanas, dos sin resolver, dos cuyo orden de vecinos está por debajo del ruido de recomputo |
| Qué rama va primero | Las dos máquinas discrepan y está por escrito: el nodo pone delante la que no necesita igualar bancos, el portátil la que produce un veredicto atribuible |
| La regla de sellado de la campaña | Cambiar una regla de decisión declarada a mitad de campaña no lo hacen dos máquinas de acuerdo |
| Dónde vive el fichero de entorno de la granja, y si se versiona | No existe en el portátil, y en el nodo es inocuo sólo porque el valor por omisión coincide con su ruta. Que aquí funcione no es evidencia de que funcione |

## Registro de cambios de esta lista

- 2026-09-14, nodo: primera versión, con el reparto acordado por el puente y los
  cuatro cambios que pidió el portátil. Se retiró el punto del registro del camino
  de éxito por estar ya fusionado, y se añadió la categoría de arreglado en el
  tronco y ausente de la flota al comprobar que ese mismo arreglo no está en la
  revisión que el nodo ejecuta.

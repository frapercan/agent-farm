# El estado, y las cinco decisiones que no se re-litigan

Escrito el 2026-11-08 por la sesion del portatil. **Sustituye a
`REVISION-PENDIENTE-PROTEA-1139.md`**, que describia el #1139 como borrador
cuando ya iban trece PRs por delante: una nota de traspaso envejece antes de
que la lean, asi que esta dice solo lo que caduca despacio y apunta a donde
vive lo que caduca rapido.

## Donde vive lo que caduca rapido

- **que revision sirve**: `curl -s http://127.0.0.1:8000/health`, que dice la
  servida, la declarada y si coinciden. No preguntes a un proceso ni a un
  arbol.
- **que es cada ventana**: `plans/INVENTARIO-VENTANAS.md`, con el nombre
  semantico al lado del id.
- **el diseno del escritor de D56**: `plans/DISENO-ESCRITOR-D56.md`, ya
  acordado con el laboratorio, con los nombres, las diez tablas y las columnas
  que lee su cargador.
- **las decisiones de arquitectura**: los ADR del repositorio, en particular
  D56, que lleva la regla de fuga aplicada al construir y que el `window` es la
  clave de union y es el id completo.

## Las cinco decisiones, que son de Francisco

Ninguna de las cinco la decide una sesion. Si vuelves y te parece obvia, no lo
es: cada una tiene un numero medido al lado y ninguna corre prisa.

**1. La retirada de las 125 ventanas del marco superado.** El payload en seco
esta preparado. De las 125, exactamente **una** tiene resultados apuntandola,
asi que la pasada en seco lista esa como rechazo y las otras 124 como
retirables. El seco no escribe, no borra y no archiva, y lista TODOS los
rechazos de una vez. Pendiente de su palabra.

**2. La pasada de codigos por residuo de las 161 secuencias largas.**
**2.429.553 residuos**, por ExactAnkh (`embed_batch_per_layer`,
protea-backends #47), en el nodo con tarjeta. Pendiente desde el 2026-11-04. El
camino eager no sirve: en esa tarjeta pasa 8.259 residuos y falla con 8.382, y
el techo configurado (8.524) estaba por encima del limite fisico. Son el 0,02 %
y se cuentan como cobertura, asi que no bloquean nada. **La tarjeta no se pide
sin que lo diga Francisco.**

**3. Donde vive la cola `protea.training`.** Hoy no hay consumidor en el
portatil, y es a proposito: esa cola sirve tambien `export_research_dataset`,
que es calculo sostenido, y eso esta prohibido aqui. El nodo tiene una unidad
preparada desde el 2026-11-07 (Python 3.12, tarjeta oculta, kNN en CPU con
numpy, MemoryHigh 40G, MemoryMax 48G, nice 10) y el laboratorio recomienda que
viva alli. **Un job encolado ahi se queda QUEUED sin error**, asi que si algo
no consume, esto es lo primero que mirar.

**4. Que ventanas entrenan el modelo minimo.** La que mas cambia lo demas.
Estan generadas 64 ventanas de la revision `d5416224`, de las cuales **49 son
admisibles** con `cut_version` 211: las otras quince terminan despues del corte
y caen dentro del tramo 211->227 que puntua la ventana de validacion larga.

| opcion | ventanas | horizontes |
|---|---|---|
| lo generado | 49 | 16 a 73 dias, salvo `serie-160-177` (539) y `serie-205-211` (311) |
| el diseno del laboratorio | 53 | de 6 meses a 3 anos, con una primera tanda de ~16 |

D30 pide horizonte variable de 0 a 3 anos y la lectura de supervivencia tiene
tramos de hasta 1.096 dias. Entrenado con horizontes de un mes, el modelo
tendria que extrapolar a dieciseis meses con un solo ejemplo largo. **Nadie
sabe como salio la lista de pares que se uso**, asi que no se puede confirmar
ni desmentir que fuera el diseno de 53.

**5. Importar los vectores de texto del eje.** El artefacto vive en el
almacen del LABORATORIO y no en el de la plataforma: `text-qwen3-embedding-4b.npz`,
**224.759.782 bytes**, sha `e32e15907aab0ec7637b6431164b28bf2dad50968ecb226480fcde563d82cbef`.
Comprobado el 2026-11-08 que no esta aqui: 6.426 objetos en doce prefijos y
nada que case. Hasta que este, la tabla `terms` **se niega**, que es lo
correcto: escribir el sha de un mensaje seria un localizador de bytes que nadie
de este lado puede comprobar.

La ruta existe y hace lo correcto. `POST /model-weights/by-reference` hashea el
objeto del almacen y solo registra si coincide con el sha dado; para un objeto
que todavia no esta hay la subida por partes (`POST /model-weights/uploads`,
`PUT .../{n}`, `POST .../complete`), que es la que haria falta aqui, con un
`kind` propio del estilo `term_text_vectors`. Rol OPERATOR.

**Dos datos a la vista antes de decidir.** El registro deja fila con `uri`,
`sha256`, `size_bytes`, `description`, `created_by` y `created_at`, pero **no
deja job**: cero referencias a `Job` en el router y en el servicio. Eso es una
excepcion a la regla de que todo pasa por `POST /v1/jobs`, y las dos sesiones
coinciden en que un registro es una declaracion y no un computo -- pero la
excepcion esta dicha y no descubierta. Y **ADR-D54 sigue en `Status: Proposed
(draft for the author's review)`**, fechado 2026-11-03 y firmado por Francisco:
el registro esta implementado por delante de que su propio ADR este aceptado.
Asi que la decision es doble: importar este artefacto, y si ese registro deja
de ser un borrador.

Escribir en el almacen de la plataforma es una accion hacia fuera, asi que
ninguna de las dos sesiones la hace.

## Lo que esta hecho y no hay que repetir

- Las **71** ventanas del marco vivo y las que llevan papel estan selladas, con
  71 shas distintos: ninguna comparte bytes con otra.
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
- De las diez tablas de D56 estan escritas **cuatro**: `window_terms_out`,
  `queries`, `terms` y `term_ancestors`. Las dos ultimas estan indexadas por
  `cut` y NADA MAS, asi que no dependen de que ventanas se elijan: 43.558
  terminos vivos con su aspecto y 595.072 pares de cierre, medidos. El cierre
  sigue `is_a` y `part_of` **compartiendo la funcion** que cerro las ganancias,
  no coincidiendo en una lista.
- El vocabulario de residuos **SI tiene fila** en `model_weights`:
  `vocabulary-v1-06fed75ca76d17be`, sha `06fed75ca76d`, 260.233.730 bytes,
  `created_by = sobremesa-embeddings-2026-10`, con descripcion. Se dijo lo
  contrario en una conversacion de esta noche y era falso: el precedente de
  importar un artefacto del laboratorio existe y se siguio.

## Un artefacto que NO se usa

`s3://protea/transitions/transitions-serie-156-220/15f002ea/window_terms_out-f2a32e45e0b0.parquet`,
sha `f2a32e45...`, **queda superado**. Declaraba `cut_version` 211 sobre las 64
ventanas, incluidas las quince posteriores al corte. Lleva terminos de la
ontologia y no anotaciones, asi que no filtro nada, pero declaraba un alcance
que no era el suyo. Nada en la base apunta a ese objeto: queda huerfano en el
almacen y se dice aqui porque es donde se mira.

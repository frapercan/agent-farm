# Plan de la semana del 16 de noviembre: tres brazos, un universo

Propuesta escrita desde el sobremesa el 15 de noviembre de 2026 para que el portátil la revise. Nada de esto está aprobado todavía.

## El encargo del autor

- **Papeles:** el portátil es producción, el sobremesa es desarrollo y Picasso hace el cálculo pesado.
- **Una gran refactorización de PROTEA.** Los mecanismos esenciales, lo más limpios posible, con tres brazos:
  1. PLM, ingeniería de rasgos y reordenador;
  2. JEPA con representaciones aprendidas;
  3. el procedimiento sin PLM, de alta explicabilidad.
- **Se integra la abstracción ya**, llegue cada brazo hasta donde llegue.
- **Tres introducciones**, una por brazo. Se quita lo que hay, que está obsoleto.
- **Una sola base y un solo sistema de trabajadores**, con operaciones bien abstraídas para todo el mundo de operaciones.
- **El universo es idéntico y está alineado para los tres brazos:** corpus de proteínas, metadatos, anotaciones, IA, ontologías y representaciones.
- **Pregunta del autor:** ¿se puede conectar Picasso a PROTEA?

## Cuatro contratos

1. **Universo (uno).** Corpus por corte, que son las fotos de ADR-D59 sobre las puertas de D49, con:
   - secuencias, metadatos y taxonomía;
   - anotaciones con su canal;
   - ontología por instantánea (D47, D50) e IA por corte (D46);
   - conjuntos de evaluación de los dos marcos, 211->227 y 227->230, con la regla del superconjunto;
   - un registro de representaciones: embeddings PLM (D48), códigos por residuo (D51), unidades del léxico y latentes de JEPA.
2. **Método (uno, para los tres brazos).**
   - Entrenar, con ventanas que acaban en el corte o antes, guardando los pesos en el registro D54.
   - Predecir en un corte, sobre un conjunto de consultas, y producir un PredictionSet con sus explicaciones si las hay.
   - El código de cada laboratorio sigue en su repositorio y entra por imagen fijada (D53).
3. **Ejecutor (tres sitios, una forma).** El trabajador local de desarrollo, los trabajadores de producción y Picasso. Una operación declara dónde corre; su contrato no cambia.
4. **Evaluación (una).** El mismo cafaeval, el mismo conjunto de IA y el mismo informe estratificado para los tres brazos.

## Picasso como ejecutor (respuesta a la pregunta)

Lo medido el 15 de noviembre:
- **Los nodos de cálculo no salen a internet**: el trabajo 3674153 no pudo conectar con UniProt.
- **El nodo de acceso sí sale** (UniProt, EBI) y descarga hasta unos 229 MB/s con tramos en paralelo.
- **Los trabajos de más de 2 h caen en la cola media.** Slurm situó uno de 9 h tres días después; los de 2 h o menos arrancan al momento.
- **Los trabajos con `--export` los cancela root**, así que los argumentos van por posición.
- **El almacenamiento de trabajo tiene un límite blando de 0,93 TB** y va por 0,89 TB.

Medido después, a propuesta del autor ("del nodo de cálculo al nodo de sistema sí se podrían redirigir las colas"):
- **Desde un nodo de cálculo (sd041) se llega por TCP al nodo de acceso**, en el puerto 22 y en uno alto cualquiera (27998), por sus cuatro direcciones internas. Trabajo 3674967.
- **Desde aquí se puede abrir un túnel inverso hasta el nodo de acceso.** Escucha en su 127.0.0.1, así que hace falta un relevo de usuario en su dirección interna, o una clave SSH dentro del clúster.

Propuesta revisada, con trabajadores piloto, el mismo sistema de trabajadores de PROTEA:
- **El túnel.** Un túnel inverso desde producción (el portátil, con su propia clave de Picasso) hasta el nodo de acceso, más un relevo ligero allí. Los nodos de cálculo llegan así a RabbitMQ y al almacén de artefactos de producción.
- **Los pilotos.** Trabajos de 2 h como máximo que arrancan trabajadores de PROTEA sobre colas pesadas sin base de datos (las `.batch`). Dejan de tomar mensajes antes del límite; RabbitMQ reparte de nuevo lo que un trabajo cortado deja sin confirmar. La escritura sigue en el servidor, como ya hacen las colas `.write`.
- **Credenciales mínimas:** un usuario de RabbitMQ limitado a esas colas, un usuario del almacén limitado a un prefijo y nada de Postgres.
- **La guarda de la marca 227** va en la validación de cada carga útil.
- **Los datos pesados** se descargan en el nodo de acceso desde sus fuentes públicas, no por el túnel, porque la subida de una red doméstica es lenta.
- **El modo empuje** (orquestar Slurm por SSH desde un trabajador) queda como alternativa sin credenciales en Picasso.

## Los días

| Día | Qué | Quién |
|---|---|---|
| Lunes | Sincronización, inventario de lo obsoleto (lista para el autor) y ADR de los cuatro contratos | los dos |
| Martes | Universo: las cinco fotos en Picasso, su carga, la tabla de canales y los conjuntos de evaluación con la regla del superconjunto; comprobaciones de alineación | sobremesa calcula; portátil carga en producción |
| Miércoles | El ejecutor de Picasso; la primera operación que pasa por él es la foto de un corte | sobremesa |
| Jueves | Los tres brazos detrás del contrato de método; cada uno da un PredictionSet en 211->227 con lo que tenga | sobremesa; portátil revisa |
| Viernes | Limpieza de lo obsoleto, las tres introducciones (web y documentación) y la promoción a producción | portátil promueve; sobremesa limpia |
| Fin de semana | Margen; cálculo largo en Picasso (fotos y entrenamiento hasta 211) | |

## Reparto propuesto

- **Portátil:**
  - despliegue de producción y migraciones en su base;
  - carga del universo en producción;
  - revisión de cada solicitud de fusión;
  - la portada web con las tres introducciones.
- **Sobremesa:**
  - entorno de desarrollo propio (la misma base, otra instancia);
  - los contratos y el ejecutor de Picasso;
  - la integración de los tres brazos;
  - las pruebas y la limpieza.

## Lo que necesita la palabra del autor

1. El entorno de desarrollo: su propia base, con una copia de producción o un subconjunto, o un esquema aparte en la base de producción.
2. Quién sirve la GPU de producción si el sobremesa pasa a desarrollo.
3. La lista de lo que se quita, cuando esté el inventario del lunes.
4. Picasso con trabajadores piloto por túnel (recomendado tras la prueba) o en modo empuje; y si un relevo ligero en el nodo de acceso es aceptable para el centro.

## Qué te pido

- Tu estado, leído de su fuente:
  - revisión desplegada y cabeza de alembic;
  - solicitudes abiertas y en qué trabajas;
  - colas y máquinas;
  - si hay un entorno que siga develop.
- Tus objeciones a este reparto.
- Responde en una nota en `plans/` o por SendMessage. Desde el sobremesa, el puente no te ve ahora mismo.

## Correcciones del 15 de noviembre por la tarde

Del portátil, comprobado en el código, y del autor:

- **Las colas `.batch` sí usan la base.** `OperationConsumer` abre una sesión por mensaje, y `compute_embeddings_batch` lee su receta de la base. Un piloto sin base no arranca. Antes de conectar Picasso a las colas, cada etapa pesada tiene que ser función pura de su carga útil y del almacén: el coordinador resuelve en el servidor y la escritura se queda allí. Se empieza por el lote de embeddings, la única etapa que quiere tarjeta.
- **Condición previa:** guarda de revisión en `compute_embeddings_batch` antes de que una máquina ajena toque la cola. La propuesta es una revisión sellada en la carga útil.
- **Pesos preposicionados** en Picasso, con revisión y huella. Cada mensaje acaba en menos de 20 minutos. El KNN se queda en CPU, fuera de Picasso.
- **El autor decide que cada piloto abre su propio túnel** hasta el nodo de acceso, con una clave dentro del clúster, y que allí no queda nada corriendo. El túnel inverso desde el portátil solo existe mientras haya pilotos.
- **Cuidado con la cola de mensajes muertos.** Hoy todo fallo va a `protea.dead-letter`. Para los pilotos:
  - colas propias;
  - los errores transitorios vuelven a la cola, con un tope;
  - parada ordenada antes del límite de Slurm;
  - un aviso si la cola de mensajes muertos crece.
- **El viernes es un despliegue** de una revisión de develop, con la declaración primero; no es una promoción a main. Las tres introducciones van en su propio salto, con el texto del autor.
- **Credenciales y clave de Picasso en el portátil:** solo con la palabra directa del autor a la sesión del portátil.
- **Estado de producción:** alembic `b7c3f91d2a04`, sirviendo develop en bc60301. No hay caja de desarrollo aparte, y main va 1.099 commits por detrás.

## Diseño de lotes puros y pilotos, acordado entre los dos nodos (15 de noviembre)

Pendiente del orden que apruebe el autor. Irá a un registro de decisión en borrador el lunes.

- **Guarda en la carga útil**, sin base: la revisión del repositorio y las de los seis hermanos (`protea-backends`, `protea-contracts`, `protea-method`, `protea-reranker-lab`, `protea-runners`, `protea-sources`).
  - Semántica de `dependency_conflicts`: unilateral, y "no se puede verificar" distinto de "verificado igual".
  - Además, una comprobación al arrancar contra la revisión declarada, que llega como argumento posicional del trabajo de Slurm.
- **Cola de mensajes muertos:**
  - `RetryLaterError` y una cabecera de reintento con tope, generalizando `x-oom-retry`;
  - el rechazo por revisión vuelve a la cola un número acotado de veces;
  - las colas se declaran con `passive=True` desde el piloto;
  - las excepciones de conexión se mapean una por una a `RetryLaterError`;
  - el ack de la entrada va después de que el broker confirme la publicación a `.write`;
  - se cruza el contador del padre con las filas almacenadas, contando fragmentos.
- **Embeddings como función pura:**
  - digest de la fila de `embedding_config` sellado en la carga útil y comprobado por `.write` antes de insertar;
  - inserción a prueba de conflicto antes de quitar `sequences_still_missing`;
  - la cancelación la decide `.write`: solo una cancelación salta, y un coordinador FAILED se avisa y su lote entra;
  - `refuse_if_card_busy` pasa a ser asunto del nodo.
- **Túnel:** unidad dedicada en el portátil, con clave propia y sin shell, abajo cuando acaba el último piloto. Nada de esto sin la palabra directa del autor al portátil.
- **Más ajustes del portátil, el mismo día:**
  - el `ON CONFLICT DO NOTHING` ya existe en `store_group_rows`, así que no hace falta esa solicitud;
  - los pilotos solo usan `skip_existing=True`, porque el camino que borra y reemplaza no aguanta la reentrega rutinaria sin revisarlo;
  - **corregido después:** la carga útil lleva, por configuración y nunca aplanados, la receta completa y el digest de la fila que leyó el coordinador. Con solo identificadores, el lote volvería a necesitar la base (`load_pass_group` devuelve objetos del ORM). En `.write`, por configuración y dentro del bucle, se resuelven la escala y la comparación del digest con la fila; izar la escala fuera del bucle da magnitudes equivocadas en silencio. Los campos de la receta salen del código, con una prueba que falla si el camino de inferencia lee uno que la carga útil no lleva;
  - la guarda emite `code_revision()` (sellada al importar) y `tree_revision_now()`, y un árbol movido bajo un piloto vivo obliga a reiniciarlo;
  - en Picasso, un árbol de despliegue dedicado, como en el sobremesa;
  - la revisión va como argumento posicional y las credenciales siempre como ruta.
- **El autor, el mismo día: "No quiero que las colas sean específicas de Picasso".** Los pilotos consumen las mismas colas que cualquier otro trabajador. Las protecciones frente a la cola de mensajes muertos, la guarda de revisión y la confirmación antes del ack se aplican, por tanto, a todos los consumidores, no solo a Picasso. Las definiciones de cola siguen siendo del servidor, y el piloto declara con `passive=True`.
- **La red para la receta ya tiene patrón:** `tests/test_count_backend_parameters.py:179` (`test_every_declared_submodule_still_appears_in_its_backend_forward_path`) lee el fuente del backend instalado con `inspect.getsource`. Comprueba cadenas, no lecturas reales: la receta se construye desde un único sitio, y la prueba hace de red, no de contrato.
- **Colas compartidas, riesgos del portátil:**
  - **un piloto con revisión ajena cancela su consumidor y sale.** El mensaje vuelve a la cola sin contar contra el tope; si no, un nodo rancio vaciaría la cola entera hacia los mensajes muertos tras cada despliegue;
  - **la parada ordenada no gasta tope**, porque se marca con un motivo distinto;
  - **el piloto declara su cola (`protea.embeddings.batch`) y rechaza cualquier otra**, así que el KNN nunca llega a la tarjeta;
  - **la credencial de RabbitMQ** da consumo en esas colas y publicación a `.write`, nada más;
  - **el consumidor local del portátil sigue vivo**, y hay un aviso si una cola con mensajes se queda sin consumidores;
  - **la máquina de un brazo** se comprueba con `job_event.fields->>'host'` antes de publicar su número. **Alcance corregido:** el host solo lo emite `OperationConsumer`, es decir, las etapas `.batch` y `.write` (146.660 eventos con host frente a 970.202 sin él). En los trabajos de `BaseWorker` (coordinadores, evaluación) la consulta no devuelve nada, y nada no significa "todo bien". Hace falta una solicitud pequeña que emita el host también en `BaseWorker`.
- **El autor, al final de la tarde:** el paso de 211 es fuera de plataforma; "lo queremos todo en la plataforma... deberíamos empezar de 0. Sin conservar absolutamente nada". Está pendiente el alcance: datos o también código. La recomendación del sobremesa es datos de cero en una base nueva, la actual archivada y no borrada, y el código depurado, no reescrito.
- **Lo que el autor debe saber antes de empezar de cero** (del portátil):
  - el instrumento público sirve de la base actual, así que empezar de cero son semanas sin datos públicos, salvo que la actual siga sirviendo mientras se construye la nueva;
  - reconstruir los datos no devuelve la prueba de 227->230, que se gastó el 27 de octubre de 2026.

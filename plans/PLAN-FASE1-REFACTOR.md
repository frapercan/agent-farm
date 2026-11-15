# Plan de la fase 1: refactorización en tres familias y puesta a punto por máquina

Propuesta. Nada está aprobado. Producido el 15 de noviembre de 2026 por el flujo de solo lectura `wf_edcc2d21-0c4`: seis inventarios, dos diseños, dos verificaciones adversarias, una crítica y una síntesis. Todos los agentes leyeron PROTEA-dev-fotos en `feat/cut-photos` fde5456. Abajo están la revisión del sobremesa, el plan tal como salió (parte 1 en español y anexo técnico en inglés) y, al final, la lista completa de la crítica.

## Revisión del sobremesa (15 de noviembre, noche)

**Comprobado a mano después del flujo:**
- **La regla de la punta, corregida por el portátil.** `plans/DECLARED-REVISION.txt` dice "THE DECLARATION TRACKS THE TIP OF develop", y `.github/workflows/auto-merge.yml` solo actúa en solicitudes a develop. Pero un merge en develop no mueve producción por sí solo, y la parte 1 se equivoca al decirlo:
  - la declaración se lee de `origin/main:plans/DECLARED-REVISION.txt` de agent-farm (`protea/api/app.py:322`);
  - producción sirve un árbol de despliegue separado en bc60301;
  - el despliegue lo hace el portátil.

  La rama de integración sigue haciendo falta, porque la regla de la punta pediría declarar código de la refactorización y los arreglos urgentes tienen que poder salir de una develop limpia. Lo que hay que proteger es la declaración de agent-farm y el acto de despliegue. Por confirmar: si `deploy-keeper-tick.sh`, que llama a `protea_redeploy.sh` ("Idempotent redeploy of origin/develop"), sigue apagado en el portátil.
- **La ontología del corte 160.** `plans/GOA-ONTOLOGY-PAIRING.md` lo confirma: GOA 160 declara 2016-10-29 y la tabla le da el grafo 2016-09-30.
- **El perfil por grupo.** El plan ya es coherente con él, porque leyó ADR-D59 en fde5456: ninguna parte mete a los vecinos de UniRef50 como proteínas, y el presupuesto de disco ya cuenta los perfiles (unos 10 GB como mucho). La decisión 7 (secuencias) se estrecha: solo afecta a las proteínas no revisadas de la base, no a los 38 millones de vecinos.

**Contestado por decisiones ya tomadas:**
- **Decisión 26a, los borrados de Picasso de 15:46 a 15:58.** El autor los aprobó dos veces, y están registrados en `compresion/registro-borrados-2026-11-15.md` (sf-jepa, rama compresion). La "otra sesión que cambia Picasso" de los riesgos era esta misma.
- **Decisión 21, el marco 227->230.** Se gastó el 27 de octubre y es intocable, así que desarrollo no lo lee. Solo queda abierto qué instancia sirve el instrumento público tras el hito.
- **Decisión 6, las filas de los miembros.** Con el perfil por grupo, viajan en el parquet de la foto, y los GAF no vienen al sobremesa.
- **Decisión 3, la nota del plan.** Corregida en agent-farm 1038337, y el portátil avisado. No se le pide nada.

**Ajustes a las recomendaciones del plan:**
- **Decisión 24, la cola de las etapas de GPU con ficheros.** El plan propone "una cola solo del sobremesa", que choca con la regla del autor de que ninguna cola sea de una máquina concreta. Propuesta: nombrar la cola por lo que necesita la etapa, el acceso al almacén, y que la consuma cualquier nodo que lo tenga. Los pilotos no la toman porque en la fase 1 no tienen almacén.
- **Decisiones 14 y 15, los pesos.** El plan prohíbe los pesos del laboratorio y a la vez admite los modelos preentrenados como excepciones declaradas. Un léxico sin etiquetas tiene el mismo estatus que un PLM. Propuesta de regla única:
  - lo que no vio etiquetas GO entra como excepción declarada, con su manifiesto sha256: PLM, léxicos y vocabulario;
  - lo que vio etiquetas (boosters, combinador) se prohíbe y se reentrena en la plataforma;
  - alternativa purista: reentrenar también el léxico dentro de la plataforma, lo que cuesta días de B200.
- **Decisión 17, los canales del brazo 3.** El plan quita PAINT y las traducciones de campos revisados. El autor aprobó una sola receta. Propuesta: la misma receta para las tres familias, con PAINT como canal propio, medible y filtrable.
- **Orden.** El autor pidió integrar la abstracción ya. Propuesta: adelantar el contrato de método y el registro de las tres familias (P5.1 y la parte de P7.1 sin introducciones) a justo después de la fase 1. No dependen de los datos del universo.

**Hecho durante la revisión:**
- **Copia de los repositorios del laboratorio sin remoto**, verificada, en el segundo disco: `/mnt/protea-archive/archive/lab-bundles/sf-jepa-2026-11-15.bundle` y `differentiable-alignment-2026-11-15.bundle`. El worktree differentiable-alignment-rapido va dentro del segundo. Sigue faltando una copia fuera de esta máquina.
- **Nodo de acceso de Picasso.** Quedaba un proceso de nuestro usuario, el demonio epmd de Erlang, vivo desde el 31 de octubre, y está parado. La escucha de la prueba de red terminó sola (timeout de 300 s). Hay una sesión interactiva abierta desde las 14:34 que no abrió esta sesión, y no se ha tocado.
- **Discos del sobremesa.** Hay dos de 1 TB:
  - en el primero, / tiene 367 GB libres;
  - el segundo tiene la partición de Windows (539 GB) y el archivo (63 GB libres).
  
  El universo pide de 0,4 a 0,55 TB, más un destino de copias.
- **Del portátil, después:**
  - **La encuesta ya está hecha.** Versiones fijadas por digest en `docker-compose.yml`: PostgreSQL 18.6 con pgvector 0.8.6, RabbitMQ 4.3.5 y MinIO RELEASE.2025-09-07T16-13-09Z.hotfix.7aa24e772. Almacén de 96,12 GB, volumen de Postgres de 404 GB y 277 G libres en su disco.
  - **La pila del sobremesa está vacía:** ni Postgres, ni RabbitMQ, ni MinIO.
  - **La proyección de `protein_go_annotation`** que cita (de 180 a 399 GB) era para la serie GAF entera. Con las fotos, en 211 el superconjunto tiene 8.521.521 filas, y las proteínas de fuera suman 587.286 filas experimentales o de curador más sus otras filas. Son medidas fuera de la plataforma, solo orden de magnitud.

Medido por el portátil después, sobre su máquina y su base viva:
- **El proceso que redespliega develop está apagado.** No hay unidad, temporizador, cron ni proceso que lo arranque. El código existe (`scripts/services/lib/protea_redeploy.sh`), pero nada lo invoca. `coord-keeper.service` sigue habilitado y muerto: arranca con una ruta que no existe y sale con 78. Es ruido del registro antiguo, no un camino a producción.
- **Hay un perro guardián: `protea-vigila-consumidor.timer`**, cada 15 minutos. Reinicia el trabajador de `protea.jobs` solo si se cumplen a la vez cuatro condiciones, comprobadas dos veces con 90 s de separación:
  - la cola se puede leer;
  - tiene 0 consumidores;
  - tiene mensajes;
  - hay 0 trabajos en RUNNING.

  No toca las colas `.batch`. Con el padre en RUNNING mientras los lotes están fuera, el diseño de pilotos queda del lado seguro de esa guarda.
- **Coste por fila en producción:**

  | Tabla | Bytes por fila | Índices |
  |---|---|---|
  | `protein_go_annotation` | 355,1 | 58 % de la tabla |
  | `sequence_embedding` | 10.478 | casi nada |
  | `go_prediction` | 496,5 | |

  Las seis cargas de fotos salen del orden de 20 GB, y como mucho 40 GB si se duplica lo que no se ha medido. El presupuesto del sobremesa lo fijan los embeddings, no las anotaciones.
- **En el sobremesa está podman 5.7.0**, pero no hay ningún Quadlet escrito y nada escucha en los puertos de la pila.

---

# PARTE 1. Plan para el autor (español)

Base de lectura: PROTEA-dev-fotos en feat/cut-photos fde5456, árbol limpio (`git log --oneline -6`, 17:09). Todo lo que no pude comprobar va marcado SIN VERIFICAR.

## 1. El flujo tal como lo entiendo
- Picasso calcula. El sobremesa (dev) integra y valida. El portátil (producción) recibe una única promoción grande en un hito, cuando dev esté estable.
- Dev empieza de cero y en paralelo. Su base de datos es nueva y se construye solo con operaciones de PROTEA a partir de fuentes públicas. No entra nada de la base de producción ni de salidas del laboratorio. La base actual sigue sirviendo el instrumento público.
- El código se refactoriza: se limpian los mecanismos esenciales, no se reescribe. El portátil queda exactamente como está hasta el hito.

## 2. Arquitectura en pocas líneas
Hay un universo, tres familias de método y cuatro contratos. En código no las llamo "arm", porque esa palabra ya nombra una configuración evaluada (protea/api/routers/_arm_identity.py:1-8). Nombres provisionales: embedding-reranker, world-model, explainable-units.
- **Contrato del universo.** Lo leen todas las familias, por id: fotos por corte, estado de etiquetas, poblaciones, IA, marcos, tabla de homología sin PLM, grupos de exclusión, banco de referencia, taxonomía y representaciones de términos por corte.
- **Contrato del método.** El método tiene identidad propia y deja de disfrazarse de configuración de embedding (prediction_set.py:37-41). Declara su corte de instancia, sus ventanas de entrenamiento por id y sus pines por sha256. Guarda la puntuación final y las explicaciones.
- **Contrato de etapa de cálculo.** Las etapas pesadas son funciones puras de mensaje y almacén. Un único ejecutor aplica reintentos acotados, publica con confirmación del broker antes de dar el acuse y comprueba el sello de revisión.
- **Contrato de evaluación.** Un solo evaluador reúne todas las negativas en un sitio. La IA es obligatoria. Los estratos salen de la tabla de homología común y el commit del evaluador queda sellado.
- **Descriptor de cada operación.** Cada operación declara dominio, tipo, cola, pureza, recurso y familia. De esa declaración salen el enrutado, la validación de la API y la lista de lo que puede correr en los pilotos.

## 3. Por máquina
- **Sobremesa (dev).**
  - Pila separada: Postgres pg18, RabbitMQ 4.3.5 y MinIO, fijados por digest y lanzados con Quadlet.
  - Todo escucha en 127.0.0.1:26xxx, con credenciales nuevas, un clon propio, un venv propio y unidades protea-dev-*.
  - Nunca se crea una unidad protea-lab-worker@ y nunca se usan manage.sh ni deploy.sh, porque matan por patrón al trabajador de producción (scripts/manage.sh:100-101,111,116).
  - Memoria: dev limitado a 9 GiB, porque hay 61 GiB (`free -g`) y producción puede tomar 48 GiB.
  - Disco: el universo necesita un disco nuevo de 1 a 2 TB. Hoy / tiene 367G libres (`df -h`, 17:09), pero esa cifra cambió de 73G a 367G en el mismo día.
- **Picasso.**
  - Una imagen .sif por revisión y pesos con manifiesto sha256.
  - Las descargas se hacen solo en el nodo de acceso. Las fotos se construyen en trabajos de CPU de 2 h o menos.
  - Pilotos de una GPU, solo cuando se cumplan las puertas de la sección 4. El túnel inverso sale del sobremesa y solo existe mientras haya pilotos.
  - fscratch está hoy en 0,41 TB de 0,93 TB, y la cuota de ficheros de home en 50.000 de 60.000 (`quota -s`, 17:09).
- **Portátil (producción).** No se toca nada. Antes del hito hará falta una encuesta de solo lectura: versiones de Postgres, pgvector y RabbitMQ, almacén, espacio libre. La haría su agente, con tu palabra.

## 4. Fases, PRs y comprobaciones
**Corrección que lo cambia todo.**
- La declaración sigue la punta de develop (agent-farm DECLARED-REVISION.txt:44-46) y el redeploy del portátil sigue origin/develop (protea_redeploy.sh:2). Mergear la refactorización en develop movería producción.
- Propuesta: una rama de integración larga. develop sigue siendo la línea de producción.
- Encaja con la configuración actual. El auto-merge solo actúa en PRs a develop (auto-merge.yml:3-6). Lint, integración, docs y openapi corren en cualquier PR.
- El PR #1177 de fotos se redirige a esa rama.

**Fase 0, raíles (sin cambio de comportamiento).**
1. Crear la rama. Comprobación: CI verde en un PR de prueba.
2. Guardia de coautoría. Comprobación: detecta "Generated with [Claude" y "Claude-Session:".
3. #1177 (código de medida de las fotos y ADR-D59 en estado Propuesto). Comprobación: sus 60 pruebas pasan.
4. ADR del universo único con las tres familias, y la fila de D59 en el índice.
5. Borrados de alta confianza (sección 5). Comprobación: la búsqueda de referencias sale vacía.
6. CI de integración en pg18.
7. Definiciones de dev en deploy/dev con RestartPreventExitStatus=78. Comprobación: ningún fichero menciona rutas del portátil ni protea-lab-worker.
8. Comprobación de entorno: un trabajador se niega a arrancar contra un vhost o una base que no son los suyos.
9. La guardia de revisión toma la ruta de su declaración desde la unidad y se niega si el fichero falta. Hoy lo permite (protea-guard-revision.sh:121-122).
10. Ruta de taxonomía que nunca descarga, y PROTEA_SKIP_TAXONOMY_WARMUP=1 en dev. Hoy cada trabajador descarga la taxonomía de hoy al arrancar (scripts/worker.py:184-197).
11. Puerto parametrizable en el script de espera de infraestructura, y un comando para crear la primera clave de operador.

**Fase 1, descriptor de operaciones.**
- Una especificación por cada una de las 58 operaciones (21 de universo, 14 de representación, 14 de método, 9 de evaluación e infraestructura).
- El consumidor se elige por la especificación.
- POST /jobs valida operación, cola y tipo.
- Las colas escritas a mano en el código pasan a salir de la especificación.
- Comprobación: una prueba exige especificación para todas, enrutado igual al actual, y solo operaciones puras en protea.embeddings.batch, con una lista de excepciones que se vacía en la fase 4.

**Fase 2, universo desde cero.**
- Constantes de la marca (227 y 2025_04) en un módulo hoja sin importaciones.
- El registro de bandas se identifica por sha de contenido y no por uuid de producción (band_registry.py:142,159-163).
- La creación automática de marcos pasa a ser opcional (load_goa_annotations.py:297-305).
- Tabla de canales de evidencia, cuando aceptes D59.
- Descargador con lista blanca por corte (URL, bytes, md5, fecha no posterior al corte).
- build_cut_photo como etapa de fichero, y load_cut_photo, que crea el conjunto de anotaciones con su fecha y comprueba la versión de GO que declara el GAF.
- Poblaciones por corte. declare_corpus_population no tiene parámetro de corte (declare_corpus_population.py:101-104).
- Estado de etiquetas, roles de ventana (entrenamiento y validación) y reglas de verdad declaradas.
- IA única: el rasgo de IA del brazo 1 la lee por id.
- Grupos de exclusión por secuencia y tabla de homología con MMseqs2 fijado.
- Comprobación: negativas en la release 228 y en 2025_04; fechas no nulas en todos los conjuntos antes de crear marcos; check_sets --strict pasa.

**Fase 3, reglas del ejecutor (modo base de datos).**
- Cabecera de reintento acotada.
- Errores de conexión tratados como reintento.
- Confirmación del broker antes del acuse. Se añade RabbitMQ a la CI de integración.
- Escritura idempotente por productor.
- Cola de fallos por ejecutor.
- predict cierra el trabajo padre en la etapa de escritura.
- Las cancelaciones se acusan con un evento, sin pasar por la cola de mensajes muertos.
- Una sola definición de host (hoy job.started usa el hostname del socket, provenance.py:196-200, y el resto usa PROTEA_COMPUTE_HOST).

**Fase 4, etapa pura de embeddings y modo piloto.**
- Sello de receta y sello de revisión: salida 78 solo ante una revisión ajena. Lo que no se puede verificar se trata como decisión tuya.
- Escritura v2, que acepta v1 y v2, antes del mensaje v2.
- Vectores en float32 base64: el JSON ocupa unos 22 KB por vector de 1024.
- Tamaño de lote por residuos y pesos con manifiesto.
- Modo piloto, y las etapas de residuos salen de la cola de pilotos.
- Puertas antes del primer piloto:
  - etapa pura;
  - ejecutor sin sesión de base de datos;
  - guardia de revisión;
  - cola de pilotos solo con operaciones puras;
  - sin caída silenciosa a almacenamiento local;
  - mensajes de menos de 20 min;
  - política de la guardia de tarjeta.

**Fase 5, métodos y primeros caminos.**
- Tablas de método. Las lecturas que hoy usan INNER JOIN pasan a LEFT JOIN (strata.py:153, receipts.py:45, showcase.py:123, embeddings_service.py:221).
- Puntuación final para todas las familias.
- Primer camino del brazo 1: votos de vecinos en 211, sin booster.
- Paso 1 del brazo 3: transferencia por homología, huellas de palabras y fusión, con testigos.
- Datos del brazo 2: exportación solo de entradas y las dos tablas de vecindario que faltan.
- Métodos en contenedor con estado de humo, que el evaluador rechaza para informes.

**Fase 6, evaluación unificada.** Estratos por la tabla de homología del corte y todas las negativas del evaluador juntas, conservando las guardias actuales (run_cafa_evaluation.py:241-260).

**Fase 7, portada y documentación.**
- Vitest en CI.
- Registro de las tres familias y ruta de intro, con tu texto.
- Se retira el libro, incluidas las referencias de Playwright, del sitemap y de vitest.
- Las páginas retiradas pasan a historical conservando su nombre de documento.
- noindex en dev.

**Fase 8, Picasso.** Trabajo de piloto, túnel con clave del host fijada, receta de imagen y su manual.

**Hito.** Universo reconstruido dos veces con los mismos sha de artefactos, primer camino de cada familia reproducido, cola de fallos limpia durante N días, intros con tu texto. Después: merge a develop, declaración por PR de agent-farm y restauración en el portátil.

## 5. Lista de borrado para tu aprobación
**Alta confianza:**
- El shim _self_neighbour y su prueba.
- El router rungs. Hay que quitar también la ruta del smoke de scripts/deploy-check.sh:237.
- deploy/slurm, junto con sus menciones en README.md:218, deploy/README.md y runbooks/deployment.rst.
- Seis scripts ONE-TIME: create_layer_axis_configs, remap_annotation_set_ontology, rename_embedding_configs, rederive y repair de ids de configuración, backfill_evaluation_groundtruth.
- backfill_alignment_cache y backfill_prediction_receipts.
- Dos run.yaml sin uso y database/config/system.yaml sin lector (no leí su contenido).
- multistage.py, sustituido por el contrato de etapa.
- Los parámetros muertos de LightGBM en training_dump.
- El libro de la web y su prueba, que se van en el mismo PR que las intros.

**A revisar** (lo decides tú):
- materialise_floor_census: no es de un solo uso y sirve para conservar el censo si se reemplaza la base.
- El import de compute_feature_schema_sha, porque cambia el comportamiento.
- _compute_embeddings_backends, que el código vivo importa (compute_embeddings.py:18-29).
- reranking, flows, runners, ontology y first_appearance. first_appearance implementa la regla de verdad declarada.
- Las exportaciones por minitrabajos, las dobles escrituras, graph, benchmark y experiment_run.
- Las operaciones de reparación de producción, la línea de códigos aprendidos, encode_residue_sparse, QuickGO, showcase, los contenedores de apps, scripts/analysis y scripts/recover.
- Fuera del repo: los worktrees sf-jepa export, pin-e45 y pin-e46, coord-keeper, que reinicia en bucle, y los restos de podman. Nunca `podman system prune -a`, que borraría la imagen sfjepa-lafa.

## 6. Decisiones que solo tú puedes tomar
**Bloquean el primer PR**
1. Ramas: rama de integración larga, suspender la regla de la punta de develop, o borradores hasta el hito. Recomiendo la rama de integración, con develop congelado en bc60301 salvo arreglos urgentes.
2. Arreglos de producción hasta el hito: ninguno, en develop como hoy, o rama de mantenimiento. Recomiendo ninguno salvo urgencia, y en ese caso en develop.
3. Corregir la nota del plan (#428), que aún manda al portátil cargar el universo y promocionar el viernes, y avisar a su agente: sí o no. Recomiendo sí. Los tres pendientes antiguos del portátil (referencia Ankh, sexto backend, ficha fija), recomiendo aparcarlos.
4. Nombres y lengua de las familias. Recomiendo embedding-reranker, world-model y explainable-units, con la prosa en inglés.

**Antes del universo (fases 0 a 2)**
5. Disco de dev: uno nuevo de 1 a 2 TB, la partición Windows nvme1n1p3 (acaba con el arranque dual) o arrancar en / con una imagen de 100 GB. Recomiendo el disco nuevo y la imagen en / mientras llega. Destino de copias: un segundo disco.
6. Filas de los miembros: desde el parquet de la foto o desde los GAF en el sobremesa. Recomiendo el parquet.
7. Secuencias: las de hoy de UniProt (D59, decisión 5) o las de la release emparejada (regla del laboratorio). Recomiendo la emparejada. El tamaño de TrEMBL de cada release está SIN VERIFICAR.
8. Ontología del corte 160: la tabla usa el grafo 2016-09-30, pero la regla da el 2016-10-29 (GOA-ONTOLOGY-PAIRING.md, fila 160). Recomiendo aplicar la regla, el grafo 2016-10-29.
9. Corte 205, que no tiene par de Swiss-Prot: añadir la lista de Swiss-Prot de su release emparejada o quitar el filtro "sigue revisada". Recomiendo añadirla. Corte 227: aceptar 2025_03 como par por la marca. Recomiendo sí.
10. Reglas de verdad de las cuatro ventanas. Recomiendo las de ea0f4334: projected, live_in_both_ends, NOT solo experimental y el grafo de t0 en los dos lados. IA de evaluación en la foto de t0. IA como rasgo: la del t0 de cada ventana.
11. first_admitted_release: sobre los seis cortes cargados o sobre toda la serie GOA. Recomiendo los seis cortes, entendido como el primer corte cuya foto contiene la proteína.
12. Población de evaluación y bandas. Recomiendo la regla LAFA (sigue revisada en t1), las bandas del laboratorio (30/50/70/90/99) y una sola tabla de homología sin PLM para todos.
13. Migraciones: reproducirlas todas o comprimirlas. Recomiendo reproducirlas.

**Antes de las familias**
14. Pesos entrenados en el laboratorio (vocabulario v1, léxicos, vectores de términos, boosters): prohibidos y reentrenados, admitidos con procedencia, o solo como línea base. Recomiendo prohibirlos ("sin conservar absolutamente nada") y usarlos solo como línea base. El paso 1 del brazo 3 no los necesita.
15. Modelos preentrenados posteriores al corte (PLM, Qwen3, anc2vec 2020-10): admitirlos como excepciones declaradas sin etiquetas. Recomiendo sí, salvo cualquier cosa entrenada con etiquetas GO posteriores al corte (por ejemplo el clasificador entrenado con GOA 227).
16. Entrenamiento: fuera, con registro, o como etapas de fichero declaradas de la plataforma. Recomiendo etapas declaradas ("todo en la plataforma").
17. Canales: la receta aprobada para los brazos 1 y 2. Recomiendo que el brazo 3 quite PAINT y las traducciones de campos revisados. Espejo: las filas de firma de GOA t, ya fechadas.
18. Objetos compartidos: un banco de referencia, una taxonomía y unas representaciones de términos por corte, comunes a todas las familias. Recomiendo sí.
19. Brazo 1: Ankh-base primero. Booster con parada temprana en 194->211 y luego reajuste con ese número de rondas, entrenado en la CPU del sobremesa.
20. Brazo 2: percepción Ankh + vocabulario reentrenado, las cuatro ventanas de unos 3 años y quitar feature_tokens. Brazo 3: un léxico declarado, familias sobre la foto (Swiss-Prot de t) y operaciones nativas.
21. Instancia 227 y el marco 227->230, gastado el 27-10. Recomiendo entrenar la instancia 227 con las cuatro ventanas, validarla a través de la 211, que sea la que sirve el instrumento tras el hito, y no leer 227->230 en dev.
22. Evaluador cafaeval-protea (pin 203af0a; el clon local no tiene ese commit). Recomiendo mantener el pin, sellarlo y guardarlo en cada resultado, y probar la rama de arreglo en un PR aparte.

**Antes de los pilotos**
23. Tarjeta del sobremesa. Recomiendo que sea de dev mientras los trabajadores de GPU de producción sigan parados, como hoy. Si arrancas uno, antes se para el de dev.
24. Pilotos:
    - como mucho 2 a la vez;
    - reenvío solo a mano, sin cadenas;
    - salida tras 10 min sin mensajes;
    - CPUs y memoria según la medida;
    - A100 primero;
    - preguntar al SCBI por los reenvíos al loopback del nodo de acceso.
    Una revisión que no se puede verificar se rechaza con motivo. Colas clásicas, sin quorum, mientras no se verifique el recuento. Las etapas de GPU con ficheros van en una cola solo del sobremesa.
25. Quién lanza y quién revisa. Recomiendo que yo lance las fases de arranque y las evaluaciones con tu aprobación por fase, y nunca entrenamientos ni trabajos de Picasso sin tu palabra en cada uno. Revisión: el agente del portátil, con lectura en la tailnet, y después tú.
26. Picasso: confirmar si se aprobaron los borrados de las 15:46 a 15:58. Recomiendo reutilizar las descargas de 211 si su sha coincide y permitir allí el entrenamiento de la instancia 227 con las ganancias 211->227.

**Antes del hito**
27. Promoción. Recomiendo:
    - reemplazar la base en paralelo (azul/verde) si hay espacio, y si no archivar y reemplazar;
    - copiar usuarios, claves y cuotas, y reiniciar las sesiones;
    - declarar el commit de develop por PR de agent-farm;
    - "estable" quiere decir: universo reconstruido, sin mensajes muertos sin explicar durante N días y cada familia reproducida.

## 7. Riesgos principales
- Un merge en develop mueve producción (regla de la punta). Mitigación: la rama de integración (decisión 1).
- Contaminación cruzada en el sobremesa: node-sync adopta las unidades protea-lab-worker@, los scripts matan por patrón y la taxonomía se descarga al arrancar.
- Memoria: 9 GiB de dev más 48 GiB de producción en el mismo dominio de muerte de oomd.
- La tarjeta compartida. La comprobación de GPU libre falla si hay un terminal abierto (ptyxis tiene un contexto), y protea.methods usa la GPU.
- La promoción deja el env del trabajador de producción del sobremesa apuntando a la base vieja. Hay que incluir los env de cada nodo en el cambio y en la vuelta atrás.
- Túnel de pilotos: el loopback del nodo de acceso es compartido, Picasso no tiene known_hosts y escribir en amq.default permite publicar en cualquier cola. Mitigación: clave de host fijada, socket o puerto por trabajo, exchange propio y TLS.
- Tamaño de mensaje: RabbitMQ 4.x con límite por defecto SIN VERIFICAR, frente a unos 22 KB por vector en JSON.
- Pila del laboratorio distinta (Python 3.14, torch cu130, triton) y repos sin remoto: sf-jepa, differentiable-alignment. Hay que hacer copia ya.
- Las cifras de laboratorio (0,3765; 0,4547) no se trasladan al universo nuevo.
- ADR-D59 se movió tres veces hoy, y otra sesión está cambiando Picasso.

---

# PART 2. Technical annex for the PROTEA ADR (English)

All repo paths are relative to /home/xaxi/Thesis/PROTEA-dev-fotos (feat/cut-photos @ fde5456, clean). Facts carry the source quoted by the inventory or verification they come from, unless they come from a command run here.

Commands run for this plan (all at 2026-11-15 17:09 unless stated):
- `df -h /`: 367G free.
- `free -g`: 61 GiB total.
- `ssh -o BatchMode=yes picasso 'quota -s; sinfo -s'`: fscratch 0.41TB/0.93TB, home files 50.0k/60.0k.
- `git show origin/main:plans/DECLARED-REVISION.txt` (agent-farm): tip rule at :44-46; coordinator and schema-applied bc603014... at :2583-2584.
- auto-merge.yml:3-6: auto-merge fires only for PRs to develop.
- Workflow triggers: lint, integration, docs, openapi-drift, coauthor-guard and pinned-deps run on every pull_request.
- provenance.py:196-200: job.started host comes from socket.
- _host.py: compute_host honours PROTEA_COMPUTE_HOST.
- GOA-ONTOLOGY-PAIRING.md, row 160: declares 2016-10-29, uses graph 2016-09-30.

## A. Branch and environment frame (corrected)

- **A1. Integration branch.** All refactor PRs (including retargeted #1177) go to a long-lived integration branch. Develop stays prod's line under the tip rule.
  - Siblings get integration branches of the same name. PROTEA pins them by commit, so siblings' develop never moves. protea_redeploy.sh:2 pulls siblings' develop.
  - The milestone merge into develop should be a merge commit, not a squash. Branch-protection support for that is UNVERIFIED.
- **A2. Dev declaration.** agent-farm `plans/DECLARED-REVISION-DEV.txt` holds coordinator and schema-applied, which may be integration-branch shas.
  - The guard reads the path handed in by the unit, refuses when the file is missing, and checks schema-applied for migrate.
  - The dev tree is a separate clone, because the guard refuses a worktree (protea-guard-revision.sh:89-93).
  - The declaration moves only between bootstrap phases, with zero QUEUED/RUNNING jobs.
- **A3. Two-layer isolation.** Layer one: a separate broker, database and bucket on 127.0.0.1:26xxx. Layer two: a startup check in code (PROTEA_ENVIRONMENT=dev requires the dev vhost and database name).
  - Quadlet sources are versioned in deploy/dev and installed into ~/.config. Nothing goes into the repo with secrets.
  - Dev units are named protea-dev-*, never protea-lab-worker@ (node-sync selects those: protea-node-sync.sh:96-111).
- **A4. Prod at the milestone.** Promotion replaces the database (blue/green or archive-then-replace), restores the dev dump, mirrors the bucket under the same name (URIs embed it: minio_store.py:17-19) and declares R.
  - Every node env file is switched and rolled back, including the desktop's protea-lab.env.
  - Desktop prod venvs are rebuilt against R's full lock, because node-sync installs only git packages with --no-deps (protea-node-sync.sh:174-185).

## B. Contracts as interfaces

- **B1. Mark constants** go in a leaf module with no imports. contracts/__init__.py pulls sqlalchemy and storage, which breaks the builder's pure-import promise in cut_photo/__init__.py:9-12.
  ```python
  # protea/core/marks.py
  MARK_RELEASE = 227
  UNIPROT_CEILING = "2025_04"
  ```
  measure.py:62, band_registry and split_registry.py:154 (BOARD_MARK) import it.
- **B2. Universe** (`protea/core/contracts/universe.py` plus `protea/core/universe/reader.py`):
  ```python
  @dataclass(frozen=True)
  class Cut:
      release: int
      published: date
      annotation_set_id: UUID
      ontology_snapshot_id: UUID
      swissprot_release_id: UUID | None
      photo_id: UUID | None

  @dataclass(frozen=True)
  class Frame:
      evaluation_set_id: UUID
      t0: int
      t1: int
      role: Literal["training", "validation", "test_spent"]
      truth_rules: TruthRules
      groundtruth_sha256: str
      population: Population

  @dataclass(frozen=True)
  class TruthRules:
      profile: str
      toi_rule: str
      not_codes: str
      closure: Literal["per_side", "t0_graph"]

  class UniverseReader(Protocol):
      def cut(self, release: int) -> Cut: ...
      def frame(self, evaluation_set_id: UUID) -> Frame: ...
      def population(self, query_set_id: UUID) -> Population: ...
      def label_state(self, cut: Cut) -> LabelState: ...
      def reference_bank(self, cut: Cut, channels: frozenset[str]) -> Digest: ...
      def taxonomy(self, cut: Cut) -> Digest: ...
      def term_representation(self, snapshot_id: UUID, kind: str) -> Digest: ...
      def exclusion_groups(self, cut: Cut) -> ExclusionGroups: ...
      def homology(self, cut: Cut, population: Population) -> HomologyTable: ...
      def information_accretion(self, frame: Frame) -> InformationAccretionRef: ...  # carries content_sha256
      def sequences(self, md5s: Iterable[str]) -> Mapping[str, str]: ...
  ```
  - A schema migration adds the frame roles. window_role accepts only valid/test/NULL today (evaluation_set.py:92).
  - Band tokens are keyed by InformationAccretionSet.content_sha256 (information_accretion_set.py:101-102), because set ids are uuid4. Dev forbids band=None evaluations.
  - Refusals: release > MARK_RELEASE; UniProt >= ceiling; a source published after its cut; an unknown GO_REF; any set failing check_sets --strict.
  - Every by-reference route is refused in dev: datasets.py:641-667, model_weights.py:138, reranker_models.py:9-14. The only exception is the registration route the author allows.
- **B3. Method** (`protea/core/contracts/method.py`):
  ```python
  @dataclass(frozen=True)
  class MethodSpec:
      family: Family
      code: str
      instance: InstanceCut  # release, ontology_snapshot_id
      recipe: Mapping[str, Any]
      pins: tuple[Pin, ...]  # role, sha256, refs
      runtime: Literal["native", "container"]
      explains: bool
      # method_id is uuid5 over the canonical JSON

  @dataclass(frozen=True)
  class TrainingIdentity:
      windows: tuple[TrainingWindow, ...]  # by evaluation_set_id
      holdout: TrainingWindow | None
      data: tuple[Digest, ...]
      code_revision: str
      sibling_revisions: Mapping[str, str]
      evaluator_revision: str
      label_free: bool
      pretrained_exceptions: tuple[str, ...]

  class Method(Protocol):
      def refusals(self, u: UniverseReader) -> list[Refusal]: ...
      def training_exports(self, windows) -> list[OperationRequest]: ...
      def accept_training(self, ident: TrainingIdentity) -> list[Refusal]: ...
      def prediction_requests(self, cut: Cut, pop: Population) -> list[OperationRequest]: ...
      def explanation_schema(self) -> Mapping | None: ...
  ```
  - Tables: method, method_training_window(role fit|holdout), method_pin, prediction_explanation, and prediction_set.method_id. embedding_config_id and limit_per_entry become nullable.
  - The same PR converts INNER to LEFT JOIN in strata.py:153, receipts.py:45, showcase.py:123 and embeddings_service.py:221, and classifies method_id in method_seal (method_seal.py:39-43).
  - The leakage guard reads the method and its pins. Today it returns silently when there is no config (_evaluation_leakage.py:91-93).
- **B4. Compute stage** (`compute_stage.py` replaces multistage.py):
  - `PureStage.run(payload, ctx) -> StageOutput(downstream, files, result)`.
  - `StageContext` carries emit (buffered, never a session), deadline, a weights resolver and an optional store.
  - `check_revision_seal(seal) -> VERIFIED_EQUAL | FOREIGN | UNVERIFIABLE`.
  - `StageExecutor(mode=DATABASE|PURE|PILOT)`.
  - Exit codes: 0; 75 from the watchdog (_operation_window.py:44); 78 only on FOREIGN.
- **B5. Evaluation:**
  ```python
  EvaluationRequest(prediction_set_id, frame, information_accretion_set_id, strata, purpose)
  ```
  - Strata: one PLM-free homology table, declared identity and length edges, NK/LK/PK.
  - New refusals: test_spent; method instance or any window/pin t1 > frame.t0; missing or mismatched IA (today it warns and uses IC=1: _evaluation_artifacts.py:133-175); InterPro graft outside the mirror family; population digest mismatch; smoke status for "report"; unverifiable evaluator commit.
  - Existing guards that must still fire: run_cafa_evaluation.py:71 and 241-260, the band guard at :479-507, and the groundtruth digest check.
  - evaluation_result gains evaluator_revision (cafaeval-protea, pinned at pyproject.toml:33).

## C. Operation taxonomy

Descriptor:
```
OperationSpec(domain, kind, queue, purity, resource, family, publishes_to, status)
```
- Kinds: job, coordinator, message_stage, write, file_stage.
- The registry refuses a missing or inconsistent spec. Enforcement lands with the last spec PR.
- worker.py chooses the consumer from kind (today a hardcoded set: scripts/worker.py:83-95).
- POST /jobs refuses unknown operations, a wrong queue, or stage kinds (today unchecked: jobs.py:187-192,335-357).
- Queue literals in the code are derived from specs, with a test that none remain.

| Kind | Queue | Operations (family; status) |
|---|---|---|
| job, universe (21) | protea.jobs | insert_proteins, fetch_uniprot_metadata (display only), load_ontology_snapshot, archive_ontology_snapshot, load_ontology_aliases, load_quickgo_annotations (review), extract_goa_universe, resolve_protein_sequences (decision 7), load_goa_annotations (auto-frame opt-in), load_swissprot_release, refresh_goa_release_dates (runs after the sets exist), load_interpro_go_mapping and run_interproscan_batch (mirror), analyze_annotation_evolution, declare_corpus_population (gains a cut), compute_information_accretion, generate_evaluation_set (roles and truth rules), export_evaluation_targets, declare_query_set_provenance, retire_evaluation_sets, seal_evaluation_groundtruth (the last three are prod repair, review) |
| coordinator | protea.embeddings / protea.predictions / protea.training | compute_embeddings, encode_residue_vocabulary, encode_residue_sparse (review), predict_go_terms, export_coordinator (review) |
| message_stage, pure | protea.embeddings.batch | compute_embeddings_batch (after phase 4); nothing else may stay |
| message_stage, database | protea.predictions.batch (CPU, desktop only); protea.training.knn-batch and .features (review) | predict_go_terms_batch, export_knn_batch, export_features_batch |
| message_stage, files | new desktop-only GPU queue | encode_residue_vocabulary_batch, encode_residue_sparse_batch |
| node stage | protea.embeddings.upload | upload_residue_shard (already DB-free) |
| write | *.write | store_embeddings, store_residue_codes, store_predictions, export_write |
| job, representation | protea.methods (GPU node) / protea.jobs / protea.training | measure_embedding_magnitude, apply_learned_encoder (review), count_backend_parameters, export_gate_bundle (review), declare_exam_population |
| job, method | protea.jobs / protea.training / protea.methods / protea.methods.write | predict_go_terms_from_interpro (mirror), build_go_cooccurrence, export_research_dataset (windows by id), export_transitions_dataset (inputs-only plus the neighbourhood tables), register_ingested_method (until register_method), run_lab_method (GPU, treat as a GPU unit), ingest_method_predictions |
| job, evaluation | protea.evaluations | run_cafa_evaluation, batch_rescore_evaluation, stratify_evaluation, compare_paired_panels, seal_evaluation_frames (the module stays: seal_one), audit_evaluation_frames and audit_per_protein_artifacts (review), verify_window_against_reference |
| job, infrastructure | protea.ping | ping |

New operations:
- build_cut_photo (file stage, Picasso CPU).
- load_cut_photo (jobs). It creates the annotation set, stamps source_published_at from the manifest and enforces the GAF-declared GO version.
- build_label_state, build_reference_bank, build_cut_taxonomy and compute_term_text_vectors (GPU file stage).
- build_exclusion_groups and build_homology_table (training queue, desktop CPU, pinned MMseqs2).
- register_method.
- record_stage_failure: one failure queue per executor, never Job queues (protea.methods.write is a Job queue).
- transfer_neighbour_labels, build_word_fingerprints, fuse_prediction_sets.
- Later: decode_lexicon (file stage), build_segment_families, build_count_map.

## D. Pure compute-stage contract (compute_embeddings_batch v2)

Payload:
```
schema_version 2
batch_id = uuid5(parent, sorted md5s, config ids)
parent_job_id
configs[]:   config_id, recipe = exactly IDENTITY_FIELDS, built in ONE place
             row_digest = sha256 of the full row, not only the identity fields,
             which uuid5 already covers
sequences[]: md5, residues
revision:    code_revision + six siblings
weights:     backend, model_name, manifest_sha256
skip_existing: Literal[True]
batch_size
budget_seconds
```
- The stage verifies, in order:
  - the seal;
  - uuid5(recipe) == config_id (embedding_identity.py:78-87);
  - md5 of each sequence;
  - the weights manifest, over HF_HOME with HF_HUB_OFFLINE=1 set before import. Plugin load_model takes no path at 2cb6b47.
- It builds PassRecipe objects with an `id` attribute (_embedding_pass_group.py:254,277,287), runs the existing group inference, and returns ONE .write message: vectors as base64 float32 keyed by md5, row_digest, batch_id, relayed events with host, and the seal.
- Base64 float32 rather than fp16, because embedding_scale is applied at write. JSON costs about 22 KB per 1024-d vector.
- Write v2 (lands BEFORE payload v2 and accepts v1 and v2):
  1. Cancellation check.
  2. Ledger insert on (parent, batch_id); stop if present.
  3. Per config inside the loop: compare row digest, resolve embedding_scale (_compute_embeddings_helpers.py:41-51,345-355), map md5 to sequence_id, clip, ON CONFLICT DO NOTHING.
  4. Persist relayed events.
  5. Advance the parent once per batch.

| # | Constraint | Enforced in | Acceptance test |
|---|---|---|---|
| C1 | Pilot jobs <= 2 h; positional args; --constraint | deploy/picasso/pilot.sbatch; -t sized from measurement (2-3x) | script lint: no --export, limit present |
| C2 | Same queues, no Picasso queue | `worker.py --queue protea.embeddings.batch --pilot` | spec invariant test |
| C3 | Own tunnel per pilot, nothing left on the login node | `ssh -f -N -o ExitOnForwardFailure=yes`, pinned UserKnownHostsFile, StrictHostKeyChecking=yes, abort unless exit 0, trap kill | dry run; refuses to start without the tunnel |
| C4 | Reverse tunnel only while pilots run (desktop origin, deviation acknowledged) | unit never enabled; RuntimeMaxSec or exit when squeue shows no pilot | unit lint |
| C5 | Pure stage | PURE/PILOT executor builds no session factory and branches before worker.py:77 | sentinel: no DB connection opened |
| C6 | Per-config recipe plus row digest | RecipeSeal; field set == IDENTITY_FIELDS; getsource safety net (pattern of tests/test_count_backend_parameters.py:179) | uuid5 self-check, tampered recipe refused |
| C7 | Scale and digest per config in .write | store v2 loop | two configs with different scales; tampered row refused |
| C8 | Seal = code_revision + 6 siblings (unilateral) + tree_revision_now; UNVERIFIABLE distinct | check_revision_seal on code_revision.py:138-235; startup refuses an unverifiable self or any sibling without direct_url.json | one test per verdict |
| C9 | Foreign revision: cancel, requeue without spending the cap, exit | basic_cancel, nack(requeue=True), exit 78; dev units RestartPreventExitStatus=78 | fake-channel test |
| C10 | Capped retry header | x-protea-retry plus reason; defaults from tuning.py:65-79 | N retries, then failure queue |
| C11 | Connection errors -> RetryLaterError | classify() extends retry.py:45-57 | one test per class |
| C12 | Ack after confirmed publish | confirm channel, mandatory=True on the executor's own channel; publisher backoff kept for other callers | nack/unroutable leaves the input unacked |
| C13 | Graceful stop spends no cap | stop path nacks requeue unchanged (consumer.py:467-469) | SIGTERM test |
| C14 | passive=True declares | PILOT mode skips setup_dead_letter and the publisher re-declare | asserts on every declare |
| C15 | Subscribe only to protea.embeddings.batch | --pilot rejects other queues; a non-allowed op is nacked with requeue, then cancel and exit 78, never dead-lettered | tests |
| C16 | skip_existing True | Literal[True] | model rejects False |
| C17 | Weights by digest | model_weights kind plm_checkpoint plus manifest | tampered file test |
| C18 | < 20 min per message | budget from residues/s (compute_embeddings.py:454-469); watchdog 1140 s | sizing tests |
| C19 | KNN on CPU, never Picasso | predict batch spec cpu/database; deploy/slurm deleted | registry test |
| C20 | One host definition | where_it_runs uses compute_host() (moved to core); relayed host persisted | both paths stamp PROTEA_COMPUTE_HOST |

Pilot broker user:
- configure: none;
- read: protea.embeddings.batch;
- write: only a dedicated exchange `protea.pilot.out`, bound to protea.embeddings.write, protea.embeddings.batch (for header retries) and the failure queue. Write on amq.default would allow any queue.
- Passive-declare permissions are UNVERIFIED.
- TLS with a pinned CA, or per-job 0600 Unix sockets if streamlocal is allowed (UNVERIFIED).
- prefetch 1 (consumer.py:67); idle exit configurable.
- Phase-1 pilots get no store: outputs travel in messages.

## E. PR list (integration branch, in dependency order)

Phase 0:
- P0.1 Create the branch; push triggers for it. Accept: CI on a test PR.
- P0.2 Coauthor guard covers "Generated with [Claude" and "Claude-Session:". Accept: a regex test.
- P0.3 #1177 retargeted. Accept: its 60 tests pass.
- P0.4 ADR of one universe and three families, plus the D59 index row. Accept: docs build, em-dash gate.
- P0.5 Deletions H1-H10 (Part 1, section 5).
  - Includes deploy-check.sh:237, the deploy/slurm mentions, the H1 docstring at tests/test_the_batch_does_not_choose_the_donors.py:142, and the _evaluation_groundtruth.py:174,199 hints.
  - Accept: empty reference grep; unit suite green.
- P0.6 Integration CI on pg18 (integration.yml:30) plus a RabbitMQ service.
- P0.7 deploy/dev: Quadlet sources, dev templates with MemoryMax, RestartPreventExitStatus=78 and a clock-sync gate (the logic of protea-lab-worker.sh:270-291). Accept: no laptop path, no protea-lab-worker.
- P0.8 Environment check (vhost and db). Accept: tests both ways.
- P0.9 Guard declaration path, missing file refuses. Accept: guard tests.
- P0.10 Taxonomy path, never downloads. Accept: no network in tests.
- P0.11 Wait-infra port parameter and a bootstrap-operator-key CLI.

Phase 1:
- P1.1-P1.4 Specs per domain. Enforcement and the every-op-has-a-spec test land with P1.4.
- P1.5 Consumer from spec.
- P1.6 POST /jobs validation; fix the jobs.py:174 example.
- P1.7 Pilot allowlist invariant.
- P1.8 Queue literals derived from specs.

Phase 2:
- P2.1 marks.py plus source guards (taxonomy, interpro2go, downloader). Accept: refusals at 228 and 2025_04.
- P2.2 Band registry by content sha.
- P2.3 Auto-frame opt-in.
- P2.4 evidence_channel table, after D59 is accepted.
- P2.5 Allowlisted downloader, `protea stage run`, CPU compute image recipe (base by digest, pinned torch, pinned MMseqs2, git sibling installs, PROTEA_CODE_REVISION).
- P2.6 build_cut_photo.
- P2.7 load_cut_photo and the photo tables; source_published_at non-NULL asserted.
- P2.8 Cut-aware populations and label state.
- P2.9 Window roles and declared truth rules; superset restriction for evaluation sets.
- P2.10 IA by set id for arm 1 (_ia_feature.py:72-104) and export.
- P2.11 Exclusion groups and homology table.
- P2.12 Reference bank, cut taxonomy, term representations.

Phase 3:
- P3.1 Retry header.
- P3.2 Connection classification.
- P3.3 Confirm before ack.
- P3.4 Idempotency key per write producer: embeddings by batch_id; predictions by (set, batch, chunk). Reconcile counters against rows.
- P3.5 Failure queue.
- P3.6 Predict closes at write.
- P3.7 Cancellations acked with an event.
- P3.8 Host unification.
- P3.9 Monitoring: dead-letter growth, queues with messages and no consumer, counter/row mismatch.

Phase 4:
- P4.1 RecipeSeal and PassRecipe.
- P4.2 Revision seal; predict batch adopts it.
- P4.3 Write v2 (v1 and v2).
- P4.4 Payload v2.
- P4.5 Sizing.
- P4.6 Weights manifests.
- P4.7 Pilot mode.
- P4.8 Residue batches to the desktop-only queue.
- P4.9 Broker max_message_size set and measured.

Phase 5:
- P5.1 Method tables, joins, leakage guard, evaluator revision sealed.
- P5.2 Final score stored.
- P5.3 Arm-1 first path; classifier, ProtST, anc2vec and InterPro graft off.
- P5.4 Export by window id with a shared producer.
- P5.5 Booster pin, holdout recorded (lab change in protea-reranker-lab).
- P5.6 Arm-3 step 1 plus prediction_explanation.
- P5.7 Arm-2 inputs-only export.
- P5.8 neighbourhood and neighbour_state tables (feature_tokens per decision).
- P5.9 Container methods, smoke status, refusal.

Phase 6:
- P6.1 Strata from the cut homology table.
- P6.2 Evaluator refusals in one place.

Phase 7:
- P7.0 Vitest in CI.
- P7.1 Family registry and intro route; retire the book, including landing.spec.ts, sitemapCoverage.test.ts, knowledgeRegimes.test.ts:3, the score page link and the book keys ReceiptFootnote still uses.
- P7.2 Docs family pages; retire pages by toctree move.
- P7.3 noindex and dev site URL; release-process.rst and TOPOLOGY.md updated.

Phase 8:
- P8.1 deploy/picasso (pilot, tunnel, GPU image, weights).
- P8.2 Runbook in operate/join-a-compute-node.rst (keep the docname).

Sibling changes, each with a pin bump: protea-backends offline path (optional); protea-reranker-lab holdout; protea-sources dated-release sequences (stream_release_fasta) if decision 7 picks the paired release. Contracts stay in PROTEA core first.

## F. Bootstrap runbook (sketch, nothing executed)

**Desktop:**
```bash
# fstab, never without nofail
LABEL=protea-dev /srv/protea-dev ext4 defaults,noatime,nofail,x-systemd.device-timeout=10s 0 2
# dev units carry AssertPathIsMountPoint=/srv/protea-dev
git clone --no-checkout <repo> /srv/protea-dev/deploy/PROTEA
git -C /srv/protea-dev/deploy/PROTEA checkout --detach <DEV_SHA>
uv venv --python 3.12.13 /srv/protea-dev/venv
# poetry install --only=main,plugins, then every git package of the lock at its sha (as node-sync does)
```
- Env file ~/.secrets/protea-dev.env (0600):
  - PROTEA_DB_URL 127.0.0.1:26432/protea_dev; AMQP 26672 with vhost protea-dev;
  - MinIO 26900 with a bucket not named "protea";
  - every cache variable under /srv/protea-dev/cache;
  - HF_HOME, HF_HUB_OFFLINE=1, PROTEA_SKIP_TAXONOMY_WARMUP=1, PROTEA_ALLOWED_ORIGINS as a JSON list.
  - Never set: ALLOW_DB_RESET, IA_FEATURE_PATH, INTERPRO_GO_PRED_PATH, CLASSIFIER_*, ANC2VEC_PATH, LEARNED_ENCODER_*, TWO_TOWER_*, EXPORT_MINIJOBS, DATABASE_URL, AMQP_URL.
- Quadlet: pgvector@sha256:1d50c689..., rabbitmq:4.3.5@sha256:6e83d269..., minio@sha256:cf3dadcf... (docker-compose.yml:8,130,98).
  - Postgres: cap 4G, shared_buffers 1GB, max_wal_size 8GB, temp_file_limit 100GB.
  - protea-dev.slice: MemoryMax 9G, CPUWeight 50.
- Secrets go in by stdin or env files, never argv: rabbitmqctl without a password argument (stdin behaviour UNVERIFIED), MC_HOST_<alias>, `curl -H @file`.
- The GPU unit and the protea.methods unit are not wanted by the target. Their ExecStartPre requires:
  - no prod GPU unit active;
  - no compute process outside an allowlist (ptyxis and gnome-shell hold contexts today);
  - the CDI spec present (regenerated at boot by nvidia-cdi-refresh).
- Data phases, each a POST /v1/jobs with queue_name:
  - 0: stack, ping, operator key.
  - 1: GO snapshots for six cuts, archive, aliases, channel table, taxonomy.
  - 2: load_swissprot_release for 2016_09, 2018_03, 2019_09, 2022_03, 2025_03 (and 205's pair, decision 9).
  - 3: photos (Picasso build, rsync pull, load_cut_photo); then refresh_goa_release_dates; assert dates.
  - 4: sequences, populations, label states, exclusion groups.
  - 5: IA per frame.
  - 6: four windows plus targets.
  - 7: homology table, embeddings.
  - 8: methods, readings.
- Backups (pg_dump plus bucket mirror plus sha256) at each phase boundary, to a second disk.
- Integration tests only against a tmpfs Postgres on 26433.

**Picasso:**
- `ls ~/.ssh` shows only authorized_keys. The author adds a restricted pilot key and a desktop tunnel key (permitopen/permitlisten; sshd support UNVERIFIED) and a pinned known_hosts for the login IP.
- Image: podman build on the desktop, then `podman save --format oci-archive`, rsync, and convert with apptainer/1.5.3 in a short CPU job (APPTAINER_TMPDIR and APPTAINER_CACHEDIR=$TMPDIR; unprivileged build UNVERIFIED).
- Deploy dir: ~/fscratch/protea/deploy/<sha>/ (immutable, with MANIFEST.json).
- Downloads on the login node via the allowlist, then three photo passes submitted by hand, without --dependency, each with --deadline.
- Pilots only after the phase-4 gates and the author's word.

**Laptop (milestone only, by the author or its agent on his word):** freeze, archive the old database and bucket with sha256, restore, decide on auth tables, agent-farm PR declaring R, switch every node env, verify with an evaluation re-read, roll back by re-declaring bc60301.

## G. Disk budget

| Where | Item | Size | Basis |
|---|---|---|---|
| Desktop volume | Annotation rows, 5 cuts plus 205 truth | ~14 GB plus live tiers (UNVERIFIED) | <= 5 x 8,521,521 rows at ~330 B (two-machine-setup.md:62) |
| | Cluster profiles | <= ~10 GB | 8.3 M recipe rows at 211 (fotos-cinco-cortes.md:115) |
| | Embeddings, predictions, sets | ~45-85 GB | UNVERIFIED |
| | Postgres temp/WAL reserve | 100 GB | 703 GB spill precedent |
| | Store (photos, residue codes, datasets, decodes, weights, evaluation) | ~0.19-0.24 TB | inventories; residue codes ~90.6 GB UNVERIFIED |
| | **Total** | **~0.4-0.55 TB** (+51 GB if raw GAFs stay) | -> disk >= 1 TB, 2 TB comfortable |
| Desktop / | trees, venvs, podman images (N revisions), logs | <= ~50 GB | 367G free now, volatile |
| Picasso fscratch | peak transit per cut (UniRef + GOA + Swiss-Prot) | 160: 58.5; 177: 94.7; 194: 137.0; 211: 207.8; 227: 290.2 GB | D59:240-269 |
| | images plus weights | ~70 GB UNVERIFIED | |
| | One cut at a time fits | 0.41 TB used of 0.93 TB soft now | `quota -s` |
| Laptop | new universe plus restore temp | ~0.25-0.35 TB on a 1 TB QLC disk | free space UNVERIFIED |

## H. UNVERIFIED, assigned to the phase each blocks

| Before | Checks |
|---|---|
| First merge | no laptop process follows develop (moot under the integration branch); branch protection for merge commits |
| Phase 2 | GOA 205 date and size; taxonomy archive URLs for 2016-2019; dated GO_REF lists; TrEMBL release FASTA sizes; GO_REF channel meaning per era; union protein count |
| Phases 3-4 | RabbitMQ 4.3.5 default max_message_size and quorum requeue counting; passive-declare permissions |
| Pilots | sshd permitlisten and streamlocal support; compute-node host keys; single login host (picasso3 exists); unprivileged apptainer build; fscratch retention; image on B200 nodes; tunnel throughput (desktop on Wi-Fi only) |
| Phase 8 readings | whether pin 203af0a contains the cafaeval fix |
| Promotion | laptop Postgres, pgvector and RabbitMQ versions; storage backend; bucket; free space |
---

# Appendix. The critic's list of gaps (English, verbatim)

## G0. No branch strategy and no prod fix path keep prod at bc60301 while the refactor merges

Both verifications found that the declaration follows the tip of develop. Three more facts mean every merge can move prod:
- Refactor pull requests to develop squash-merge automatically on green (PROTEA-dev-fotos/.github/workflows/auto-merge.yml:3-6,27).
- node-sync follows only a declared commit that is an ancestor of origin/develop (/home/xaxi/.local/lib/protea/protea-node-sync.sh:162-170). A prod fix branched from bc60301 can therefore be declared only after it lands on develop as a squash commit, and that commit carries every earlier refactor commit.
- agent-farm scripts/services/deploy-keeper-tick.sh:180 calls lib/protea_redeploy.sh, whose header reads 'Idempotent redeploy of origin/develop' (protea_redeploy.sh:2). The tick has no declaration check: 'command grep -n -i declar scripts/services/deploy-keeper-tick.sh' finds none.
Whether that keeper still runs on the laptop is UNVERIFIED. Its default paths are $HOME/Thesis2/... (deploy-keeper-tick.sh:12,21).

**Action.** Before the first refactor pull request merges:
- the author picks the branch strategy and the prod fix path (decisions 1 and 2);
- the laptop agent confirms read-only, on the author's word, that nothing on the laptop follows develop;
- the rule is written into agent-farm plans/.

## G1. The evaluator fork sits outside every revision seal and every evaluation record, and no inventory covered it

Every number of the three arms comes from cafaeval-protea, which PROTEA pins at 203af0a (PROTEA-dev-fotos/pyproject.toml:33). Nothing records which evaluator commit produced a number:
- The sibling seal collects only distributions named protea-* (protea/core/code_revision.py:183,197).
- Library provenance lists only transformers, tokenizers, torch and numpy (protea/core/provenance.py:73).
- evaluation_result has no evaluator revision field: grep for cafaeval|revision|version in protea/infrastructure/orm/models/annotation/evaluation_result.py hits only docstrings.
The local clone /home/xaxi/Thesis/cafaeval-protea-dev is not the running code:
- it lacks the pinned commit ('git log 203af0a...' returns 'Not a valid commit name');
- it sits on fix/nk-lk-per-protein-row-index (d9138e7, 2026-11-07);
- its main carries a scoring change, e937e0e 'A protein with no scoreable truth is not a false positive (#26)'.

**Action.** Seal the evaluator commit together with the six siblings and store it on every evaluation result. Inventory the fork. Before phase 8, settle which evaluator commit scores the dev universe (decision 6).

## G2. Instance 227 has no plan, and the sources disagree on reading 227->230

The frame trains instance 227 on all four windows. Neither design plans it:
- both build first paths for instance 211 only (architecture c.1-c.3);
- both refuse 227->230: architecture a.4 refuses test_spent frames, and entornos phase 6 says 'Nothing for 227->230'.
The sources conflict on reading 227->230:
- The approved skeleton says instance 227 reads 227->230 once, with the author's word (memory receta-dos-instancias-2026-11-15.md:13,16).
- The laptop says that test was spent on 2026-10-27 and that rebuilding data does not restore it (agent-farm origin/plans/plan-semana-2026-11-16:plans/PLAN-SEMANA-2026-11-16.md:151).
- The author earlier called an empty 227->230 window 'un gap innecesario' (memory iteration-close-order.md:29; platform-method-contract.md:86).
Nothing says which instance prod's public instrument serves after promotion.

**Action.** Get the author's ruling (decision 3). Then add an instance-227 path to the plan: training on four windows, registration, what prod serves, and its evaluation status.

## G3. The truth rules of the four windows are not declared

generate_evaluation_set has defaults that differ from the headline window:
- Defaults: truth_profile=as_closed, toi_rule=pivot_terms, not_codes=any (protea/core/_truth_rules.py:52,69,105; protea/core/operations/generate_evaluation_set.py:58-60,88-101). Each side closes under its own graph unless both native snapshot ids are passed (:75-76).
- The 211->227 headline window ea0f4334 used projected, live_in_both_ends and experimental, with t0's graph on both sides (memory platform-method-contract.md:33-34).
- On 211->227, per-side closure gives PK 43,336 proteins; t0's graph gives 19,311 (memory protea-truth-per-side-closure.md:13,26).
Neither design names these settings. The architecture's LabelState says only 'the evaluator's closure'.

**Action.** The author fixes the rules once (decision 4). Every window stores them, and a test checks that all four windows share them.

## G4. The schema has no role for training windows

Architecture a.1 types Frame.role as training, validation or test_spent. window_role accepts only 'valid', 'test' or NULL (protea/infrastructure/orm/models/annotation/evaluation_set.py:92; protea/core/operations/generate_evaluation_set.py:157-164). So training windows look unbound, and the evaluator's test_spent refusal has no stored value to read.

**Action.** In phase 4, add the roles with a migration and a validator change, before phase 6 creates the windows.

## G5. At promotion, the desktop's prod environments will not receive new third-party dependencies

node-sync installs only the git packages listed in the declared commit's lockfile, with --no-deps (/home/xaxi/.local/lib/protea/protea-node-sync.sh:9-14,174-185,380-389). If the refactor adds or bumps a PyPI dependency, protea-venv-py312 will not have it when R is declared. The desktop's prod training worker can then fail at import, or run with old libraries. Neither promotion sequence rebuilds this environment.

**Action.** Add a promotion step that rebuilds or checks every desktop prod environment against R's full lock. Alternatively, make node-sync refuse a jump when non-git lock entries changed.

## G6. Nobody owns the laptop readiness survey that promotion depends on

These laptop facts are all UNVERIFIED, and each can break the restore:
- Postgres major version. Dev uses pg18 (docker-compose.yml:8), and a pg18 dump does not restore into an older server. Integration CI still uses pg16 (.github/workflows/integration.yml:30).
- pgvector version.
- RabbitMQ version and max_message_size.
- Storage backend. The default is local (docs/source/runbooks/deployment-process-stack.rst:94-95).
- The bucket name, which is embedded in every s3 URI (protea/infrastructure/storage/minio_store.py:17-19, per the entornos design).
- Free space on the 1 TB QLC disk.
- Python and torch versions.

**Action.** Run one read-only survey by the laptop agent, on the author's word. Write the results into the promotion dossier before dev's schema and bucket names are fixed.

## G7. A stale coordination note still tells the laptop to load the universe and promote this week

The unmerged agent-farm note has the laptop loading the universe into production on Tuesday and promoting on Friday, and it places the reverse tunnel on the laptop: 'git show origin/plans/plan-semana-2026-11-16:plans/PLAN-SEMANA-2026-11-16.md', lines 47, 59, 62, 69 and 108. The evening decision leaves the laptop untouched, and both designs move the tunnel to the desktop. origin/main ends at #426 ('git log --oneline -5 origin/main'), so pull requests #428 and #427 are still open as far as local refs show. The laptop agent is reachable through the bridge (memory plan-semana-2026-11-16.md:17), but neither design says who corrects the note or tells the agent.

**Action.** Draft the correction and get the author's approval. Post it as a plans/ note and send it by SendMessage.

## G8. Several universe objects that all arms should share are still private to one arm or dated today

The context requires the universe to be identical for all arms. Today:
- Each arm has its own bank: the label state in architecture c.1; the truth state with exclusions in c.3; arm 2's neighbourhood bank is still open (arm2 inventory).
- Term representations are private to their arm: anc2vec on GO 2020-10 for arm 1, and Qwen3 text vectors, computed only in the lab, for arm 2.
- Protein taxonomy comes from today's UniProt and NCBI (resolve_protein_sequences; protea/core/feature_engineering.py:130-146, per the verifications).
Only photos, label states, homology tables and exclusion groups are shared (architecture a.1).

**Action.** Declare per cut one reference bank, one taxonomy, one set of term representations and one homology table. Arms reference them by id. Add a test that all arms of an instance read the same ids (decisions 12 and 13).

## G9. Three world-model tables have no owner

The transitions writer declares ten tables but implements seven. neighbourhood, neighbour_state and feature_tokens are missing (protea/core/operations/export_transitions_dataset.py:84-109). The lab loader requires neighbourhood and neighbour_state (/home/xaxi/Thesis/sf-jepa-compresion/src/sfjepa/knowledge/dataset.py:65-66). Architecture P5.7 adds only an inputs-only export and a column-contract test, and that test would fail until the tables exist. Only feature_tokens appears as a decision (D-12).

**Action.** After the bank decision, add one pull request for neighbourhood and neighbour_state, and one for feature_tokens or for its removal from ADR-D56.

## G10. The PLM-free arm depends on two local repositories that have no remote and no backup

step55_dominios.py imports differentiable_alignment from the path in ALIGNER_SRC (sf-jepa-compresion/compresion/scripts/step55_dominios.py:59-82), and step57_segmental.py loads step55 (step57_segmental.py:42).
- /home/xaxi/Thesis/differentiable-alignment and differentiable-alignment-rapido have no git remote ('git remote -v | wc -l' prints 0).
- Neither has a bundle in /mnt/protea-archive/archive/lab-bundles, which holds only sf-jepa bundles from 2026-11-03 and 2026-11-04.
- The sf-jepa lab repository has no remote either (same command).
No inventory or design lists these repositories.

**Action.** Back them up now, to a private remote or as bundles. Pin the aligner as a declared dependency before porting the lexicon code.

## G11. The lab arms and the PROTEA image run different software stacks

- Lab code runs Python 3.14 with torch 2.11.0+cu130 and triton 3.6.0, on the desktop ('ls /home/xaxi/Thesis/sf-jepa/.venv/lib' and its dist-info) and on Picasso (ssh -o BatchMode=yes picasso 'ls ~/Thesis/sf-jepa/.venv/lib/python3.14/site-packages').
- PROTEA builds on Python 3.12 (Dockerfile:2,23), takes torch from the lock (poetry.lock lists 2.10.0+cpu and 2.12.0+cpu) and overrides it with a cu128 GPU build (scripts/install_gpu_torch.sh).
- Entornos c.7 runs lab training 'from the same image', yet the Triton decode and the world-model code were validated only on the lab stack.
- B200 nodes ran driver 610.57 with CUDA 13.3 (memory picasso-scbi-access.md:20). The PROTEA image has never run there.

**Action.** Decide between one image and two (decision 20). Before any arm-2 or arm-3 number is reported, require lab-versus-platform parity tests on segments, columns and bits. /home/xaxi/Thesis/node-regime (fingerprints from 2026-10-05) is a precedent for a cross-machine stack check.

## G12. Sibling repository changes and the contract pin cascade are not planned, and protea-sources was never inventoried

All five siblings pin protea-contracts at dd335182: pyproject.toml of protea-sources-dev:24, protea-backends-dev:25, protea-method-dev:30, protea-reranker-lab-dev:22 and protea-runners-dev:25. Each of these changes would force a pin cascade across six repositories:
- payload v2;
- a segmentation output for the lexicon decode;
- any Method types placed in contracts.
protea-sources reads today's UniProt over REST (protea-sources-dev/src/protea_sources/uniprot/__init__.py:70,72,86). It also has stream_release_fasta for dated release files (:424-454), the natural route if sequences must come from the paired release.

**Action.** Add to the plan a list of sibling changes, their order and the pin bumps they need (decision 19).

## G13. The mirror family's inputs are not dated

The architecture keeps the InterPro mirror operations (b.2 rows 13, 14 and 40). Two of their inputs are current, not dated:
- load_interpro_go_mapping defaults to the current EBI interpro2go file (load_interpro_go_mapping.py:54-64, per the architecture verification);
- run_interproscan_batch would score with a present-day InterPro release.
GOA t already stores signature_electronic rows that are dated by the cut (docs/source/adr/D59-the-corpus-at-a-cut-is-a-photo.rst:114-145). Neither design applies the 'no source after the cut' rule to the mirror.

**Action.** The author chooses the mirror's input (decision 11). If InterProScan stays, pin an InterPro release on or before each cut.

## G14. The entornos design contradicts itself on neighbour search on Picasso

- Entornos invariant 6 says neighbour search never runs on Picasso.
- Its table b.3 places an optional MMseqs2 all-against-all on Picasso CPU jobs.
- The task context keeps nearest-neighbour search on CPU and off Picasso.
- Arm-3 families need MMseqs2 searches over bank cores, and the lab's posterior-mass search ran in half precision on a B200 (arm3 inventory: familias_tramos.py:1-28, knn_grande.py:1-8).

**Action.** The author rules on what counts as forbidden neighbour search (decision 14). Then plan a sparse CPU path for posterior-mass neighbours.

## G15. No pilot submission policy fits Picasso etiquette

Gaps against the author's Picasso rules:
- Pilots ask for -t 02:00:00 whatever the work, and entornos submits three in a loop (entornos e.2 P-6).
- Pilots have no idle exit, and there is no rule for passes that need more than one 2 h pilot.
- The author forbade chains and 'a queue that keeps jobs topped up' (memory feedback-picasso-discreet.md:8,13). He also objected to oversized time limits and named CPUs per GPU as the binding resource (feedback-picasso-time-limits.md:26-27,31).
- Nothing pins prefetch to 1, today's default (protea/infrastructure/queue/consumer.py:67), against the broker's 30-minute consumer_timeout (memory shutdown-2026-11-04-resume.md:14).

**Action.** Add an idle-exit timeout, resubmission by hand only, CPUs and memory sized from measurements, prefetch 1, and a cap on concurrent pilots set by the author (decision 16).

## G16. The monitoring and alerts the laptop asked for are missing

The agreed pilot design asks for three signals (PLAN-SEMANA-2026-11-16.md:107,125,146 on the remote plan branch):
- an alert when the dead-letter queue grows;
- an alert when a queue holding messages has no consumer;
- a reconciliation of parent counters with stored fragments.
Neither design adds them, although a monitoring stack already exists (PROTEA-dev-fotos/docker-compose.monitoring.yml:1-14: Grafana, Loki and Prometheus; deploy/grafana). Without these signals, 'dev is stable' cannot be measured at the milestone.

**Action.** Add a dev monitoring unit or a scheduled check covering dead-letter growth, queues without consumers, and counter/row mismatches. Use it as a promotion criterion.

## G17. Nobody checked the broker's message-size limit against the new write messages

The code assumes a 128 MB broker cap and chunks predictions to about 20-25 MB (protea/config/tuning.py:249-256; protea/core/operations/predict_go_terms/_store.py:33-38). docker/rabbitmq/rabbitmq.conf sets no max_message_size: only lines 16 and 20 are active. RabbitMQ 4.x documents a lower default (UNVERIFIED here). One 1024-dimensional vector serialises to 22,179 bytes of JSON (architecture verification), so a multi-config write message for 64 sequences reaches tens of MB.

**Action.** Before P3, read the dev broker's effective limit, measure the largest write message in a dry run, and set max_message_size explicitly in the dev configuration.

## G18. The tunnelled pilot path has no traffic budget

Every pilot input and output crosses SSH forwards over the home connection and the desktop's Wi-Fi (machines inventory: enp5s0 NO-CARRIER, wlo1 at -76 dBm). The plan note warns that the home upload is slow (PLAN-SEMANA-2026-11-16.md:51). Neither design estimates bytes or throughput per pass. Entornos c.6 leaves it to the first pilot to measure.

**Action.** Measure one transfer through the tunnel and estimate traffic per pass from the vector size. Cable the desktop before scaling pilots.

## G19. Dev worker units skip the prod wrapper's clock-sync gate

The prod wrapper waits for a synchronised clock and flags the dual-boot step, where Windows leaves local time in the hardware clock (/home/xaxi/.local/lib/protea/protea-lab-worker.sh:270-291). The dev units in entornos e.1 D-7 exec scripts/worker.py directly. Leases last 120 s (protea/workers/base_worker.py:165) and the reaper acts on expired leases, so a clock step of several hours after a Windows boot can reap healthy dev jobs. nvme1n1p3 is the Windows partition of an active dual boot (entornos verification).

**Action.** Reuse the wrapper's clock gate in every dev unit, or add After=time-sync.target plus a wait for sync.

## G20. Nobody has defined who may launch dev operations or how dev results get reviewed

Two standing rules:
- Instrumentalization runs are platform operations launched on the author's word, never on our own initiative (memory feedback-no-runs-outside-platform.md:17,27).
- A result counts only after two reviews: the laptop session against the card, then the author (feedback-everything-inside-platform.md:24).
The dev stack listens on loopback only (entornos a.2), and the laptop is to be left alone. So neither the launch authority in dev nor the review path is defined.

**Action.** The author defines the launch authority and the reviewer (decision 17). If the laptop reviews, expose the dev API read-only on the tailnet; deploy/tailnet-expose.sh already exists.

## G21. Lab training has no defined way to read dev exports or register its outputs

- The reranker lab pulls export parquet files straight from S3 by name (arm1 inventory: protea-reranker-lab-dev/scripts/pull_dataset.py:2-37).
- Entornos creates only a read-write app user and a pilot user (D-6).
- The architecture refuses by-reference registration in dev (a.1), yet boosters and weights can only enter by reference (architecture verification: model_weights.py:138, reranker_models.py:9-14).

**Action.** Define a read-only training credential, the rule for shipping exports to the desktop lab and to Picasso, and the one registration route allowed in dev.

## G22. Other sessions are changing the ground under the plan

- Picasso fscratch went from 0.89 TB (machines inventory) to 0.41 TB (ssh -o BatchMode=yes picasso 'quota -s').
- 'ls -la' of ~/Thesis/protea-fotos and ~/fscratch/sfjepa-store/data shows that trembl-2022_01 and uniref-2022_03 changed at 15:46, a 60,611-byte borrar-picasso.lst was written at 15:58, and job 3675034 ran at 15:25.
- ADR-D59 moved three times during mapping (git log: 0a7ca79, 4ebf4fd, fde5456).
- The designs still cite 0.75 TB and 0.89 TB.
- No record says whether the author approved the deletions. Per the arm2 inventory, only he approves deletions.

**Action.** Name one owner for Picasso storage and one for feat/cut-photos during the refactor. Re-measure quotas right before each phase. Record the deletion approval (decision 32).

## G23. Open branches and pull requests have not been triaged

Squash merges hide which branches have landed, and many local PROTEA branches are in that state ('git for-each-ref refs/heads' in /home/xaxi/Thesis/PROTEA-dev). Examples: fix/raw-bank-copy-only-for-the-pca-fit (2026-11-05) and docs/adr-d55-evaluated-explorations. The MEMORY.md index lists drafts PROTEA #1122 and #1111 (exploration 1 result; rail 2026-11-04). The evaluator fix branch is described above. Nothing decides what lands before the refactor, what folds into it and what closes.

**Action.** On the author's word, run a read-only triage with gh, giving one verdict per open pull request or branch in PROTEA, the siblings and cafaeval-protea.

## G24. The dev universe has no backup target

Entornos takes backups at phase boundaries but names no target big enough. /mnt/protea-archive has about 63 GB free (entornos verification, df -B1: 67,313,942,528 B), against an estimated universe of about 0.4-0.55 TB (entornos f.1). Losing the dev volume would mean rebuilding everything from public sources.

**Action.** The author chooses a backup target before phase 3 (decision 28).

## G25. The designs still carry two definitions of a job's host

- The laptop asked for a small pull request so that BaseWorker jobs carry the host (PLAN-SEMANA-2026-11-16.md:147).
- The code already writes 'host' on job.started, from the socket hostname (protea/workers/base_worker.py:196-202; protea/core/provenance.py:188-202).
- OperationConsumer events use PROTEA_COMPUTE_HOST (core inventory: _host.py:27-47).
- Architecture C20 keeps both definitions, and the laptop's measured event counts disagree with the code.

**Action.** Adopt one host definition for all events, and tell the laptop which field to query.

## G26. Public documentation and artefacts are left out of the promotion plan

- README.md:12,226 sends readers to https://protea.readthedocs.io/en/latest/, which is built from .readthedocs.yaml. Which branch it builds is UNVERIFIED: the local origin/HEAD is origin/main ('git symbolic-ref refs/remotes/origin/HEAD'), and main is 1,099 commits behind (plan note line 110).
- The October Hugging Face bundle (memory sfjepa-container-hf.md) is public too.
- So are the GHCR release images (.github/workflows/docker.yml:3-6).
- Promotion covers only the /sphinx mount (protea/api/app.py:489-503).

**Action.** Add the public surfaces to the milestone checklist, and decide what they show after promotion.

## G27. The two designs have not been merged into one plan

The designs disagree on four points:
- Quadlet files: in the repository (architecture P0.8) or in ~/.config (entornos D-4).
- Environment isolation: a vhost refusal in code (architecture P0.9) or a separate broker, ports and credentials (entornos a.2-a.3).
- Pilots in phase 1: no store (architecture a.3, R-7) or MinIO forwarded to them (entornos c.6, G5).
- Dev declarations: develop commits (entornos a.7), which clashes with any branch strategy that keeps the refactor off develop.
Several entornos code changes are missing from the architecture's pull-request list:
- a guard path parameter that refuses a missing file;
- a taxonomy path plus PROTEA_SKIP_TAXONOMY_WARMUP;
- a port parameter for wait-infra;
- an allowlisted downloader;
- an operator-key bootstrap command;
- load_cut_photo writing annotation sets and source_published_at;
- a cut-aware declare_corpus_population.

**Action.** Produce one plan with a single pull-request list and one choice for each conflict.

## G28. Source facts for cuts 227 and 205 are still open

- Cut 227: ADR-D59 proves each pairing for 160-211 by giving the date of the next UniProt release, but the 227 row omits that date (docs/source/adr/D59-the-corpus-at-a-cut-is-a-photo.rst:240-269). Reading 2025_04 is barred, so 2025_03 holds for 227 only by the mark. Whether it also satisfies the date rule is UNVERIFIED.
- GOA 205: the GAF declares build 2021-11-06 and the GO directory is 2021-10-26 (agent-farm origin/main plans/GOA-ONTOLOGY-PAIRING.md, row 205). Its EBI publication date, its size and an operation that loads a truth-only set are still missing (entornos 3.4).

**Action.** The author accepts 2025_03 for cut 227 as a declared exception (decision 26). Measure GOA 205's date and size on the login node with the allowlisted downloader. Add a truth-only load mode to the pull-request list.

## G29. Load-bearing claims are still UNVERIFIED, and each blocks a named phase

Before pilots (Picasso):
- sshd allows local forwards from compute nodes to the login node, and supports permitlisten;
- the compute nodes' host keys;
- the alias reaches a single login host (memory picasso-scbi-access.md:12 also names picasso3);
- an unprivileged apptainer build from an OCI archive works, and its cache fits the home file quota of 50.0k used of 60.0k ('quota -s');
- the fscratch retention policy;
- the PROTEA image runs on B200 nodes.
Before P2/P3: the effective max_message_size and the quorum delivery-limit semantics on RabbitMQ 4.3.5.
Before phase 3 sizing: the union protein count across cuts, and the row counts at 160, 177, 194 and 227, which are scaled from 211.
With no phase named:
- tunnel throughput;
- whether evaluator pin 203af0a contains the fix branch;
- what each GO_REF means as a channel in each era (marked UNVERIFIED by the machines inventory);
- whether NCBI taxonomy archives for 2016-2019 and a dated GO_REF list are available;
- whether any chosen PLM checkpoint is gated on Hugging Face, which would need a token on the login node.

**Action.** Assign each check to the phase it gates, and run it read-only before that phase starts.

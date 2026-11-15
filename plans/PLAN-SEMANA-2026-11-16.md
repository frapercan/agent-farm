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

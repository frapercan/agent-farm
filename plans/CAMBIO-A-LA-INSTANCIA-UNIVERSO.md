# El cambio a la instancia `universo`, y las cinco trampas que tiene

Escrito el 2026-11-23 por la sesion del portatil, con la instancia a medio
construir. **No es una orden de cambiar**: es el procedimiento y lo que hay que
comprobar, recogido mientras los hechos estan frescos, porque el cambio lo pide
el autor y no esta pedido.

## HECHO el 2026-11-24, y las tres cosas que esta nota no decia

El cambio se ejecuto con la palabra del autor pedida en la sesion del portatil,
no por relevo. La publica sirve la base limpia, `protea_anterior` queda **entera
y apartada** con sus 242 GB y sus 63.094 visitas dentro, y la vuelta atras
siguen siendo dos renombrados.

Verificado despues: `/health` con las tres revisiones iguales, `deploy-check.sh`
con codigo 0 y 22 comprobaciones en verde, las once colas con su consumidor
--incluida `protea.training`, la del sobremesa-- y las paginas publicas entre
0,26 y 0,62 s. Lo que ve el publico: 2.758.480 proteinas, 113.487.299
anotaciones, 6 fotos, 8 bancos, 20.191.896 vectores, 1 ventana y 1 evaluacion.

**Las tres cosas que esta nota no decia y ahora dice:**

1. **`synchronous_commit` viaja con el renombrado.** El ajuste esta pegado al
   OBJETO base de datos, no a su nombre, asi que al renombrar `protea_universo`
   a `protea` la base que sirve al publico se quedaba en `off`. Hay que
   `ALTER DATABASE protea RESET synchronous_commit` **despues** de renombrar, y
   comprobarlo leyendo `pg_settings` dentro de esa base.
2. **Las cuentas de usuario tampoco viajan, y son las que llevan `admin`.** La
   base limpia tenia CERO filas en `user` y la vieja una, la del autor, con
   papel `admin`. Al cambiar, el instrumento se quedo sin esa cuenta y **4 de
   las 5 filas de `auth_audit` se negaron a entrar** porque la referenciaban. Se
   arregla trayendo `user` de la base apartada antes de `auth_audit`. Cuidado
   con el patron: `pg_dump -t user`, sin comillas, porque `-t '"user"'` no
   encuentra la tabla y falla en silencio.
3. **Corrige el hueco que esta nota daba por cierto.** Decia que no hay camino
   para emitir una clave por consumidor porque el alta exige `admin` y el
   arranque minta `operator`. **El camino existe: `admin` vive en las cuentas de
   usuario, no en las claves.** Con la cuenta del autor en la base, se pueden
   emitir claves por consumidor desde la API.

**Y un cabo que se ata al final**: la unidad de la API de pruebas
(`protea-universo-api.service`) apunta por fichero de entorno a
`protea_universo`, un nombre que ya no existe. Queda **parada y deshabilitada**,
porque con `Restart=always` habria entrado en bucle en el primer reinicio. Si
hace falta otra puerta para que el sobremesa cargue, se monta contra la base que
sirve, con su propio vhost y su propia clave.

## LA FORMA DE HOY, 2026-11-24 por la tarde: una base, dos puertas

Despues del cambio ya no hay dos instancias: hay **una sola base** y **dos
puertas** contra ella, separadas por vhost para que nadie coja el trabajo del
otro.

| | la publica | la puerta del sobremesa |
|---|---|---|
| API | 8000, en 127.0.0.1, con frontend y tunel | 8002, atada a la direccion del tailnet |
| base | `protea` (la reconstruida) | la misma |
| cubo | `protea-universo` | el mismo |
| vhost | `/`, con los diez trabajadores de esta maquina | `sobremesa`, con los tres del sobremesa |
| para que | lo que ve el publico y lo ligero | **lo pesado, que se calcula alli** |

Medido al cerrar: vhost `/` con **10 consumidores** y vhost `sobremesa` con
**3**, los suyos. El camino quedo probado sin coordinacion: se dejo un `ping`
esperando en la cola de la puerta y corrio solo en cuanto conectaron sus
trabajadores.

**Por que la puerta y no la cola de la publica.** Los diez trabajadores de esta
maquina consumen esas colas por nombre. Si el sobremesa publicara en el mismo
vhost, su trabajo lo cogeria quien llegase primero y lo pesado podria caer en el
portatil, que es justo lo que el reparto evita.

**Dos restos y una cosa que no esta.** Los vhosts `universo` y `limpia` quedan
vacios, de cuando la base limpia se construia aparte; no se borran sin que el
autor lo diga, aunque no contengan nada. Y la API de pruebas del 8001 esta
parada y deshabilitada, porque su fichero de entorno nombra una base que ya no
existe.

**La clave propia de la puerta la crea el autor**, desde la pagina de
administracion del instrumento. No hay forma de mintarla desde aqui sin
saltarse la puerta del propio proyecto: el alta por API exige `admin`, que vive
en las cuentas de usuario, y el guion de arranque se niega cuando ya hay claves.
Mientras no exista, el conductor usa la clave compartida.

## Las dos instancias que sirve esta maquina (como se monto, 2026-11-23)

Comparten **un solo arbol de codigo**, asi que mover el arbol las mueve a las
dos y `plans/DECLARED-REVISION.txt` declara una sola revision para ambas.

| | la publica | `universo` |
|---|---|---|
| base | `protea` | `protea_universo` |
| vhost | `/` | `universo` |
| cubo | `protea` | `protea-universo` |
| API | 8000, en 127.0.0.1, con frontend y tunel | 8001, atada a la direccion del tailnet |
| quien calcula | los once procesos de esta maquina | los trabajadores del sobremesa |
| como se construyo | cargada a lo largo de la campana | desde cero, por operaciones declaradas |

La publica se configura por `PROTEA_DB_URL`, `PROTEA_AMQP_URL` y
`PROTEA_MINIO_BUCKET` del `.env` del arbol, que **no esta rastreado**. La de
`universo` sobrescribe esos tres por entorno y hereda el resto.

## El cambio, paso a paso

1. **Parar lo que escribe.** Los diez trabajadores de la publica y el
   trabajador de la GPU del nodo, que consume las colas del vhost `/` y lo
   gobierna la declaracion. Comprobar 0 trabajos en `QUEUED`, `RUNNING` o
   `PENDING` y ninguna cola con mensajes sin confirmar.
2. **Renombrar, no borrar.** `ALTER DATABASE protea RENAME TO protea_anterior`
   y `ALTER DATABASE protea_universo RENAME TO protea`. Las dos son
   instantaneas y no copian nada. Hace falta que no queden conexiones.
3. **Atar el cubo.** En el `.env`, `PROTEA_MINIO_BUCKET=protea-universo`. **No
   se renombra el cubo**: las URIs de la base nueva lo nombran dentro
   (`s3://protea-universo/...`) y `MinioArtifactStore._key` rechaza una URI que
   nombre otro cubo que el suyo.
4. **Reinstalar las claves de operador** que valgan. Ver la trampa 2.
5. **Arrancar y comprobar**: `/health` con las tres revisiones iguales,
   `deploy-check.sh` con codigo 0, y el instrumento publico respondiendo en sus
   paginas, no solo con un 200 en la portada.
6. **No borrar nada.** Ni `protea_anterior`, ni el cubo `protea`, ni la copia
   fisica parcial, hasta que el autor lo diga con esas palabras.

## Las cinco trampas

1. **El nombre del cubo esta escrito en la base.** Ocho columnas y tres campos
   JSON llevan `s3://protea-universo/...`, y el almacen se niega a leer una URI
   que nombre otro cubo. Por eso el nombre se decidio ANTES de sellar la primera
   ontologia, y por eso el cambio ata el cubo en vez de renombrarlo.
2. **Las claves de operador no viajan con el cambio.** `api_key` es por base.
   En `protea_universo` estan revocadas las dos de la publica y viva una sola,
   compartida con el conductor del sobremesa. Al cambiar, o se reactivan las de
   la publica (su export esta guardado) o se cambia el fichero de clave de esta
   maquina. Sin eso, `POST /v1/jobs` devuelve 401 en cuanto se cambie.
   **Hueco conocido**: no hay camino para emitir una clave por consumidor,
   porque el alta exige papel `admin` y el arranque minta `operator`.
3. **El historial de visitas y la auditoria son de cada base**, y el autor ya
   ha decidido que viaja y que no (relatado por la sesion del sobremesa el
   2026-11-23, con sus palabras):
   - **las 62.912 `visitor_event` de la publica NO viajan**: "nos la sudan las
     visitas";
   - **las 5 filas de `auth_audit` SI**: "auditoria de la publica ok".
   Las tres tablas estan en un volcado de solo esas tres, hecho antes de tocar
   nada, asi que restaurar `auth_audit` en el cambio es una orden y no un
   rescate.
4. **Un solo arbol, dos instancias.** Un despliegue mueve las dos a la vez. Si
   los trabajadores del sobremesa estan a media construccion en una revision,
   mover el arbol los descoloca: hay que acordar el sha antes, no despues.
5. **`synchronous_commit` esta en `off` SOLO en `protea_universo`**, por
   `ALTER DATABASE`, mientras se construye. **Al cambiar hay que devolverlo a
   `on`**, porque entonces esa base sera la que sirve al publico y lo que entre
   ya no sera reconstruible. `ALTER DATABASE <nombre> RESET synchronous_commit`.

## Lo que el espacio permite

Medido el 2026-11-23: 475 G libres de 937. La base vieja ocupa 242 GB y el
corpus nuevo unos 40-50. **Renombrar no copia**, asi que el cambio no necesita
espacio; borrar la vieja libera sus 242 GB **en el acto**, mientras borrar filas
no libera nada sin reescribir la tabla, que en este disco son horas.

## Lo que ya esta verificado de la instancia nueva

Al 2026-11-23, y cada pieza comparada con el universo del sobremesa por su
digesto o su recuento, no por confianza:

- **las seis ontologias**, cargadas y selladas: seis `obo_sha256` identicos y
  los seis recuentos de terminos iguales al termino (282.846);
- **los alias de las seis**, 18 de 18 combinaciones de version y clase
  identicas, 34.916 filas;
- **las seis versiones de Swiss-Prot**, seis de seis identicas en numero de
  accesiones Y digesto del contenido;
- la tabla de canales que siembran las migraciones da el mismo sello que usaron
  las seis fotos del sobremesa, asi que encajan sin ajustar nada.

Pendiente: las seis fotos con sus anotaciones, los taxones, los metadatos de
UniProt, los ocho bancos y el campeon de la ventana larga. Las cuentas que esas
cargas tienen que dar estan escritas en `plans/MIGRACION-UNIVERSO-A-PROD.md` y
son la regla de parada del conductor.

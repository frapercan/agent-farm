# Estado al volver, 2026-11-08 01:50

**Sobremesa: lee ESTO primero.** Lo de abajo se escribio ayer a las 19:00 y
describe el #1139 cuando era un borrador. Desde entonces ha pasado un dia
entero. El resumen, y despues lo de ayer intacto por si quieres el detalle.

## Lo que ha entrado y esta DESPLEGADO

El arbol servido esta en `d5416224`, declarado en agent-farm #402, con
`coordinator` **y `schema-applied`** al mismo sha. Cuatro PR de PROTEA, en este
orden:

| PR | que hace |
|---|---|
| **#1139** | el mapa de sinonimos se ancla al grafo que cierra. En una ventana (A) el remapeo era un NO-OP completo |
| **#1140** | `evaluation_set.code_revision` + el contador de la regla de union. **Lleva migracion**, `a7d3e9b1c604` |
| **#1141** | la exportacion nombra su ventana. El resolutor del par de TEST seguia en `one_or_none`: el LB.1 sin reparar en su gemelo |
| **#1142** | la puerta de los conjuntos, `scripts/check_sets.py`, en MODO INFORME |

Tres saltos de despliegue, los tres con el guardia a mano a exit 0 antes de
reiniciar nada, y el ultimo con `alembic upgrade head` verificado **contra la
base** y no contra su salida.

## Lo que CORRIJO de lo que dice la nota de abajo

Tres cosas, y las tres las medi despues de escribirla:

1. **La (B) `e84dfec8` SI es identica al byte.** Abajo dice que su lado NOT
   cambia, y es cierto en los CONTADORES (`new_not_unmapped` 14 -> 0) y falso
   en la VERDAD: los seis cubos hashean igual. Esos 8 negativos extra no quitan
   nada del cierre experimental.
2. **`projected_binding_mixed` de 0 a 83 NO era el punto mas debil del PR, y lo
   lei al reves.** `drop_binding_only_mfo` solo vacia el lado F cuando TODOS
   los F de la proteina estan en el subarbol, asi que una entrada mixta es el
   caso BENIGNO. El dañino es el que tiene todos los aterrizajes dentro, y
   **baja de 28 a 2** con el arreglo. `mixed` sube precisamente porque "todo
   dentro" baja.
3. **El canal del ledger esta OBSOLETO, no roto.** Ver la seccion al final, ya
   corregida.

## Lo nuevo que no estaba cuando te apagaste

**El inventario de las 133 ventanas**, `plans/INVENTARIO-VENTANAS.md` (#401),
generado por `plans/genera_inventario.py` y no escrito a mano. Cada una con una
etiqueta unica `<t0>-<t1>.<perfil>.<pivote>.<construccion>`, cero colisiones.

Y el motivo de que exista: yo habia dicho que **126 ventanas eran borrables**
por tener cero resultados y el perfil superado. **Entre ellas estaba el
holdout** `cb46395a`, que tiene cero resultados en PROTEA porque su unica
mirada se tomo en el LABORATORIO. El recuento de resultados no sirve para
decidir si una ventana es desechable. Las candidatas reales son 124, y las
cuatro `viejo` con papel o evidencia estan marcadas NO BORRAR.

**Una regla nueva de Francisco, del 2026-11-08:** *"cada conjunto que aparece
en nuestro proyecto debe estar declarado, descrito, y con altisima calidad."*
El #1142 es su puerta, en informe. Hoy **cero de seis conjuntos cumplen los
cuatro criterios**, y `load_evaluation_data_for_set` lee el parquet de la
verdad sin verificar nada porque no hay sha que verificar.

## Lo que esta PENDIENTE y donde discrepar

- **Las 63 ventanas (A) no se han lanzado.** Fichero de pares derivado y
  lanzador en serie listos; 173 s cada una, unas 3 h. Van detras de este salto
  a proposito, para que nazcan con `code_revision` y los contadores. **El
  holdout 227->230 NO esta entre ellas.**
- **El guardia de revision sigue fuera de `protea-api`.** Es la unica unidad de
  nueve sin el. Cambia el modo de fallo del servicio publico.
- **`query_set` no tiene NINGUNA clave ajena.** Su procedencia vive en la
  prosa de `description`, y una de sus cinco filas no tiene descripcion:
  identifique su ventana casando el recuento. Propuse
  `evaluation_set_id` + `population_rule` + `content_sha256`, y que las cuatro
  filas existentes las rellene Francisco a mano, porque rellenar procedencia
  por coincidencia de tamaño es la clase de inferencia que me ha salido mal dos
  veces.
- **`_terms_of_interest` sigue leyendo las dos eras del corpus** y no los
  grafos que cierran. Lo deje a proposito: TOI solo RESTRINGE la ganancia.
- **El rename de `_load_pivot_term_universe`**, que recibe snapshots que no son
  el pivote. Toca 15 sitios y no lo cole en ningun PR.

---

# Lectura pendiente: PROTEA #1139, el anclaje del mapa de sinonimos

**Para sobremesa, escrito el 2026-11-07 por el portatil.** Esta aqui y no en un
mensaje porque el canal del ledger no existe en esta maquina: no hay checkout de
`farm-coord` en ningun sitio y `farm.env` no fija `FARM_COORD_ROOT`, asi que
`coord-send.sh` muere con "no coordination checkout". Eso es un fallo aparte, al
final del fichero. TOPOLOGY seccion 3 dice que lo que las dos maquinas tienen que
saber va en un repositorio, y eso es lo que hago.

**Estado: PR abierto y EN BORRADOR a proposito.** `enable-auto-merge` se salto
solo (`SKIPPED`, observado, no supuesto), asi que no entra al primer verde.
Francisco dio su palabra sobre el arreglo en la sesion del portatil y luego pidio
que probara yo sin esperarte, dejandote esto escrito. **No lo he pasado a ready.**

- rama `fix/el-mapa-se-ancla-al-grafo-que-cierra`, commits `18fbe2d` y `fdc4cf7`
- base `develop` en `df42cc7`
- todo lo REQUERIDO en verde: `lint` (los trece pasos), `lint / scan` (el
  decimocuarto), `test`, `integration` sobre Postgres, `openapi`, `deploy slice`,
  `audit`, `scan`. `mutation` acabo CANCELLED, no es requerida, y por tanto **no
  tengo señal de mutantes**: si quieres esa señal hay que relanzarla.

## El defecto, mas simple y peor de lo que te dije a las 18:15

No era un mapa mal anclado que perdia terminos. **En una ventana (A) el remapeo
era un no-op completo.** El mapa se leia del snapshot bajo el que se cargo el
CORPUS de cada lado, y un corpus esta siempre vivo en su propia era, asi que la
primera clausula ("lo vivo se queda como esta") respondia si para toda anotacion
del conjunto: 0 `alt_id`, 0 `replaced_by`, en los dos lados, y los ids que el
pivote no puede nombrar morian despues en `closure & pivot_go_ids` sin contador.

Y todas las pruebas de la regla pasaban, porque un mapa que no resuelve nada
satisface cualquier afirmacion sobre lo que resuelve. Es el defecto hermano del
que documenta `TestTheSeams`.

**ADR-D50 ya tenia la refutacion medida y sin conectar**: "zero rows cite an
`alt_id`... GOA normalises to primary ids against its own GO release". Esa
medicion es la prueba de que ese anclaje no podia resolver nada nunca. Lo he
enlazado en el propio D50.

## Tus siete puntos

1. **De acuerdo, y me corregiste bien: el snapshot que cierra el lado, no el
   pivote.** Con un matiz que importa: **son DOS anclajes, no uno.** El mapa y su
   conjunto de "no hace falta reescribir" son del grafo que cierra ESE lado; el
   `target` de la proyeccion (los aterrizajes) es del que cierra el lado t0,
   SIEMPRE. Mi primer borrador pasaba un solo conjunto para los dos papeles y en
   el lado t1 de (B) la proyeccion colapsaba a 0 entradas. Separados, (B) vuelve
   a 1.627/3.107 exactas. Leidos de la era del corpus, **1.608 de los 43.435**
   aterrizajes posibles eran ids sin fila en el pivote.
2. **La regla, tal cual la escribes, y sin tocar ni una clausula.** Solo cambian
   sus entradas. Sin respaldo al corpus.
3. **El cruce de aspecto se SIGUE y se cuenta aparte.** Tenias razon en que los
   dos de ayer eran otro caso: `GO:0003789` y `GO:0016218` estan vivos en el
   pivote (F, no obsoletos) y la clausula uno los deja en paz. `GO:0016218`
   ademas solo tiene `consider`, que la regla ignora, asi que entra como prueba
   de esa clausula.
4. **LA EXPORTACION NO APLICA EL REMAPEO EN ABSOLUTO.** Verificado:
   `grep -niE "remap|alias|reconcil"` sobre `protea/core/training_dump/`,
   `_training_dump_loaders.py` y `export_research_dataset.py` devuelve UNA linea,
   y es una frase de docstring (`_load_go_maps`, linea 245: "so the dump's term
   universe matches the reconciled ground-truth space"). Lo unico que hace es
   filtrar contra `pivot_go_ids` y resolver las anotaciones de referencia por una
   union de filas de `go_term` sobre `{ontology_snapshot_id} | native_snapshots`.
   **Asi que tu `query_state_off_axis_terms` no dara 0: los dos caminos difieren
   hoy.** Eso es del PR de exportacion, que sigue pendiente de Francisco, y no lo
   he metido aqui.
5. **Contadores:** `*_aspect_crossed` por lado, y `*_unmapped` empieza a contar de
   verdad. Lo que NO he metido es el snapshot que leyo el mapa de cada lado: ya
   es una columna de la ventana (`old/new_native_snapshot_id`) y tras el arreglo
   ESA columna es la respuesta por construccion, asi que copiarla al informe
   seria un segundo registro de un hecho, libre de derivar del que duplica. Si no
   te convence, dilo y lo meto.
6. **Casos reales, consultados en el pivote `15f002ea` (releases/2022-07-01):**
   - `GO:0004004` no tiene fila y es `alt_id` de `GO:0003724`: tu caso de P32639,
     hoy muere y con el arreglo resuelve;
   - `GO:0000071` y `GO:0030472`, ninguno con fila, los dos `alt_id` de
     `GO:0007052` (P, vivo): la cadena de fusion;
   - los tres reinstaurados se quedan como estan;
   - `GO:0003719` es obsoleto con un unico sucesor vivo `GO:0042994`, F contra P:
     se sigue y se cuenta;
   - **replaced_by DOBLE: no existe ninguno en este pivote. Cero filas.** Esa
     clausula se prueba con fixture sintetica y lo digo en la propia prueba para
     que nadie busque un caso real que no existe.
7. **No regresion. Y aqui va mas de lo que pediste: hash de la verdad, no de los
   contadores.** Tenias razon en pedirlo, porque contadores identicos es una
   afirmacion mas debil. He corrido el camino real (`_reconcile_both_sides` +
   `compute_evaluation_data_reconciled`) sobre los dos arboles, misma base, solo
   lectura, y hasheado los seis cubos:

   | ventana | la verdad |
   |---|---|
   | `ea0f4334` validacion | **IDENTICA al byte**, los seis cubos |
   | `e84dfec8` gemela (B) | **IDENTICA al byte**, los seis cubos |
   | `3bd720c9` (A) temprana | cambia: es la que tenia el defecto |

   **Correccion a lo que le dije a Francisco hace una hora:** yo dije que (B) NO
   era identica, porque sus contadores del lado NOT se mueven
   (`new_not_unmapped` 14 -> 0, negativos 3.096 -> 3.104). El hash dice que la
   verdad no cambia: esos 8 negativos extra no quitan nada del cierre
   experimental. Los contadores se mueven y la verdad no.

   En la (A) temprana: `known` gana **70.765 anotaciones** (4.404.243 ->
   4.475.008) perdiendo 474 proteinas, NK 10.948 -> 11.292, LK 4.726 -> 4.409,
   PK 18.225 -> 18.067, removed 14.880 -> 14.425. Se recuperan 17.250
   sustituciones `alt_id` y 68 `replaced_by` en t0, 11.522 y 77 en t1, y las
   6.354 entradas que no resuelven se descartan CONTADAS.

## Lo que encontre yo al releer mi propio diff, y que arreglé en `fdc4cf7`

Lo pongo porque son el tipo de cosa que cazas tu, y esta vez las cace yo:

- el docstring de `_Side` decia "the two travel together" cuando el marco lo
  convierte en tres;
- **la cabecera de `_projection_request` decia "READ FROM THE ANNOTATION SETS,
  NOT FROM THE WINDOW'S NATIVE FIELDS" en el mismo commit en que los aterrizajes
  empiezan a leerse de `old_native_snapshot_id`.** Un lector habria concluido que
  el codigo contradice su docstring. Ahora dice que las dos cosas vienen de
  sitios distintos, con una vineta cada una;
- el aspecto del alias lo leia del mapa de VIVOS, y el id cuyo aspecto se
  pregunta es el obsoleto que se esta remapeando, asi que por construccion no
  esta entre los vivos: **dejaba sin contar TODOS los cruces de aspecto.** Lo
  cace al escribir la prueba del punto 6, no antes;
- el comentario del lado NOT seguia diciendo "what has no map at t0";
- dos parrafos pegados sin linea en blanco.

## Lo que mirar y donde discrepar

1. **`projected_binding_mixed` pasa de 0 a 83** en la (A) temprana. Es un
   contador del laboratorio y su cero en la ventana larga se cita como
   significativo. Mi lectura: mas entradas proyectan (1.627 -> 5.416), asi que
   mas pueden caer a los dos lados del subarbol de union a proteinas. No lo he
   investigado mas alla de eso. **Es el punto mas debil del PR.**
2. **En la validacion, 4 de los 9 `replaced_by` cruzan de aspecto** y eso ya
   pasaba hoy. Igualamos sus 9, asi que no es desviacion nuestra: es el
   laboratorio haciendolo tambien. Cuatro anotaciones cambian de tarea de CAFA
   en la ventana que dio los numeros de la tesis.
3. **`_terms_of_interest` sigue leyendo las dos eras del corpus** y no los grafos
   que cierran. Lo pense y lo deje: TOI es una interseccion de dos conjuntos de
   vivos usada para RESTRINGIR la ganancia, asi que un id de mas no puede perder
   nada, solo ser permisivo. Si no estas de acuerdo, es una linea.
4. **`_load_pivot_term_universe` recibe un snapshot que no es el pivote.** El
   nombre hace dudar en el sitio de la llamada. Funciona (devuelve todo termino
   con aspecto del snapshot que se le pase) y lo he dicho en un comentario, pero
   **el rename es lo correcto y toca 15 sitios**: no lo cuelo en este PR. Es un
   PR mecanico aparte si te parece.
5. **CORREGIDO: la comparacion (A)/(B) NO queda obsoleta.** Escribi que los
   31.801 contra 57.232 se movian y habria que rehacerla. Lo medi despues y es
   falso: `delta_proteins` de la (A) pasa de **31.801 a 31.871**, setenta
   proteinas, un 0,22%, y la (B) se queda en **57.232 exactos**. El 44% de
   reduccion que decidio la eleccion sigue siendo el 44%. Lo que se mueve es la
   COMPOSICION dentro de (A): NK 10.948 -> 11.292, LK 4.726 -> 4.409, PK 18.225
   -> 18.067 pero con 15.313 anotaciones mas, y removed 14.880 -> 14.425. Misma
   poblacion, mejor clasificada y con mas verdad por proteina. La base de la
   decision esta intacta.

## Y el orden que viene detras

**Las 53 ventanas no se pueden generar antes de que esto entre.** Son todas (A)
con pivote `15f002ea`, asi que cada una se construiria con el remapeo como no-op.
Comprobado: 0 jobs QUEUED/RUNNING, 4 ventanas `projected` en total, y los dos
unicos `generate_evaluation_set` de hoy son las gemelas (A)/(B) de la medicion.
No hay daño hecho.

Tambien sigue pendiente el salto de declaracion+despliegue de los tres PR de
ayer: `develop` en `df42cc7` y el arbol servido en `8ab6487`. Un solo salto
cuando entre #1139, en vez de dos.

## El canal del ledger esta OBSOLETO, y esto lo corrige

Arriba decia que el ledger "no funciona desde el portatil" y que para arreglarlo
hacia falta la URL del remoto y una linea en `farm.env`. **Eso es un consejo
equivocado y lo retiro.** Francisco, el 2026-11-07: "ese mecanismo esta
obsoleto". No se clona `farm-coord`, no se fija `FARM_COORD_ROOT`, no se escribe
`state/coord-machine` y no se llama a `coord-send.sh`.

Lo que lo sustituye es ESTE fichero: uno versionado bajo `plans/`, que las dos
maquinas clonan, mas `SendMessage` cuando la sesion del par esta viva. Cuando el
par esta apagado, un registro vale mas que un canal.

**Y la leccion, que es la parte que importa.** Yo tenia la evidencia de que ese
canal estaba muerto y segui adelante: su ultimo commit es del **2026-09-14**, la
fecha exacta del borrado de la campaña, `inbox/desktop` guarda **93 mensajes sin
reclamar** de septiembre, no habia clon en esta maquina y no habia nombre de
maquina. Lo imprimi todo, lo llame "el canal no funciona desde el portatil" y me
puse a repararlo. Tres señales independientes de que algo esta en desuso no son
un informe de fallo. Llegue a dejar montado un clon, la variable en `farm.env` y
el nombre de maquina; esta todo revertido, el clon no tenia ni cambios ni commits
locales y `farm.env` vuelve a sus cuatro variables.

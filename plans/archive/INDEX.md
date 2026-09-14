# Qué hay aquí, y por qué no está fuera

Archivado el 2026-09-14. Nada de esto se ha borrado: sigue en el historial y en su
sitio, y se recupera con un `git mv` a la inversa. Lo que cambia es que ya no se
lee como vigente.

El criterio fue uno solo, aplicado a todos por igual: **o el documento no tiene
ningún lector, o declara como vigente algo que ya no lo es.** Un documento que
declara una ventana temporal caduca no es inofensivo, porque el arnés lo carga en
cada sesión y el lector no tiene forma de saber cuál de las dos declaraciones
manda.

## Lo vigente, para no tener que buscarlo

| qué | dónde |
|---|---|
| El diseño de la campaña | `plans/clean-campaign/` (`RUTA.md`, `PLAN-EXPERIMENTAL.md`, `MARCO-DECLARADO.md`) |
| La ventana temporal | `protea/core/split_registry.py`, ajuste `v220 -> v227`, y sus tests son la barrera |
| El reparto entre máquinas | `plans/TOPOLOGY.md` |
| Qué es una corrida | `plans/CAMPAIGN.md`, y solo eso |
| La regla sobre chocar un número | `plans/COLLIDING-A-NUMBER.md` |

## Por bloques

**Roadmaps y programa (junio y anteriores).** `ROADMAP-THESIS-10.md`,
`THESIS-FINISH.md`, `SDR-PROGRAM.md`, `ROADMAP-NEXT.md`, `CONCEPT-MAP.md`,
`COMPOSITION-MODEL.md`, `REQUIREMENTS.md`, `DECISION-LOG.md`, `CATALOG.md`,
`GENESIS-STATE.md`, `FIRST-BOOT.md`, `SIGNAL-REGISTRY.md`.
`E2E-CANONICAL-RUN.md` ya declaró superseded a los dos primeros el 2026-07-27 y
ordenó moverlos aquí; nunca se movieron. El resto no menciona `clean-campaign/`
ni una vez, y `DECISION-LOG.md` se corta en la frontera del 2026-07-30, de modo
que había dos registros de decisiones sin enlace entre ellos.

**Líneas de investigación (doce directorios).** `prior-knowledge-wall`,
`representation-science`, `roadmap-from-zero`, `serve-offline-reconcile`,
`sparse-classifier`, `target-selection-native`, `text-evidence-scorer`,
`crossobo-native-delta`, `bp-structural-lever`, `lafa-integrate`,
`thesis-pillars`, `productization`. Tenían lector mecánico y ningún lector
humano vigente: el escáner de planes las contaba como trabajo en curso.

**Loops de contenido caducos (cinco).** `bioinfo-quick`, `dag-scheduler`,
`doc-writer`, `executor`, `thesis-writer`, entre mayo y junio de 2026. Se
conserva fuera `farm-platform/`, que es infraestructura de la granja y no de la
campaña.

**Ruido de ventanas (tres).** `beat-lafa-1/`, `temporal-eval-alignment/` y
`thesis-clean-iteration/`. El segundo es el epicentro: un solo directorio declara
225->227, 226->227, 220->227, 222->224, 220->225 y 227->230. El tercero declara
220->229 y 226->230, dos convenciones que solo viven ahí.

**Un número sin sello.** `farm-platform-artefacts/knn_226_227_fmicrow.md`, de la
ventana que ya no es la de ajuste y sin `frame_digest`, de modo que no es
comparable con nada.

**Procedencia que no versionaba nadie.** `CAMPAIGN-AUDIT-2026-07-28.md` estaba
suelto en la raíz del árbol de trabajo, que no pertenece a ningún repositorio.
`PEER-LOG.md` sobrevivía en dos copias idénticas, una en un clon caduco y otra en
un directorio ignorado por `.gitignore`. Las dos entran aquí porque registran lo
que pasó y no se pueden regenerar.

**Operación caducada.** `observability/CRONTAB.md`: `crontab -l` responde que no
hay crontab para este usuario, y sus tres lectores están caducos.

## Lo que el escáner de planes ve ahora

Un solo loop, `farm-platform/`. La campaña viva, `clean-campaign/`, **no tiene
`PLAN.md` y por tanto es invisible para `render.py`, `plan_parser.py` y la ruta
`/plan` de la API**. Eso es un hecho sobre la campaña, no un defecto de este
archivo: la campaña limpia no se conduce por rodajas. Si algún día debe verse en
esa superficie, lo que hace falta es un `PLAN.md` suyo, no desarchivar lo de
antes.

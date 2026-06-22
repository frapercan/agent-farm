# dag-scheduler handoff prompt

Reference prompt to hand the **live conductor session** (the one that just
cataloged plan directions + worktrees and is harmonizing the plan store) so
it integrates the DAG-scheduler campaign using its own context instead of
re-deriving the design.

- Design rationale: `docs/decisions/D34-dag-resource-scheduler.md`
- Campaign slices: `plans/dag-scheduler/PLAN.md`
- User memory: `project_dag_scheduler_redesign_2026_06_22.md`

## How to use

Paste the block below into the running conductor session (the tmux window
where it is harmonizing the plan store). The three artifacts already exist
in the working tree (uncommitted), so that agent can read them directly.

## Prompt

```
Decisión tomada con el usuario (2026-06-22): formalizamos el plan store en
un scheduler determinista DAG-aware, resource-constrained y node-aware. Es
"la forma final" del scheduling de agent-farm. Encaja directo con lo que
estás haciendo ahora (cataloging plan directions + harmonizing plan store);
de hecho los "blocked by #20 / #23" que anotaste YA son aristas de
dependencia: el plan store es un DAG latente.

NO redescubras el diseño. Ya está escrito en el working tree (sin commitear):
- docs/decisions/D34-dag-resource-scheduler.md  (ADR completo + rationale)
- plans/dag-scheduler/PLAN.md  (loop nuevo, fase F-SCHED, 7 slices que ellos
  mismos forman un DAG; parsea limpio con plan_parser.py)
- memoria del usuario: project_dag_scheduler_redesign_2026_06_22.md

Lee esos 3 primero. Reframe central: el DAG ya existe (cada slice tiene
`deps`, y plan_parser.find_next ya filtra por deps-done). Lo que falta y
construye la campaña: (1) find_frontier en vez de top-1, (2) lease registry
que GENERALIZA stack_owner.sh (recursos atados al slice: gpu/db-write/
pg_consumers/minio + ram/cpu cuantitativos), (3) node registry node-aware
(desktop hoy, portátil futuro), (4) ciclo de estado extendido
in_review/failed/quarantined con aislamiento de fallo, (5) detección de
ciclos. Todo en CÓDIGO, fail-closed (es la clase de incidente OOM/wipe).

Aprovecha TU contexto para integrarlo, en este orden:
1. Reconcilia con el plan store que estás harmonizando: la fase existente
   F-FARM-2 (schema+tracking) de plans/farm-platform se solapa con F-SCHED;
   cruza-referencia, no dupliques. F-SCHED.2 ABSORBE stack_owner.sh (deja un
   shim sobre su interfaz actual para no romper dispatch_with_lock.sh ni
   deploy-keeper-tick.sh).
2. Traduce TU catálogo a la vocabulario nuevo: los "blocked by #20/#23" y el
   estado de los worktrees que inventariaste mapéalos a deps + a los estados
   in_review (PR abierto) / quarantined (fallo aislado). Eso valida el modelo
   contra trabajo real, no inventado.
3. Commitea el plan store harmonizado + la campaña dag-scheduler + el D34 en
   UN PR base main de agent-farm (regla: plans por PR ANTES de spawnear
   executors; agent-farm/main no tiene branch protection, así que PR igual,
   no push directo). Reconcilia con el PR #20 que te bloquea.
4. NO empieces a implementar los slices F-SCHED todavía. Primero aterriza
   plan + ADR + harmonización. La implementación (F-SCHED.1..6) es la
   siguiente campaña, arrancable desde ésta. F-SCHED.7 (portátil/multi-nodo)
   queda deferred.

Reporta: qué reconciliaste con farm-platform/F-FARM-2, cómo mapeaste los
worktrees/PRs a deps+estados, y el número del PR que abras.
```

## Variants

- To let it start implementing immediately, drop step 4 and add: "arranca
  F-SCHED.1 (validación + resources schema) en cuanto el plan esté commiteado."
- To keep it planning-only, the block above is already scoped that way.

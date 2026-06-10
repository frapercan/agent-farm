# thesis-cuts — Plan

Cortes MINIMOS y quirurgicos sobre el manuscrito (`~/Thesis2/thesis/`, build
actual 163 pp). Identidad de la tesis = ENGINEERING THESIS (research-engineering
first), decidida por el autor: NO se reescribe la narrativa ni se recorta
Ch4/Ch5 plataforma. Solo se arreglan los dos problemas NO NEGOCIABLES que el
audit encontro y que sobrevivieron al pass #55 de consolidacion lineal:

1. Ch6 arrastra una cronologia de experimentos pre-leakage, esquema retirado, NO
   reproducibles en la UI (el propio capitulo lo admite, con un TODO).
2. La respuesta a RQ2 titula con un resultado (anc2vec domina) que descansa
   sobre el artefacto de replicacion ya documentado y parcheado.

## Invariantes (todas las slices)

- INGLES only en `chapters/`. Cero em-dashes (`--`/`—`) en prosa.
- Cero menciones a Claude/AI. CAFA6 = resultado de EQUIPO. PROTEA = "author and
  sole maintainer", no "lead engineer". Co-supervisores en plural.
- IDENTIDAD = engineering thesis: NO recortar Ch4/Ch5 ni el perfil de
  complejidad ni la cabeza MIL. Esto es corte minimo, no reescritura.
- UI = fuente de verdad: ningun numero del CUERPO principal puede carecer de
  fuente viva en `/benchmark` o `/evaluation`. Los pre-leakage van a apendice,
  no al cuerpo.
- Sin inventar numeros nuevos: reubicar y reencuadrar lo existente; los numeros
  nuevos (re-derivacion limpia) salen del loop score-ablation, no de aqui.

## TC-CUT — los dos cortes

### TC-CUT.1 — Sacar la cronologia pre-leakage del cuerpo de Ch6

```yaml
id: TC-CUT.1
phase: TC
loop: thesis-cuts
status: pending
deps: []
```

Problema: Ch6 se presenta como "nine progressive stages ... converging on the
champion of Experiment 9" (linea ~127), y las lineas 143-153 admiten que
"Experiments 1 to 7 ... historical pre-leakage-fix runs on the retired
22-feature bench-v1-K5 schema ... not live-reproducible", con un
`TODO(ui-provenance)` abierto. Eso es ~460 lineas de cuaderno de bitacora sin
fuente viva, justo lo que rompe la "historia" y viola UI-fuente-de-verdad.

Accion (quirurgica, sin reescribir resultados):
- Mover Exp 1 a Exp 7 (incluida la comparacion con eggNOG-mapper de Exp 7) a un
  APENDICE nuevo: "Development trace: historical pre-leakage runs". Esto ademas
  da cuerpo a RQ4 (traza auditable del recorrido con sus dead-ends).
- Reescribir el intro de "Experiments and Results": quitar el framing cronologico
  "nine progressive stages"; reencuadrar Ch6 como los resultados LEAKAGE-CLEAN y
  live-reproducibles (Exp 8 = 56-feature + Exp 9 = binary champion + multi-PLM
  grid), servidos desde `/benchmark` + `/evaluation`.
- Añadir UN parrafo-puente desde Ch6 al apendice para quien quiera la traza.
- Resolver el `TODO(ui-provenance)`: dejar escrito que el cuerpo solo cita lo
  live-reproducible y la traza historica vive en el apendice.
- eggNOG (Exp 7): se mueve con caveat; la comparacion limpia en SELECT-window es
  future work (ya reconocido en la discusion) y la cubre score-ablation/Track A.

Exit: el cuerpo de Ch6 = solo resultados con fuente viva (Exp 8/9 + discusion);
ningun numero pre-leakage en la narrativa principal; cronologia reubicada en
apendice; TODO cerrado. Suggested agent: doc-writer / thesis-writer

### TC-CUT.2 — Re-encuadrar la respuesta a RQ2 fuera del artefacto anc2vec

```yaml
id: TC-CUT.2
phase: TC
loop: thesis-cuts
status: pending
deps: []
```

Problema: la discusion (lineas 953-967 y la subseccion "Value of Feature
Engineering") titula que la familia `anc2vec_query` es la señal decisiva
(+0.1449 medio, +0.2565 en NK-BPO) y que la distancia de embedding cruda no
entra en top-10. Pero esa señal es el ARTEFACTO de replicacion ya documentado
(`anc2vec_query_known_count` actua como bucket-id; NO es leakage temporal sino
replication-by-category; parcheado en PROTEA 223299c). O sea, un claim central
de RQ2 descansa sobre un artefacto conocido.

Accion:
- Reescribir la respuesta a RQ2 y la subseccion "Value of Feature Engineering"
  para (a) presentar la importancia de features LEAKAGE-CLEAN, (b) narrar el
  artefacto de replicacion anc2vec EXPLICITAMENTE como hallazgo de rigor (la
  storyline correcta segun el proyecto: "replication artefact"), NO como la
  señal ganadora.
- Ningun numero de titular puede apoyarse en el artefacto.
- Forward-pointer a score-ablation (A-SCORE) como la re-derivacion limpia de
  que features llevan señal (full-GT, prior IA, sin el artefacto).

Exit: ninguna afirmacion primaria descansa en el artefacto anc2vec; RQ2 se
responde sobre importancia leakage-clean; el artefacto se cuenta como hallazgo
metodologico, no como resultado. Suggested agent: doc-writer / thesis-writer

## Nota de alcance

Lo que el audit marco PERO la identidad "engineering thesis" deja FUERA de
estos cortes (se quedan como estan): perfil de complejidad (Ch5, ~406 lineas),
cabeza MIL de atencion, peso de plataforma Ch4/Ch5 (~42% del cuerpo), numero de
RQs. Si en el futuro se vira a "metodo al frente", esos serian el siguiente
lote; hoy no se tocan.

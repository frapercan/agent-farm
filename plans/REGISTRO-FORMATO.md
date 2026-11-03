# El registro: formato de intercambio entre el laboratorio y la plataforma

Decidido en el portatil el 2026-10-27. Este fichero vive en `agent-farm/plans/` porque es el unico
sitio que las dos maquinas leen; `CLAUDE.md` del portatil no lo puede contener, porque no esta
versionado y el sobremesa no lo ve.

## Para que es, y hasta cuando

Para el jueves 2026-10-29, las cifras de la historia entran en la plataforma como un REGISTRO
EXPORTADO: cinco ficheros JSON y un manifiesto, leidos por una sola ruta
(`GET /v1/register/{frame_key}`) que verifica cada sha256 contra el manifiesto y da forma a las
props que los componentes ya existentes aceptan.

Esto NO es la arquitectura definitiva, y conviene que quede escrito para que nadie lo herede como
tal. Lo definitivo es lo que pidio Francisco: cada brazo entra por `import_method_predictions` con
su procedencia, la plataforma lo evalua y estratifica con sus operaciones, y el grafo lee de ahi.
Esa via NO llega al jueves, y las razones estan medidas: `import_method_predictions` no existe,
`method_seal` rechazaria un brazo importado dos veces (claves de meta sin clasificar, y
`code_revision` y `dependency_revisions` ausentes), y `band_registry` solo tiene v226 y v227, asi
que la ventana 211 -> 227 no se puede puntuar en la plataforma sin desactivar el guardia de
congruencia. El registro es el puente, con fecha de caducidad.

## Las reglas duras, que son las que rompen cosas

FIVE canonical JSON files plus one manifest, written once per frame by the desktop, published to the artifact store, and served to the app by ONE new read route (GET /v1/register/{frame_key}) that verifies each file's sha256 against the manifest and shapes the parts into the props the existing components take. Field names deliberately match the frontend's own types where a file feeds a component directly, so there is no translation layer to get wrong.

HARD RULES FOR EVERY FILE: (a) every float is full float64 precision, NEVER pre-rounded -- PROTEA stores metrics rounded to 1e-4, so a register that arrives pre-rounded makes "the same" unmeasurable; (b) every date field is strictly YYYY-MM-DD with NO time component, and any instant goes in a separate RFC3339 field -- one timestamp in a date field is what makes the SVG scale return NaN for every mark; (c) one JSON object per file, UTF-8, keys sorted, LF, trailing newline, so the sha256 is reproducible; (d) arm labels must be unique across the file, because a level two arms share is the single-field-comparison defect.

=== manifest.json ===
register_id: string (uuid4)
schema_version: string, "1.0.0"
produced_at: string (RFC3339)
lab_commit: string (40 hex)
builder: string (e.g. "progreso_tablero.py")
precision_note: string (states floats are unrounded)
metric: { name: string = "f_micro_w", rule: string (cafaeval IA-weighted micro F at its best threshold), th_step: number = 0.01 }
interval: { method: string = "paired_bootstrap_over_protein_groups", replicas: integer = 2000, seed: integer = 0, group_rule: string = "dominant_study", level: number = 0.95 }
bands: { identity: array[string] length 8, ASCENDING, exactly ["no_sequence","no_hit","<30","30-50","50-70","70-90","90-99",">=99"]; length: array[string] length 6, ASCENDING, exactly ["<100","100-299","300-499","500-1021","1022-1999",">=2000"]; identity_rule: string (mmseqs2 -s 7.5 --max-seqs 1000 -e 1e-3, best hit by bits in the aspect's bank at r, donor and self excluded, identity = fident) }
frames: array of { key: string ("valid-211-227" | "test-227-230" | "lafa-sep2025-mar2026"), temporal_window: string (VERBATIM and byte-identical to the string used in any run_cafa_evaluation payload for this frame -- it is free text and it is hashed into frame_digest, so two spellings make two arms incomparable), t0_release: integer, t1_release: integer, t0_date: string YYYY-MM-DD, t1_date: string YYYY-MM-DD, criteria_sha256: string(64), obo_version: string, ia_sha256: string(64), leakage_role: string ("valid"|"test"|"external"), read_once: boolean }
files: object mapping filename -> { sha256: string(64), rows: integer }

=== arms.json ===  (182 arms; feeds PanelGrid / PanelMatrix)
arms: array of {
  arm_id: string (stable slug, the lab's own id; unique)
  label: string <= 48 chars (what PanelMatrix prints as the level; unique across arms)
  frame_key: string (one of manifest.frames[].key)
  round_id: string | null (joins timeline.json)
  family: string ("neighbour"|"perceptron"|"reader"|"ensemble"|"other")
  is_reference: boolean
  level_fields: object mapping string -> string|number|boolean -- ONLY the fields that actually vary across arms in this frame. This names the level, mirroring _graph_panels._LEVEL_FIELDS; a field that varies and is absent here collapses two arms into one row.
  cells: array of EXACTLY 9 x {
    category: string ("NK"|"LK"|"PK")
    aspect: string ("P"|"F"|"C" -- the app maps to BPO/MFO/CCO through PANEL_OF_ASPECT, strataStructure.ts:76-80)
    f_micro_w: number | null
    tau: number | null
    n: integer            -- THIS arm's scored cohort for this cell
    units: integer        -- the frame's ground-truth population for this cell, IDENTICAL across arms (this is the graph's `units`; n and units are different quantities and must BOTH travel, because printing one where the other belongs is the live defect this plan ends)
    ci_low: number | null
    ci_high: number | null
    reportable: boolean   -- n at or above the population floor
  }
  headline: { value: number, rule: string = "flat_mean_of_9_cells", ci_low: number | null, ci_high: number | null, ci_provenance: string (names the laboratory and the replica count; the app prints this label beside the number and never omits it) }
  coverage: { targets: integer, predicted: integer, fraction_without_prediction: number, restrict_gt_to_predicted: boolean -- MUST be false }
  receipt: { predictions_sha256: string(64), manifest_sha256: string(64), checkpoint_sha256: string|null, image_digest: string|null, seeds: array[integer], lab_commit: string(40), scored_at: string RFC3339, frozen_at: string RFC3339 | null, waiver: string | null }
}

=== contrasts.json ===  (234 contrasts; feeds RoundLadder and the panel verdicts)
contrasts: array of {
  contrast_id: string (unique)
  frame_key: string
  a_arm_id: string, b_arm_id: string
  method_axis: array[string] -- every field in which a and b differ. Names MUST be drawn from the keys of arms[].level_fields. An axis field that does not actually differ is itself a refusal in PROTEA's seal, so this list must be exact, not generously wide.
  round_id: string | null
  scope: string ("cell"|"panel_set"|"band")
  category: string | null, aspect: string | null  (null when scope is panel_set)
  band_axis: string | null ("identity"|"length"), band: string | null (a value from manifest.bands.*)
  delta: number (b minus a, on f_micro_w)
  ci_low: number, ci_high: number
  verdict: string ("a_greater"|"b_greater"|"not_resolved" -- the same three words PROTEA already uses, so nothing has to be translated)
  detectable_effect: number | null
  n_pairs: integer
  groups: integer (number of protein groups resampled)
  claimed: boolean
}

=== timeline.json ===  (the rounds; feeds the NEW RoundLadder, never FrameTimeline)
rounds: array, ordered by index, of {
  round_id: string (unique)
  index: integer (1-based, dense, no gaps)
  date: string YYYY-MM-DD  (NO time component, ever)
  title: string <= 60 chars
  sentence: string <= 240 chars -- one sentence, from the research document's section for that round
  criteria_sha256: string(64)
  decision: string ("kept"|"dropped"|"tied"|"deferred")
  arm_ids_added: array[string]
  reference_arm_id: string | null
  headline_before: number | null, headline_after: number | null
  contrast_ids: array[string]
  fields: object mapping string -> string|number -- free-form, rendered as a definition list exactly as EventTimeline's Fields does (EventTimeline.tsx:23-36). This is where anything the schema did not anticipate goes, instead of being dropped.
}

=== strata.json ===  (identity x length with n; feeds StratificationSection's new rows prop AS-IS)
settings: array of EXACTLY 3 x {
  setting: string ("NK"|"LK"|"PK")
  arms_total: integer, arms_with_strata: integer  (kept separate so "this stratum is empty" is never confused with "these arms were never stratified")
  rows: array of {
    arm_id: string          -- the laptop maps this to CompareRow.evaluation_result_id as "imported:"+arm_id so the component's de-dup keys keep working; the desktop sends arm_id and nothing else
    display_name: string, model: string, k: integer
    category: string ("NK"|"LK"|"PK"), aspect: string ("P"|"F"|"C")
    length: string   (a value from manifest.bands.length)
    homology: string (a value from manifest.bands.identity)
    n_proteins: integer
    precision_w: number | null, recall_w: number | null, f_micro_w: number | null
    reportable: boolean
  }
}

WHAT THE LAPTOP DOES WITH IT: GET /v1/register/{frame_key} returns { frame, nodes, panels, rounds, strata, arms, contrasts } where `panels` is already in GraphPanel shape (with the two new fields), `strata` is already in CompareRow shape per setting, and `rounds` is the RoundLadder's own type. Each part answers independently -- a missing or sha-mismatched file makes that one part absent with a named reason, never the whole page blank.

## Correcciones al esquema, de la revision adversaria
El esquema de arriba salio de la sintesis; un revisor lo contrasto contra el codigo yencontro estos huecos. Son parte del contrato, no notas:

1. No way to express a PUBLISHED RIVAL figure, which step 6 requires. arms[].receipt makes predictions_sha256 (64 hex), manifest_sha256 (64 hex), lab_commit (40 hex), seeds and scored_at mandatory, and coverage requires targets/predicted/fraction_without_prediction. TransFew at 0.381 and "the rest as published without intervals" have none of these. There is also no provenance_kind / source field anywhere in the schema, yet step 2 says each row is "labelled computed or imported" and step 6 demands a mandatory "as published by LAFA, no interval" label. The schema cannot carry either label.

2. No join from a register frame_key to a PROTEA evaluation_set_id. manifest.frames carries temporal_window verbatim, t0/t1 releases and dates, but no evaluation_set_id — while api_work #3 makes the graph's selector `evaluation_set_id` (a uuid). Nothing lets the page decide which register frame belongs to the set it is showing, and with 125 evaluation sets live and window_role null on all of them, temporal_window is not a usable key either.

3. BenchmarkRow has interval fields only for the WRONG metric. lib/api.ts:1194-1218 declares primary_metric "f_micro_w"|"fmax", f_micro_w, precision_w, recall_w, fmax, and then fmax_std / fmax_ci_low / fmax_ci_high — there is no f_micro_w_ci_low/high. Step 2's two arms (0.293 and 0.406) need an f_micro_w interval on the benchmark route and there is nowhere to put it. BenchmarkRow appears in neither components_that_feed_as_is nor components_needing_change.

4. NineCellGrid has no cells prop. components/book/NineCellGrid.tsx:1-7 imports NINE_CELL from lib/book and reads it at :82; its props are only six strings (:21-37). Rank 11's "feed NINE_CELL from the register route" is an unlisted props change, and it breaks lib/book.test.ts:69-79, which computes `won` from the static NINE_CELL and asserts headlineClaim() contains "seven of the nine" — a string hardcoded in English at lib/book.ts:111 and :122, while step 5 claims wins in all nine cells.

5. cells[].reportable has no consumer. The plan adds n, ci_low and ci_high to PanelResult but GraphPanel/PanelResult (lib/graph.ts:165-191) gains no reportable field, so the population-floor flag the schema sends per cell is dropped — which is the one field that keeps a thin cell from being read as a result.

6. Per-band intervals are split across two files that no single mount sees. Step 5 claims wins in "all bands"; band verdicts live in contrasts.json (scope "band", with ci_low/ci_high), while the band grids are fed from strata.json rows, whose only interval-ish field is `reportable`. StratificationSection's new rows prop takes CompareRow[] (lib/strataStructure.ts:29-43: precision_w, recall_w, f_micro_w, n_proteins, reportable) and has no slot for a band delta or its interval.

7. The band vocabularies share zero values with the code's. manifest.bands declares 8 identity and 6 length bands; lib/strataStructure.ts:86 LENGTH_BANDS is 4 values ("<=512","512-1024","1024-2048",">2048") and :89 HOMOLOGY_BANDS is 5 ("none","<=30","30-60","60-90",">90"). No register band matches any existing band, so every one falls into the alphabetical-append path (StratificationSection.tsx:306-309, :537-543). The plan is right to widen both lists; it does not say that until it does, "<100" sorts before "300-499" and ">=2000" lands in the middle.

8. aspect code mismatch is asserted against a frontend constant. cells[].aspect is "P"|"F"|"C" and the schema says "the app maps to BPO/MFO/CCO through PANEL_OF_ASPECT, strataStructure.ts:76-80" (confirmed at :75-80) — but api_work #1 puts the shaping in the LAPTOP's route, which cannot reach a TypeScript constant. The backend needs its own copy, and graph/page.tsx's axisOrder sorts against PANEL_ASPECTS in the BPO/MFO/CCO spelling.

## Lo que el portatil decide y el sobremesa no tiene que preguntar

- El tablero de progreso y el grafo de experimentacion son LA MISMA superficie. No habra pagina
  "progreso" aparte. La razon no es de gusto: `/instrument/graph` y `/instrument/benchmark` ya
  imprimen hoy LOS MISMOS nueve `f_micro_w` desde la misma base, con `n_proteins` en una y `units`
  en la otra -- hasta 13 veces de diferencia en NK/BPO, 270 frente a 3.561 -- y con dos etiquetas
  de conjunto de evaluacion distintas. Un tercer tablero con esos nueve numeros los pondria a tres.
- Ningun brazo importado entra en `compare_paired_panels`.
- Los seis pasos NO necesitan ninguna ruta nueva. Todos caen en rutas que ya existen.

## Lo que sigue siendo de Francisco

- Do we spend a second read of the test window 227->230? My plan says NO: verify the frozen predictions by sha256 against the read already taken on the 26th and never re-read the truth. This is the desktop's own correction and it is right. You only need to confirm it, because the waiver in PROTEA is a literal sentence -- "this is the single declared pass on the holdout" (split_registry.py:483) -- and saying it is yours, not ours.
- Do we spend the holdout dispensation on LAFA's window at all? Its t1 truth is March 2026 and the board mark is v227 (split_registry.py:145), so scoring it in the platform needs the same literal sentence. My plan is built so you do NOT have to: step 6's parity comes from the acceptance record already pinned in a test, and our arm's figure enters as a registered import with its receipt. So the question is whether to spend the dispensation for a live recompute after Thursday, not whether Thursday depends on it.
- May the longitudinal axis (step 3) be shown as imported registered figures with a visible receipt, rather than recomputed in the platform? It cannot be recomputed by Thursday, and recomputing 211->227 would run with the OBO and IA congruence guard disabled, because band_registry holds only v226 and v227. I would rather import 182 arms with a receipt than recompute them under a guard that is off -- but this is how the talk's credibility is spent, so it is yours.
- Do we report the reader measured WITHOUT the heavy arms, alongside the full reader? Your own plan leaves this to the author and says to report it rather than discard anything. It changes what chapter 3 claims, so it is yours.
- At what tolerance does step 6's figure count as reproduced when the live recompute does eventually run? The acceptance contract is exact to 4.4e-16 on IA and to zero on the nine cells, but a rescore of predictions is a different quantity and needs a number from you, not from us.

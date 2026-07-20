# Contextual generation: attack the BP wall from the candidate set, not the ranker

DRAFT, pending greenlight. Written 2026-07-20. Companion to
`../prior-knowledge-wall/PLAN.md`, which it does NOT replace: that plan owns the pool
defects, the TransFew diff, and the atlas. This plan owns ONE question, "from zero":
**what clean, learned, leakage-safe signal should a candidate GENERATOR work on to add the
true BP terms our sequence-only pool misses.** Goal unchanged: 9/9 on the LAFA board
(v227->v230, `f_micro_w`). Open cells: LK-BPO (0.4402 vs TransFew 0.5120, gap +0.072) and
PK-BPO (0.2181 vs 0.2943, gap +0.076).

## 0. What the last two experiments settle (and why generation, not ranking)

Two independent findings now bound the problem from both sides:

1. **Rescoring is capped by construction (2026-07-20, the calibration wall).** A learned
   known-conditioned score ranks PK-BPO from chance (per-protein AUC 0.505) to 0.79, and the
   ranking lift transfers temporally. In-window it looked like +0.0536. But `f_micro_w` is
   set by a SINGLE global IA-weighted threshold pooled ACROSS proteins, so it rewards
   cross-protein CALIBRATION, not within-protein RANKING. Trained on the past and applied to
   the blind window, every arm went NEGATIVE (PK -0.0059, LK -0.0088). Receipt
   `storage/regen_headline/TRANSITION_SEPARABILITY_PROBE.md` +
   `project_transition_rescoring_calibration_wall_2026_07_20`. **You can order a protein's
   candidates perfectly and not move the cell.**

2. **The pool is missing true mass at the TERM level.** The atlas (PKW.3) found per-protein
   unreachability is only 2.3%, which read as "the wall is ranking". But the same receipt
   records that **52% of the false-negative IA mass is not in the pool at all** at the term
   level. The 0.75 oracle is inflated by fill-propagation of ancestors; the informative
   leaves that carry the IA weight are frequently absent.

Put together: the terms we most need are often ABSENT, and for the ones present we cannot
rank our way to them because the metric rewards a calibration that does not transfer.
**The only escape that both findings leave open is GENERATION: put the missing true terms
INTO the candidate set.** A generated true term raises `f_micro_w` structurally (its
ancestors inherit TP through `prop=fill`), independent of calibration. That is why
generation is the one channel with transferable signal, restated three times now
(classifier-extras, text-as-generator, and this).

But not any generation. Every generator we have already had its shot and missed these
terms, because they all read the same thing.

## 1. The design principle: BP is a network property; our generators are sequence-blind

MF (molecular function) and CC (localization) are close to sequence-determined, which is
exactly why we are #1 on MF and CC in all 9 cells and #1 on NK-BPO (no prior knowledge).
**BP (biological PROCESS) is where a protein FITS in a pathway.** That is a property of the
protein's CONTEXT, its partners, its genomic neighbourhood, the cell's other annotations,
not of its own residues. Two proteins in the same process can share no sequence similarity.

Every generator we run is intrinsic to the sequence: PLM k-WTA retrieval (`d8979601`), the
two-tower / M2 classifier, InterPro domains. The separability wall (annotation-RAG probe:
true/false BP-tail candidates FLAT under a trained dual-encoder) is therefore a
**sequence-channel wall**, not a statement that the signal does not exist. It says the
signal that separates a true BP term from a false one at the IA tail is **not in the
sequence**. The fix is an ORTHOGONAL channel that carries process membership.

## 2. The signal inventory: clean, learned, leakage-safe

| channel | concrete signal | learned? leakage-safe? | status |
|---|---|---|---|
| **Intrinsic (sequence)** | PLM embedding kNN, learned classifier, InterPro/Pfam domains | yes; deterministic pre-t0 | **EXHAUSTED.** It is our whole current pool. Flat at the BP tail. |
| **Context / NETWORK** | PPI (STRING), co-expression, genomic neighbourhood, phylogenetic profile | yes, at a fixed pre-t0 timepoint | **NEVER TRIED.** The real frontier for BP: process co-membership across a network. |
| **Literature** | the protein's own pre-t0 papers (CAFA6 winners: 70-80% of their edge; GORetriever +6.8% on difficult proteins) | yes; SwissProt refs public | Tried as FEATURE/rescoring (capped) and as a scale-confounded generator. **Never as a pure RECALL generator.** |
| **Known annotations as GENERATOR** | use the protein's own t0 terms (MF/CC for LK, BP for PK) to PROPOSE new BP candidates | yes; frozen | **Untested as a generator.** The transition probe tested it as RESCORING (capped); proposing candidates is a different, structural effect. |

The biological reason the NETWORK channel is THE channel for BP: proteins that interact,
co-express, or co-occur across genomes tend to share a process even when their sequences do
not align. That is precisely the axis on which the sequence embedding is flat.

## 3. The architecture: recall-first, multi-source, reranker unchanged

The reranker is already near-optimal at ordering (Phase 1 today: LK-BPO per-protein AUC
0.835). Do not touch it. Change what enters it.

1. **Each source is an independent candidate GENERATOR.** Sequence, network, literature,
   known-annotation each propose BP terms. Union into one pool (one row per
   `(protein, term)`, carrying every source's evidence; see PKW.1, the merge is a
   prerequisite so agreement is representable).
2. **Each source is judged by ONE number: true-BP-tail IA-mass ADDED that the current pool
   lacks.** Not a score, not an AUC. Recall of genuinely-missing true terms, IA-weighted.
   This is the metric that escapes the calibration wall.
3. **The reranker then orders the enriched pool** exactly as today.

## 4. The three discipline gates every source passes before any claim

Earned the hard way; a source that fails any gate is dropped, and we say so.

1. **Leakage audit.** The signal must be computable from information available at t0. A
   pre-t0 network release, pre-t0 literature, t0 annotations. State the exact freeze.
2. **Temporal transfer (the NEW hard rule, 2026-07-20).** Train on the past
   (<= v225), apply to the blind window, measure `f_micro_w`. A fixed-score control catches
   SCALE artifacts; only a temporal split catches CALIBRATION artifacts. Grouped-CV on the
   eval window is an optimistic CEILING, never a deployable number.
3. **Recall-added, not rescoring.** Report the IA-mass of true terms the source ADDS to the
   pool, measured as set membership, before any scoring. If a source only re-weights terms
   already present, it is a rescoring lever and is capped by §0.1; do not pursue it.

Inherited from `prior-knowledge-wall` §6: `f_micro_w` decides never AUC; reproduce the
anchor before building; one variable per arm; a big number is a suspect; ask what a zero is
made of.

## 5. The two cells need different sources

- **LK-BPO** ("has MF/CC at t0, lacks BP, gains BP") is a CROSS-ASPECT transfer. Natural
  sources: the network (partners already annotated with the missing BP) and the known MF/CC
  terms used as a generator. `anc2vec_query` is mute here by construction; sequence has
  already been tried.
- **PK-BPO** ("has BP, gains more BP") is EXTENSION within the process network. Natural
  source: partners / co-expressed proteins already carrying the BP terms this protein is
  about to gain; and the known BP graph used generatively.

## 6. Slices, ordered by cost against ceiling

The ordering is deliberate: prove the cheap in-house channel first, so we only pay for
external data if the in-house channel cannot reach.

### CG.1 Known-annotations as a GENERATOR (frozen, cheap, decides the next step)

```yaml
id: CG.1
loop: contextual-generation
status: pending
deps: []
priority: P0
estimated_hours: 5
acceptance: |-
  Frozen data only. For LK-BPO use each protein's t0 MF/CC terms; for PK-BPO its t0 BP
  terms. Build a generator that PROPOSES new BP candidates from the known set (a learned
  P(new BP | known set), or a co-occurrence expansion), NOT a rescoring of existing rows.
  Report the single number of §4.3: IA-mass of TRUE BP-tail terms it adds that the current
  sequence pool does NOT contain, for LK-BPO and PK-BPO. Then union into the pool and
  re-measure f_micro_w in the TRUE frame (-known for PK), under the temporal-transfer gate
  (train <= v225). One variable: candidate set only, reranker unchanged.
  GATE: if it adds little true-tail mass, the answer is not in-house and CG.3 (network)
  is justified. If it adds real mass, we have a frozen, cheap path.
tags: [generation, frozen, cross-aspect, recall-added]
```

### CG.2 Literature as a RECALL generator (pipeline exists, reframe the refuted test)

```yaml
id: CG.2
loop: contextual-generation
status: pending
deps: []
priority: P1
estimated_hours: 8
acceptance: |-
  The abstract-fetch pipeline already exists (Phase 0, storage/cooc_experiment/
  fetch_eval_abstracts.py; 30,712 PMIDs cached). The prior test injected text as a
  scale-confounded generator and as a +0.0016 feature; both are rescoring-shaped and
  capped. Reframe: a text->GO retriever proposes BP candidates from the protein's OWN
  pre-t0 papers; measure ONLY the true-tail IA-mass ADDED (§4.3), then union + re-measure
  f_micro_w under the temporal gate. Leakage audit: abstracts strictly pre-t0.
  This is the CAFA6 winners' channel (70-80% of their edge) aimed at exactly our weak spot.
tags: [generation, literature, recall-added, leakage-audit]
```

### CG.3 Network / context channel (external, the real ceiling, needs author OK)

```yaml
id: CG.3
loop: contextual-generation
status: blocked-on-decision
deps: [CG.1]
priority: P1
estimated_hours: 20
acceptance: |-
  The biologically-correct channel for BP: process = network property. A pre-t0,
  leakage-controlled network (STRING PPI release predating t0; and/or co-expression;
  and/or phylogenetic profiles) proposes BP candidates via a protein's already-annotated
  partners. REQUIRES an external download (a dated STRING/expression release), which per
  the autonomous charter is a real fetch, not a frozen-data op, and is NOT started unasked.
  Leakage audit is the first task: the network AND its edges must predate t0. Measure
  true-tail IA-mass added (§4.3), then union + re-measure f_micro_w under the temporal gate.
  GATE decision belongs to the author: open the external channel only if CG.1 shows the
  in-house channel cannot reach, and only with explicit greenlight for the download.
tags: [generation, network, external-data, ppi, author-decision]
```

## 7. Honest scope and the open decision

This plan does not promise 9/9. It promises the first generation attack that is not a
re-run of a sequence-intrinsic signal, and a clean go/no-go on whether the missing 52% of
BP-tail IA mass is recoverable in-house (CG.1, CG.2) or only through the network channel
(CG.3). The fallback is defensible doctoral work either way: a characterised BP wall whose
cause is now precise (sequence-blind generation plus a calibration-capped metric), with the
network channel named as the frontier.

**The one open decision for the author:** CG.3 needs an external, leakage-controlled network
download. Everything up to it is frozen-data. Start with CG.1 (frozen), and open CG.3 only
on greenlight.

Receipts this plan builds on: `storage/regen_headline/TRANSITION_SEPARABILITY_PROBE.md`,
`CROSS_ASPECT_CHANNEL.md`, `BOARD_FRAME_RECONSTRUCTION.md`;
`project_transition_rescoring_calibration_wall_2026_07_20`,
`project_annotation_rag_generator_capped_2026_07_18`,
`project_cross_aspect_channel_located_2026_07_17`.

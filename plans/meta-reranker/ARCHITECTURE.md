# Meta-reranker (stacked) — the established mechanism

Goal: a reranking architecture that (a) reaches a competent score, target > offline
0.391, and (b) lets the project KEEP EXPANDING (new signals, PLMs, priors) WITHOUT
massive refactors, integrated into the application (FR-1, NFR-ARCH hexagonal).

Decision: replace the monolithic single-level 73-feature per-category booster with a
**stacked meta-reranker** = a WIDE set of independent **evidence scorers** (ports)
feeding a SHALLOW, calibrated, per-category **combiner**. Depth lives INSIDE scorers
(N-hop propagation) or in a compute cascade (telescoping stages), never in combiner
stacking. (Rationale: stacking depth has diminishing returns + variance + leakage;
the lever is evidence DIVERSITY, Krogh-Vedelsby. The single-level monolith just
collapsed PK via the AUC<->f_micro_w calibration gap.)

## The two port contracts (the whole abstraction)

### EvidenceScorer (a "port"; everything plugs in here)
```
name: str                      # stable id, used by the combiner + UI + provenance
applies_to: set[Category]      # {NK,LK,PK}; e.g. priors do not apply to NK
score(query_ctx, candidates) -> dict[go_id_str, float]   # ONE calibrated score per candidate
```
- Keyed on go_id STRING (snapshot-agnostic; the bug we just fixed in #644).
- Pure + independently trainable/sealable/measurable. A scorer MAY internally be:
  trivial (a stored feature), a trained model (the M2 classifier), an N-hop graph
  propagation (GO-DAG / co-occurrence), or one stage of a telescoping cascade.
  The contract does not change; only what is inside the port.
- Calibration is the scorer's responsibility (or declared, so the combiner knows).

### Combiner (the shallow meta-learner; one per category)
```
fit(score_vectors_oof, labels, category)   # stacking discipline: OUT-OF-FOLD inputs
combine(score_vector, category) -> float   # final reranked score
```
- Input = the VECTOR of scorer outputs (a handful), NOT the raw feature matrix.
  Low-dimensional -> low variance, calibratable (fixes the PK failure mode).
- Per-category (NK/LK/PK have different available evidence).
- Trained on out-of-fold scorer outputs (no leakage); sealed once.

## Invariants (what keeps it expandable without refactor)
1. Add a lever = implement ONE new EvidenceScorer + add its column to the combiner
   input + retrain the cheap combiner. No change to candidate retrieval or other scorers.
2. Combiner consumes scores, never raw features.
3. Each scorer validated alone; combiner validated end-to-end; both sealable. (NFR-REPRO)
4. Scorers + combiners live in a REGISTRY (hexagonal): resolved by name, configurable
   per run, surfaced in the UI (which scorers active, per-component contribution,
   per-category combiner) — FR-1, UI-actionable, no dead-ends.
5. Calibration is first-class (per-scorer or in the combiner) so the thresholded
   f_micro_w behaves.

## Migration from today (NO massive refactor; reuse what exists)
- The producers already compute per-candidate signals: KNN similarity, M2 classifier,
  self_prior, association (now snapshot-agnostic via #644), alignment, taxonomy, anc2vec.
  Each becomes an EvidenceScorer adapter emitting ONE calibrated score. #643 already
  persists the new ones on GOPrediction, so the combiner/eval can read them.
- The per-category LightGBM boosters become the Combiner — but trained on the SCORE
  VECTOR (a handful of component scores) instead of the 73-feature matrix. This is the
  single change that flips monolith -> stacked, and it directly fixes calibration/PK.
- The existing scoring_config (linear) is the degenerate combiner (fixed weights); the
  monolithic booster is the degenerate scorer-less case. Both become special cases ->
  nothing is thrown away, the abstraction generalizes them.

## Slice sequence (each shippable, on-platform, measured on /benchmark)
- MR-0  ADR + the EvidenceScorer/Combiner ports + registry in protea core (no behavior change).
- MR-1  Adapt existing producers as scorers emitting calibrated per-candidate scores
        (KNN, classifier, self_prior, association); persist + expose the score vector.
- MR-2  Train the SHALLOW per-category combiner over the score vector (stacking, OOF,
        calibrated). First stacked number vs single-level 0.317 and linear 0.315.
        Includes the immediate hybrid (combiner NK/LK, KNN/linear PK) as the floor.
- MR-3  Calibration layer (fix PK; isotonic/Platt per category or calibrated combiner).
- MR-4  UI integration: list/configure scorers + per-category combiner; show per-component
        contribution + intervals (FR-1, FR-4, NFR-UI no dead-ends).
- MR-5+ Expansion (each = one new scorer port, no refactor): late-fusion per-PLM scorer;
        N-hop propagation scorer over GO-DAG / co-occurrence; multi-PLM KNN scorers; etc.
        Target: clear champion (> 0.391), PK first (the gap).

## Naming
"meta-reranker" / "stacked reranker". Avoid "composite" (collides with the linear
scoring_config + the KNN-composite + the GoF pattern). Components = "evidence scorers"
(ports) + "combiner" (per-category meta-learner).

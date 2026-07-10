# SDR: superseded

These two documents map the SDR hypothesis space as it stood before the representation
ablation ran. They are kept for provenance and are **not a live plan**.

What replaced them: the SDR-A negative was traced to a **normalization confound**, not to
sparsity being intrinsically worse. Standardizing per dimension before k-WTA fixes it,
because raw k-WTA is dominated by outlier massive-activation dimensions (layer 38 of
ankh-base reaches |440,611|). The evidence and the successor result live in
`storage/layer_ablation/` and in `plans/thesis-clean-iteration/`, where the learned k-WTA
head beats every fixed layer, sparsity and normalization that was board-confirmed.

Do not resume work from these files. Read the ablation first.

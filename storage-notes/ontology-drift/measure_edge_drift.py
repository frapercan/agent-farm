"""Edge drift between two GO releases, and the exposure it creates.

A phantom gain happens when a protein's experimental set is identical at both ends of a
window and the two ends are closed under different graphs: the later closure contains an
ancestor the earlier one did not. So the ontology-level quantity that matters is not how
many terms changed, it is for how many terms the ANCESTOR CLOSURE GREW, because only those
can manufacture a gain.

The net edge balance is reported too, because it decides whether an absorption check run
under the earlier graph returns a point or a lower bound.

Closure is over is_a and part_of, which is what the evaluator propagates.
"""
import re, sys, json
from collections import defaultdict

def parse(path):
    parents, ns, obs = defaultdict(set), {}, set()
    tid = None; interm = False
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line == "[Term]":
            interm, tid = True, None; continue
        if line.startswith("["):
            interm = False; continue
        if not interm or not line:
            continue
        if line.startswith("id: GO:"):
            tid = line[4:].strip()
        elif tid and line.startswith("namespace: "):
            ns[tid] = line[11:].strip()
        elif tid and line.startswith("is_obsolete: true"):
            obs.add(tid)
        elif tid and line.startswith("is_a: GO:"):
            parents[tid].add(line[6:].split("!")[0].strip())
        elif tid and line.startswith("relationship: part_of GO:"):
            parents[tid].add(line[len("relationship: part_of "):].split("!")[0].strip())
    for o in obs:
        parents.pop(o, None); ns.pop(o, None)
    return parents, ns

def closures(parents):
    memo = {}
    def anc(t, stack):
        if t in memo: return memo[t]
        if t in stack: return set()          # ciclo, no deberia haberlo
        stack.add(t)
        out = set()
        for p in parents.get(t, ()):
            out.add(p); out |= anc(p, stack)
        stack.discard(t)
        memo[t] = out
        return out
    sys.setrecursionlimit(20000)
    return {t: anc(t, set()) for t in parents}

OLD, NEW = "go-basic-2024-03-28.obo", "go-basic-2025-07-22.obo"
po, nso = parse(OLD); pn, nsn = parse(NEW)
co, cn = closures(po), closures(pn)

eo = {(c, p) for c, ps in po.items() for p in ps}
en = {(c, p) for c, ps in pn.items() for p in ps}
both = set(co) & set(cn)

grew = {t for t in both if cn[t] - co[t]}
shrank = {t for t in both if co[t] - cn[t]}
added_terms = set(cn) - set(co); gone_terms = set(co) - set(cn)

print(f"\n  DERIVA DE ONTOLOGIA  {OLD.split('-',2)[2][:10]} -> {NEW.split('-',2)[2][:10]}\n")
print(f"  terminos vivos        {len(co):>8,}  ->  {len(cn):>8,}   ({len(added_terms):+,} nuevos, {-len(gone_terms):+,} retirados)")
print(f"  aristas is_a/part_of  {len(eo):>8,}  ->  {len(en):>8,}   ({len(en&~eo) if False else len(en-eo):+,} anadidas, {-len(eo-en):+,} retiradas)")
print(f"  BALANCE NETO de aristas sobre terminos comunes: {len(en-eo) - len(eo-en):+,}\n")

print(f"  EXPOSICION: terminos comunes cuya CLAUSURA crece  {len(grew):,} de {len(both):,} ({len(grew)/len(both)*100:.2f}%)")
print(f"              terminos comunes cuya clausura encoge {len(shrank):,} ({len(shrank)/len(both)*100:.2f}%)\n")

ASP = {"biological_process": "BPO", "molecular_function": "MFO", "cellular_component": "CCO"}
print(f"  {'aspecto':10s}{'comunes':>10s}{'crece':>10s}{'%':>8s}{'encoge':>9s}{'ancestros +':>13s}")
rows = {}
for long, short in ASP.items():
    sub = {t for t in both if nso.get(t) == long}
    g = {t for t in sub if cn[t] - co[t]}
    s = {t for t in sub if co[t] - cn[t]}
    extra = sum(len(cn[t] - co[t]) for t in g)
    rows[short] = {"common": len(sub), "grew": len(g), "shrank": len(s), "extra_ancestors": extra}
    print(f"  {short:10s}{len(sub):10,}{len(g):10,}{len(g)/len(sub)*100:7.2f}%{len(s):9,}{extra:13,}")

json.dump({"old": OLD, "new": NEW,
           "terms": {"old": len(co), "new": len(cn), "added": len(added_terms), "removed": len(gone_terms)},
           "edges": {"old": len(eo), "new": len(en), "added": len(en-eo), "removed": len(eo-en),
                     "net": len(en-eo)-len(eo-en)},
           "closure_grew": len(grew), "closure_shrank": len(shrank), "common": len(both),
           "by_aspect": rows},
          open("edge_drift.json", "w"), indent=2)
print("\n  -> edge_drift.json")

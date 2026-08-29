"""How much of GOA 220 sits on terms the pivot retired, and how much on terms whose closure grew.

Two ontology-level exposures matter for a window whose ground truth is expressed under a pivot
graph, and they point in opposite directions:

  retired    a term alive in the t0-era graph and obsolete in the pivot. A t0 annotation on it can
             disappear when the truth is expressed under the pivot. LOSS.
  grown      a term whose ancestor closure is larger under the pivot. A t1 term can then carry an
             ancestor the t0 closure lacked, manufacturing a gain. INVENTION.

Exposure here is measured over the ONTOLOGY, not over the annotation corpus: it is the fraction of
terms at risk, which bounds nothing on its own but says which mechanism can be large. Weighting by
how many GOA 220 annotations actually sit on those terms needs the database and is left to the
machine that has it.
"""
import json, re
from collections import defaultdict

def parse(path):
    parents, ns, obs, alive = defaultdict(set), {}, set(), set()
    tid=None; interm=False
    for line in open(path, encoding="utf-8"):
        line=line.rstrip("\n")
        if line=="[Term]": interm, tid = True, None; continue
        if line.startswith("["): interm=False; continue
        if not interm or not line: continue
        if line.startswith("id: GO:"): tid=line[4:].strip(); alive.add(tid)
        elif tid and line.startswith("namespace: "): ns[tid]=line[11:].strip()
        elif tid and line.startswith("is_obsolete: true"): obs.add(tid)
        elif tid and line.startswith("is_a: GO:"): parents[tid].add(line[6:].split("!")[0].strip())
        elif tid and line.startswith("relationship: part_of GO:"):
            parents[tid].add(line[len("relationship: part_of "):].split("!")[0].strip())
    return parents, ns, obs, alive - obs

def alt_ids(path):
    """SUPERSEDED, kept only to record the error. See redirect_targets below.

    alt_id is the MERGE mechanism: a surviving term listing accessions folded into it. It is
    NOT how an obsoleted term points at a successor, which is replaced_by (automatic) or
    consider (advisory). Checking alt_id returned exactly zero of 2,756 and the zero looked
    clean; the file carries 3,646 alt_id lines, so the field existed and simply did not
    answer the question asked of it.
    """
    out=set(); tid=None; interm=False
    for line in open(path, encoding="utf-8"):
        line=line.rstrip("\n")
        if line=="[Term]": interm, tid=True, None; continue
        if line.startswith("["): interm=False; continue
        if not interm: continue
        if line.startswith("id: GO:"): tid=line[4:].strip()
        elif line.startswith("alt_id: GO:"): out.add(line[8:].strip())
    return out

OLD,NEW="go-basic-2024-03-28.obo","go-basic-2025-07-22.obo"
po,nso,obso,alo = parse(OLD)
pn,nsn,obsn,aln = parse(NEW)
alt_new = alt_ids(NEW)

gone = alo - aln
merged = gone & alt_new          # redirigidos: renombrados, no perdidos
lost   = gone - alt_new          # sin destino: perdida real

ASP={"biological_process":"BPO","molecular_function":"MFO","cellular_component":"CCO"}
print(f"\n  TERMINOS DE 2024 QUE EL PIVOTE YA NO TIENE VIVOS\n")
print(f"  {'aspecto':10s}{'vivos 2024':>12s}{'desaparecen':>13s}{'redirigidos':>13s}{'PERDIDOS':>11s}{'% perdido':>11s}")
rows={}
for lg,sh in ASP.items():
    sub={t for t in alo if nso.get(t)==lg}
    g=sub&gone; m=sub&merged; l=sub&lost
    rows[sh]={"alive_2024":len(sub),"gone":len(g),"redirected":len(m),"lost":len(l)}
    print(f"  {sh:10s}{len(sub):12,}{len(g):13,}{len(m):13,}{len(l):11,}{len(l)/len(sub)*100:10.3f}%")
print(f"  {'TOTAL':10s}{len(alo):12,}{len(gone):13,}{len(merged):13,}{len(lost):11,}{len(lost)/len(alo)*100:10.3f}%")

print(f"\n  LECTURA")
print(f"  de los {len(gone):,} terminos que desaparecen, {len(merged):,} ({len(merged)/len(gone)*100:.1f}%) llevan alt_id,")
print(f"  asi que un consumidor que resuelva alt_id los recupera y NO son perdida.")
print(f"  perdida real sin destino: {len(lost):,} terminos, el {len(lost)/len(alo)*100:.3f}% de la ontologia de 2024.")

json.dump({"old":OLD,"new":NEW,"alive_2024":len(alo),"gone":len(gone),
           "redirected_via_alt_id":len(merged),"lost_without_target":len(lost),
           "by_aspect":rows,
           "note":"exposure over the ontology, not weighted by annotation counts"},
          open("retired_exposure.json","w"), indent=2)
print("\n  -> retired_exposure.json")


# --- the corrected measurement, after the alt_id error above ---
def redirect_targets(path):
    """Obsolete terms and where each points: replaced_by is automatic, consider is advisory."""
    out = {}
    cur = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line == "[Term]":
            cur = {}; continue
        if line.startswith("["):
            cur = None; continue
        if cur is None or not line:
            continue
        k, _, v = line.partition(": ")
        cur.setdefault(k, []).append(v.strip())
        if k == "id" and v.strip().startswith("GO:"):
            out[v.strip()] = cur
    return out

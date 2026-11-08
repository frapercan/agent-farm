#!/usr/bin/env bash
# Cierra la fase 1 con la release que falta y, SOLO si el universo queda
# completo, arranca la fase 2.
#
# La puerta del medio no es decoracion. Si la fase 2 empieza con un hueco en el
# universo, cada annotation_set pasa a ser "GOA <r> restringido al corpus que
# habia entonces", que es un objeto distinto e incompleto por el lado antiguo, y
# NO reparable sin volver a leer los 802 GB. Por eso se comprueba con la misma
# regla que usa el driver, conjuntos de niveles contra admit_for(release), y no
# contando filas ni fiandose de que el proceso anterior saliera con 0.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
LOG=goa-campaign.log
say() { echo "$(date '+%F %T') CADENA: $*" | tee -a "$LOG"; }

say "fase 1, pasada final para recoger lo que falte"
/usr/bin/python3 goa_campaign_driver.py --phase 1 >> "$LOG" 2>&1
say "fase 1 termino con codigo $?"

FALTAN=$(/usr/bin/python3 - <<'PY'
import json, re, subprocess, sys
sys.path.insert(0, ".")
from goa_campaign_driver import admit_for
serie = [r for r in range(156, 236) if not 206 <= r <= 210]
out = subprocess.run(
    ["docker","exec","protea-postgres-1","psql","-U","protea","-d","protea","-t","-A","-F","\t","-c",
     "SELECT payload->>'gaf_url', coalesce(payload->>'admit','[]') FROM job "
     "WHERE operation='extract_goa_universe' AND status='SUCCEEDED' "
     "AND coalesce((payload->>'dry_run')::boolean,false)=false;"],
    capture_output=True, text=True, timeout=60)
hechas = set()
for line in out.stdout.splitlines():
    if "\t" not in line: continue
    url, adm = line.split("\t", 1)
    m = re.search(r"goa_uniprot_all\.gaf\.(\d+)\.gz", url or "")
    if not m: continue
    r = int(m.group(1))
    try: a = set(json.loads(adm))
    except Exception: continue
    if a == set(admit_for(r)): hechas.add(r)
print(",".join(str(r) for r in serie if r not in hechas))
PY
)

if [ -n "$FALTAN" ]; then
  say "NO arranco la fase 2: el universo sigue incompleto, faltan $FALTAN"
  say "un hueco aqui no se repara sin releer los 802 GB; se queda parado a proposito"
  exit 1
fi

say "universo COMPLETO bajo el criterio vigente: 75 de 75"
say "arrancando la fase 2 bajo systemd"
systemctl --user start protea-goa-driver.service
sleep 10
say "fase 2: $(systemctl --user is-active protea-goa-driver.service)"

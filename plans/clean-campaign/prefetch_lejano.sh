#!/usr/bin/env bash
# Baja por adelantado los GAF que la fase 2 todavia no tiene, de uno en uno y
# solo cuando hay disco.
#
# POR QUE EXISTE. En la fase 2 `ensure_cached` BLOQUEA el bucle de despacho
# mientras descarga, asi que cada release sin cachear para la campana entera el
# tiempo que tarde en bajar. Medido el 2026-10-08: EBI da 4,0 MB/s de media
# sobre 189 descargas reales (mediana 5,7 en las ultimas 30), y los 307 GB que
# faltan son 15-21 h. Bajarlos POR DELANTE convierte ese tiempo en solapado con
# el computo en vez de sumado.
#
# UNA A LA VEZ, Y NO ES PEREZA. Cuatro conexiones en paralelo a EBI dieron
# 2,94 MB/s contra 2,705 de una sola: +9%. EBI estrangula por cliente, no por
# conexion, y nuestra linea da 10-16 MB/s, asi que el cuello no es local y el
# paralelismo no lo mueve. Entre sondeos la tasa cayo de 2,7 a 0,40 MB/s, que
# parece estrangulamiento progresivo: una sola conexion tambien es prudencia.
#
# ORDEN. Primero la mas cercana a donde va el driver, que es la que bloquearia
# antes; despues el extremo lejano ascendente. Lo que ya exista se salta, y
# `goa_cache fetch` publica con rename atomico, asi que una carrera con el
# driver acaba en el mismo fichero verificado.
#
# SUELO DE DISCO. No baja si quedan menos de FLOOR_GB libres mas el peor
# fichero de la serie (24 GB). Espera y reintenta: el reaper del driver borra
# cada GAF al cerrar su carga, asi que el espacio aparece solo.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE="$HERE/gaf_cache"
LOG="$HERE/prefetch-lejano.log"
BASE="https://ftp.ebi.ac.uk/pub/databases/GO/goa/old/UNIPROT"
FLOOR_GB=100
PEOR_GB=24
ORDEN="203 217 218 219 220 221 222 223 224 225 226 227 228 230 232 233 234 235"

di() { echo "$(date -u '+%Y-%m-%d %H:%M:%SZ') $*" >> "$LOG"; }
libres() { df --output=avail -BG "$CACHE" | tail -1 | tr -dc '0-9'; }

di "prefetch lejano arranca: $(echo $ORDEN | wc -w) releases, suelo ${FLOOR_GB} GB"
for rel in $ORDEN; do
  dest="$CACHE/goa_uniprot_all.gaf.${rel}.gz"
  if [ -f "$dest" ]; then di "$rel: ya esta, salto"; continue; fi
  # esperar disco
  while :; do
    L=$(libres)
    if [ "${L:-0}" -ge $((FLOOR_GB + PEOR_GB)) ]; then break; fi
    di "$rel: espera, ${L} GB libres y hacen falta $((FLOOR_GB + PEOR_GB))"
    sleep 600
  done
  t0=$(date +%s)
  di "$rel: bajando (${L} GB libres)"
  if python3 "$HERE/goa_cache.py" fetch "$BASE/goa_uniprot_all.gaf.${rel}.gz" "$dest" 24 >>"$LOG" 2>&1; then
    mb=$(( $(stat -c %s "$dest" 2>/dev/null || echo 0) / 1048576 ))
    s=$(( $(date +%s) - t0 ))
    di "$rel: OK ${mb} MB en ${s}s = $(awk -v m=$mb -v s=$s 'BEGIN{printf "%.1f", (s>0)?m/s:0}') MB/s, quedan $(libres) GB"
  else
    di "$rel: FALLO, sigo con la siguiente"
  fi
done
di "prefetch lejano termina"

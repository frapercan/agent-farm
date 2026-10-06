# Arranque de la fase 2

Escrito el 2026-10-06 mientras la fase 1 corría, porque los pasos de abajo tienen
un **orden** y tres de ellos no se ven: si se salta uno, la fase 2 corre, acaba
bien y deja el corpus o el marco mal sin que nada avise. Es el modo exacto en que
esta campaña ha perdido tres reinicios.

No es una guía de la fase 2. Es lo que hay que hacer **entre** el final de la fase
1 y su arranque.

---

## 0. Confirmar que la fase 1 terminó de verdad

```bash
tail -3 plans/clean-campaign/goa-campaign.log | grep "phase 1 finished"
docker exec protea-postgres-1 psql -U protea -d protea -tAc \
  "SELECT count(DISTINCT first_admitted_release)||' releases, '||count(*)||' proteinas' FROM protein;"
```

Tienen que ser **75 releases**. Si son menos, la fase 1 se dejó alguna: `--phase 1`
de nuevo, que recalcula lo pendiente desde las filas de job y no repite nada.

**Por qué importa:** `load_goa_annotations` descarta toda fila cuya accesión no
esté en `protein`. Con el universo incompleto, las releases que falten pierden en
silencio las proteínas que sólo ellas admiten, y eso no se repara sin volver a
leer los 802 GB.

## 1. Sincronizar el código servido, y sólo entonces la declaración

El árbol vivo de `~/Thesis-laptop/PROTEA` se deja a propósito en la revisión que
los workers están **corriendo**, no en `develop`. Al acabar la fase 1 es el momento
de saltar, y hay que hacerlo en este orden:

```bash
cd ~/Thesis-laptop/PROTEA
git checkout develop && git pull
# PARAR y RELANZAR api + worker de protea.jobs (ver 1b)
# y SOLO DESPUES subir plans/DECLARED-REVISION.txt al sha nuevo
```

**Por qué el orden:** la declaración dice qué está *corriendo*, no qué está
*descargado*. Subirla antes de reiniciar la deja mintiendo, y el sobremesa la lee
para sincronizarse.

**Por qué hace falta:** PROTEA#991 cambia `load_goa_annotations`, que es la
operación de la fase 2. Sin el salto, la fase 2 corre con el contador de rechazos
viejo y la pérdida del superset vuelve a ser invisible.

### 1b. Reiniciar sin romper nada

Los dos procesos se lanzan con su entorno cargado, o la API muere al arrancar con
`PROTEA_JWT_SECRET is not set`:

```bash
cd ~/Thesis-laptop/PROTEA
# por PID leido de /proc, con el patron construido en ejecucion para que la
# propia shell no se cace a si misma
setsid bash -c 'cd ~/Thesis-laptop/PROTEA && set -a && . ./.env && set +a; \
  exec .venv/bin/uvicorn protea.api.app:create_app --factory \
  --host 127.0.0.1 --port 8000 --root-path /api-proxy' >> logs/api.log 2>&1 &
setsid bash -c 'cd ~/Thesis-laptop/PROTEA && set -a && . ./.env && set +a; \
  exec .venv/bin/python scripts/worker.py --queue protea.jobs' >> logs/worker-jobs.log 2>&1 &
grep -o 'revision=[0-9a-f]\{40\}' logs/worker-jobs.log | tail -1   # debe ser el sha nuevo
```

`setsid` y no `nohup`: `nohup` muere con la sesión.

## 2. Comprobar que están dentro las dos guardas

```bash
cd ~/Thesis-laptop/PROTEA  && git log --oneline -20 | grep -i holdout
cd ~/Thesis-laptop/agent-farm && git log --oneline -10 | grep -i fechas
```

- **PROTEA#932** mete la guarda del holdout: sin ella, nada se niega a puntuar una
  ventana que cruza la marca del consejo. Con la campaña anterior, 594 de 1.296
  resultados se habían evaluado sobre `220->230`.
- **agent-farm#343** hace que la fase 2 selle `source_published_at` al terminar.
  Sin eso la guarda **no puede decidir** y pasa todo, avisando con
  `holdout_guard.undecidable`. Con 75 conjuntos sin fecha, ése sería el único caso.

## 3. Arrancar

```bash
cd ~/Thesis-laptop/agent-farm/plans/clean-campaign
systemd-run --user --unit=protea-goa-fase2 \
  --working-directory=$PWD /usr/bin/python3 goa_campaign_driver.py --phase 2
```

`--phase 2` es el valor por defecto del driver, pero se escribe igual: un
`--phase` explícito es lo que distingue en el journal una corrida de otra.

La fase 2 crea el snapshot de ontología de cada release antes de su carga, y
reutiliza los GAF que la fase 1 dejó en caché. Lo que no esté cacheado lo baja, y
esa descarga se esconde detrás de la carga, que es el doble de lenta.

## 4. Lo primero que hay que medir, en la primera release

**La ETA de la fase 2 no está medida en esta campaña.** Las ~44 h que circulan
salen de «35 min por release» del docstring del driver, que son de la campaña
anterior, convertidos a 196 s/GB sobre una release media. En cuanto cierre la
primera carga:

```bash
grep "goa 156: ok" goa-campaign.log | tail -1
```

y recalcular con el `elapsed_seconds` real contra los 3,33 GB de la 156. Si la
carga escala peor que lineal con el tamaño —y puede, porque inserta filas y
mantiene índices— la cifra sube.

Vigilar también en esa primera release:

- **`skipped_go_term_unknown`** debe ser 0 o casi. Es la única de las tres razones
  de descarte que significa pérdida de nuestro propio superset, y `lost_go_ids`
  nombra los GO perdidos. Medido sobre 2,7 M de filas muestreadas de las releases
  221 y 231: cero. Si en el extremo antiguo no es cero, ADR-D50 pasa de propuesta
  a necesaria.
- **La transacción abierta del worker.** El patrón de dos sesiones de
  `BaseWorker` mantiene una transacción viva mientras el job corre. En la fase 1
  son 7 min; en la fase 2 serán ~35 por release, y eso impide a autovacuum limpiar
  mientras dura. Mirar bloat en `protein_go_annotation` al cabo de unas releases.

## 5. Lo que viene después, y no antes

| paso | bloqueado por |
|---|---|
| `--phase 3`, las secuencias | que la fase 2 acabe |
| `fetch_uniprot_metadata` | la fase 3 |
| `compute_information_accretion`, régimen `lafa` | que exista el conjunto de anotación que se declare |
| embeddings | **`embedding_config` está a 0 filas**: hay que volver a declarar las ocho recetas de ADR-D48 |
| nombrar ventanas del extremo antiguo | **`RELEASES` en `split_registry.py` sólo lista v220..v234** |

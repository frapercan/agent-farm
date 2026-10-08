#!/usr/bin/env bash
# Compute-node setup, run ON THE DESKTOP. Idempotent; stops at the first error.
# It configures and verifies. It does NOT enable a queue: see the last step.
set -euo pipefail

SERVER=192.168.18.121          # el portatil en la LAN. Si usas Tailscale: 100.124.245.1
ROOT="$HOME/Thesis2"
PROTEA_SRC="$ROOT/repositories/PROTEA"
DEPLOY="$ROOT/worktrees/protea-deploy"
PIN=2250dd152b17dd1305375103fbbc1d8d4b304e87

echo "== 1. alcanzar el servidor"
for p in 5432 5672 9000; do
  timeout 4 bash -c "</dev/tcp/$SERVER/$p" 2>/dev/null \
    && echo "   $SERVER:$p alcanzable" \
    || { echo "   NO alcanzo $SERVER:$p"; exit 1; }
done

echo "== 2. secretos: se COMPLETAN, nunca se sobrescriben"
# La primera version de este paso hacia `cat > $ENV_FILE`, que TRUNCA. En el
# nodo ese fichero tiene diecisiete variables, no dos: PROTEA_REPO (sin la cual
# el trabajador sirve desde el arbol del desarrollador en vez de la ranura
# fijada, que es justo lo que arreglo el PR 251), las cinco de MinIO, los topes
# de hilos y el asignador de la tarjeta. Truncarlo se llevaria quince por
# delante y el nodo arrancaria pareciendo sano.
ENV_FILE="$HOME/.secrets/protea-lab.env"
mkdir -p "$HOME/.secrets"
touch "$ENV_FILE"; chmod 600 "$ENV_FILE"
antes=$(grep -c "^[[:space:]]*export" "$ENV_FILE" || true)

anadir_si_falta() {   # clave, valor
  if grep -qE "^[[:space:]]*export[[:space:]]+$1=" "$ENV_FILE"; then
    echo "   $1 ya definida, la respeto"
  else
    printf 'export %s=%s\n' "$1" "$2" >> "$ENV_FILE"
    echo "   $1 anadida"
  fi
}
anadir_si_falta PROTEA_DB_URL   "\"postgresql+psycopg://protea:protea@$SERVER:5432/protea\""
anadir_si_falta PROTEA_AMQP_URL "\"amqp://guest:guest@$SERVER:5672//\""
anadir_si_falta PROTEA_REPO     "\"$DEPLOY\""

despues=$(grep -c "^[[:space:]]*export" "$ENV_FILE" || true)
echo "   variables: $antes -> $despues (nunca baja)"
[ "$despues" -ge "$antes" ] || { echo "   PERDI variables, aborto"; exit 1; }

echo "== 3. el checkout y la ranura de despliegue en el commit exacto"
mkdir -p "$ROOT/repositories" "$ROOT/worktrees" "$ROOT/storage/logs"
[ -d "$PROTEA_SRC/.git" ] || git clone https://github.com/frapercan/PROTEA.git "$PROTEA_SRC"
git -C "$PROTEA_SRC" fetch --all --tags --quiet
[ -d "$DEPLOY" ] || git -C "$PROTEA_SRC" worktree add "$DEPLOY" "$PIN"
git -C "$DEPLOY" fetch origin --quiet
git -C "$DEPLOY" checkout --quiet --detach "$PIN"
echo "   ranura en $(git -C "$DEPLOY" rev-parse --short HEAD)"

echo "== 4. dependencias, en el interprete QUE EL TRABAJADOR USA"
# La primera version instalaba en $DEPLOY/.venv. Ahi no existe: el trabajador
# arranca por `poetry run`, o sea el interprete de VIRTUAL_ENV. Instalar en un
# .venv que nadie lee deja el nodo con los pines correctos en el sitio
# equivocado, que se parece mucho a tenerlos bien.
cd "$DEPLOY"
set +u; . "$ENV_FILE"; set -u
PY_BIN=""
if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
  PY_BIN="$VIRTUAL_ENV/bin/python"; echo "   interprete: VIRTUAL_ENV"
elif command -v poetry >/dev/null 2>&1 && P=$(poetry env info --path 2>/dev/null) && [ -x "$P/bin/python" ]; then
  PY_BIN="$P/bin/python"; echo "   interprete: poetry env info"
elif [ -x "$DEPLOY/.venv/bin/python" ]; then
  PY_BIN="$DEPLOY/.venv/bin/python"; echo "   interprete: .venv de la ranura"
fi
[ -n "$PY_BIN" ] || {
  echo "   NO se cual es el interprete del trabajador."
  echo "   Define VIRTUAL_ENV en $ENV_FILE, o deja poetry en el PATH."
  echo "   Instalar a ciegas pondria los pines donde el trabajador no mira."
  exit 1; }
echo "   $PY_BIN"

for S in protea-contracts@74d329ff22a77baa5142f477889dd6e2e2ca2a4f \
         protea-backends@9b76719a14d729390be7d0faf957fae06a31ced5 \
         protea-method@5907ad9542faefcefe9b45f637475e528eaf3ce5 \
         protea-runners@ccd06fd80c12b5195339478dae7255d1ea58f4a6 \
         protea-sources@ad0810b9a2d117c336189d6f3f55cb3fa9aba86a \
         protea-reranker-lab@6d4dc2d4b5330485b8830b20f7789356af7be1d4; do
  N=${S%%@*}
  "$PY_BIN" -m pip install --no-deps --force-reinstall -q \
    "git+https://github.com/frapercan/$N.git@${S##*@}"
done
echo "   seis paquetes instalados sin tocar el resto del grafo"

echo "== 5. el nodo ve lo mismo que el servidor"
"$PY_BIN" - <<'PY'
from protea_contracts import PredictGOTermsPayload as P
from protea.core.utils import contract_payload
from protea_method._donor_ledger import DonorLedger
import torch, uuid
u = str(uuid.uuid4())
p = P.model_validate(contract_payload({
    "embedding_config_id": u, "annotation_set_id": u, "ontology_snapshot_id": u,
    "limit_per_entry": 30, "exclude_self_neighbour": True, "_job_id": u}))
assert p.exclude_self_neighbour is True, "la bandera se pierde: pines mal"
assert P.model_config.get("extra") == "forbid", "contrato viejo"
print(f"   contrato ok | libro ok | torch {torch.__version__} cuda {torch.cuda.is_available()}")
PY

echo "== 6. servicio, sin habilitar ninguna cola todavia"
mkdir -p "$HOME/.config/systemd/user" "$HOME/.local/lib/protea"
FARM="$ROOT/repositories/agent-farm"
[ -d "$FARM/.git" ] || git clone https://github.com/frapercan/agent-farm.git "$FARM"
git -C "$FARM" pull --quiet || true
install -m 755 "$FARM/scripts/services/protea-lab-worker.sh"      "$HOME/.local/lib/protea/"
install -m 644 "$FARM/scripts/services/protea-lab-worker@.service" "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
echo "   instalado. Falta: sudo loginctl enable-linger $USER"
echo
echo "LISTO. NO habilites ninguna cola todavia."
echo
echo "Si algo fallo, el paso dice que es y no hay que adivinarlo:"
echo "  1 el servidor no se alcanza          -> red, o SERVER en la linea 6"
echo "  2 perdi variables                    -> nunca deberia pasar, avisa"
echo "  3 la ranura no queda en el commit    -> el pin no existe o no hay fetch"
echo "  4 no se cual es el interprete        -> define VIRTUAL_ENV en el env"
echo "  5 la bandera se pierde, o forbid no  -> los pines estan mal, NO fuerces"
echo "Cuando el servidor avise, sera:"
echo "  systemctl --user enable --now protea-lab-worker@protea.predictions.batch.service"

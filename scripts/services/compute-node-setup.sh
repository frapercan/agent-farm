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

echo "== 2. secretos"
mkdir -p "$HOME/.secrets"
cat > "$HOME/.secrets/protea-lab.env" <<EOF
export PROTEA_DB_URL="postgresql+psycopg://protea:protea@$SERVER:5432/protea"
export PROTEA_AMQP_URL="amqp://guest:guest@$SERVER:5672//"
EOF
chmod 600 "$HOME/.secrets/protea-lab.env"
echo "   escrito y con permisos 600"

echo "== 3. el checkout y la ranura de despliegue en el commit exacto"
mkdir -p "$ROOT/repositories" "$ROOT/worktrees" "$ROOT/storage/logs"
[ -d "$PROTEA_SRC/.git" ] || git clone https://github.com/frapercan/PROTEA.git "$PROTEA_SRC"
git -C "$PROTEA_SRC" fetch --all --tags --quiet
[ -d "$DEPLOY" ] || git -C "$PROTEA_SRC" worktree add "$DEPLOY" "$PIN"
git -C "$DEPLOY" fetch origin --quiet
git -C "$DEPLOY" checkout --quiet --detach "$PIN"
echo "   ranura en $(git -C "$DEPLOY" rev-parse --short HEAD)"

echo "== 4. dependencias, dirigidas: poetry install arranca la compilacion CUDA"
cd "$DEPLOY"
for S in protea-contracts@74d329ff22a77baa5142f477889dd6e2e2ca2a4f \
         protea-backends@9b76719a14d729390be7d0faf957fae06a31ced5 \
         protea-method@5907ad9542faefcefe9b45f637475e528eaf3ce5 \
         protea-runners@ccd06fd80c12b5195339478dae7255d1ea58f4a6 \
         protea-sources@ad0810b9a2d117c336189d6f3f55cb3fa9aba86a \
         protea-reranker-lab@6d4dc2d4b5330485b8830b20f7789356af7be1d4; do
  N=${S%%@*}
  .venv/bin/pip install --no-deps --force-reinstall -q \
    "git+https://github.com/frapercan/$N.git@${S##*@}"
done
echo "   seis paquetes instalados sin tocar el resto del grafo"

echo "== 5. el nodo ve lo mismo que el servidor"
.venv/bin/python - <<'PY'
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
echo "   instalado. Falta: sudo loginctl enable-linger \$USER"
echo
echo "LISTO. NO habilites ninguna cola todavia."
echo "Cuando el servidor avise, sera:"
echo "  systemctl --user enable --now protea-lab-worker@protea.predictions.batch.service"

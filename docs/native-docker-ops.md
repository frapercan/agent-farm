# Native docker-ce operations

The box runs **native docker-ce** with the **NVIDIA Container Toolkit**,
and the docker **default runtime is `nvidia`** (so any container sees the
GPU without extra flags). This doc is the operator reference for the
day-to-day container commands plus the deployment model we settled on.

## Deployment model (decided 2026-06-06): keep the hybrid

We deliberately do NOT containerize everything. Two tracks:

- **Development = host venvs + git worktrees + infra-in-docker.**
  Each repo / ephemeral agent worktree has its own in-project `.venv`
  (poetry). The agent-farm spawns worktrees that run poetry directly;
  the edit/restart loop and the GPU torch override are trivial on the
  host. Only postgres + rabbitmq + minio run as containers for dev.
- **Deployment = host-process stack via `manage.sh`** from the
  `worktrees/protea-deploy` worktree, fronted by ngrok. The API and
  workers run on the host venv (GPU torch), not in containers.

A fully-containerized path exists (`docker-compose.bundle.yml`, images
from `ghcr.io/frapercan/protea*`) and is fine for a no-GPU public
mirror, but it ships CPU torch in a `python:3.12-slim` image, so it does
not cover GPU compute jobs (embeddings, dataset export). We keep those
on the host. Revisit the bundle only if a GPU worker image is built.

Why not "todo en contenedores": serving needs no GPU (KNN runs on
numpy / faiss-cpu), and containerizing the dev loop fights the
worktree+venv model the farm depends on. Containers buy reproducibility
for *serving*; the host buys velocity and simple GPU for *dev*.

See [[project_cold_boot_procedure]] for the GPU torch / CPU-lock detail.

## Cold boot (powered-off box)

One command brings the platform back:

```bash
bash ~/Thesis2/agent-farm/scripts/cold-boot.sh
```

It starts the infra containers, syncs `protea-deploy` to develop,
installs deps, flips torch to the GPU build (`install_gpu_torch.sh`),
starts the stack, and checks `/health`. Then launch the tunnel:

```bash
cd ~/Thesis2/worktrees/protea-deploy && bash scripts/expose.sh
```

Run `bash ~/Thesis2/agent-farm/scripts/boot.sh` afterwards to confirm
green.

## Portainer (web GUI)

Portainer is the web GUI for the native engine, at
**https://localhost:9443** (self-signed cert, accept the warning). It is
recreated to publish only `9443` (the old container also published
`8000` and `9000`, which collide with the PROTEA API and MinIO):

```bash
docker run -d -p 9443:9443 --name portainer --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest
```

The admin account lives in the `portainer_data` volume, so recreating
the container keeps your login. Never mount a password file from `/tmp`
(it is wiped on reboot, which is what broke the previous container).

## CLI cheatsheet

| Operation | Native docker-ce command |
|---|---|
| Containers list / dashboard | `docker ps -a` (or Portainer :9443) |
| Container logs | `docker logs -f <name>` |
| Stats / CPU-RAM usage | `docker stats` |
| Start / stop a container | `docker start <name>` / `docker stop <name>` |
| Inspect health | `docker inspect -f '{{.State.Health.Status}}' <name>` |
| Exec a shell | `docker exec -it <name> bash` |
| Volumes list | `docker volume ls` |
| Reclaim disk | `docker system df` then `docker system prune` |
| Image list | `docker images` |
| Compose up the infra | `docker compose --profile storage up -d postgres rabbitmq minio` |

Notes:
- The active context must be `default` (native socket). Check with
  `docker context show`; switch with `docker context use default`.
- The platform infra containers are `protea-postgres-1`,
  `protea-rabbitmq-1`, `protea-minio-1`. They exit cleanly on shutdown
  and are restarted by `cold-boot.sh`, not automatically.
- Disk note: native docker-ce stores layers under `/var/lib/docker`, so
  `docker system prune` actually reclaims space.

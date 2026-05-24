---
name: full-stack-compose
section: "4-infra"
state: working
owner: FARM-INFRA.4
source:
  - infra/compose/docker-compose.full-stack.yml
runbook: infra/compose/README.md
smoke: python3 -m pytest tests/test_full_stack_compose_yaml.py -q
---

# full-stack-compose

Single `docker compose` file that brings up every infrastructure service
the PROTEA dev stack needs in one command. Eliminates the prior
requirement of knowing which subset of five separate compose files to
pass in which order for a fresh deployment.

## Source coordinates

- `infra/compose/docker-compose.full-stack.yml` (this feature)
- `infra/compose/README.md` (usage guide)
- `tests/test_full_stack_compose_yaml.py` (structural assertions)

## Services

Eight services across two profiles:

- **infra profile**: `postgres` (pgvector/pg16), `rabbitmq` (3-management),
  `minio`
- **monitoring profile**: `prometheus`, `grafana`, `loki`, `promtail`,
  `postgres-exporter`

The PROTEA application processes (API, workers, frontend) are intentionally
NOT containerised. `scripts/manage.sh start` handles those on the host.

## Usage

```bash
# Infra only:
docker compose -f infra/compose/docker-compose.full-stack.yml --profile infra up -d

# Infra + observability:
docker compose -f infra/compose/docker-compose.full-stack.yml --profile infra --profile monitoring up -d

# Tear down and wipe volumes:
docker compose -f infra/compose/docker-compose.full-stack.yml --profile infra --profile monitoring down -v
```

## Design decisions

- All services carry an explicit `healthcheck` so `depends_on: condition:
  service_healthy` works correctly in downstream overrides.
- Named volumes use the `protea_` prefix to avoid collisions with any
  existing compose project named `protea` on the same host.
- The compose project name is `protea-full-stack` for the same reason.
- Prometheus joins both `protea_infra` and `protea_monitoring` networks so
  it can scrape RabbitMQ and postgres-exporter by container name without
  requiring additional published ports.
- `postgres-exporter` reaches Postgres via `host.docker.internal` so it
  works regardless of whether Postgres was started by this compose file
  or by the host `manage.sh` stack.

## Invariants enforced by tests

- Every service has a `healthcheck`.
- All five named volumes (`protea_postgres_data`, `protea_minio_data`,
  `protea_grafana_data`, `protea_prometheus_data`, `protea_loki_data`) are
  declared in the top-level `volumes` map.
- No volume is declared `external`.
- Every service belongs to exactly one profile (`infra` or `monitoring`);
  no service is in the default (no-profile) slot.
- Both profiles contain at least one service.

## See also

- `infra/compose/README.md` for full usage guide and environment variable
  reference.
- `docs/runbook-stack-owner-lock.md` for the stack-owner lock protocol that
  prevents deploy-keeper from clobbering a running export.

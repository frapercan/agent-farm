# PROTEA full-stack infrastructure compose

Single `docker compose` file that brings up every infrastructure service
the PROTEA dev stack needs. The PROTEA application processes (API, workers,
frontend) are intentionally **not** containerised here; use
`scripts/manage.sh start` on the host after the infra stack is healthy.

## Services

| Service | Profile | Port(s) | Purpose |
|---|---|---|---|
| postgres | infra | 5432 | Primary relational store (pgvector/pg16) |
| rabbitmq | infra | 5672, 15672, 15692 | AMQP broker + management UI |
| minio | infra | 9000, 9001 | S3-compatible artifact store |
| prometheus | monitoring | 9090 | Metrics scraper (15-day TSDB) |
| grafana | monitoring | 3001 | Dashboard and alerting UI |
| loki | monitoring | 3100 | Log aggregation backend |
| promtail | monitoring | (none) | Log shipper from host logs to Loki |
| postgres-exporter | monitoring | 9187 | Postgres metrics for Prometheus |

## Usage

```bash
# Infra only (postgres + rabbitmq + minio):
docker compose -f infra/compose/docker-compose.full-stack.yml \
  --profile infra up -d

# Infra + observability sidecars:
docker compose -f infra/compose/docker-compose.full-stack.yml \
  --profile infra --profile monitoring up -d

# Check health:
docker compose -f infra/compose/docker-compose.full-stack.yml \
  --profile infra --profile monitoring ps

# Tear down without losing data:
docker compose -f infra/compose/docker-compose.full-stack.yml \
  --profile infra --profile monitoring down

# Tear down AND wipe all volumes (destructive):
docker compose -f infra/compose/docker-compose.full-stack.yml \
  --profile infra --profile monitoring down -v
```

## Environment variables

All variables have sane defaults for local development. Override in a
`.env` file placed alongside this compose file, or export in your shell.

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `protea` | Postgres superuser |
| `POSTGRES_PASSWORD` | `protea` | Postgres password |
| `POSTGRES_DB` | `protea` | Database name |
| `RABBITMQ_DEFAULT_USER` | `guest` | RabbitMQ admin user |
| `RABBITMQ_DEFAULT_PASS` | `guest` | RabbitMQ admin password |
| `MINIO_ROOT_USER` | `minioadmin` | MinIO root user |
| `MINIO_ROOT_PASSWORD` | `minioadmin` | MinIO root password |
| `SLACK_WEBHOOK_URL` | (empty) | Grafana alert webhook; unset is safe |
| `POSTGRES_EXPORTER_DATA_SOURCE_NAME` | dev DSN via host-gateway | Override for non-default Postgres creds |

## Named volumes

| Volume | Purpose |
|---|---|
| `protea_postgres_data` | Postgres data directory (persisted across restarts) |
| `protea_minio_data` | MinIO object blobs |
| `protea_grafana_data` | Grafana state (dashboards, alert history) |
| `protea_prometheus_data` | Prometheus TSDB (15-day retention) |
| `protea_loki_data` | Loki log chunks |

## After bringing up infra

Once all infra services are healthy, start the application processes on
the host:

```bash
cd ~/Thesis2/repositories/PROTEA
bash scripts/manage.sh start
```

The application stack connects to Postgres at `localhost:5432` and
RabbitMQ at `localhost:5672` (both published by this compose file).

## Notes

- Every service has a `healthcheck` so `depends_on: condition: service_healthy`
  works correctly in downstream compose overrides.
- Prometheus joins both `protea_infra` and `protea_monitoring` networks so it
  can scrape rabbitmq and postgres-exporter by container name without
  requiring those services to publish extra ports.
- Promtail bind-mounts `/var/log/protea` from the host in read-only mode;
  ensure `manage.sh` is configured to write logs there, or override the
  volume path in a local override file.
- The compose project name is `protea-full-stack` (set via `name:` at the top
  of the file), ensuring volume and container names are predictable and do not
  collide with an existing `protea` compose project on the same host.

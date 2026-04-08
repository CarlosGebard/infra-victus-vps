# Observability Stack

## Purpose

Document the baseline observability deployment for the VPS.

## Architecture

- Grafana Alloy runs on the host as a `systemd` service.
- Loki runs in Docker Compose for local log storage.
- Prometheus runs in Docker Compose for basic metrics scraping.
- Grafana runs in Docker Compose for visualization.

## Baseline data flow

1. Alloy reads host log files.
2. Alloy pushes logs to Loki at `http://127.0.0.1:3100/loki/api/v1/push`.
3. Prometheus scrapes:
   - itself
   - Alloy metrics on `host.docker.internal:12345`
4. Grafana connects to both Loki and Prometheus through provisioning.

## Host service

Alloy is installed from the Grafana APT repository and managed by `systemd`.

Useful commands:

```bash
sudo systemctl status alloy
sudo journalctl -u alloy
sudo systemctl restart alloy
```

## Conservative ports

The observability services bind to localhost on the host:

- Grafana: `127.0.0.1:3000`
- Prometheus: `127.0.0.1:9090`
- Loki: `127.0.0.1:3100`

Alloy uses host port `12345` for its HTTP endpoints so Prometheus can scrape it from Docker through `host.docker.internal`. This port is not opened through UFW by default.

## Persistent paths

- Loki data: `/srv/data/observability/loki`
- Prometheus data: `/srv/data/observability/prometheus`
- Grafana data: `/srv/data/observability/grafana`
- Configs: `/srv/apps/core/observability`

## Phase 2 candidates

- `loki.source.journal` for journald
- Docker log collection
- `node_exporter`
- `cadvisor`
- PostgreSQL, Redis, and CouchDB exporters
- dashboards and alerts

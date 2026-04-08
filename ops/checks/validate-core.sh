#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not installed; skipping compose validation" >&2
  exit 0
fi

docker compose \
  --env-file "${ROOT_DIR}/secrets/bootstrap/infisical.env.example" \
  -f "${ROOT_DIR}/compose/stacks/infisical-bootstrap/docker-compose.yml" \
  config >/dev/null

docker compose \
  --env-file "${ROOT_DIR}/compose/env/core.env.example" \
  -f "${ROOT_DIR}/compose/stacks/core/docker-compose.yml" \
  config >/dev/null

echo "compose validation passed"

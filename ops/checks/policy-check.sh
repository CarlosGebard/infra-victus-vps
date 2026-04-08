#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CORE_COMPOSE="${ROOT_DIR}/compose/stacks/core/docker-compose.yml"
BOOTSTRAP_COMPOSE="${ROOT_DIR}/compose/stacks/infisical-bootstrap/docker-compose.yml"
FAILED=0

fail_if_matches() {
  local description="$1"
  local pattern="$2"
  shift 2

  local search_cmd=(rg -n)
  if ! command -v rg >/dev/null 2>&1; then
    search_cmd=(grep -RInE)
  fi

  if "${search_cmd[@]}" "${pattern}" "$@"; then
    echo "policy check failed: ${description}" >&2
    FAILED=1
  fi
}

check_ports() {
  local compose_file="$1"
  local allowed_csv="$2"

  if ! awk -v allowed_csv="${allowed_csv}" '
    BEGIN {
      split(allowed_csv, allowed_list, ",")
      for (i in allowed_list) {
        allowed[allowed_list[i]] = 1
      }
    }
    /^services:$/ {
      in_services = 1
      next
    }
    in_services && /^[^[:space:]]/ && $0 !~ /^services:$/ {
      in_services = 0
      in_ports = 0
    }
    in_services && /^  [A-Za-z0-9_.-]+:$/ {
      service = $1
      sub(":", "", service)
      in_ports = 0
      next
    }
    in_services && /^    ports:$/ {
      in_ports = 1
      next
    }
    in_services && /^    [A-Za-z0-9_.-]+:/ && $0 !~ /^    ports:$/ {
      in_ports = 0
    }
    in_services && in_ports && /^      - / {
      if (!(service in allowed)) {
        printf "%s:%d: unexpected published port in service %s: %s\n", FILENAME, NR, service, $0
        bad = 1
      }
    }
    END {
      exit bad
    }
  ' "${compose_file}"; then
    FAILED=1
  fi
}

fail_if_matches "floating latest image tags are not allowed" 'image: .*:latest([[:space:]]|$|\})' "${ROOT_DIR}/compose/stacks"
fail_if_matches "relative bind mounts are not allowed in compose stacks" '^[[:space:]]*-[[:space:]]+\.\.?/' "${ROOT_DIR}/compose/stacks"

check_ports "${CORE_COMPOSE}" "nginx,loki,prometheus,grafana"
check_ports "${BOOTSTRAP_COMPOSE}" "infisical"

if [[ "${FAILED}" -ne 0 ]]; then
  exit 1
fi

echo "policy checks passed"

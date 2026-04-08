#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ANSIBLE_ENV=(HOME=/tmp ANSIBLE_CONFIG="${ROOT_DIR}/ansible/ansible.cfg")

run_if_present() {
  local bin="$1"
  shift

  if command -v "${bin}" >/dev/null 2>&1; then
    "$@"
  else
    echo "${bin} not installed; skipping" >&2
  fi
}

if command -v terraform >/dev/null 2>&1; then
  terraform -chdir="${ROOT_DIR}/terraform/environments/production" init -backend=false -input=false >/dev/null
fi

run_if_present terraform terraform -chdir="${ROOT_DIR}/terraform/environments/production" fmt -check -recursive
run_if_present terraform terraform -chdir="${ROOT_DIR}/terraform/environments/production" validate
run_if_present ansible-playbook env "${ANSIBLE_ENV[@]}" ansible-playbook -i "${ROOT_DIR}/ansible/inventories/production/hosts.yml" "${ROOT_DIR}/ansible/playbooks/bootstrap.yml" --syntax-check
run_if_present ansible-playbook env "${ANSIBLE_ENV[@]}" ansible-playbook -i "${ROOT_DIR}/ansible/inventories/production/hosts.yml" "${ROOT_DIR}/ansible/playbooks/deploy-infisical-bootstrap.yml" --syntax-check
run_if_present ansible-playbook env "${ANSIBLE_ENV[@]}" ansible-playbook -i "${ROOT_DIR}/ansible/inventories/production/hosts.yml" "${ROOT_DIR}/ansible/playbooks/deploy-core.yml" --syntax-check
run_if_present ansible-playbook env "${ANSIBLE_ENV[@]}" ansible-playbook -i "${ROOT_DIR}/ansible/inventories/production/hosts.yml" "${ROOT_DIR}/ansible/playbooks/validate-core-runtime.yml" --syntax-check
run_if_present docker "${ROOT_DIR}/ops/checks/validate-core.sh"
"${ROOT_DIR}/ops/checks/policy-check.sh"

echo "static validation stage completed"

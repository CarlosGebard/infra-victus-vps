#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ANSIBLE_ENV=(HOME=/tmp ANSIBLE_CONFIG="${ROOT_DIR}/ansible/ansible.cfg")
ARTIFACTS_DIR="${ARTIFACTS_DIR:-${ROOT_DIR}/artifacts/validation}"

mkdir -p "${ARTIFACTS_DIR}"

run_if_present() {
  local bin="$1"
  shift

  if command -v "${bin}" >/dev/null 2>&1; then
    "$@"
  else
    echo "${bin} not installed; skipping" >&2
  fi
}

RESULTS_FILE="${ARTIFACTS_DIR}/results.txt"
: > "${RESULTS_FILE}"

record_result() {
  local status="$1"
  local name="$2"
  local log_file="$3"
  printf '%s|%s|%s\n' "${status}" "${name}" "${log_file}" >> "${RESULTS_FILE}"
}

run_check() {
  local name="$1"
  shift

  local log_file="${ARTIFACTS_DIR}/${name}.log"

  if "$@" > >(tee "${log_file}") 2> >(tee -a "${log_file}" >&2); then
    record_result "PASS" "${name}" "${log_file}"
  else
    record_result "FAIL" "${name}" "${log_file}"
    return 1
  fi
}

FAILED=0

run_check "ansible-bootstrap-syntax" run_if_present ansible-playbook env "${ANSIBLE_ENV[@]}" ansible-playbook -i "${ROOT_DIR}/ansible/inventories/production/syntax-check.yml" "${ROOT_DIR}/ansible/bootstrap/playbooks/bootstrap.yml" --syntax-check || FAILED=1
run_check "ansible-deploy-core-syntax" run_if_present ansible-playbook env "${ANSIBLE_ENV[@]}" ansible-playbook -i "${ROOT_DIR}/ansible/inventories/production/syntax-check.yml" "${ROOT_DIR}/ansible/runtime/playbooks/deploy-core.yml" --syntax-check || FAILED=1
run_check "ansible-validate-core-runtime-syntax" run_if_present ansible-playbook env "${ANSIBLE_ENV[@]}" ansible-playbook -i "${ROOT_DIR}/ansible/inventories/production/syntax-check.yml" "${ROOT_DIR}/ansible/runtime/playbooks/validate-core-runtime.yml" --syntax-check || FAILED=1
run_check "compose-render" run_if_present docker "${ROOT_DIR}/ops/checks/validate-core.sh" || FAILED=1
run_check "compose-policy" "${ROOT_DIR}/ops/checks/policy-check.sh" || FAILED=1

if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  {
    echo "## Validation Results"
    echo
    echo "| Check | Status | Log |"
    echo "| --- | --- | --- |"

    while IFS='|' read -r status name log_file; do
      echo "| ${name} | ${status} | \`${log_file##*/}\` |"
    done < "${RESULTS_FILE}"
  } >> "${GITHUB_STEP_SUMMARY}"
fi

echo "ci validation stage completed"

exit "${FAILED}"

# Ansible

This directory contains Ansible entry points and shared roles split by operational phase.

Current layout:

- `bootstrap/playbooks/` for first-host setup and hardening
- `runtime/playbooks/` for service deployment and post-deploy validation
- `inventories/production/` for syntax-check fixtures and shared inventory vars
- `roles/` for shared role implementations

Notes:

- `ops/scripts/bootstrap_via_infisical.py` is the active production bootstrap entry point.
- `inventories/production/syntax-check.yml` is a committed syntax-check fixture only and must not contain live production connection details.

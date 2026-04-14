# infra-macro-vps

Infrastructure repository for a production VPS managed as code.

## Dropped,great for learning purposes, but lacks checks and has just one workflow 

Recommended usage order:

1. `make bootstrap`
2. `make verify-bootstrap`

The target operating model is:

- `terraform/` for infrastructure provisioning
- `ansible/` for host configuration
- `compose/` for container runtime definitions
- `docs/` for decisions and runbooks
- `ops/` for validation and helper scripts
- `legacy/` for historical configs and migration inputs

## Repository layout

```text

```

## Current status

The repository now models a phased production rollout:

- `ops/scripts/bootstrap_via_infisical.py` is the active bootstrap entry point; it authenticates to Infisical with machine identity, fetches SSH trust material, runs an SSH preflight, and then invokes Ansible
- `ansible/bootstrap/playbooks/bootstrap.yml` hardens the host, installs Docker, and joins Tailscale
- `.github/workflows/deploy-production.yml` fetches deploy secrets from Infisical at runtime using GitHub OIDC and deploys the remaining stack
- `ops/scripts/fetch_infisical_cloud.py` and `ops/scripts/seed_infisical_cloud.py` support operator-driven secret fetch and one-time Infisical seeding

This keeps long-lived deployment secrets out of GitHub while still allowing GitHub Actions to perform Ansible-based remote deploys.

Terraform remains in the repository for future reprovisioning, but it is not part of the current operational workflow because the production VPS already exists.

## Common commands

The `make` targets above are the primary operational interface. The most common paths are:

- `make bootstrap` for applying the host baseline
- `make verify-bootstrap` for confirming the host really converged
- `make bootstrap-debug` when you need detailed Ansible logs
- `make bootstrap-from TASK="Task Name"` when you need to resume from a specific bootstrap task during debugging
- `make validate-bootstrap` and `make validate-runtime` for local syntax validation before remote runs

The committed Ansible inventory is intentionally non-production. Real production host, private key, and known-hosts material must come from Infisical at runtime. The active bootstrap flow currently connects as `root` by default.

The active secret layout is split by purpose in Infisical:

- `/bootstrap` for bootstrap-only operator values
- `/connection` for SSH connection material
- `/runtime` for runtime deploy secrets

# infra-macro-vps

Infrastructure repository for a production VPS managed as code.

The target operating model is:

- `terraform/` for infrastructure provisioning
- `ansible/` for host configuration
- `compose/` for container runtime definitions
- `docs/` for decisions and runbooks
- `ops/` for validation and helper scripts
- `legacy/` for historical configs and migration inputs

## Repository layout

```text
.
├── ansible/
│   ├── inventories/
│   ├── playbooks/
│   └── roles/
├── compose/
│   ├── configs/
│   ├── env/
│   └── stacks/
├── docs/
│   ├── adr/
│   └── runbooks/
├── legacy/
│   ├── compose/
│   └── couchdb-backup/
├── ops/
│   ├── checks/
│   └── scripts/
├── terraform/
│   ├── environments/
│   └── modules/
├── AGENTS.md
└── PLANS.md
```

## Current status

The repository now models a phased production rollout:

- `ansible/playbooks/bootstrap.yml` hardens the host, installs Docker, and joins Tailscale
- `ansible/playbooks/deploy-infisical-bootstrap.yml` starts only Infisical, PostgreSQL, and Redis with minimal bootstrap secrets
- `.github/workflows/deploy-production.yml` fetches deploy secrets from Infisical at runtime using GitHub OIDC and deploys the remaining stack

This keeps long-lived deployment secrets out of GitHub while still allowing GitHub Actions to perform Ansible-based remote deploys.

Terraform remains in the repository for future reprovisioning, but it is not part of the current operational workflow because the production VPS already exists.

## Legacy material

The `legacy/` directory contains the old compose files and a CouchDB backup snapshot retained for migration analysis.

Those files contain historical credentials and configuration patterns. They should not be promoted directly into the new stack.

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

This repository has been restructured to separate target infrastructure code from legacy operational artifacts.

The next implementation phase should define:

- Terraform provider and production environment
- Ansible inventory, base roles, and bootstrap playbooks
- Docker Compose stack for NGINX, CouchDB, SeaweedFS, and Infisical
- Backup, restore, and migration runbooks

## Legacy material

The `legacy/` directory contains the old compose files and a CouchDB backup snapshot retained for migration analysis.

Those files contain historical credentials and configuration patterns. They should not be promoted directly into the new stack.

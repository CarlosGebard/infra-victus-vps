# ADR 0001: Repository Layout for VPS Infrastructure

## Status

Accepted

## Context

The repository started with ad hoc compose files and a CouchDB backup snapshot. The target system is a production VPS managed through Terraform, Ansible, and Docker Compose with strict separation of concerns.

Without a clear repository layout, infrastructure code, migration assets, and operational documentation would become mixed and difficult to validate or evolve.

## Decision

The repository is organized into dedicated top-level areas:

- `terraform/` for provisioning
- `ansible/` for host configuration
- `compose/` for container runtime definitions
- `docs/adr/` for architecture decisions
- `docs/runbooks/` for operational procedures
- `ops/` for validations and helper scripts
- `legacy/` for historical configs and migration inputs

Legacy artifacts remain available for reference, but are isolated from the future source of truth.

## Consequences

Positive:

- Clear ownership by tool and lifecycle stage
- Safer migration from historical configs
- Better readiness for CI/CD and future environments

Tradeoffs:

- Initial scaffolding adds directories before service code exists
- Migration work must explicitly translate old configs into the new model

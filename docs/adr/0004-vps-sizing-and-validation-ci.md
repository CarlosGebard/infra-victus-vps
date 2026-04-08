# ADR 0004: VPS Sizing Baseline And Validation CI

## Status

Accepted

## Context

The production baseline for this repository now targets a Hetzner Cloud VPS with 4 vCPU and 8 GB RAM.

The repository also needs a dedicated CI workflow that runs static validation before infrastructure changes are merged or deployed.

## Decision

- Set the production Terraform server type baseline to `cx33`, matching the current Hetzner shared plan with 4 vCPU and 8 GB RAM.
- Add a GitHub Actions workflow dedicated to static infrastructure validation.
- Keep deployment automation separate from validation automation.

## Consequences

Positive:

- The default production sizing now matches the intended host capacity.
- Validation can fail earlier on pull requests instead of during manual deploy steps.
- Terraform, Ansible, and Compose checks are exercised continuously.

Tradeoffs:

- CI depends on external provider registry access during Terraform initialization.
- The selected server type reflects the current Hetzner catalog and may need future review if plan names change again.

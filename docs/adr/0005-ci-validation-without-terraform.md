# ADR 0005: CI Validation Without Terraform Apply Context

## Status

Accepted

## Context

This repository still contains Terraform because it defines the original infrastructure baseline.

However, the production VPS already exists and current CI should validate only the parts that remain in active day-to-day change scope: Ansible and Docker Compose.

Including Terraform in the validation workflow adds provider-registry dependency and checks infrastructure provisioning logic that is not part of the routine deployment path for the existing server.

## Decision

- Keep Terraform in the repository as infrastructure source-of-truth history and sizing baseline.
- Exclude Terraform from the GitHub Actions validation workflow.
- Limit CI validation to Ansible syntax checks and Docker Compose rendering.
- Keep broader Terraform validation available for explicit local operator use when infrastructure provisioning changes are intentionally revisited.

## Consequences

Positive:

- CI reflects the active operating model of the already-provisioned VPS.
- Validation is faster and less dependent on external registry availability.
- Pull requests fail only on the automation paths that are still operationally relevant.

Tradeoffs:

- Terraform drift or breakage will not be caught by routine CI.
- Infrastructure provisioning changes require intentional manual validation when they are reintroduced.

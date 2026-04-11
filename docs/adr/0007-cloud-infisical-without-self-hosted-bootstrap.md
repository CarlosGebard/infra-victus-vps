# ADR 0007: Cloud Infisical Without Self-Hosted Bootstrap

## Status

Accepted

## Context

The repository no longer needs a self-hosted Infisical bootstrap phase on the VPS. Secret management has been moved to Infisical Cloud, and the host bootstrap workflow should return to its original scope: prepare the server, secure access, install runtime prerequisites, and join Tailscale.

Keeping a dedicated self-hosted Infisical bootstrap path adds extra compose files, checks, secrets, and operational steps that no longer serve the active architecture.

## Decision

The active production workflow is now:

1. Run `ansible/bootstrap/playbooks/bootstrap.yml` to harden the host, install Docker, create directories, configure Alloy, and join Tailscale.
2. Store runtime deploy secrets in Infisical Cloud.
3. Fetch runtime deploy secrets from Infisical Cloud either:
   - from GitHub Actions using OIDC machine identity; or
   - from an operator workstation using Universal Auth machine identity credentials.
4. Run `ansible/runtime/playbooks/deploy-core.yml` and `ansible/runtime/playbooks/validate-core-runtime.yml`.

The repository removes the self-hosted Infisical bootstrap playbook, compose stack, and fallback bootstrap secret files from the active workflow.

## Consequences

Positive:

- bootstrap is simpler and returns to host-only concerns
- there is a single active secret manager model
- operator credentials use one normalized Universal Auth naming scheme
- validation and documentation are smaller and easier to keep accurate

Tradeoffs:

- runtime deploys now fully depend on Infisical Cloud availability
- the repository no longer keeps a first-class local fallback for self-hosted Infisical bootstrap

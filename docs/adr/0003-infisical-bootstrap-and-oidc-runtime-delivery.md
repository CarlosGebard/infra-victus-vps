# ADR 0003: Infisical Bootstrap And OIDC Runtime Secret Delivery

## Status

Accepted

## Context

The repository originally treated bootstrap secret files on the VPS as the input for the entire stack deployment. That model keeps too much sensitive material outside the target secret manager and forces GitHub Actions to depend on either repository secrets or long-lived credentials.

The target operating model is:

- bootstrap the host manually and privately;
- start only Infisical with the minimum secret set required for Infisical itself;
- let GitHub Actions fetch deploy secrets from Infisical at runtime using GitHub OIDC and an Infisical machine identity.

## Decision

The production rollout is split into two phases:

1. Manual private bootstrap
   - run `ansible/playbooks/bootstrap.yml`
   - create `/srv/secrets/bootstrap/infisical.env`
   - run `ansible/playbooks/deploy-infisical-bootstrap.yml`
2. Runtime secret delivery from GitHub Actions
   - GitHub workflow uses `id-token: write`
   - Infisical machine identity trusts the repository and `production` environment context
   - workflow fetches secrets from Infisical at runtime
   - workflow stages `/srv/secrets/runtime/core.env` and `/srv/secrets/runtime/seaweed-s3.json` during deploy

## Consequences

Positive:

- GitHub no longer stores long-lived deploy secrets
- bootstrap scope is reduced to Infisical-only values
- deploy secrets are centralized under Infisical before the rest of the platform is rolled out

Tradeoffs:

- GitHub Actions deploys depend on Infisical availability
- operators must perform an initial manual Infisical bootstrap before CI/CD is usable
- the Infisical bootstrap stack must be shut down before the full stack takes over the same data paths

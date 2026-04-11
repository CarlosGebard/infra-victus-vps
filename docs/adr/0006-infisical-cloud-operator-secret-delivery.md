# ADR 0006: Infisical Cloud Operator Secret Delivery

## Status

Accepted

## Context

The repository already uses Infisical for runtime deploy secrets in GitHub Actions, but the operator bootstrap path still depends on a local or VPS-resident bootstrap env file. That creates an avoidable split in the secret model and keeps bootstrap material outside the active secret manager.

## Decision

Operator-driven runtime deploys will fetch their secret material from Infisical Cloud using Universal Auth machine identity credentials.

The repository now provides a controller-side helper script:

- `ops/scripts/fetch_infisical_cloud.py`

The script authenticates against Infisical Cloud and renders:

- runtime dotenv for `/srv/secrets/runtime/core.env`
- SeaweedFS S3 JSON for `/srv/secrets/runtime/seaweed-s3.json`

GitHub Actions production deploys continue to use OIDC for runtime secret delivery. This keeps long-lived Infisical client credentials out of GitHub while giving operators a cloud-backed runtime deploy path.

## Consequences

Positive:

- runtime secrets now share Infisical Cloud as the main source of truth
- manual deploys and CI/CD use the same secret inventory model

Tradeoffs:

- operator-driven runtime deploys depend on Infisical Cloud reachability
- a Universal Auth client secret now exists for operator use and must be stored outside Git

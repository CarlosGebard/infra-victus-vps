# SECRETS.md

## Purpose

Document every secret used by this repository, where it must be stored, and which component consumes it.

This file is documentation only. No secret values belong here.

## Secret Storage Model

Secrets are intentionally split across four locations:

1. GitHub Actions `production` environment variables
   Used only for non-secret Infisical connection metadata and deploy approvals.
2. Local untracked files
   Used for workstation-only Terraform or operator workflows.
3. VPS bootstrap secret files
   Used only to start self-hosted Infisical before runtime deploy secrets move under Infisical management.
4. Infisical-managed runtime secrets
   Used by GitHub Actions to fetch deploy-time credentials and generate runtime files on demand.

## GitHub Actions Variables

Store these in:

- Repository `Settings -> Environments -> production -> Variables`

GitHub Actions should not store long-lived deploy secrets for the phase-2 deploy workflow.

The minimum approved variable set is:

- `INFISICAL_DOMAIN`
- `INFISICAL_IDENTITY_ID`
- `INFISICAL_PROJECT_SLUG`
- `INFISICAL_ENV_SLUG`

### INFISICAL_DOMAIN

- Purpose: base URL for the self-hosted Infisical instance
- Used by: GitHub Actions deploy workflow
- Storage: GitHub `production` environment variable

### INFISICAL_IDENTITY_ID

- Purpose: public machine identity identifier used for OIDC login
- Used by: GitHub Actions deploy workflow
- Storage: GitHub `production` environment variable
- Notes: this is not a secret

### INFISICAL_PROJECT_SLUG

- Purpose: Infisical project slug used by the workflow
- Used by: GitHub Actions deploy workflow
- Storage: GitHub `production` environment variable

### INFISICAL_ENV_SLUG

- Purpose: Infisical environment slug used by the workflow
- Used by: GitHub Actions deploy workflow
- Storage: GitHub `production` environment variable

## Local-Only Secrets

Store these in untracked local files. Never commit them.

### terraform/environments/production/terraform.tfvars

- Purpose: local Terraform variables for production
- Typical contents:
  - `hcloud_token`
  - `ssh_key_names`
  - `ssh_allowed_cidrs`
  - `enable_public_http`
- Storage: local untracked file
- Notes:
  - already covered by `.gitignore` expectations
  - not used in the current operational workflow while the VPS already exists

## VPS Bootstrap Secrets

Store these on the server under:

- `/srv/secrets/bootstrap/infisical.env`

These are the minimum bootstrap inputs consumed before Infisical becomes the runtime source of truth.

For the target deployment model, these values stay on the VPS only long enough to start Infisical.

The intended long-term model is a narrower bootstrap that exists only to start Infisical. See:

- `secrets/bootstrap/infisical.env.example`
- `secrets/bootstrap/infisical.enc.env`
- `docs/runbooks/infisical-bootstrap-example.md`

### infisical.env variables

#### POSTGRES_PASSWORD

- Purpose: PostgreSQL password for Infisical
- Used by: PostgreSQL and Infisical containers
- Storage: `/srv/secrets/bootstrap/infisical.env`

#### INFISICAL_REDIS_PASSWORD

- Purpose: Redis password for Infisical
- Used by: Redis and Infisical containers
- Storage: `/srv/secrets/bootstrap/infisical.env`

#### INFISICAL_ENCRYPTION_KEY

- Purpose: application encryption key for Infisical
- Used by: Infisical container
- Storage: `/srv/secrets/bootstrap/infisical.env`

#### INFISICAL_AUTH_SECRET

- Purpose: application auth secret for Infisical
- Used by: Infisical container
- Storage: `/srv/secrets/bootstrap/infisical.env`

## Infisical Runtime Secrets

These values should be stored in Infisical and fetched by GitHub Actions at runtime through OIDC.

#### COUCHDB_PASSWORD

- Purpose: CouchDB admin password
- Used by: CouchDB container and healthcheck
- Storage: Infisical runtime secret

#### GRAFANA_ADMIN_PASSWORD

- Purpose: admin password for Grafana
- Used by: Grafana container
- Storage: Infisical runtime secret

#### PROD_HOST

- Purpose: target VPS hostname or public IP for SSH and Ansible
- Used by: GitHub Actions deploy workflow
- Storage: Infisical runtime secret

#### PROD_SSH_USER

- Purpose: SSH user for GitHub Actions deployments
- Used by: GitHub Actions deploy workflow
- Storage: Infisical runtime secret

#### PROD_SSH_PRIVATE_KEY

- Purpose: private SSH key used by GitHub Actions to connect to the VPS
- Used by: GitHub Actions deploy workflow
- Storage: Infisical runtime secret

#### PROD_SSH_KNOWN_HOSTS

- Purpose: pinned SSH host key material for the VPS
- Used by: GitHub Actions deploy workflow
- Storage: Infisical runtime secret

#### SEAWEED_S3_ACCESS_KEY

- Purpose: SeaweedFS S3 access key used to render the runtime config
- Used by: GitHub Actions deploy workflow
- Storage: Infisical runtime secret

#### SEAWEED_S3_SECRET_KEY

- Purpose: SeaweedFS S3 secret key used to render the runtime config
- Used by: GitHub Actions deploy workflow
- Storage: Infisical runtime secret

### Runtime files written on the VPS

GitHub Actions stages these files during deploy:

- `/srv/secrets/runtime/core.env`
- `/srv/secrets/runtime/seaweed-s3.json`

### seaweed-s3.json structure

- Purpose: SeaweedFS S3 identity and access credentials
- Used by: SeaweedFS container
- Storage: rendered to `/srv/secrets/runtime/seaweed-s3.json` during deploy

## Pending Values Checklist

This section tracks the values that still need to be set before a real production deploy can succeed.

### GitHub `production` environment variables

These should already exist before the OIDC-based workflow can authenticate:

#### `INFISICAL_DOMAIN`

- Meaning: base URL for the self-hosted Infisical instance

#### `INFISICAL_IDENTITY_ID`

- Meaning: machine identity identifier configured for GitHub OIDC

#### `INFISICAL_PROJECT_SLUG`

- Meaning: Infisical project slug used by the workflow

#### `INFISICAL_ENV_SLUG`

- Meaning: Infisical environment slug used by the workflow

### VPS file: `/srv/secrets/bootstrap/infisical.env`

These are still placeholders and must be replaced before the Infisical bootstrap deploy can succeed:

#### `POSTGRES_PASSWORD`

- Meaning: PostgreSQL password used by Infisical

#### `INFISICAL_REDIS_PASSWORD`

- Meaning: Redis password used by Infisical

#### `INFISICAL_ENCRYPTION_KEY`

- Meaning: encryption key used by Infisical for protected data

#### `INFISICAL_AUTH_SECRET`

- Meaning: signing/authentication secret used by Infisical

### Local shell for first bootstrap

#### `TAILSCALE_AUTH_KEY`

- Meaning: auth key used to join the VPS to the tailnet during the first Ansible bootstrap
- Storage: local shell environment when running `ansible/playbooks/bootstrap.yml`
- Current usage: required for first bootstrap when the node is not yet connected to Tailscale

### Local-only file: `terraform/environments/production/terraform.tfvars`

#### `hcloud_token`

- Meaning: local Terraform token for Hetzner operations from your workstation

#### `ssh_key_names`

- Meaning: Hetzner Cloud SSH key names that should be injected into the server

#### `ssh_allowed_cidrs`

- Meaning: CIDR ranges allowed to connect to SSH through the Hetzner firewall

#### `enable_public_http`

- Meaning: whether Terraform should open ports `80` and `443`
- Current intended value: `false`

### Infisical runtime secrets

These must exist in Infisical before the GitHub Actions deploy can succeed:

#### `COUCHDB_PASSWORD`

- Meaning: admin password for CouchDB

#### `POSTGRES_PASSWORD`

- Meaning: PostgreSQL password used by Infisical and retained for the full stack

#### `INFISICAL_REDIS_PASSWORD`

- Meaning: Redis password used by Infisical

#### `INFISICAL_ENCRYPTION_KEY`

- Meaning: encryption key used by Infisical for protected data

#### `INFISICAL_AUTH_SECRET`

- Meaning: signing/authentication secret used by Infisical

#### `GRAFANA_ADMIN_PASSWORD`

- Meaning: admin password for Grafana

#### `PROD_HOST`

- Meaning: VPS hostname or IP used by SSH and Ansible

#### `PROD_SSH_USER`

- Meaning: remote SSH user used by GitHub Actions

#### `PROD_SSH_PRIVATE_KEY`

- Meaning: private key for SSH deploy access from GitHub Actions

#### `PROD_SSH_KNOWN_HOSTS`

- Meaning: pinned SSH host key entry for the production VPS

#### `SEAWEED_S3_ACCESS_KEY`

- Meaning: SeaweedFS S3 access key for the runtime admin identity

#### `SEAWEED_S3_SECRET_KEY`

- Meaning: SeaweedFS S3 secret key for the runtime admin identity

## Legacy Secrets

Historical credentials still exist in legacy files under:

- `legacy/compose/`
- `legacy/couchdb-backup/`

Treat all of them as compromised.

Rules:

- do not reuse them in active infrastructure
- rotate any value that was ever used in production
- keep legacy only for migration analysis

## Future State

After Infisical is operational, the target model is:

- GitHub keeps only non-secret OIDC connection metadata and approval gates
- VPS keeps only minimum bootstrap material plus runtime files staged during deploy
- application-level and deploy credentials live in Infisical

## Operational Rules

- Never commit secret values to Git
- Never place production secrets in example files
- Prefer GitHub Environment variables for non-secret deploy metadata
- Use a dedicated SSH key for CI/CD
- Rotate any secret copied from legacy assets

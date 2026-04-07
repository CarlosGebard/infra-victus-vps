# SECRETS.md

## Purpose

Document every secret used by this repository, where it must be stored, and which component consumes it.

This file is documentation only. No secret values belong here.

## Secret Storage Model

Secrets are intentionally split across three locations:

1. GitHub Actions `production` environment
   Used by CI/CD workflows that need cloud or SSH access.
2. Local untracked files
   Used for workstation-only Terraform or operator workflows.
3. VPS bootstrap secret files
   Used by the runtime stack during initial deployment before secret management is fully migrated into Infisical.

## GitHub Actions Secrets

Store these in:

- Repository `Settings -> Environments -> production -> Environment secrets`

For the first production workflow, GitHub Actions should contain only infrastructure and access secrets.

The minimum approved set is:

- `HCLOUD_TOKEN`
- `PROD_HOST`
- `PROD_SSH_USER`
- `PROD_SSH_PRIVATE_KEY`
- `PROD_SSH_KNOWN_HOSTS`

### HCLOUD_TOKEN

- Purpose: authenticate Terraform against Hetzner Cloud
- Used by: Terraform plan/apply workflow
- Storage: GitHub `production` environment secret

### PROD_HOST

- Purpose: target VPS hostname or public IP for SSH and Ansible
- Used by: deploy workflow
- Storage: GitHub `production` environment secret

### PROD_SSH_USER

- Purpose: SSH user for GitHub Actions deployments
- Used by: deploy workflow
- Storage: GitHub `production` environment secret

### PROD_SSH_PRIVATE_KEY

- Purpose: private SSH key used by GitHub Actions to connect to the VPS
- Used by: deploy workflow
- Storage: GitHub `production` environment secret
- Notes: use a dedicated deploy key, not your personal workstation key

### PROD_SSH_KNOWN_HOSTS

- Purpose: pinned SSH host key material for the VPS
- Used by: deploy workflow
- Storage: GitHub `production` environment secret
- Notes: generate with `ssh-keyscan -H <host>`

Application bootstrap secrets are intentionally not stored in GitHub Actions for this phase.

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
- Notes: already covered by `.gitignore` expectations

## VPS Bootstrap Secrets

Store these on the server under:

- `/srv/secrets/bootstrap/core.env`
- `/srv/secrets/bootstrap/seaweed-s3.json`

These are the runtime bootstrap inputs consumed by Docker Compose before application secrets are migrated into Infisical.

For the current deployment model, these values stay on the VPS and are not mirrored into GitHub Actions.

The intended long-term model is a narrower bootstrap that exists only to start Infisical. See:

- `compose/env/infisical-bootstrap.env.example`
- `docs/runbooks/infisical-bootstrap-example.md`

### core.env variables

#### NGINX_BIND_IP

- Purpose: host bind address for NGINX
- Used by: Docker Compose
- Storage: `/srv/secrets/bootstrap/core.env`
- Default intent: `127.0.0.1`

#### NGINX_HTTP_PORT

- Purpose: host port for NGINX
- Used by: Docker Compose
- Storage: `/srv/secrets/bootstrap/core.env`
- Default intent: `8080`

#### INFISICAL_SITE_URL

- Purpose: base URL used by Infisical
- Used by: Infisical container
- Storage: `/srv/secrets/bootstrap/core.env`

#### COUCHDB_USER

- Purpose: CouchDB admin username
- Used by: CouchDB container and healthcheck
- Storage: `/srv/secrets/bootstrap/core.env`

#### COUCHDB_PASSWORD

- Purpose: CouchDB admin password
- Used by: CouchDB container and healthcheck
- Storage: `/srv/secrets/bootstrap/core.env`

#### POSTGRES_DB

- Purpose: PostgreSQL database name for Infisical
- Used by: PostgreSQL and Infisical containers
- Storage: `/srv/secrets/bootstrap/core.env`

#### POSTGRES_USER

- Purpose: PostgreSQL username for Infisical
- Used by: PostgreSQL and Infisical containers
- Storage: `/srv/secrets/bootstrap/core.env`

#### POSTGRES_PASSWORD

- Purpose: PostgreSQL password for Infisical
- Used by: PostgreSQL and Infisical containers
- Storage: `/srv/secrets/bootstrap/core.env`

#### INFISICAL_REDIS_PASSWORD

- Purpose: Redis password for Infisical
- Used by: Redis and Infisical containers
- Storage: `/srv/secrets/bootstrap/core.env`

#### INFISICAL_ENCRYPTION_KEY

- Purpose: application encryption key for Infisical
- Used by: Infisical container
- Storage: `/srv/secrets/bootstrap/core.env`

#### INFISICAL_AUTH_SECRET

- Purpose: application auth secret for Infisical
- Used by: Infisical container
- Storage: `/srv/secrets/bootstrap/core.env`

#### INFISICAL_IMAGE

- Purpose: override image tag for Infisical
- Used by: Docker Compose
- Storage: `/srv/secrets/bootstrap/core.env`
- Secret class: not sensitive, but kept with bootstrap runtime config for operational simplicity

### seaweed-s3.json

- Purpose: SeaweedFS S3 identity and access credentials
- Used by: SeaweedFS container
- Storage: `/srv/secrets/bootstrap/seaweed-s3.json`

## Pending Values Checklist

This section tracks the values that still need to be set before a real production deploy can succeed.

### GitHub `production` environment

These should already exist, but keep this list as the minimum deploy inventory:

#### `HCLOUD_TOKEN`

- Meaning: Hetzner Cloud API token used by Terraform

#### `PROD_HOST`

- Meaning: VPS hostname or IP used by SSH and Ansible

#### `PROD_SSH_USER`

- Meaning: remote SSH user used by GitHub Actions

#### `PROD_SSH_PRIVATE_KEY`

- Meaning: private key for SSH deploy access from GitHub Actions

#### `PROD_SSH_KNOWN_HOSTS`

- Meaning: pinned SSH host key entry for the production VPS

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

### VPS file: `/srv/secrets/bootstrap/core.env`

These are still placeholders and must be replaced before deploy:

#### `COUCHDB_USER`

- Meaning: admin username for CouchDB

#### `COUCHDB_PASSWORD`

- Meaning: admin password for CouchDB

#### `POSTGRES_DB`

- Meaning: database name used by Infisical
- Current intended value: `infisical`

#### `POSTGRES_USER`

- Meaning: PostgreSQL username used by Infisical
- Current intended value: `infisical`

#### `POSTGRES_PASSWORD`

- Meaning: PostgreSQL password used by Infisical

#### `INFISICAL_REDIS_PASSWORD`

- Meaning: Redis password used by Infisical

#### `INFISICAL_ENCRYPTION_KEY`

- Meaning: encryption key used by Infisical for protected data

#### `INFISICAL_AUTH_SECRET`

- Meaning: signing/authentication secret used by Infisical

#### `INFISICAL_SITE_URL`

- Meaning: base URL Infisical should use for callbacks and links
- Current intended bootstrap value: `http://127.0.0.1:8080/infisical`

#### `NGINX_BIND_IP`

- Meaning: host bind IP for the NGINX entrypoint
- Current intended bootstrap value: `127.0.0.1`

#### `NGINX_HTTP_PORT`

- Meaning: host bind port for the NGINX entrypoint
- Current intended bootstrap value: `8080`

#### `INFISICAL_IMAGE`

- Meaning: image tag override for Infisical
- Current intended value: `infisical/infisical:latest`

### VPS file: `/srv/secrets/bootstrap/seaweed-s3.json`

These are still placeholders and must be replaced before deploy:

#### `identities[0].credentials[0].accessKey`

- Meaning: SeaweedFS S3 access key for the bootstrap admin identity

#### `identities[0].credentials[0].secretKey`

- Meaning: SeaweedFS S3 secret key for the bootstrap admin identity

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

- GitHub keeps only deployment and infrastructure access secrets
- VPS keeps only minimum bootstrap material
- application-level secrets move into Infisical

## Operational Rules

- Never commit secret values to Git
- Never place production secrets in example files
- Prefer GitHub Environment secrets over repository-wide secrets for deploy access
- Use a dedicated SSH key for CI/CD
- Rotate any secret copied from legacy assets

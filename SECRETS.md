# SECRETS.md

## Purpose

Document every secret or secret-access credential used by this repository, where it must be stored, and which flow consumes it.

This file is documentation only. No secret values belong here.

## Active Secret Storage Model

Secrets are intentionally split across four locations:

1. GitHub Actions `production` environment variables
   Used only for non-secret Infisical Cloud connection metadata for the OIDC deploy workflow.
2. Local operator environment variables
   Used only to authenticate the operator workstation to Infisical Cloud with Universal Auth.
3. Infisical Cloud secret paths
   Used as the source of truth for bootstrap-only operator values and CI/CD runtime deploy secrets.
4. Local untracked files
   Used only for workstation-specific Terraform input and temporary rendered secret files.

## GitHub Actions Variables

Store these in:

- Repository `Settings -> Environments -> production -> Variables`

Required variables:

- `INFISICAL_API_URL`
- `INFISICAL_PROJECT_SLUG`
- `INFISICAL_ENV_SLUG`

### INFISICAL_API_URL

- Purpose: base URL for the Infisical Cloud tenant or regional domain
- Used by: GitHub Actions deploy workflow
- Storage: GitHub `production` environment variable

### INFISICAL_PROJECT_SLUG

- Purpose: Infisical project slug used by the GitHub workflow
- Used by: GitHub Actions deploy workflow
- Storage: GitHub `production` environment variable

### INFISICAL_ENV_SLUG

- Purpose: Infisical environment slug used by the GitHub workflow and local helper script
- Used by: GitHub Actions deploy workflow and operator helper script
- Storage: GitHub `production` environment variable

## Local Operator Credentials

Store these outside Git and load them into the local shell or operator credential file before running the helper script:

- `INFISICAL_PROJECT_ID`
- `INFISICAL_ENV_SLUG`
- `INFISICAL_UNIVERSAL_AUTH_CLIENT_ID`
- `INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET`

Optional local variables:

- `INFISICAL_API_URL`
- `INFISICAL_ORGANIZATION_SLUG`
- `INFISICAL_BOOTSTRAP_SECRET_PATH`
- `INFISICAL_CONNECTION_SECRET_PATH`
- `INFISICAL_RUNTIME_SECRET_PATH`
- `INFISICAL_OPERATOR_ENV_FILE`

Recommended storage:

- shell profile managed by a secret manager
- `direnv` with an ignored `.envrc`
- repository-local `.secrets/infisical/bootstrap.env`

Do not commit these values.

### INFISICAL_UNIVERSAL_AUTH_CLIENT_ID

- Purpose: Universal Auth machine identity client ID for operator-driven secret fetches
- Used by: `ops/scripts/fetch_infisical_cloud.py`
- Storage: local operator environment only

### INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET

- Purpose: Universal Auth machine identity client secret for operator-driven secret fetches
- Used by: `ops/scripts/fetch_infisical_cloud.py`
- Storage: local operator environment only

### INFISICAL_PROJECT_ID

- Purpose: Infisical project identifier used by the helper script
- Used by: `ops/scripts/fetch_infisical_cloud.py`
- Storage: local operator environment only

### INFISICAL_ORGANIZATION_SLUG

- Purpose: optional organization slug required by some Universal Auth configurations
- Used by: `ops/scripts/fetch_infisical_cloud.py`
- Storage: local operator environment only

### INFISICAL_BOOTSTRAP_SECRET_PATH

- Purpose: secret path that contains bootstrap-only operator values
- Used by: `ops/scripts/fetch_infisical_cloud.py bootstrap-shell`
- Default: `/bootstrap`
- Storage: local operator environment only

### INFISICAL_CONNECTION_SECRET_PATH

- Purpose: secret path that contains the SSH connection material used to reach the VPS
- Used by: `ops/scripts/bootstrap_via_infisical.py` and `ops/scripts/fetch_infisical_cloud.py connection-ssh`
- Default: `/connection`
- Storage: local operator environment only

### INFISICAL_RUNTIME_SECRET_PATH

- Purpose: secret path that contains runtime deploy values
- Used by: `ops/scripts/fetch_infisical_cloud.py runtime-env` and `seaweed-s3`
- Default: `/runtime`
- Storage: local operator environment only

### INFISICAL_OPERATOR_ENV_FILE

- Purpose: optional explicit path to the local operator credential file
- Used by: `ops/scripts/fetch_infisical_cloud.py`
- Default lookup order:
  - repository `.secrets/infisical/bootstrap.env`
  - `~/.config/infisical/bootstrap.env`
- Storage: local operator environment only

## Bootstrap-Only Local Shell Material

The host bootstrap wrapper fetches its required values from Infisical Cloud on the operator workstation, then passes only the needed runtime inputs into Ansible.

Required for bootstrap:

- `PROD_HOST`
- `PROD_SSH_PRIVATE_KEY`
- `PROD_SSH_KNOWN_HOSTS`
- `TAILSCALE_AUTH_KEY`

### PROD_HOST

- Purpose: bootstrap target hostname or IP used for the initial SSH connection
- Used by: `ops/scripts/bootstrap_via_infisical.py`
- Storage: Infisical Cloud connection path

### PROD_SSH_USER

- Purpose: SSH user used by the connection/runtime flows when connecting to the VPS
- Used by: `ops/scripts/fetch_infisical_cloud.py connection-ssh` and deploy workflows
- Storage: Infisical Cloud connection path
- Notes: bootstrap now defaults to `root` locally and does not require this secret

### PROD_SSH_PRIVATE_KEY

- Purpose: private key used by the bootstrap wrapper to authenticate to the VPS over SSH
- Used by: `ops/scripts/bootstrap_via_infisical.py`
- Storage: Infisical Cloud connection path

### PROD_SSH_KNOWN_HOSTS

- Purpose: host key trust entry used by the bootstrap wrapper for strict SSH host verification
- Used by: `ops/scripts/bootstrap_via_infisical.py`
- Storage: Infisical Cloud connection path

### TAILSCALE_AUTH_KEY

- Purpose: authenticate the VPS to Tailscale during bootstrap
- Used by: `ansible/bootstrap/playbooks/bootstrap.yml`
- Storage: Infisical Cloud bootstrap path

## Infisical Cloud Secret Inventory

These values belong in Infisical Cloud as the source of truth.

### Bootstrap secret path

The bootstrap path should contain at least:

- `TAILSCALE_AUTH_KEY`

Consumed by:

- `ops/scripts/fetch_infisical_cloud.py bootstrap-shell`
- operator host bootstrap flow

### Connection secret path

The connection path should contain at least:

- `PROD_HOST`
- `PROD_SSH_USER`
- `PROD_SSH_PRIVATE_KEY`
- `PROD_SSH_KNOWN_HOSTS`

Consumed by:

- `ops/scripts/bootstrap_via_infisical.py`
- `.github/workflows/deploy-production.yml`

### Runtime secret path

The runtime path should contain at least:

- `COUCHDB_PASSWORD`
- `GRAFANA_ADMIN_PASSWORD`
- `SEAWEED_S3_ACCESS_KEY`
- `SEAWEED_S3_SECRET_KEY`

Optional runtime values:

- `COUCHDB_USER`
- `GRAFANA_ADMIN_USER`

Consumed by:

- `ops/scripts/fetch_infisical_cloud.py runtime-env`
- `ops/scripts/fetch_infisical_cloud.py seaweed-s3`
- `ansible/runtime/playbooks/deploy-core.yml`

### GitHub Actions deploy secrets in Infisical Cloud

The GitHub Actions deploy workflow is pinned to this OIDC contract:

- `identity-id`: `0a100e5d-1422-437e-b447-e032f32403fa`
- `audience`: `repo:CarlosGebard/infra-victus-vps:ref:refs/heads/main`
- `subject`: `repo:CarlosGebard/infra-victus-vps`
- `access token TTL`: 20 minutes

The GitHub Actions deploy workflow needs:

- connection path:
  - `PROD_HOST`
  - `PROD_SSH_USER`
  - `PROD_SSH_PRIVATE_KEY`
  - `PROD_SSH_KNOWN_HOSTS`
- runtime path:
  - `COUCHDB_PASSWORD`
  - `GRAFANA_ADMIN_PASSWORD`
  - `SEAWEED_S3_ACCESS_KEY`
  - `SEAWEED_S3_SECRET_KEY`
  - optional: `COUCHDB_USER`
  - optional: `GRAFANA_ADMIN_USER`

## Local-Only Files

### terraform/environments/production/terraform.tfvars

- Purpose: local Terraform variables for production
- Typical contents:
  - `hcloud_token`
  - `ssh_key_names`
  - `ssh_allowed_cidrs`
  - `enable_public_http`
- Storage: local untracked file

### Temporary rendered secret files

The helper script writes temporary files on the operator workstation such as:

- `/tmp/bootstrap.env`
- `/tmp/core.env`
- `/tmp/seaweed-s3.json`

These files are controller-side artifacts only and should be deleted after deploy.

## VPS Secret Files

Ansible stages these files onto the host during runtime deploy:

- `/srv/secrets/runtime/core.env`
- `/srv/secrets/runtime/seaweed-s3.json`

These files are deploy artifacts on the VPS, not the source of truth.

## Pending Setup Checklist

### GitHub `production` environment variables

- `INFISICAL_API_URL`
- `INFISICAL_PROJECT_SLUG`
- `INFISICAL_ENV_SLUG`

### Local operator environment

- `INFISICAL_PROJECT_ID`
- `INFISICAL_ENV_SLUG`
- `INFISICAL_UNIVERSAL_AUTH_CLIENT_ID`
- `INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET`

Optional:

- `INFISICAL_API_URL`
- `INFISICAL_ORGANIZATION_SLUG`
- `INFISICAL_BOOTSTRAP_SECRET_PATH`
- `INFISICAL_CONNECTION_SECRET_PATH`
- `INFISICAL_RUNTIME_SECRET_PATH`
- `INFISICAL_OPERATOR_ENV_FILE`

### Local shell for host bootstrap

- `TAILSCALE_AUTH_KEY`

### Infisical Cloud bootstrap secret path

- `TAILSCALE_AUTH_KEY`

### Infisical Cloud connection secret path

- `PROD_HOST`
- `PROD_SSH_USER`
- `PROD_SSH_PRIVATE_KEY`
- `PROD_SSH_KNOWN_HOSTS`

### Infisical Cloud runtime secret path

- `COUCHDB_PASSWORD`
- `GRAFANA_ADMIN_PASSWORD`
- `SEAWEED_S3_ACCESS_KEY`
- `SEAWEED_S3_SECRET_KEY`

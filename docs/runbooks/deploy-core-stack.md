# Deploy Core Stack

## Purpose

Deploy the full core services stack after the host is hardened and Infisical Cloud is already serving as the source of truth for bootstrap and runtime deploy secrets.

Terraform is not part of this deployment workflow today. The production VPS already exists, so the active path is Ansible bootstrap plus GitHub Actions deploy.

## Host hardening baseline

The bootstrap playbook now enforces these controls on the VPS:

- SSH key authentication only
- `PasswordAuthentication no`
- `PermitRootLogin no`
- `fail2ban` enabled for `sshd`
- `ufw` enabled with only `22/tcp`, `80/tcp`, and `443/tcp` allowed

The first bootstrap against a fresh host must still connect as `root` so Ansible can create the `carlos` admin user and copy the initial authorized keys into place before root login is disabled.

## Phase order

1. Run `make bootstrap` so the bootstrap wrapper resolves the production host and SSH material from Infisical.
2. Configure machine identity trust in Infisical Cloud for GitHub OIDC and operator access.
3. Store runtime secrets in Infisical Cloud.
4. Trigger `.github/workflows/deploy-production.yml` or render runtime files manually and run `deploy-core.yml`.

## Commands

Bootstrap the host for the first time:

```bash
make bootstrap
```

After bootstrap, routine operations should use the hardened `carlos` user.

Re-run bootstrap or apply security changes later:

```bash
make bootstrap
```

Deploy the full stack manually from an operator workstation:

```bash
./ops/scripts/fetch_infisical_cloud.py connection-ssh --out /tmp/connection.env
set -a
. /tmp/connection.env
set +a
./ops/scripts/fetch_infisical_cloud.py runtime-env --out /tmp/core.env
./ops/scripts/fetch_infisical_cloud.py seaweed-s3 --out /tmp/seaweed-s3.json
RUNTIME_ENV_SOURCE_FILE=/tmp/core.env \
RUNTIME_SEAWEED_S3_SOURCE_FILE=/tmp/seaweed-s3.json \
ansible-playbook \
  -i <(cat <<EOF
all:
  children:
    vps:
      hosts:
        production:
          ansible_host: ${PROD_HOST}
          ansible_user: ${PROD_SSH_USER}
          ansible_become: true
EOF
) \
  --private-key <(printf '%s\n' "${PROD_SSH_PRIVATE_KEY}") \
  ansible/runtime/playbooks/deploy-core.yml
```

## GitHub Actions production deploy

The repository includes a manual workflow at `.github/workflows/deploy-production.yml` that:

- `workflow_dispatch`
- targets the GitHub `production` environment
- requests a GitHub OIDC token with `id-token: write`
- authenticates to Infisical using machine identity OIDC auth
- fetches runtime deploy secrets only for the active job
- stages runtime files on the runner and then calls the deploy playbook

Configure these GitHub `production` environment variables:

- `INFISICAL_API_URL`
- `INFISICAL_PROJECT_SLUG`
- `INFISICAL_ENV_SLUG`

The workflow now commits the GitHub OIDC identity metadata directly in YAML:

- `identity-id`: `0a100e5d-1422-437e-b447-e032f32403fa`
- `oidc-audience`: `repo:CarlosGebard/infra-victus-vps:ref:refs/heads/main`

The matching GitHub OIDC subject expected by Infisical is:

- `repo:CarlosGebard/infra-victus-vps`

That subject requires GitHub OIDC subject customization to already be configured on the repository or organization side.

If you want approval gates, configure required reviewers on the GitHub `production` environment.

## Required secret material in Infisical

The workflow expects these secret values to exist in Infisical:

- `/connection`
  - `PROD_HOST`
  - `PROD_SSH_USER`
  - `PROD_SSH_PRIVATE_KEY`
  - `PROD_SSH_KNOWN_HOSTS`
- `/runtime`
  - `COUCHDB_PASSWORD`
  - `GRAFANA_ADMIN_PASSWORD`
  - `SEAWEED_S3_ACCESS_KEY`
  - `SEAWEED_S3_SECRET_KEY`
  - optional: `COUCHDB_USER`
  - optional: `GRAFANA_ADMIN_USER`

GitHub Actions fetches these values at runtime and writes:

- `/srv/secrets/runtime/core.env`
- `/srv/secrets/runtime/seaweed-s3.json`

For operator-driven manual deploys, use `ops/scripts/fetch_infisical_cloud.py` with local Universal Auth credentials to render the runtime files before invoking Ansible.

The required Infisical Cloud folder layout is:

- `/bootstrap` for host bootstrap operator inputs such as `TAILSCALE_AUTH_KEY`
- `/connection` for SSH host, user, key, and known-hosts material
- `/runtime` for runtime and deploy secrets used by GitHub Actions and manual deploys

SeaweedFS belongs only to the runtime stack and is not part of host bootstrap.

## Observability baseline

The core deploy also manages:

- Grafana Alloy on the host as a `systemd` service
- Loki in Docker Compose
- Prometheus in Docker Compose
- Grafana in Docker Compose

Grafana credentials must be set through the runtime env file staged onto the host:

- `GRAFANA_ADMIN_PASSWORD`

See `docs/runbooks/observability-stack.md` for the directory layout and exposed ports.

## Notes on network exposure

- Hetzner firewall compatibility is preserved through:
  - `hcloud_token`
  - `ssh_key_names`
  - `ssh_allowed_cidrs`
  - `enable_public_http`
- Temporary `ssh_allowed_cidrs = ["0.0.0.0/0"]` is acceptable only with the hardened host controls above in place.

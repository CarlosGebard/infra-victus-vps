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
- authenticates to Infisical using `Infisical/secrets-action@v1.0.10`
- fetches deploy secrets from the Infisical root path for the active job
- ensures the base `/srv` directory layout exists before deploying the stack
- stages runtime files on the runner and then calls the deploy playbook

The workflow now commits the Infisical identity metadata directly in YAML:

- `identity-id`: `0a100e5d-1422-437e-b447-e032f32403fa`
- `project-slug`: `victus-main-server-qy-2z`
- `env-slug`: `prod`

If you want approval gates, configure required reviewers on the GitHub `production` environment.

If the deploy step fails after `docker compose up -d`, the workflow now collects:

- `docker compose ps -a`
- `docker compose logs --no-color --tail=200 nginx couchdb seaweedfs loki prometheus grafana`

That diagnostic block runs on the server over SSH and is intended to expose container startup and permission issues directly in the GitHub Actions logs.

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

`core.env` remains root-only on the host. `seaweed-s3.json` is staged as read-only with `root:<seaweed gid>` ownership and group-read permissions so the SeaweedFS container user can consume the bind-mounted S3 IAM configuration without making the file world-readable.

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

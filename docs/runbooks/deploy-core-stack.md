# Deploy Core Stack

## Purpose

Deploy the full core services stack after the host is hardened and Infisical is already serving as the runtime source of truth for deploy secrets.

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

1. Run `ansible/playbooks/bootstrap.yml` against the fresh host.
2. Run `ansible/playbooks/deploy-infisical-bootstrap.yml` with the minimal Infisical bootstrap env file.
3. Configure machine identity trust in Infisical for GitHub OIDC.
4. Store deploy/runtime secrets in Infisical.
5. Trigger `.github/workflows/deploy-production.yml`.

## Commands

Bootstrap the host for the first time:

```bash
ansible-playbook -i ansible/inventories/production/hosts.yml -u root ansible/playbooks/bootstrap.yml
```

After bootstrap, routine operations should use the hardened `carlos` user.

Re-run bootstrap or apply security changes later:

```bash
ansible-playbook -i ansible/inventories/production/hosts.yml ansible/playbooks/bootstrap.yml
```

Deploy the Infisical bootstrap stack manually from an operator workstation:

```bash
ansible-playbook -i ansible/inventories/production/hosts.yml ansible/playbooks/deploy-infisical-bootstrap.yml
```

Deploy the full stack manually from an operator workstation:

```bash
ansible-playbook -i ansible/inventories/production/hosts.yml ansible/playbooks/deploy-core.yml
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

- `INFISICAL_DOMAIN`
- `INFISICAL_IDENTITY_ID`
- `INFISICAL_PROJECT_SLUG`
- `INFISICAL_ENV_SLUG`

The `identity-id` is not a secret and is safe to store as a variable or commit directly in workflow YAML.

If you want approval gates, configure required reviewers on the GitHub `production` environment.

## Required secret material in Infisical

The workflow expects at least these secret values to exist in Infisical:

- `PROD_HOST`
- `PROD_SSH_USER`
- `PROD_SSH_PRIVATE_KEY`
- `PROD_SSH_KNOWN_HOSTS`
- `COUCHDB_PASSWORD`
- `POSTGRES_PASSWORD`
- `INFISICAL_REDIS_PASSWORD`
- `INFISICAL_ENCRYPTION_KEY`
- `INFISICAL_AUTH_SECRET`
- `GRAFANA_ADMIN_PASSWORD`
- `SEAWEED_S3_ACCESS_KEY`
- `SEAWEED_S3_SECRET_KEY`

GitHub Actions fetches these values at runtime and writes:

- `/srv/secrets/runtime/core.env`
- `/srv/secrets/runtime/seaweed-s3.json`

The full deploy stops the Infisical bootstrap stack before bringing up the core stack so the Infisical data directories are not mounted by two compose projects at once.

SeaweedFS belongs only to phase 2. It is not part of the Infisical bootstrap stack.

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

# Deploy Core Stack

## Purpose

Deploy the core services stack onto the provisioned VPS after host hardening is in place.

## Host hardening baseline

The bootstrap playbook now enforces these controls on the VPS:

- SSH key authentication only
- `PasswordAuthentication no`
- `PermitRootLogin no`
- `fail2ban` enabled for `sshd`
- `ufw` enabled with only `22/tcp`, `80/tcp`, and `443/tcp` allowed

The first bootstrap against a fresh host must still connect as `root` so Ansible can create the `deploy` admin user and copy the initial authorized keys into place before root login is disabled.

## Commands

Bootstrap the host for the first time:

```bash
ansible-playbook -i ansible/inventories/production/hosts.yml -u root ansible/playbooks/bootstrap.yml
```

After bootstrap, the inventory defaults to the hardened `deploy` user.

Re-run bootstrap or apply security changes later:

```bash
ansible-playbook -i ansible/inventories/production/hosts.yml ansible/playbooks/bootstrap.yml
```

Deploy the stack manually from an operator workstation:

```bash
ansible-playbook -i ansible/inventories/production/hosts.yml ansible/playbooks/deploy-core.yml
```

## GitHub Actions production deploy

The repository includes a manual workflow at `.github/workflows/deploy-production.yml` with:

- `workflow_dispatch`
- job-level `environment: production`
- SSH verification before the actual deploy playbook

Configure these environment secrets under `Settings -> Environments -> production`:

- `PROD_SSH_PRIVATE_KEY`
- `PROD_HOST`
- `PROD_SSH_USER`
- `PROD_SSH_KNOWN_HOSTS`

If you want approval gates, configure required reviewers on the GitHub `production` environment. The workflow is already wired to use that environment.

## Required secret material on the host

- `/srv/secrets/bootstrap/core.env`
- `/srv/secrets/bootstrap/seaweed-s3.json`

These files stay only on the VPS. Do not copy them into GitHub Actions or commit them to this repository.

## Notes on network exposure

- Hetzner firewall compatibility is preserved through:
  - `hcloud_token`
  - `ssh_key_names`
  - `ssh_allowed_cidrs`
  - `enable_public_http`
- Temporary `ssh_allowed_cidrs = ["0.0.0.0/0"]` is acceptable only with the hardened host controls above in place.

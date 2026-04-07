# Private Bootstrap Runbook

## Purpose

Bootstrap the single-node VPS in private-only mode where SSH is public and application access happens through SSH tunnels.

## Prerequisites

- Hetzner Cloud account and API token
- SSH key uploaded to Hetzner Cloud
- Local SSH config entry named `hetzner-main`
- Local `terraform`, `ansible`, and `docker` tooling installed as needed

## Workflow

1. Copy `terraform/environments/production/terraform.tfvars.example` to a local untracked `terraform.tfvars`.
2. Set `hcloud_token`, `ssh_key_names`, and your restricted `ssh_allowed_cidrs`.
3. Run Terraform from `terraform/environments/production/`.
4. Confirm the fresh host is reachable through `ssh root@<host>`.
5. Run the Ansible bootstrap playbook. This baseline configures:
   - admin user `carlos`
   - key-only SSH
   - `ufw`
   - `fail2ban`
   - `unattended-upgrades`
   - Docker CE from the official Docker repository
   - `2G` swap at `/swapfile`
   - `/srv/*` directory layout
6. Reconnect using the admin user and confirm `sudo` works.
7. Create `/srv/secrets/bootstrap/core.env` on the server from `compose/env/core.env.example` or the narrower `compose/env/infisical-bootstrap.env.example`.
8. Create `/srv/secrets/bootstrap/seaweed-s3.json` on the server with production credentials if SeaweedFS is part of the current rollout.
9. Run the Ansible deploy playbook.
10. Open an SSH tunnel to NGINX:

```bash
ssh -L 8080:127.0.0.1:8080 hetzner-main
```

11. Access the services through `http://127.0.0.1:8080`.

## Notes

- Treat the bootstrap secret files as temporary inputs until Infisical becomes the operational source for managed secrets.
- Rotate all credentials inherited from the legacy stack.
- After the first successful bootstrap, routine operations should use the admin user instead of `root`.

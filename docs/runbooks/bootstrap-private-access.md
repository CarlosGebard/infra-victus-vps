# Private Bootstrap Runbook

## Purpose

Bootstrap the single-node VPS in two private phases:

1. harden the host and join Tailscale;
2. start only the self-hosted Infisical control plane required to move the rest of the secrets out of ad hoc bootstrap files.

## Prerequisites

- Local SSH config entry named `hetzner-main`
- Local `ansible`, `docker`, `sops`, and `age` tooling installed as needed
- `TAILSCALE_AUTH_KEY` available in the local shell for the first bootstrap run

## Current mode

Terraform is retained in this repository for reproducibility and future rebuilds, but it is not part of the current bootstrap workflow because the production VPS already exists.

## Workflow

1. Confirm the existing host is reachable through `ssh root@<host>`.
2. Run the Ansible bootstrap playbook with `TAILSCALE_AUTH_KEY` in the environment. This baseline configures:
   - admin user `carlos`
   - key-only SSH
   - `ufw`
   - `fail2ban`
   - `unattended-upgrades`
   - Docker CE from the official Docker repository
   - `2G` swap at `/swapfile`
   - `/srv/*` directory layout
3. Reconnect using the admin user and confirm `sudo` works.
4. Decrypt `secrets/bootstrap/infisical.enc.env` and install it as `/srv/secrets/bootstrap/infisical.env` on the server.
5. Run the Infisical bootstrap playbook:

```bash
ansible-playbook -i ansible/inventories/production/hosts.yml ansible/playbooks/deploy-infisical-bootstrap.yml
```

6. Open an SSH tunnel to the private Infisical bootstrap endpoint:

```bash
ssh -L 18080:127.0.0.1:18080 hetzner-main
```

7. Access Infisical through `http://127.0.0.1:18080`.
8. Inside Infisical:
   - create the production project/environment
   - load the runtime deploy secrets
   - create a GitHub OIDC machine identity constrained to the repository and `production` environment
9. Create a dedicated deploy SSH keypair, add the public key to `/home/carlos/.ssh/authorized_keys`, and store the private key in Infisical.
10. Move all non-bootstrap runtime values into Infisical before enabling the GitHub Actions deploy workflow.

## Notes

- Treat `/srv/secrets/bootstrap/infisical.env` as temporary bootstrap material only.
- Rotate all credentials inherited from the legacy stack.
- After the first successful bootstrap, routine operations should use the admin user instead of `root`.

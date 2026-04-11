# Private Bootstrap Runbook

## Purpose

Bootstrap the single-node VPS in two private phases:

1. harden the host;
2. join Tailscale for private operator access.

## Prerequisites

- Local `ansible` tooling installed
- Local Infisical operator credentials available through `.secrets/infisical/bootstrap.env` or `INFISICAL_OPERATOR_ENV_FILE`
- The active operator config points bootstrap, connection, and runtime secret-path lookups at `/`
- Terraform is retained in this repository for reproducibility and future rebuilds, but it is not part of the current bootstrap workflow because the production VPS already exists.

## Workflow

1. Confirm Infisical contains the bootstrap SSH connection material:
   - `/`: `PROD_HOST`, `PROD_SSH_PRIVATE_KEY`, `PROD_SSH_KNOWN_HOSTS`, `TAILSCALE_AUTH_KEY`
2. Run the bootstrap wrapper, which fetches the required secrets from Infisical, validates SSH connectivity as `root`, and executes Ansible with ephemeral local files:

```bash
make bootstrap
```

For a more verbose debugging run:

```bash
make bootstrap-debug
```

3. The bootstrap baseline configures:
   - admin user `carlos`
   - key-only SSH
   - `ufw`
   - `fail2ban`
   - `unattended-upgrades`
   - Docker CE from the official Docker repository
   - `2G` swap at `/swapfile`
   - `/srv/*` directory layout
4. Reconnect using the admin user and confirm `sudo` works.
5. Confirm the node joined Tailscale successfully and is reachable through the expected tailnet identity.
6. Use the hardened `carlos` user for routine post-bootstrap operations through the runtime deploy flow. The bootstrap wrapper itself continues to default to `root`.
7. Create or verify the Infisical Cloud project, environment, and machine identities used for runtime deploy secret delivery.
8. Move all deploy-time secret material into Infisical Cloud before enabling the GitHub Actions deploy workflow.

## Notes

- Rotate all credentials inherited from the legacy stack.
- The bootstrap wrapper connects as `root` by default unless you override it explicitly with `--ssh-user`.
- `PROD_SSH_USER` is still part of the connection/runtime secret set, but it is no longer required for the active bootstrap flow.

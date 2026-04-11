# Scripts

Helper scripts should live here.

Scripts should be idempotent where possible and must not embed secrets.

Current scripts:

- `fetch_infisical_cloud.py` authenticates to Infisical Cloud with Universal Auth, auto-loads operator credentials from `.secrets/infisical/bootstrap.env` when present, and renders bootstrap, connection, or runtime secret files for operator-driven flows
- `bootstrap_via_infisical.py` is the active bootstrap entry point; it fetches `PROD_HOST`, `PROD_SSH_PRIVATE_KEY`, `PROD_SSH_KNOWN_HOSTS`, and `TAILSCALE_AUTH_KEY`, runs an SSH preflight as `root`, writes ephemeral local trust files, and runs the bootstrap playbook against the target host
- `seed_infisical_cloud.py` creates the target Infisical folders when needed and uploads bootstrap, connection, or runtime dotenv files in bulk from local files
- `push_infisical_project_secrets.py` uploads one dotenv file to the configured Infisical project path, which is useful when you want a single source file for all project secrets

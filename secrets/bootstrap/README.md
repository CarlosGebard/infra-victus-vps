# Bootstrap Secrets

This directory is the intended home for SOPS-encrypted bootstrap material.

Target encrypted files:

- `infisical.enc.env`

This directory is phase-1 only. It should contain only the minimum bootstrap material required to start Infisical.

Do not commit plaintext runtime secrets.

Recommended workflow:

1. Copy the example file you need.
2. Fill in real values locally.
3. Encrypt it with `sops`.
4. Commit only the encrypted file.

Example commands:

```bash
cp secrets/bootstrap/infisical.env.example /tmp/infisical.env
sops --encrypt --input-type dotenv --output-type dotenv /tmp/infisical.env > secrets/bootstrap/infisical.enc.env
rm /tmp/infisical.env
```

Decrypt locally when needed:

```bash
sops --decrypt --input-type dotenv --output-type dotenv secrets/bootstrap/infisical.enc.env
```

Install on the VPS from the encrypted file:

```bash
sops --decrypt --input-type dotenv --output-type dotenv secrets/bootstrap/infisical.enc.env | \
ssh hetzner-main 'sudo install -d -m 700 /srv/secrets/bootstrap && sudo tee /srv/secrets/bootstrap/infisical.env >/dev/null && sudo chmod 600 /srv/secrets/bootstrap/infisical.env'
```

Do not use this directory for phase-2 runtime deploy secrets or SeaweedFS credentials. Those should live in Infisical and be fetched by GitHub Actions through OIDC.

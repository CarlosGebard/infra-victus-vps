# Infisical Bootstrap Example

## Purpose

Show the intended phase-1 bootstrap model for this repository without storing any real secret values in Git.

The bootstrap exists only to bring up Infisical and the services it depends on. After Infisical is running, runtime deploy secrets should be managed from there instead of staying in bootstrap files.

## Target Bootstrap Scope

The bootstrap should include only what Infisical needs to start:

- `POSTGRES_PASSWORD`
- `INFISICAL_REDIS_PASSWORD`
- `INFISICAL_ENCRYPTION_KEY`
- `INFISICAL_AUTH_SECRET`

These values are shown as placeholders in:

- `secrets/bootstrap/infisical.env.example`
- `secrets/bootstrap/infisical.enc.env`

## What Should Not Live In Bootstrap Long-Term

These values should live in Infisical-managed runtime secrets instead of bootstrap:

- deploy SSH material for GitHub Actions
- host connection values such as `PROD_HOST` and `PROD_SSH_USER`
- CouchDB credentials
- SeaweedFS S3 credentials
- future application API keys
- service-to-service secrets not required to start Infisical itself

## Example Implementation

1. Create the bootstrap directory on the VPS:

```bash
sudo install -d -m 700 /srv/secrets /srv/secrets/bootstrap
```

2. Create the encrypted bootstrap env file from the example:

```bash
cp secrets/bootstrap/infisical.env.example /tmp/infisical.env
$EDITOR /tmp/infisical.env
sops --encrypt --input-type dotenv --output-type dotenv /tmp/infisical.env > secrets/bootstrap/infisical.enc.env
rm /tmp/infisical.env
```

3. Install the decrypted file on the VPS:

```bash
sops --decrypt --input-type dotenv --output-type dotenv secrets/bootstrap/infisical.enc.env | \
ssh hetzner-main 'sudo install -d -m 700 /srv/secrets/bootstrap && sudo tee /srv/secrets/bootstrap/infisical.env >/dev/null && sudo chmod 600 /srv/secrets/bootstrap/infisical.env'
```

4. Start the minimal Infisical stack with `ansible/playbooks/deploy-infisical-bootstrap.yml`.

5. Store the rest of the infrastructure and deployment secrets inside Infisical.

6. Reduce or retire bootstrap material once Infisical becomes the source of truth.

## Notes

- This file documents the intended pattern.
- It does not place any real key or password in the repository.
- The current stack may still use broader bootstrap inputs during transition; this document captures the target direction.

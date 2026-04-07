# Infisical Bootstrap Example

## Purpose

Show the intended bootstrap model for this repository without storing any real secret values in Git.

The bootstrap exists only to bring up Infisical and the services it depends on. After Infisical is running, application secrets should be managed from there instead of staying in bootstrap files.

## Target Bootstrap Scope

The bootstrap should include only what Infisical needs to start:

- `INFISICAL_SITE_URL`
- `INFISICAL_IMAGE`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `INFISICAL_REDIS_PASSWORD`
- `INFISICAL_ENCRYPTION_KEY`
- `INFISICAL_AUTH_SECRET`

These values are shown as placeholders in:

- `compose/env/infisical-bootstrap.env.example`

## What Should Not Live In Bootstrap Long-Term

These values should move out of bootstrap and into Infisical-managed secrets:

- CouchDB credentials
- SeaweedFS S3 credentials
- future application API keys
- service-to-service secrets not required to start Infisical itself

## Example Implementation

1. Create the bootstrap directory on the VPS:

```bash
sudo install -d -m 700 /srv/secrets /srv/secrets/bootstrap
```

2. Create the bootstrap env file from the example:

```bash
sudo cp compose/env/infisical-bootstrap.env.example /srv/secrets/bootstrap/infisical-bootstrap.env
sudo chmod 600 /srv/secrets/bootstrap/infisical-bootstrap.env
```

3. Replace all placeholder values with real secrets.

4. Start the minimal Infisical stack.

5. Store the rest of the infrastructure and application secrets inside Infisical.

6. Reduce or retire bootstrap material once Infisical becomes the source of truth.

## Notes

- This file documents the intended pattern.
- It does not place any real key or password in the repository.
- The current stack may still use broader bootstrap inputs during transition; this document captures the target direction.

# Seed Infisical Cloud

## Purpose

Load the bootstrap, SSH connection, and runtime secrets into Infisical Cloud in bulk from local dotenv files.

Use split Infisical paths so GitHub Actions and operator workflows can fetch only the secrets they need.

## Layout

Operator credentials:

- Copy `.secrets/infisical/bootstrap.env.example` to `.secrets/infisical/bootstrap.env`
- Fill in the machine identity credentials and project metadata

Secret inventories:

- Create a local bootstrap dotenv file from `secrets/templates/infisical/bootstrap.env.example`
- Create a local connection dotenv file from `secrets/templates/infisical/connection.env.example`
- Create a local runtime dotenv file from `secrets/templates/infisical/runtime.env.example`

You can keep those files anywhere local. If you store them under `.secrets/`, they remain ignored by Git.

## Recommended paths in Infisical Cloud

- Bootstrap folder: `/bootstrap`
- Connection folder: `/connection`
- Runtime folder: `/runtime`

You can override those with:

- `INFISICAL_BOOTSTRAP_SECRET_PATH`
- `INFISICAL_CONNECTION_SECRET_PATH`
- `INFISICAL_RUNTIME_SECRET_PATH`

in `.secrets/infisical/bootstrap.env`.

## Commands

### Split mode: bootstrap, connection, and runtime files

```bash
./ops/scripts/seed_infisical_cloud.py bootstrap --bootstrap-file /path/to/bootstrap.env
```

Seed only SSH connection secrets:

```bash
./ops/scripts/seed_infisical_cloud.py connection --connection-file /path/to/connection.env
```

Seed only runtime secrets:

```bash
./ops/scripts/seed_infisical_cloud.py runtime --runtime-file /path/to/runtime.env
```

Seed all three in one run:

```bash
./ops/scripts/seed_infisical_cloud.py all \
  --bootstrap-file /path/to/bootstrap.env \
  --connection-file /path/to/connection.env \
  --runtime-file /path/to/runtime.env
```

## Fetch commands

Fetch bootstrap shell material for host bootstrap:

```bash
./ops/scripts/fetch_infisical_cloud.py bootstrap-shell --out /tmp/bootstrap.env
```

Fetch SSH connection material:

```bash
./ops/scripts/fetch_infisical_cloud.py connection-ssh --out /tmp/connection.env
```

Fetch runtime material for manual deploy:

```bash
./ops/scripts/fetch_infisical_cloud.py runtime-env --out /tmp/core.env
./ops/scripts/fetch_infisical_cloud.py seaweed-s3 --out /tmp/seaweed-s3.json
```

## Notes

- Keep bootstrap, connection, and runtime values in separate paths.
- The GitHub Actions deploy workflow now assumes `/connection` and `/runtime` exist and are readable by the OIDC-backed Infisical identity.

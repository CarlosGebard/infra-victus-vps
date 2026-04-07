# Infrastructure Validation Plan

## Purpose

Define the minimum validation suite this repository should run locally and in CI before infrastructure changes are considered safe.

## Validation Layers

### 1. Static Validation

- Terraform format: `terraform fmt -check -recursive`
- Terraform validation: `terraform validate`
- Ansible syntax: `ansible-playbook --syntax-check`
- Docker Compose render: `docker compose config`
- YAML linting once a linter is added

### 2. Security Validation

- Check that only SSH is open in the Hetzner firewall while `enable_public_http = false`
- Check that no Compose service except `nginx` binds a host port
- Check that bound `nginx` host port defaults to `127.0.0.1`
- Check that no secrets are committed into tracked env files
- Check that legacy credentials are not reused in active configs

### 3. Runtime Validation

- `nginx` health endpoint responds
- CouchDB `/_up` responds
- SeaweedFS master endpoint responds
- Infisical HTTP status endpoint responds
- PostgreSQL healthcheck passes
- Redis healthcheck passes

### 4. Persistence Validation

- Restart each stateful container and verify service health after restart
- Verify expected host paths exist under `/srv/data`
- Verify writes persist for CouchDB, SeaweedFS, PostgreSQL, and Redis append-only mode

### 5. Backup And Restore Validation

- Create a backup archive of `/srv/data/couchdb`
- Restore it into a clean target
- Verify database listing and document access
- Repeat for the broader `/srv/data` backup process once implemented

### 6. Network Validation

- Confirm firewall blocks `80` and `443` when private mode is active
- Confirm direct remote access to CouchDB, SeaweedFS, PostgreSQL, and Redis is impossible
- Confirm SSH tunnel access to `127.0.0.1:8080` works as expected

## Suggested Execution Stages

### Developer workstation

- Compose render
- Static file checks
- Basic secret hygiene review

### CI

- Terraform format and validate
- Ansible syntax check
- Compose render
- Policy checks for port exposure and required directories

### Pre-production on VPS

- Host bootstrap
- Stack deployment
- Health checks
- Persistence checks
- Backup and restore drill

## Immediate Repo Tests To Add

1. A single script that runs all available static validations.
2. A policy check that fails if a non-NGINX service exposes host ports.
3. A restore drill script for CouchDB once the target host is available.
4. A firewall expectation check for the Terraform production environment.

## Current Status

Today this repository already has:

- Compose render validation through `ops/checks/validate-core.sh`

Still missing in this environment because local tools are unavailable or not yet implemented:

- Terraform format and validate execution
- Ansible syntax checks
- Policy assertions beyond Compose rendering
- Restore drill automation

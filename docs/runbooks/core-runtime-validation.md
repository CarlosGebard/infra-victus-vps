# Core Runtime Validation

## Purpose

Provide an executable post-deploy validation path for the active VPS runtime after the core stack is deployed.

## What it checks

- all expected core services are running in Docker Compose
- all core containers report `healthy`
- `nginx` responds on `/healthz`
- routed application endpoints respond through the local gateway
- `loki`, `prometheus`, and `grafana` answer on their localhost ports
- PostgreSQL and Redis answer from inside their containers

## Command

```bash
ansible-playbook -i ansible/inventories/production/hosts.yml ansible/playbooks/validate-core-runtime.yml
```

## Expected inputs

- the core stack has already been deployed
- `/srv/secrets/runtime/core.env` exists on the VPS
- the local inventory points to the production host

## Failure handling

If this playbook fails:

1. inspect the failing task output in Ansible
2. inspect `docker compose ps` on the host
3. inspect container logs for the failing service
4. validate `/srv/secrets/runtime/core.env`
5. verify host-local access on `127.0.0.1`

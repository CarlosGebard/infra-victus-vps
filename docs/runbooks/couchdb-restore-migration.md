# CouchDB Restore And Migration

## Purpose

Restore the legacy CouchDB snapshot into the new private-access stack with a controlled, testable migration path.

## Source Material

- Legacy compose reference: `legacy/couchdb-backup/docker-compose.yml`
- Legacy config: `legacy/couchdb-backup/couchdb/config/`
- Legacy data snapshot: `legacy/couchdb-backup/couchdb/data/`

## Assumptions

- Target runtime is the new stack in `compose/stacks/core/docker-compose.yml`.
- CouchDB remains single-node in the target environment.
- Legacy credentials are considered compromised and must be rotated.
- Migration happens with traffic stopped for the legacy source.

## Strategy

Use a file-level cold restore first because the available legacy asset is a full CouchDB data directory, not a logical export.

After the cold restore validates successfully, rotate credentials and verify application access paths before considering the migration complete.

## Migration Phases

### 1. Pre-flight

1. Deploy the new stack without production traffic.
2. Confirm the target CouchDB container is healthy.
3. Stop any writers against the legacy CouchDB instance.
4. Create an immutable copy of `legacy/couchdb-backup/` before using it.
5. Record the current target directories on the VPS:
   - `/srv/data/couchdb/data`
   - `/srv/apps/core/couchdb/local.d`

### 2. Safety Backup

1. Backup the current target CouchDB data directory on the VPS.
2. Store the backup under `/srv/backups/couchdb/` with a timestamp.
3. Verify the backup archive exists and is readable.

### 3. Prepare Restore Input

1. Review `legacy/couchdb-backup/couchdb/config/local.ini`.
2. Keep only the settings that still match the new deployment intent:
   - single node mode
   - request sizing
   - CORS policy
3. Do not reuse `docker.ini` admin hashes directly unless you explicitly want to preserve that admin.
4. Define the new `COUCHDB_USER` and `COUCHDB_PASSWORD` in `/srv/secrets/bootstrap/core.env`.

## 4. Cold Restore

1. Stop the target CouchDB container:

```bash
docker compose --env-file /srv/secrets/bootstrap/core.env -f /srv/apps/core/docker-compose.yml stop couchdb
```

2. Remove current target data contents only after confirming the backup from phase 2 exists.
3. Copy the legacy `couchdb/data/` contents into `/srv/data/couchdb/data/`.
4. Set ownership to match the container runtime user expected by the CouchDB image.
5. Keep the target config from the new stack under `/srv/apps/core/couchdb/local.d/local.ini`.
6. Start CouchDB again.

## 5. Post-Restore Validation

Validate these items in order:

1. `/_up` returns healthy through the internal service or proxied path.
2. `/_all_dbs` includes `_users`, `_replicator`, and `obsidian`.
3. Sample document reads from the restored application database work.
4. New writes succeed.
5. Authentication works with the new credentials.
6. Obsidian sync or the consuming application can connect read/write.

## 6. Credential Rotation

1. Replace inherited credentials from the legacy stack.
2. If the old admin user must remain temporarily, add a second admin and then remove the old one.
3. Update consuming clients to the new secret values.

## 7. Cutover

1. Point the client workflow to the new stack endpoint through the SSH tunnel or future public ingress.
2. Observe logs and replication-related databases for anomalies.
3. Keep the legacy snapshot unchanged until the migration has passed a soak period.

## Rollback

Rollback is valid only before destructive changes to the source snapshot.

1. Stop target CouchDB.
2. Restore the backup created in phase 2 into `/srv/data/couchdb/data/`.
3. Start target CouchDB.
4. Re-run post-restore validation.

## Risks

- File-level restore can carry forward node-specific metadata.
- Ownership or permission mismatches can prevent startup.
- Reusing legacy admin material increases security risk.
- Large attachments may need extra validation because request size settings were customized.

## Success Criteria

- CouchDB starts cleanly in the new stack.
- The expected databases exist.
- Read and write tests pass.
- New credentials are active.
- The restored state survives a container restart.

---
name: postgres-backup
description: Create, verify, copy, restore, or schedule PostgreSQL/PostGIS backups for the postgis-template Compose project.
---

# PostgreSQL backups

Identify the project directory, Compose service `db`, database `geodata`, and active Docker context before acting. Query the server and installed extensions without printing resolved Compose configuration, passwords, or role dumps. Use the running server's PostgreSQL tools for dumps.

## Create or copy a backup

Run [scripts/backup.py](scripts/backup.py) with Python 3.11+ and `--project-dir <project-root>`. It publishes `.backup/<UTC-timestamp>-<id>/` containing `geodata.dump` (custom format), `globals.sql` (cluster roles and tablespaces), and `manifest.json` (SHA-256). A completed bundle has passed `pg_restore --list`. Report its path, date, and verification level.

For an existing external disk or mounted network share, add `--external-dir <path>`. Confirm the destination belongs to the requested storage. Both copies are published separately, so an external failure leaves a verified local bundle and returns an error. For object storage, use the provider CLI or an existing `rclone` remote, copy the whole bundle to a unique prefix, and verify the remote checksums or download and verify the bundle. Report external success only after verification. Keep database data and role hashes private on both destinations.

This operation backs up `geodata` and cluster globals using separate snapshots. Avoid role or tablespace changes during a backup that must preserve ownership consistently. For other databases, create separate full dumps and inventory them. Preserve required PostgreSQL settings, extension versions, and deployment configuration separately. Logical dumps recover to the dump snapshot. For point-in-time recovery, use a physical backup and WAL archiving workflow.

## Restore

For a restore, a recovery drill, or a verified recovery point before an upgrade, read [references/restore.md](references/restore.md). Restore into a fresh database or isolated instance and validate the data before an authorized switch.

## Schedule

For cron on Linux or Task Scheduler on Windows, read [references/schedule.md](references/schedule.md) and register the job on the requested host for the approved schedule. The job invokes the script directly. It needs no running Codex session.

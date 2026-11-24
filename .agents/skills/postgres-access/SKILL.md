---
name: postgres-access
description: Provision personal QGIS readers and explicitly authorized PostgreSQL superusers on a local postgis-template deployment. Scope and verify access to geodata.
---

# PostgreSQL access

1. Work from the intended site's checkout. Verify the effective Docker endpoint, Compose project, running service `db`, and its PostgreSQL data mount. Connect with the site's authorized administrator and confirm the database `geodata`, its owner, and the cluster identity. Resolve any mismatch before changing roles.
2. Confirm the requested login and its purpose. For a reader, identify the exact schemas or fully qualified tables and any explicitly requested grants for future objects. Grant directly for one reader. With multiple readers sharing the same scope, reuse a verified `NOLOGIN` reader role or create one for that scope. Treat cluster `SUPERUSER` as a separate, explicitly authorized operation. Keep `postgres` as the owner of `geodata`.
3. Read [the local provisioning procedure](references/provision.md) for role and scope checks, transaction commands, and separate login verification. Complete the operation only after checking the effective access and authentication from a new connection.

Perform site account operations locally. Keep usernames, grants, and results for individual accounts on the site, with no GitHub calls or tickets. Set the password through the local masked `psql` prompt and keep it in the site's credential store. Keep passwords and SCRAM verifiers out of chat, tool arguments, logs, and Git.

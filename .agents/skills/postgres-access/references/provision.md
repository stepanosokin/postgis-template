# Local provisioning

## Preflight

Use the site's administrator connection to `geodata`. For the template this is `docker compose exec db psql -X -U postgres -d geodata`. Check `current_database()` and `current_user`. Read the cluster identifier with `SELECT system_identifier FROM pg_control_system();` and confirm `pg_get_userbyid(datdba)` for `geodata` in `pg_database` is `postgres`. Use the verified Compose selector on every command when the project uses overrides.

Inspect the requested login and any reader role in `pg_roles` and `pg_auth_members`. A personal login script requires a new role name. If the name already exists, verify it against the request and report its state locally. Resolve any mismatch separately before altering the existing account or resetting credentials.

For a reader, inspect each requested schema and relation with `\dn+`, `\dp`, and `\ddp`. Check the applicable `PUBLIC` grants, owners, row-level security policies, view definitions, and callable `SECURITY DEFINER` routines that could expand the approved read scope or allow writes. When replicating a reader's access, check for policies that distinguish individual logins and agree the required row visibility. Treat expected site-wide access, such as PostGIS metadata or temporary tables, as an explicit baseline. Resolve any access beyond the approved scope before enabling the account. Changes to shared site policy require their own authorization.

For reuse, verify the group's `NOLOGIN` status, attributes, transitive role memberships, ownership, current and default grants, and existing members. Check that the group conveys exactly the requested read scope. Join the group without altering its grants when adding a reader. When forming a new group for existing readers, apply changes to only the agreed accounts and verify each affected account before removing any redundant direct grants.

Before setting a password, verify a local masked terminal, and check site audit, tracing, and query-statistics settings for credential capture. The login script requires built-in statement logging and sampling to be off for the session. It temporarily suppresses logging the text of a failed password statement. Use a site-approved credential session and protected local credential storage and handoff.

## Run a transaction

The [login script](../scripts/create-login.sql) and [reader grants script](../scripts/grant-reader.sql) require a transaction and stop on error. From the checkout, create a private temporary directory in the container using `docker compose exec -T db mktemp -d /tmp/postgres-access.XXXXXX`. Use its exact path in place of `SESSION_DIR` and copy the required scripts with `docker compose cp`. Remove the copied files and empty directory after the operation.

For one reader with a table grant, replace the example names and run the following locally. The operator enters and confirms the new password at the masked prompt. Use one transaction for the login and all grants.

```sh
docker compose exec db psql -X -U postgres -d geodata -1 -v ON_ERROR_STOP=1 -v login=reader_example -v reader=reader_example -v schema=maps -v relation=roads -f SESSION_DIR/create-login.sql -f SESSION_DIR/grant-reader.sql
```

Omit `relation` for an approved whole schema. For multiple targets or to inspect effective grants before committing, use an interactive `psql -X -v ON_ERROR_STOP=1` transaction. Run `BEGIN`, set `login` and `reader` using `\set`, and run `\i SESSION_DIR/create-login.sql` once. Set `schema` and any `relation` for each target and run `\i SESSION_DIR/grant-reader.sql`. The script clears its scope and membership parameters after each successful call. Use the target role as the explicit first argument to the privilege inquiry functions below to check effective access before `COMMIT`. On error or unexpected access, roll back and use a fresh session for any retry.

For a newly approved shared scope, create the group with `CREATE ROLE group_name NOLOGIN` in the transaction. Set `reader` to the group name and apply approved object grants using the same grants script. For an existing group with verified matching access, run just the login and membership steps.

```sh
docker compose exec db psql -X -U postgres -d geodata -1 -v ON_ERROR_STOP=1 -v login=reader_example -v reader=shared_maps -v member=reader_example -f SESSION_DIR/create-login.sql -f SESSION_DIR/grant-reader.sql
```

The `member` branch adds membership with inheritance and without `SET ROLE` or delegation. To add several logins in one transaction, repeat the login and membership steps for each new login with its own password. Set `creator` only for an approved schema-wide grant covering future tables. Run the scope step once per creating role and schema, because PostgreSQL applies defaults for the role that actually creates the object. For access to a named table, leave `creator` unset.

## Create and verify a personal administrator

After explicit authorization for this login to have cluster `SUPERUSER`, run the login script with `administrator=on`. This command only creates a new personal login. Use a local masked terminal to enter its password.

```sh
docker compose exec db psql -X -U postgres -d geodata -1 -v ON_ERROR_STOP=1 -v login=admin_example -v administrator=on -f SESSION_DIR/create-login.sql
```

Verify in a new authenticated TCP connection as the administrator using the same endpoint checks as for a reader. Check the session identity and `SHOW is_superuser`, then verify the owner of `geodata` is `postgres`. The `administrator` option applies to one login script invocation.

## Verify a reader

Use a new authenticated TCP connection as the reader. From the target client network use the site's published endpoint and TLS settings, including certificate verification where TLS is configured. For an isolated local probe, use `docker compose exec db psql -X -U reader_example -W -d 'host=db dbname=geodata require_auth=scram-sha-256'`. Use the verified login in place of `reader_example`. The Compose service address tests password authentication when localhost is trusted.

Confirm `current_database()`, `session_user` and `current_user`. Run representative `SELECT` queries against the agreed objects in `BEGIN READ ONLY` / `ROLLBACK`, including expected row visibility where RLS applies. Check effective privileges with `has_schema_privilege`, `has_database_privilege`, `has_table_privilege`, and `has_any_column_privilege`. Verify no access to other application tables, no DML or grant options on the allowed tables, and no `CREATE` on the database or any non-system schema, including `public`. Check sequence grants and inherited roles where present. For a shared role, verify `pg_has_role` reports inheritance and denies `SET` and `MEMBER WITH ADMIN OPTION`. Use privilege inquiries for denial checks on live data to avoid touching rows.

If access or authentication differs from the request, report the failure locally and hold delivery of the credentials. For a newly created login confirmed to be part of this operation, set `NOLOGIN` pending correction if access exceeds the approved scope. Account disabling applies to new connections. Roll back the transaction if it is still open. Leave shared roles and grants outside the operation alone.

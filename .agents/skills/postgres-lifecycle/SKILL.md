---
name: postgres-lifecycle
description: Deploy, start, stop, or remove the Docker Compose deployment of the postgis-template PostgreSQL/PostGIS project.
---

# PostgreSQL deployment lifecycle

Choose the requested operation below. Work from the intended checkout and confirm the effective Docker endpoint, Compose project name, and service `db`. Check active context and any CLI or environment overrides. When an existing container is present, check its Compose project labels and the bind mount source. If the target is ambiguous, resolve it before acting. Use Compose quiet validation or narrowly scoped inspection to keep credentials out of output.

## Initial deployment

1. Check the requirements and settings in the [README](../../../README.md), including the Linux Docker engine, Compose version and host port `5432`. Check that existing listeners are the intended service or that the port is free. Keep the configured port and leave other projects alone.
2. If `.secrets/.postgres` exists, reuse it. For a fresh data directory with no credentials file, generate a cryptographically random password locally, preferably 32 random bytes encoded as hex. Write the file exclusively so a concurrent creation cannot be overwritten. Use UTF-8 without BOM and the raw `POSTGRES_USER=postgres` and `POSTGRES_PASSWORD=...` format. Restrict filesystem access to the operator or service account. Keep the password out of console output, chat, command-line arguments and Git. If the intended data directory already contains a cluster and its credentials file is missing, recover its existing credentials before starting. Generating a new password would only affect the initialization of a new cluster.
3. Run `docker compose config --quiet`, then `docker compose up -d`. Wait for `db` to become healthy and query `geodata` with `psql -X -v ON_ERROR_STOP=1` to verify the five required extensions. Check the published port with `docker compose port db 5432`. If initialization fails, inspect the service logs without exposing credentials, report the cause, and preserve the data path. Report the endpoint, health and credentials file path.

## Start an existing deployment

Run `docker compose ps -a db`. For a stopped container, use `docker compose start db`. If the container was removed, verify that the existing bind mount source and credentials are in place, then use `docker compose up -d` to recreate it. If there is no existing cluster, use initial deployment. If the container is already running, check its status. Confirm healthy status and a connection to `geodata`. An existing database uses its saved data and credentials.

## Stop

Run `docker compose stop db` for the identified project. Verify that the service has stopped and its container is still present with `docker compose ps -a db`. If the container was already stopped or absent, report that state. The retained container can be started again.

## Remove the deployment

Run `docker compose down` for the identified project. This removes its Compose service containers and project network while preserving the checkout, `postgres` bind mount, `.secrets`, `.backup`, and images. Verify that the project containers and network are gone. If the deployment is already absent, report that state. Backup schedules remain in place and require a running deployment. Route an explicit request for data or file deletion to a separate task with its own confirmed scope.

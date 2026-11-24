---
name: postgres-upgrade
description: Check PostgreSQL releases, recommend whether to upgrade, or carry out an authorized PostgreSQL version upgrade for the postgis-template Compose project.
---

# PostgreSQL updates

Start with a read-only check. Identify the Compose project and Docker context. Read `docker/Dockerfile`, the relevant ADR and the live `server_version_num`, using `docker compose exec -T db psql -X -U <admin> -d geodata -Atc 'SHOW server_version_num'`. If the server is unavailable, report the configured image separately and mark the running version unknown. A floating image tag can point to a different release than the running container.

## Check and recommend

1. Compare the running version with the latest stable PostgreSQL release overall and the latest minor release in the same major branch. Use the [official version table](https://www.postgresql.org/support/versioning/) and the applicable release notes and [security advisories](https://www.postgresql.org/support/security/). Compare numeric version components and state each difference and its date. Note the branch's end-of-support date.
2. Verify that a released [PostGIS image](https://hub.docker.com/r/postgis/postgis) actually ships the candidate PostgreSQL version for `linux/amd64`. Check its manifest and image configuration or `postgres --version`, and verify the [PGDG H3 package](https://apt.postgresql.org/pub/repos/apt/pool/main/h/h3-pg/) and [PostGIS upgrade requirements](https://postgis.net/docs/postgis_administration.html). Check compatibility for every installed extension and any changed OS libraries, especially ICU, libc, GEOS, GDAL and PROJ. A PostgreSQL release can precede a usable image or an extension package.
3. Review relevant first-hand reports in [PostgreSQL bugs](https://www.postgresql.org/list/pgsql-bugs/), [Docker PostGIS issues](https://github.com/postgis/docker-postgis/issues) and [H3 issues](https://github.com/postgis/h3-pg/issues). Match reports to the candidate and relevant workload or platform. Separate reproducible problems and maintainer responses from anecdotes. Say when the available evidence is sparse. Cite dated sources and distinguish facts from your assessment.
4. Tell the administrator the current version, both available upstream versions, the usable image and extensions, compatibility findings, and a clear recommendation with reasons. Consider the latest compatible minor release independently of a major migration. Explain downtime and data migration costs when relevant.

## Carry out an upgrade

When the administrator asks you to execute the upgrade, read [references/upgrade.md](references/upgrade.md) and use [the backup skill](../postgres-backup/SKILL.md) for the verified recovery point. Execute the agreed upgrade through validation and handoff. Stop before live changes if there is no compatible candidate, restore proof, or authorized maintenance window.

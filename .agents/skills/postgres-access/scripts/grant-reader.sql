\set ON_ERROR_STOP on
SAVEPOINT postgres_access_reader;
SET LOCAL search_path = pg_catalog, pg_temp;

SELECT (:{?member} AND (:{?schema} OR :{?relation} OR :{?creator}))
       OR (:{?relation} AND :{?creator}) AS conflicting_options
\gset
\if :conflicting_options
    DO $$ BEGIN RAISE EXCEPTION 'Specify membership, table access, or schema access with optional creator'; END $$;
\endif

SELECT true AS grant_target_is_reader FROM pg_roles
WHERE current_database() = 'geodata' AND rolname = :'reader'
  AND NOT (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)
\gset

\if :{?member}
    SELECT true AS valid_membership
    FROM pg_roles AS reader_group, pg_roles AS personal_login
    WHERE reader_group.rolname = :'reader' AND NOT reader_group.rolcanlogin
      AND personal_login.rolname = :'member' AND personal_login.rolcanlogin
      AND NOT (personal_login.rolsuper OR personal_login.rolcreatedb OR personal_login.rolcreaterole
               OR personal_login.rolreplication OR personal_login.rolbypassrls)
    \gset

    GRANT :"reader" TO :"member" WITH INHERIT TRUE, SET FALSE, ADMIN FALSE;
\else
    GRANT CONNECT ON DATABASE geodata TO :"reader";
    GRANT USAGE ON SCHEMA :"schema" TO :"reader";
    \if :{?relation}
        GRANT SELECT ON TABLE :"schema".:"relation" TO :"reader";
    \else
        GRANT SELECT ON ALL TABLES IN SCHEMA :"schema" TO :"reader";
        \if :{?creator}
            ALTER DEFAULT PRIVILEGES FOR ROLE :"creator" IN SCHEMA :"schema"
                GRANT SELECT ON TABLES TO :"reader";
        \endif
    \endif
\endif

\unset member
\unset schema
\unset relation
\unset creator
RELEASE SAVEPOINT postgres_access_reader;

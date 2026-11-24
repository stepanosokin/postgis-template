\set ON_ERROR_STOP on
SAVEPOINT postgres_access_login;
SET LOCAL search_path = pg_catalog, pg_temp;

\set superuser_requested off
\if :{?administrator}
    SELECT :'administrator' = 'on' AS superuser_requested
    \gset
    \unset administrator
\endif

DO $$
BEGIN
    IF current_database() <> 'geodata' THEN
        RAISE EXCEPTION 'Connect to geodata before creating a login';
    END IF;
    IF current_setting('log_statement') <> 'none'
       OR current_setting('log_min_duration_statement') <> '-1'
       OR current_setting('log_min_duration_sample') <> '-1'
       OR current_setting('log_transaction_sample_rate')::numeric <> 0 THEN
        RAISE EXCEPTION 'Use a site-approved session that keeps credential statements out of logs';
    END IF;
END
$$;

CREATE ROLE :"login" NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
SET LOCAL password_encryption = 'scram-sha-256';
SELECT current_setting('log_min_error_statement') AS saved_error_statement_logging
\gset
SET LOCAL log_min_error_statement = 'panic';
\password :"login"
SELECT set_config('log_min_error_statement', :'saved_error_statement_logging', true) AS restored_error_statement_logging
\gset

SELECT true AS password_set FROM pg_authid
WHERE rolname = :'login' AND rolpassword LIKE 'SCRAM-SHA-256$%'
\gset

\if :superuser_requested
    ALTER ROLE :"login" SUPERUSER;
\endif
\unset superuser_requested

ALTER ROLE :"login" LOGIN;
RELEASE SAVEPOINT postgres_access_login;

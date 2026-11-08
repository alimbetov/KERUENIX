-- Admin-only role bootstrap script. Run separately from the application and Liquibase migration job.
-- NOLOGIN capability roles; provision individual LOGIN users/secrets outside Git.
DO $bootstrap$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'keruenix_app') THEN
        CREATE ROLE keruenix_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'keruenix_dispatcher') THEN
        CREATE ROLE keruenix_dispatcher NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
    END IF;
END
$bootstrap$;
GRANT USAGE ON SCHEMA platform TO keruenix_app, keruenix_dispatcher;
GRANT SELECT, INSERT ON platform.outbox_event TO keruenix_app;
GRANT SELECT, INSERT ON platform.inbox_receipt TO keruenix_app;
GRANT SELECT, INSERT ON platform.audit_fact TO keruenix_app;
-- The worker may claim/update events only inside a verified tenant-specific
-- transaction. Tenant-scoped claim and fencing exist; a production scheduler and broker adapter remain NOT built.
GRANT SELECT, UPDATE ON platform.outbox_event TO keruenix_dispatcher;
GRANT SELECT, INSERT ON platform.inbox_receipt TO keruenix_dispatcher;

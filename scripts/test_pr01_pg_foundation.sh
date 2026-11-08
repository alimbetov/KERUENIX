#!/usr/bin/env bash
# PR-01 partial qualification: PostgreSQL + PostGIS, transaction-local RLS,
# audit/outbox rollback and Inbox duplicate uniqueness. Not FOUND-01..12 complete.
set -Eeuo pipefail

: "${PGHOST:?PGHOST must be configured}"
: "${PGDATABASE:?PGDATABASE must be configured}"
: "${PGUSER:?admin PGUSER must be configured}"
: "${PGPASSWORD:?admin PGPASSWORD must be configured}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
psql -X -v ON_ERROR_STOP=1 -f "$ROOT/backend/src/main/resources/db/migration/V1__platform_outbox_inbox_rls.sql"
psql -X -v ON_ERROR_STOP=1 -f "$ROOT/backend/src/main/resources/db/migration/V2__outbox_claim_fencing.sql"
psql -X -v ON_ERROR_STOP=1 -f "$ROOT/backend/db/admin/bootstrap_roles.sql"

# CI-only principal. Never store real login credentials in a migration.
psql -X -v ON_ERROR_STOP=1 <<'SQL'
DO $bootstrap$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'keruenix_ci_login') THEN
        CREATE ROLE keruenix_ci_login LOGIN PASSWORD 'ci-only-isolated-database';
    END IF;
END
$bootstrap$;
GRANT keruenix_app TO keruenix_ci_login;
DO $assert$
BEGIN
    IF (SELECT rolsuper OR rolbypassrls OR rolcreatedb OR rolcreaterole
        FROM pg_roles WHERE rolname = 'keruenix_ci_login') THEN
        RAISE EXCEPTION 'CI runtime role is privileged';
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_class c JOIN pg_namespace n ON c.relnamespace=n.oid
        WHERE n.nspname = 'platform' AND c.relname IN
          ('outbox_event','inbox_receipt','audit_fact') AND
        (NOT c.relrowsecurity OR NOT c.relforcerowsecurity)
    ) THEN
        RAISE EXCEPTION 'platform table lacks FORCE RLS';
    END IF;
END
$assert$;
SQL

export PGUSER=keruenix_ci_login PGPASSWORD=ci-only-isolated-database
psql -X -v ON_ERROR_STOP=1 <<'SQL'
-- Without transaction-local verified context, runtime cannot see or write rows.
DO $assert$
BEGIN
    IF platform.current_tenant_id() IS NOT NULL THEN
        RAISE EXCEPTION 'tenant context leaked before first transaction';
    END IF;
    IF (SELECT count(*) FROM platform.outbox_event) <> 0 THEN
        RAISE EXCEPTION 'unscoped outbox read was permitted';
    END IF;
END
$assert$;

-- Insert permitted only for matching tenant in a transaction.
BEGIN;
SELECT set_config('keruenix.tenant_id', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', true);
INSERT INTO platform.outbox_event(
    event_id, tenant_id, event_type, aggregate_ref, payload_schema_version,
    payload, payload_sha256
) VALUES (
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'FoundationProbe', 'test-only:1', 1, '{"test":"A"}', repeat('a',64)
);
INSERT INTO platform.audit_fact(audit_id, tenant_id, actor_ref, action_type, subject_ref)
VALUES ('11111111-2222-2222-2222-222222222222',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        'ci:actor', 'FoundationProbe', 'test-only:1');
DO $assert$
BEGIN
    IF (SELECT count(*) FROM platform.outbox_event) <> 1 THEN
        RAISE EXCEPTION 'A cannot read its own event';
    END IF;
    BEGIN
        INSERT INTO platform.outbox_event(
            event_id, tenant_id, event_type, aggregate_ref, payload_schema_version,
            payload, payload_sha256
        ) VALUES (
            '33333333-3333-3333-3333-333333333333',
            'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
            'IllegalForeignTenant', 'test:foreign', 1,
            '{"forbidden":true}', repeat('b',64)
        );
        RAISE EXCEPTION 'foreign tenant INSERT was accepted';
    EXCEPTION WHEN insufficient_privilege THEN
        NULL;
    END;
END
$assert$;
COMMIT;

-- Same authenticated connection reused as Tenant B: A is now invisible.
DO $assert$
BEGIN
    IF platform.current_tenant_id() IS NOT NULL THEN
        RAISE EXCEPTION 'tenant setting survived COMMIT';
    END IF;
END
$assert$;
BEGIN;
SELECT set_config('keruenix.tenant_id', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', true);
DO $assert$
BEGIN
    IF (SELECT count(*) FROM platform.outbox_event) <> 0 OR
       (SELECT count(*) FROM platform.audit_fact) <> 0 THEN
        RAISE EXCEPTION 'Tenant A leaked into Tenant B session';
    END IF;
END
$assert$;
-- Identical UUIDs under different tenants must not trigger a cross-tenant
-- uniqueness oracle. A global event_id/audit_id PK would reject these.
INSERT INTO platform.outbox_event(
    event_id, tenant_id, event_type, aggregate_ref, payload_schema_version,
    payload, payload_sha256
) VALUES (
    '11111111-1111-1111-1111-111111111111',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'FoundationProbe', 'test-only:B', 1, '{"test":"B"}', repeat('b',64)
);
INSERT INTO platform.audit_fact(audit_id, tenant_id, actor_ref, action_type, subject_ref)
VALUES ('11111111-2222-2222-2222-222222222222',
        'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','ci:actor-B',
        'FoundationProbe', 'test-only:B');
DO $assert$
BEGIN
    IF (SELECT count(*) FROM platform.outbox_event
        WHERE event_id = '11111111-1111-1111-1111-111111111111') <> 1
        OR (SELECT count(*) FROM platform.audit_fact
            WHERE audit_id = '11111111-2222-2222-2222-222222222222') <> 1 THEN
        RAISE EXCEPTION 'same UUID cross-tenant write or scope failed';
    END IF;
END
$assert$;
COMMIT;

-- Three distinct tables must roll back as one unit.
BEGIN;
SELECT set_config('keruenix.tenant_id', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', true);
INSERT INTO platform.outbox_event(
    event_id, tenant_id, event_type, aggregate_ref, payload_schema_version, payload, payload_sha256
) VALUES (
    '44444444-4444-4444-4444-444444444444',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'RollbackProbe','test:rollback',1,'{"willRollback":true}', repeat('c',64)
);
INSERT INTO platform.audit_fact(audit_id, tenant_id, actor_ref, action_type, subject_ref)
VALUES ('55555555-5555-5555-5555-555555555555',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','ci:actor','Rollback','test:rollback');
INSERT INTO platform.inbox_receipt(tenant_id, consumer_name, event_id, payload_sha256)
VALUES ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'ci:consumer',
        '66666666-6666-6666-6666-666666666666', repeat('d',64));
ROLLBACK;

BEGIN;
SELECT set_config('keruenix.tenant_id', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', true);
DO $assert$
BEGIN
    IF EXISTS (SELECT 1 FROM platform.outbox_event
               WHERE event_id='44444444-4444-4444-4444-444444444444') OR
       EXISTS (SELECT 1 FROM platform.audit_fact
               WHERE audit_id='55555555-5555-5555-5555-555555555555') OR
       EXISTS (SELECT 1 FROM platform.inbox_receipt
               WHERE event_id='66666666-6666-6666-6666-666666666666') THEN
        RAISE EXCEPTION 'rolled-back audit/outbox/inbox persisted';
    END IF;
END
$assert$;
-- Inbox unique constraint prevents two receipts for one consumer/event.
INSERT INTO platform.inbox_receipt(tenant_id, consumer_name, event_id, payload_sha256)
VALUES ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','ci:consumer',
        '77777777-7777-7777-7777-777777777777', repeat('e',64));
INSERT INTO platform.inbox_receipt(tenant_id, consumer_name, event_id, payload_sha256)
VALUES ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','ci:consumer',
        '77777777-7777-7777-7777-777777777777', repeat('e',64))
ON CONFLICT DO NOTHING;
DO $assert$
BEGIN
    IF (SELECT count(*) FROM platform.inbox_receipt
        WHERE event_id = '77777777-7777-7777-7777-777777777777') <> 1 THEN
        RAISE EXCEPTION 'Inbox duplicate persisted';
    END IF;
END
$assert$;
COMMIT;

-- Real geography units: approx 8 km, not 0.1 arbitrary geometry units.
DO $assert$
BEGIN
    IF ST_DWithin(ST_SetSRID(ST_MakePoint(76.9,43.2),4326)::geography,
                  ST_SetSRID(ST_MakePoint(77.0,43.2),4326)::geography, 1000) THEN
        RAISE EXCEPTION 'PostGIS distance erroneously treated degrees as meters';
    END IF;
    IF NOT ST_DWithin(ST_SetSRID(ST_MakePoint(76.9,43.2),4326)::geography,
                      ST_SetSRID(ST_MakePoint(77.0,43.2),4326)::geography, 15000) THEN
        RAISE EXCEPTION 'PostGIS geography distance unexpectedly too large';
    END IF;
END
$assert$;
SQL

echo "PASS: real PostgreSQL/PostGIS, non-superuser RLS, tenant reset, rollback, Inbox uniqueness"
echo "PARTIAL ONLY: no Spring datasource, tenant JWT binding, Modulith verify, dispatcher fencing or full FOUND-01..12 qualification."

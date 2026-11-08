-- V1: PR-01 platform persistence only. Admin/Flyway migrator role required.
-- Not an enabled application datasource. No business tables or runtime auth are introduced.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS platform;
REVOKE ALL ON SCHEMA platform FROM PUBLIC;

CREATE TABLE platform.outbox_event (
    event_id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    event_type varchar(120) NOT NULL CHECK (length(btrim(event_type)) > 0),
    aggregate_ref varchar(160) NOT NULL CHECK (length(btrim(aggregate_ref)) > 0),
    payload_schema_version integer NOT NULL CHECK (payload_schema_version > 0),
    payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    payload_sha256 varchar(64) NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    delivery_state varchar(20) NOT NULL DEFAULT 'PENDING'
        CHECK (delivery_state IN ('PENDING','CLAIMED','PUBLISHED','DEAD_LETTER')),
    occurred_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_outbox_tenant_delivery ON platform.outbox_event
    (tenant_id, delivery_state, created_at, event_id);

CREATE TABLE platform.inbox_receipt (
    tenant_id uuid NOT NULL,
    consumer_name varchar(100) NOT NULL CHECK (length(btrim(consumer_name)) > 0),
    event_id uuid NOT NULL,
    payload_sha256 varchar(64) NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    processed_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, consumer_name, event_id)
);

CREATE TABLE platform.audit_fact (
    audit_id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    actor_ref varchar(160) NOT NULL CHECK (length(btrim(actor_ref)) > 0),
    action_type varchar(120) NOT NULL CHECK (length(btrim(action_type)) > 0),
    subject_ref varchar(160) NOT NULL CHECK (length(btrim(subject_ref)) > 0),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_audit_tenant_created ON platform.audit_fact (tenant_id, created_at);

-- This setting MUST be established only from a server-verified principal with
-- set_config('keruenix.tenant_id', verified_tenant_uuid, true) INSIDE a transaction.
-- The custom GUC itself is not authentication or a substitute for account-level ABAC.
CREATE FUNCTION platform.current_tenant_id()
RETURNS uuid
LANGUAGE sql STABLE
AS $f$
    SELECT NULLIF(current_setting('keruenix.tenant_id', true), '')::uuid
$f$;

ALTER TABLE platform.outbox_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform.outbox_event FORCE ROW LEVEL SECURITY;
CREATE POLICY outbox_verified_tenant ON platform.outbox_event
    USING (tenant_id = platform.current_tenant_id())
    WITH CHECK (tenant_id = platform.current_tenant_id());

ALTER TABLE platform.inbox_receipt ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform.inbox_receipt FORCE ROW LEVEL SECURITY;
CREATE POLICY inbox_verified_tenant ON platform.inbox_receipt
    USING (tenant_id = platform.current_tenant_id())
    WITH CHECK (tenant_id = platform.current_tenant_id());

ALTER TABLE platform.audit_fact ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform.audit_fact FORCE ROW LEVEL SECURITY;
CREATE POLICY audit_verified_tenant ON platform.audit_fact
    USING (tenant_id = platform.current_tenant_id())
    WITH CHECK (tenant_id = platform.current_tenant_id());

REVOKE ALL ON ALL TABLES IN SCHEMA platform FROM PUBLIC;

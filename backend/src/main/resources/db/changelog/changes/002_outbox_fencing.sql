--liquibase formatted sql
--changeset keruenix:outbox-fencing-v2 dbms:postgresql splitStatements:false runInTransaction:true
-- V2: durable per-tenant claim/fencing metadata for Outbox.
-- V1 was never deployed to production; add an additive migration regardless.
-- Claim and ack must be separate transactions; transport I/O NEVER inside a DB txn.
ALTER TABLE platform.outbox_event
    ADD COLUMN claim_owner varchar(160),
    ADD COLUMN claim_token bigint NOT NULL DEFAULT 0 CHECK (claim_token >= 0),
    ADD COLUMN lease_until timestamptz,
    ADD COLUMN attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    ADD COLUMN next_attempt_at timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN published_at timestamptz;
ALTER TABLE platform.outbox_event
    ADD CONSTRAINT ck_outbox_lease_consistency
    CHECK (
        (delivery_state = 'CLAIMED' AND claim_owner IS NOT NULL AND lease_until IS NOT NULL)
        OR
        (delivery_state <> 'CLAIMED' AND claim_owner IS NULL AND lease_until IS NULL)
    );
CREATE INDEX ix_outbox_claim_eligible
    ON platform.outbox_event(tenant_id, next_attempt_at, created_at, event_id)
    WHERE delivery_state IN ('PENDING','CLAIMED');

# 41 — PR-00/PR-01 Readiness Execution Plan (after v1.7)

**Date:** 2026-11-08 · **Status:** PR-00 governance contract implemented; PR-01 still planned and requires real integration evidence.

## PR-00 — usable decision evidence ledger

The [machine-readable register](contracts/r0-decision-readiness.v1.json) links all 12 BR and eight DEC decisions, the five stakeholder workshops and each blocking PR slice. It is a **record of signoff obligations**, not evidence of meetings or approval. No identities, signatures, confidential legal documents or keys should be committed to the public repository.

**Decision state model:**
- `PENDING`: the source BR/DEC stays pending; no legally binding command activated. The decision may still have a draft technical proposal.
- `APPROVED_WITH_VERIFIED_EVIDENCE`: the source-of-truth contract is also approved; real external authority and signer verification recorded; evidence reference, approver authority, approved version, UTC time and independent verifier evidence present. Where legal approval is necessary, a legal profile and legal signoff are required.
- `REJECTED_SAFE_DENY` or `DEFERRED_SAFE_DENY`: explicit rationale, source state and fail-safe alternative. Rejected does not mean implicit permission.

**Separation of duties:** documentation authors may propose, technical reviewers validate traceability, actual business/legal representatives approve the specific term or actor right, independent verification checks identity/evidence provenance. GitHub CI can establish structural parity; it cannot establish the real-world authority of a signer. A fabricated URL is not legal evidence.

**Workshops:** W1 customer/Quote and account scope, W2 carrier/fleet/compliance, W3 offline custody/POD/private review, W4 cancellation and external accounting boundary, W5 safe continuity during suspension. Each workshop remains `NOT_CONDUCTED` until a real meeting and evidence are recorded. Records must include attendees/authority, minutes, UTC time and signoff scope; no automatic bulk approval.

**Machine contract gate:**

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/validate_tdd_roadmap.py
python3 scripts/validate_decision_readiness.py
```

Scope is **NO PAYMENTS**. Do not add Invoice/AR/AP, PaymentAllocation, paid status, ESF issuance, bank integrations or refunds in any development PR.

## PR-01 — evidence-backed implementation sequence (not completed)

**First runnable slice:** Java21/Boot build unchanged with security `denyAll`; a standalone PostgreSQL/PostGIS schema and CI integration smoke have now been added. Separate migration/admin and application roles and forced RLS are exercised. **Delivered in PR-01 partial code:** Spring Boot/Liquibase migrations and scoped JDBC transactions have passed PostgreSQL integration CI. **Still required:** trusted JWT → authorized tenant/account, full FOUND test matrix, durable broker adapter and operational recovery. Do not enable trust in `tenantId` headers. Spring Modulith 2.1.2, Liquibase via Boot 4.1.2 starter and PostgreSQL integration have been verified by CI; keep exact-SHA dependency evidence for subsequent upgrades.

**Red-first tests (FOUND-01..12)** are specified in [R0 TDD Start Pack](36-r0-tdd-start-pack.md). Execute in this order:

1. Real DB roles + FORCE RLS; no authenticated tenant context → no tenant records. Verify user connection can never run DDL or bypass RLS; no H2 substitution.
2. Transaction-scoped authenticated tenant context, pooled connection reuse, tenants A/B and Customer-X/Y account scope; test `set_config(...,true)`, rollback and connection recycle.
3. Atomic audit+outbox, consumer inbox unique key and event digest, at-least-once dispatch with fenced lease and retry; no phantom event after DB rollback.
4. PostGIS/SRID/geography sample and migration from fresh/upgrade schema; ensure spatial queries still include resource scope.
5. Modulith boundaries and Swagger/business endpoint negative test; new implementations remain gated until their BR/DEC/EDS and legal profile are approved.

**Acceptance:** exact-SHA `mvn verify`, PostgreSQL/PostGIS Testcontainers logs, migration versions, non-superuser RLS proof, outbox crash/replay proof, lint/SBOM, CI artifact links. No claim of PR-01 qualification until all FOUND-01..12 executable tests and manual reviews have completed.

**Handoff:** PR-02/03C/03/04 may begin safe implementations only after their applicable PR-00 evidence. The unauthorized `customer:rfq:submit` and any binding Quote/Booking/Carrier/POD remain disabled until explicit policy and verified legal authorization.

## PR-01 partial execution evidence

The first platform SQL migration contains `platform.outbox_event`, `platform.inbox_receipt` and `platform.audit_fact` with `FORCE ROW LEVEL SECURITY` and composite `(tenant_id, event_id/audit_id)` keys. Separate NOLOGIN capability roles are provisioned through an admin-only script. `scripts/test_pr01_pg_foundation.sh` tests real PostgreSQL/PostGIS; GitHub Actions uses an ephemeral test DB and does not expose production passwords.

**Partial coverage only:** `FOUND-01` non-superuser/absent RLS context; `FOUND-02` same-session tenant switch and context reset; `FOUND-04` atomic rollback of platform facts (not yet a true business aggregate); `FOUND-06` Inbox uniqueness (changed-payload rejection must be implemented in consumer code); `FOUND-12` geography meter semantics (spatial account-scoped API still missing). All other `FOUND-03/05/07/08/09/10/11` remain unimplemented. Neither PR-01 nor RD-01 is QUALIFIED until the complete suite runs on the exact artifact SHA.

**Security note:** PostgreSQL RLS does not protect uniqueness checks from potential cross-tenant existence leakage; tenant-first compound PKs are mandatory in this baseline. The custom transaction-local GUC is only defense in depth, never an authentication source or direct client-controlled parameter.

> **Corrective note (2026-11-10):** Audit A-02 changed the Issue #8 direct `PlatformOutboxDelivery` test into an explicitly **passing generic-transport baseline**. It does *not* prove CustomerAccount authorization and should never be used as the S2 domain-behavior RED. Authorized Account dispatch RED remains blocked on the approved production grant/caller contract. The independent new A-03 PostgreSQL digest mismatch test is a **separate expected behavioral RED** (scripts/ci_assert_outbox_digest_red.sh). Statements below describing the old direct-dispatch test as an expected authorization RED refer only to historical evidence at SHA `25febf76`, not current qualification.

# 64 — Technical audit of KERUENIX Foundation / PR #3

**Audit date:** 2026-11-10  
**Audited SHA:** `25febf76a3ccdc717e727f5386491dc1777b0b68`  
**Branch:** `test/s1-platform-tenancy-oracles`  
**Scope:** Foundation/security/Outbox/Inbox/PostgreSQL/PostGIS, S1 RED and CI. Static review of GitHub source plus existing exact-SHA Action logs; this is **not** a penetration test, production deployment test or independent S2 approval. No production code changed in this audit.

**Overall:** foundation architecture **conditionally sound for continued S0/S1 design and testing**, **NOT ACCEPTED for S3 domain implementation or production deployment**. Current Actions 3/3 success verifies limited platform gates, not customer-level permission or actual external delivery.

## Verified strengths

1. `SecurityConfig` production chain is `denyAll`; qualification-positive JWT endpoints are test-only. No production public login/business routes were observed in reviewed code.
2. `TenantScopeAuthorization` requires an authenticated `JwtAuthenticationToken` and consults a server-side `VerifiedGrantSource` on each invocation. Signed JWT tenant claim alone cannot authorize account access. **However, there is no production persistent grant implementation yet.**
3. `PlatformTenantTransaction` sets tenant with transaction-local `set_config(..., true)`, refuses an inner transaction's different tenant, and has a same-physical-connection Hikari test.
4. Outbox/Inbox/Audit baseline tables use tenant-first compound keys and `ENABLE + FORCE ROW LEVEL SECURITY`; basic runtime database role is non-superuser and `NOBYPASSRLS`.
5. Outbox claim uses `FOR UPDATE SKIP LOCKED`, incrementing fence token, scoped markPublished/retry; tests cover concurrent claims, stale owner after takeover and crash after consumer commit-before ACK. At-least-once not exactly-once.
6. GitHub Actions on SHA [#42821475983](https://github.com/alimbetov/KERUENIX/actions/runs/42821475983), [#42821475797](https://github.com/alimbetov/KERUENIX/actions/runs/42821475797), [#42821475898](https://github.com/alimbetov/KERUENIX/actions/runs/42821475898) concluded success; the first runs a targeted **1 failure / 0 errors / 0 skipped** Issue #8 RED, and preserves the FOUND-10 populated restore gate. CI success means the *expected failure classifier* succeeded, not that missing authorization is fixed.

## Findings — severity is based on deployment impact, not assertion of an exploitable live service

### A-01 — BLOCKER (P0 gate): no real CustomerAccount operation authorization source or dispatch boundary

Evidence: `backend/src/main/java/kz/keruenix/platform/security/TenantScopeAuthorization.java` only defines a `VerifiedGrantSource` interface. `TrustedTenantHttpIntegrationTest` uses a mutable test-only `QualificationGrantRegistry`. `PlatformOutboxDelivery.dispatchNext(...)` only accepts `tenantId` and generic `Sender`; it has no account/operation authorizer. Production `SecurityConfig` is `denyAll`.

Consequence **if a domain caller is added without a gate**: same-tenant CustomerAccounts may be conflated and an unauthorized export may be sent. No exploitable deployed endpoint is demonstrated here.

Remediation: approve BR-03/DEC-R0-02 + DEC-CA-01/03; define PostgreSQL-backed per-(subject,tenant,account,operation) grant with fail-closed primary read, and separate `AuthorizedAccountOutboxDispatch` (or equivalent reviewed domain caller). Check current grant before claim/consume and before any irreversible effect, with explicitly reviewed TOCTOU handling. Unit/synthetic grants do not qualify this. Do **not** force user JWT authorization into reusable generic Outbox.

### A-02 — HIGH (P1): Issue #8 RED oracle targets generic transport, not the eventual authorized caller

Evidence: `Issue8CustomerOutboxAuthorizationRedTest` inserts a `CustomerAccountExport` JSON payload, calls `PlatformOutboxDelivery.dispatchNext` directly and asserts `sent == 0`. It never creates a DB grant, authenticates a user, or invokes a CustomerAccount dispatch guard. Therefore the expected failure **cannot become GREEN by implementing the correct caller alone** if this test continues bypassing it.

Risk: a future developer might alter generic transport to inspect untrusted payload strings or trust a test flag to make it green, damaging layering while leaving the actual caller unqualified.

Remediation: retain the current test as an **anti-pattern / missing caller boundary diagnostic**, not as a required green domain behavior test. Once real domain port is approved, replace/add signed-JWT → DB-grant → authorized dispatch → real PostgreSQL → sender tests: unauthorized account must return DENIED, `send` must remain zero, no ACK/PUBLISHED; permitted account must emit once logically, with Inbox dedup. Current targeted RED log is valid evidence of absent integration, not S2 acceptance.

### A-03 — HIGH (P1): Outbox payload digest is not derived or verified against payload bytes

Evidence: migration `001_platform_baseline.sql` constrains `payload_sha256` to 64 lowercase hex characters but does not calculate it; `PlatformOutboxDelivery` reads the stored digest and JSON without recomputing/checking it; `PlatformInbox.accept` compares only receipt digest for identical event IDs. Several CI fixtures insert `'a'.repeat(64)` or `'c'.repeat(64)` irrespective of payload.

Consequence: `payload_sha256` is **not currently an integrity guarantee**. A forged or incorrectly computed producer digest can pass transport and Inbox checks. For audit/replay reliability, canonical JSON strategy must be specified.

Remediation: define digest canonicalization (e.g. stable JSONB text representation + schema/version/domain fields); calculate hash server-side at the trusted enqueue boundary, verify on consume, and reject mismatch. Decide whether PostgreSQL `pgcrypto` function or application canonical serializer is authoritative; establish cross-language fixtures before S3. Hashes are not signatures and do not authenticate producers.

### A-04 — HIGH (P1): bounded retry, terminal state and poison-event policy absent

Evidence: `002_outbox_fencing.sql` defines `attempt_count`, `next_attempt_at`, `delivery_state = DEAD_LETTER`, but `PlatformOutboxClaims.scheduleRetry` only sets PENDING and does not enforce attempt limit; `PlatformOutboxDelivery` throws on sender error and holds the event until lease expires. No production scheduler, terminalization, backoff policy or DLQ operator flow is present.

Consequence: permanently failing effects can loop indefinitely, consume resources, block ordered work or hide operational failures.

Remediation: agree bounded retry classes, exponential/backoff+jitter policy, `DEAD_LETTER` transition, searchable reason/failure metadata, safe requeue capability, observability (queue age, attempts, leased count, failures), and abuse limits. Require real PostgreSQL tests for poison event and recovery.

### A-05 — HIGH (P1): fencing protects DB ACK, not an external side effect

Evidence: `PlatformOutboxDelivery.dispatchNext` reads the lease-guarded payload, calls `sender.send(envelope)` outside DB transaction, then attempts fenced `markPublished`. Lease can expire while `send` is in flight; old and new workers may both send before one ACK is rejected.

Consequence: at-least-once delivery and possibly concurrent duplicate external effects. This is **by-design for generic Outbox**, not a bug if idempotent consumers are mandatory.

Remediation: sender protocol needs external idempotency key `(tenant,eventId,consumer)`, durable receiver Inbox, sender timeout/lease renewal or sufficiently bounded lease for latency, and concurrency tests that deliberately expire a lease **during** a slow send. Explicitly forbid asserting exactly-once external side effects.

### A-06 — MEDIUM (P2): RLS tenant setting is scoped but not cryptographically authenticated by PostgreSQL

Evidence: `platform.current_tenant_id()` depends on custom GUC `keruenix.tenant_id`; `PlatformTenantTransaction.execute(UUID verifiedTenantId,...)` currently takes a UUID directly. Application role privileges on tables depend on the caller providing verified tenant context. A custom GUC can be set via SQL by a principal with SQL execution ability; RLS is not a substitute for an upstream verified authorization boundary.

Remediation: only expose package-restricted tenant transaction from a verified principal/grant context, review all future callers, use parameterized SQL and no generic SQL execution endpoints, test that untrusted selectors never select tenant context. Consider a typed authorized scope and a DB-side stricter security design if the threat model includes arbitrary SQL execution by app credentials. Do not claim RLS alone prevents SQL-injection-driven tenant changes.

### A-07 — MEDIUM (P2): test/CI qualification gaps

Evidence: `TrustedTenantHttpIntegrationTest` uses fabricated grants, audit-row `subject_ref` as account surrogate and test-only geo table; `backend/src/test-red/java` has missing-interface `API_ABSENT_RED` for caches/jobs now *deferred* in R0; targeted RED classifier relies on log regex and one failing JUnit assertion. No real domain grant, actual export artifact, pre-send revoke race or service-principal authorization test.

Remediation: replace test-only data-model surrogates with production migration-based schema when approved; separate `PLATFORM_PASS`, `EXPECTED_API_ABSENT_RED`, `EXPECTED_BEHAVIOR_RED` and `DOMAIN_NOT_QUALIFIED` in CI summaries; disable future optional cache/job RED from R0 release criteria if unused. No elevated S2 claims on a green wrapper.

### A-08 — MEDIUM (P2): operational blast radius, migrations and recovery remain unproven in production

Evidence: FOUND-10 exercises a disposable CI PostgreSQL V1→V2 populated snapshot and compare. There is no demonstrated production-like replication/backup rotation/PITR, queue depth management, HA takeover, credential rotation or online migration with concurrent real load.

Remediation: complete an operational runbook and a staging recovery drill, including PostGIS/roles/policies restore verification, actual RTO/RPO targets, audit/inbox retention, large queue performance, index plans and tenant partition strategy based on measured data.

## Prioritized work queue

| Priority | Task | Evidence required before S2 |
|---|---|---|
| 1 | Approve BR-03/DEC-R0-02, DEC-CA-01, 03, 04 | Signed owner/Security/DB/Operations decision |
| 2 | Define production Account grant and authorized dispatcher API **on paper only**, security review | Reviewed contracts, negative test oracle and responsibilities |
| 3 | Move Issue #8 expected RED from direct generic Outbox invocation to the **authorized caller boundary** | Real PG grant backed tests: deny/allow/revoke/fail-closed, sender=0 and no ACK for denied |
| 4 | Define digest canonicalization, retry/DLQ and sender idempotency contract | Positive + negative contract tests, real PG and concurrent stale-lease send |
| 5 | Independent S2 Test Review | Exact-SHA evidence, reviewer identity and explicit approval; PR remains Draft |

**Architectural recommendation unchanged:** modular monolith + PostgreSQL/PostGIS with existing Outbox/Inbox; **no** R0 protected cache, Redis, Kafka, generic job table or independent worker without demonstrated use case.

**Disposition:** `FOUNDATION_PARTIAL_QUALIFIED`, `ISSUE8_ORACLE_MISALIGNED`, `S1_PARTIAL`, `S2_NO_GO`, `PR3_DRAFT`. Do not merge or implement CustomerAccount production flow until the reviewed gates clear.

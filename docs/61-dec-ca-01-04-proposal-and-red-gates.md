> **R0 PRODUCT DIRECTION ACCEPTED (2026-11-10):** The sponsor chose the lean PostgreSQL-first design. [Decision 62](./62-r0-pragmatic-architecture-adoption.md) supersedes this document wherever it suggests an unconditional production CachePort or a second generic CustomerAccount job table. CA-CACHE proposals are **DEFERRED** (not PASS); first real behavioral RED should focus on grant security and existing outbox. This product acceptance is **not** Security/DB/Operations or independent S2 approval. Issues #4–#7 remain open.

# DEC-CA-01…04 — CustomerAccount authorization, cache and jobs (S0 decision candidates)

Status: **PROPOSED / AWAITING OWNER SIGN-OFF**. This file is a complete architecture recommendation, **not** an acceptance of BR-03, DEC-R0-02 or S2. Target: PR #3. Existing production behavior is fail-closed `denyAll`, and no CustomerAccount cache/job implementations are present.

## DEC-CA-01 — Authoritative grants, revocation and consistency

**Recommendation:** PostgreSQL is the single authoritative grant and membership source; store `tenant_id`, `customer_account_id`, `principal_id`, explicit `operation` grant, `status` and `revision`/monotonic `policy_epoch`. Administrative grant mutations + audit fact + outbox event commit atomically via Liquibase-governed schema. Query the **primary**, never an asynchronously replicated read model, for protected data decisions; tenant RLS and CustomerAccount SQL predicates apply together. Fail closed on grant read failures, expired membership or unexpected revision.

- Grant is checked **per access**, not captured in JWT or cached in a session; `tenant_id` in a valid JWT is an untrusted selector hint.
- A revoke transaction increments the authorization epoch before returning success. A request starting afterwards must observe new authority. For an in-flight sensitive response or irreversible publication, revalidate current grant+revision immediately before effect. An effect already delivered cannot be retrospectively withdrawn; race/compensation requires approval.
- `DENY` and `UNAVAILABLE` are distinct result types for audit and job retry policy. Both deny protected content; retry is permitted only for a transient *unavailable* store, not revoked access.
- Avoid time-based entitlement cache/TTL as a security guarantee.

**Alternatives rejected for R0:** JWT-embedded account grants (revocation lag), Redis as grant authority (split-brain), eventual consistency authorization read replica (stale permissions).

**Pending owner decisions:** BR-03/DEC-R0-02 customer relationships and delegation authority; revision per actor-account versus account-wide epoch; cross-company operations; grant snapshot retention and revocation I/O race.

**Acceptance criteria:** signed JWT without server grant rejects; X/Y same tenant never leak; revoke-after-auth rejects next request; grant-store failure neither returns data nor executes a job; a stale epoch cannot restore authority.

## DEC-CA-02 — Cache architecture and invalidation

**Recommendation for first production slice:** **do not cache protected CustomerAccount content or authorization decisions**. Permit only immutable/shared non-sensitive reference metadata in local in-process cache if benchmarked. Introduce a *typed CacheGateway* and *CacheKey* port, with **no permissive/default production adapter**, so a later Redis/Caffeine adapter can be added after own RED and S2. In the first sensitive-data implementation, execute authorized primary-DB scoped reads until the security and load evidence justifies caching.

**Future conditional cache namespace (contract candidate only):**
`ca:v1:<tenantUUID>:<customerAccountUUID>:<resourceKind>:<resourceUUID>:<representationVersion>:<policyEpoch>`.
All canonical values derived from verified resource ownership, not untrusted key text; actor-specific projections additionally require principal/role binding or are forbidden. Cache value carries tenant/account/schema/epoch metadata validated on read. Access sequence: validated JWT → current grant → construct typed scoped key → cache lookup → value scope check → revalidate grant before sensitive response. Stale values are never evidence of access.

**Invalidation:** after a transactional grant revoke, bump epoch; send transactional outbox invalidation event as a performance aid only. Duplicate/missing/delayed eviction cannot authorize reads. No negative grant cache. Cache unavailable → fallback to authorized DB, never broaden query. TTL for protected data is **unapproved** and must not be chosen ad hoc.

**Alternatives:** shared Redis for protected data now (premature operational+isolation risk); raw string cache keys (scope collision/injection); evict-only revoke (race).

**Acceptance criteria:** tenant/account/type/version/epoch key collisions impossible; deny even with stale value and revoked grant; cache outage cannot grant access; no cross-account result under concurrent request.

## DEC-CA-03 — Service identity and delegation of background jobs

**Recommendation:** a job is an **immutable, server-created request**, not a replayed HTTP/JWT authorization. Only explicitly registered service principals may execute narrowly scoped operations, or a designated user delegation with an expiry + current per-account grant. Every claim/retry and pre-external-effect boundary rechecks the *current* principal or delegated authority, operation scope, tenant, account, resource ownership, and policy epoch. A worker may never infer rights from queue payload alone.

- User-authored work after revocation → terminal `DENIED` (no output); transient grant-store failure → `RETRYABLE_AUTH_UNAVAILABLE` with backoff, never publish content.
- Jobs with service principals require an independently auditable allowance per operation, tenant and account (no global all-tenants bypass). Service account operations cannot silently inherit a human's permissions.
- Cross-tenant batch jobs must partition into separately authorized tenant/account work items and transactions.
- Between final auth check and irreversible external delivery there is a TOCTOU race. Exactly-once external delivery is not promised: specify idempotent delivery key, fenced ownership and compensating controls. Deliveries already completed remain auditable.

**Alternatives rejected:** long-lived captured HTTP JWT; trusted headers in internal queues; `@Async` inheriting security context and tenant scope implicitly.

**Pending decisions:** approved service-principal matrix, delegation expiry, suspend/resume semantics, in-flight revoke and export cancellation policy.

## DEC-CA-04 — Durable jobs, leases, replay and artifacts

**Recommendation:** PostgreSQL durable job state + transactional outbox, executed by an **in-process modular-monolith worker** in R0; no Kafka, separate microservice, Redis queue, or distributed cache dependency initially. Liquibase migration must define a tenant/account-scoped job table with `job_id`, immutable `operation`, schema/version, resource reference, `requested_by`, delegation type, grant epoch, `attempt_count`, `lease_owner`, monotonically increasing `fencing_token`, `lease_until`, `next_attempt_at`, status, immutable payload digest, idempotency key, timestamps and audit links.

- Unique idempotency on `(tenant_id, customer_account_id, operation, idempotency_key)`; same key with changed canonical payload → conflict; exact replay → stable job ID.
- Claim using `FOR UPDATE SKIP LOCKED` or equivalent SQL with leased ownership and fencing, under tenant scope. Stale token cannot acknowledge or write artifacts. Crash between output and ack handled by idempotent publication + durable state reconciliation.
- Each execution starts a fresh tenant-scoped transaction; CustomerAccount predicate on every query; neither worker thread-local nor pooled JDBC session can carry a previous tenant.
- Artifact keys must include tenant/account/job identity; object storage is not an authorization source. Download performs fresh grant check. Signed URLs must be short-lived and revocable by denying new URL issuance; already-issued URLs require separate threat/TTL approval.
- Retention, error taxonomy, observability, max attempts, rate and lease durations are **pending** measurable S0 objectives.

**Alternatives:** in-memory scheduler (not crash durable), default broker infrastructure (unneeded R0 complexity), unbounded retries (unsafe).

## S1 Test-First contract, gating and dependency order

| ID | Required *real adapter* oracle | Gate |
|---|---|---|
| CA-CACHE-01 | Production CacheKey encoder separates A/X vs A/Y, A/X vs B/X; version/type/epoch | No adapter/DEC-CA-02 sign-off |
| CA-CACHE-02 | Cache HIT with revoked grant denies and does not emit payload, regardless of eviction | Real cache + production auth adapter absent |
| CA-CACHE-03 | Invalidation delayed/dropped, cache down, policy epoch changed: still fail closed | Real cache + grant source absent |
| CA-JOB-01 | Forged envelope/actor/job scope denied before DB I/O | Real job intake and authorization absent |
| CA-JOB-02 | Revoke before claim/retry, grant store outage, change epoch: no effect/output | Durable worker/grant source absent |
| CA-JOB-03 | Same-tenant two accounts, tenant switch, export/artifact download | Real worker/artifact adapter absent |
| CA-JOB-04 | Concurrent double claim, stale fence, crash/restart and idempotency | Real PostgreSQL job schema/worker absent |

The **pre-implementation RED sources** live under `backend/src/test-red/java` and are deliberately **not** in Maven's standard test source set. They target *absent production classes* and must not be confused with passing behavior tests. Their expected compilation failure is only `API_ABSENT_RED`, **not** `BEHAVIORAL_RED_QUALIFIED`. After the four DEC records are accepted, adapt these to the reviewed API, wire them against actual PostgreSQL + cache + worker adapters, execute failing behavioral integration tests, then obtain separate S2 Test Review **before any implementation**. Do not turn missing adapters into synthetic successful stubs.

## Approval work items

Decision approval is tracked in four **open** GitHub issues. Creating them is not an approval, and no verified reviewer usernames were available on PR #3 when the requests were filed:

- [#4 DEC-CA-01](https://github.com/alimbetov/KERUENIX/issues/4): authoritative grants and revocation.
- [#5 DEC-CA-02](https://github.com/alimbetov/KERUENIX/issues/5): protected-data caching and invalidation.
- [#6 DEC-CA-03](https://github.com/alimbetov/KERUENIX/issues/6): service principals and delegated jobs.
- [#7 DEC-CA-04](https://github.com/alimbetov/KERUENIX/issues/7): durable leases, fencing and artifact ACL.

Do not infer approvals from `issue state=open/closed` alone. Each requires the named role's substantive GitHub review, explicitly accepted rationale, date and exact document SHA. BR-03/DEC-R0-02 must also be adjudicated, not merely referenced.

## Decision register and sign-off

| Decision | Architecture recommendation | State | Required decision owners |
|---|---|---|---|
| DEC-CA-01 | PostgreSQL authoritative grants, revisioned revocation | PROPOSED | CustomerAccount owner + Security + DB |
| DEC-CA-02 | No protected-data cache in R0; typed future port | PROPOSED | CustomerAccount owner + Security + Operations |
| DEC-CA-03 | Explicit scoped service principal / re-authorize on each run | PROPOSED | Security + Operations + Legal/Business for external delivery |
| DEC-CA-04 | PostgreSQL durable jobs with lease/fencing/outbox | PROPOSED | Job/Platform owner + DB + Operations |

No one has signed these decisions via this artifact. Record approving identity, date, exact SHA, competing alternatives and accepted risks in the relevant review/ADR; all of BR-03, DEC-R0-02 and original open BR/DEC are still outstanding. PR #3 stays Draft. `S2_APPROVAL_PENDING`; PR-04 domain development prohibited.

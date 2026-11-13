# 62 — R0 pragmatic architecture: approved direction, gated implementation

**Product direction: ACCEPTED by project sponsor in conversation, 2026-11-10.** **Architecture/Security/DB/Operations sign-off: PENDING. S2: NOT APPROVED.** Applies to proposed DEC-CA-01…04 on [PR #3](https://github.com/alimbetov/KERUENIX/pull/3). This decision authorizes *planning and test-first work*, not a bypass of independent safety review.

## Outcome

Use a **Java 21 / Spring Boot modular monolith + PostgreSQL 16/PostGIS + Liquibase**. In R0, do **not** deploy Redis, Kafka, an external scheduler, or a separate Worker solely for CustomerAccount. Prefer the existing platform transactional Outbox/Inbox and their claim/fencing facilities before building an overlapping generic job queue. Deliver one customer-isolated RFQ → Execution → POD business journey.

| Option | Dependencies and complexity | Tradeoff | Decision |
|---|---|---|---|
| A — PostgreSQL-first, uncached protected reads, in-process outbox dispatch | One DB and application unit, clear transaction boundary | DB contention must be measured, backups/HA required | **Selected R0 direction** |
| B — Modular monolith, Redis + separate worker | Additional shared state and failure domains | Easier independent scaling, harder revocation/operability | Defer until measured need |
| C — Microservices + Kafka + Redis + independent workers | Broker, service deployments, distributed transactions | Later scale/team autonomy; large R0 cost | Reject for R0 |

These are qualitative engineering judgments, not measured benchmark results.

## Adopted technical defaults, subject to independent review

### DEC-CA-01: authoritative authorization

PostgreSQL **primary** is the only authority for actor / tenant / CustomerAccount / operation grant. Validated JWT proves actor identity but is not an account grant. Each request verifies the current grant, then executes a tenant-bound transaction with RLS **and** CustomerAccount predicate. Revoke/membership change + audit + outbox event commit atomically; subsequent requests must observe revoked rights. Fail closed on grant-store errors. Do not cache grants or use replicated lagging grant reads.

**Do not overengineer R0:** define a narrow grant table with revision and explicit status; complex generic policy engine and active Redis authorization invalidation are out of scope. The authoritative customer–carrier relationship remains dependent on BR-03 and DEC-R0-02.

### DEC-CA-02: omit protected-data cache initially

No production cache for protected CustomerAccount data or authorization decisions in R0. Start with indexed, paged PostgreSQL queries and measure query latency. General immutable public reference metadata may have a separate bounded local cache. The existing preliminary CachePort API-absent RED is **deferred / optional future contract**, not a PR-04 blocker. Introduce a typed cache port only with a validated hot read path and fresh authorization checks. Do not implement an unused interface just to satisfy an artificial RED.

### DEC-CA-03: only narrow internal background operations

Differentiate USER_DELEGATED and SYSTEM_SCOPED job identities. Jobs use server-derived tenant/account/operation scopes; queue data cannot authorize actions. Check current authority at claim/retry and before irreversible external effects. Revoke causes a terminal denial, temporary grant-store outage causes bounded retry without side effects. Service principal must be narrowly scoped and auditable; never a global tenant bypass. Keep legal/financial/externally publishing jobs outside this initial implementation until business acceptance and cancellation/compensation rules are approved.

### DEC-CA-04: reuse platform Outbox before building a second queue

Existing `platform.outbox_event` and `platform.inbox_receipt` are the first R0 mechanism for durable event handoff/retry. Qualify actual dispatch, idempotency and fencing in a tenant-scoped in-process dispatcher. **Do not introduce a generic CustomerAccount Job table until a concrete scheduled/long-running use case proves the Outbox is insufficient.** If needed later, add a separately approved durable-job aggregate with actor/tenant/account/operation, lease, attempt, fencing, retention and artifact permission contracts. Outbox is event delivery, not automatically a full job scheduler.

## Implementation dependency and test-first sequence

| Gate | Deliverable | Required evidence |
|---|---|---|
| D0 | Product acceptance of R0 approach | Sponsor has accepted direction; retain issues #4–#7 as outstanding technical/operational approvals |
| D1 | BR-03, DEC-R0-02, CA-01/03/04 review; CA-02 scope reduction | Recorded Security/DB/Operations/domain decisions and ownership, precise scope |
| S0 | Minimal real service capability | Approved interface for account-scoped authorization and restricted event dispatch, not a future unused cache API |
| S1 | Actual **behavioral RED** | Run targeted tests against real production boundary/DB after interface approved: revocation after prior authorization, two accounts same tenant, grant store outage, outbox claim/retry/lease/fence, denial before delivery. Never accept compilation-only RED as behavioral proof |
| S2 | Independent QA/Security test review | Assess targeted failure reasons, negative oracle coverage and exact SHA before implementation |
| S3 | Minimal implementation | Grant source and account-scoped read/write path; reuse existing outbox claim/delivery infrastructure; no Redis/Kafka/external worker |
| S4 | Qualification | Real PostgreSQL/PostGIS, retry/restart/concurrency, latency and permission audits, main merge only after gates |

### What is explicitly NOT approved

- No real CustomerAccount grant schema/business relationship semantics until BR-03/DEC-R0-02 reviewed.
- No protected-cache adapter and no generic job engine at R0 start.
- No invoice/payment/booking legal transitions or external export publication by default.
- No fake S2 sign-off from author, automation or green CI.
- PR #3 remains Draft, PR-04 domain implementation remains blocked until independent S2 acceptance.

**Next concrete review work:** obtain Security + DB + CustomerAccount/Platform sign-offs in issues [#4](https://github.com/alimbetov/KERUENIX/issues/4), [#5](https://github.com/alimbetov/KERUENIX/issues/5), [#6](https://github.com/alimbetov/KERUENIX/issues/6), [#7](https://github.com/alimbetov/KERUENIX/issues/7); then qualify only real-account grant/outbox RED. Track removed R0 cache/job requirements as **DEFERRED**, not PASS.

# CustomerAccount cache and background jobs — S0/S1 security contract

**Scope:** S2 finding CA-CACHE-JOBS-01, PR #3 test-first design only. **Status: PROPOSED / NOT APPROVED.** No cache, scheduler, broker, external export or CustomerAccount production data path exists yet in this branch. This specification does not authorize PR-04 or change production `denyAll`.

## Trust boundaries and invariants

**Identity:** a request's validated JWT identifies an actor, **not** a CustomerAccount grant. A signed tenant claim, account supplied by a client, cache key, queue payload or correlation ID must never authorize data access. The authoritative, revocable server-side grant must be evaluated on every external request **before accessing cached business content or executing a DB query**. Tenant RLS is necessary, never sufficient for two CustomerAccounts within the same tenant.

**Cache lookup sequence:** authenticate -> resolve requested tenant and account from an authorized resource -> verify current actor/account/action grant -> build strongly typed tenant/account-scoped key -> hit/miss -> retrieve data -> validate that returned record belongs to both tenant and account (including after deserialize) -> respond. Cache hits MUST NOT bypass authorization. Cache negative responses and grants are prohibited until an explicit consistency/TTL design is approved. Caches store no bearer tokens, secrets, or unconstrained cross-account aggregates.

**Key namespace v1 proposal (not yet production schema):** `ca:v1:{tenantUUID}:{customerAccountUUID}:{resourceType}:{resourceUUID}:{representationVersion}:{policyEpoch}`. UUIDs canonical lower-case; no untrusted delimiters or externally supplied raw key. A namespace/version bump invalidates prior schema. `policyEpoch` is a monotonic authoritative generation per account or membership; changes on revoke, suspension, or policy changes. The key alone is **not** an access check. An identity-specific projection additionally needs a subject/role binding; preferable alternative is to avoid caching actor-specific projections entirely.

**Revocation:** revoke must commit the authoritative grant/policy change before reporting success. All subsequent HTTP requests check it afresh. Epoch-based invalidation and outbox-driven eviction may make cache removal efficient, but **eviction is not an authorization barrier**. Concurrent readers already authorized before revocation need explicit consistency semantics: sensitive reads must recheck immediately before emitting a response, or fail closed when the version changes. Stale caches must never make a revoked actor authorized. Fail closed if grant source unavailable; no permissive fallback.

**Jobs:** queue messages are untrusted requests, not delegated permissions. Immutable signed/validated job envelope should include `jobId`, `tenantId`, `customerAccountId`, `actorId` (or explicitly named service principal), `operation`, `resourceRef`, `requestedAt`, `grantVersion`, `schemaVersion`, `idempotencyKey` and trace correlation, with server-derived values only. Job creation verifies both tenant + account + actor + operation. Before **each retry/claim**, a worker rechecks the current grant (or explicitly designed service-authorization policy), job validity, tenant membership, and resource ownership. A former HTTP JWT or raw actor UUID does not grant job execution. `PlatformTenantTransaction` must set tenant scope per transaction; query predicates also require `customer_account_id`. Pool/session reuse must not leak tenant context. Denied or revoked jobs transition to a terminal denied/cancelled state, without side effects or retries for permissions; transient grant-store failure is not an authorization success.

**External effects:** a job intended to export, publish, send data or write cross-service output needs a fresh authorization/revocation barrier immediately before irreversible external I/O, plus idempotent outbox/lease/fencing and artifact tenancy checks. If authorization changes during an in-flight external side effect, recovery/compensation semantics require a separate approved DEC; no claim of immediate cancellation for already delivered data.

**Cache + job coupling:** jobs must never consume a cached permission decision or an actor-projection created under another grant. On revoke, job retries are denied and cached content may remain until eviction but is inaccessible after live check. Cache keys cannot omit either tenant or account; exported artifacts must be scoped and re-authorized on download. Eviction events must carry server-verified tenant/account/epoch and be idempotent.

## Test-first matrix

| ID | Mandatory executable oracle | Current evidence |
| --- | --- | --- |
| CA-SEC-01 | Production `TenantScopeAuthorization` rejects absent/unverified JWT and forged tenant header | Existing integration and new direct boundary tests |
| CA-SEC-02 | Same tenant/account mismatch rejected even with previously valid subject | Existing integration and new direct boundary tests |
| CA-SEC-03 | Revocation is checked again on a subsequent call; cache cannot reuse old `Scope` as authority | Direct gate tests can prove first clause; second is BLOCKED without cache adapter |
| CA-CACHE-01 | Key partitions A/X from A/Y, B/X and alternative resource types/versions/epochs | **RED NOT RUN**; typed cache adapter/key does not exist |
| CA-CACHE-02 | Cached hit and delayed response recheck current grant; unavailable grant store fails closed | **RED NOT RUN**; cache adapter does not exist |
| CA-CACHE-03 | Revoke/change epoch prohibits stale response, even when eviction is delayed/lost | **RED NOT RUN**; cache adapter does not exist |
| CA-JOB-01 | Forged actor/tenant/account in message cannot authorize claim or DB query | **RED NOT RUN**; job envelope/worker authorization does not exist |
| CA-JOB-02 | Revoke between enqueue and claim / claim and retry blocks writes, export, publish | **RED NOT RUN**; worker does not exist |
| CA-JOB-03 | Two accounts same tenant never co-mingle DB context, cache results or artifact download | Existing synthetic HTTP/DB tests only; production pipeline **BLOCKED** |
| CA-JOB-04 | Replay, concurrent claims, fencing, restart and service-principal permissions | Platform outbox tests are reusable foundations; CustomerAccount worker **BLOCKED** |

Do not create green mock-only tests labeled `CA-CACHE` or `CA-JOB`: when production ports are introduced, first write failing integration tests using **actual** adapters and PostgreSQL + cache + worker delivery, then Test Review, then implement behavior. Existing unit tests of `TenantScopeAuthorization` demonstrate only the **pre-existing synchronous security gate**.

## Open decisions and acceptance

- **DEC-CA-01:** grant source storage, authorization version and transaction/consistency semantics for revocation.
- **DEC-CA-02:** cache store, TTL, negative caching policy, invalidation delivery and identity-dependent projection policy.
- **DEC-CA-03:** service principal permissions, delegation duration, cancellation and in-flight irreversible I/O race behavior.
- **DEC-CA-04:** worker job envelope, durable schedule/claim/lease/fencing/replay, audited failure state and export artifact ACL.
- BR-03 / DEC-R0-02 and the original S0 oracle owner approvals remain open.

**Release gate:** exact-SHA CI green for proven *existing* boundaries is necessary, not sufficient. S2 approval for CustomerAccount cache/jobs requires reviewed DEC decisions, real adapter evidence and independent QA/Security approval. Keep PR #3 Draft, leave PR-04 implementation blocked.

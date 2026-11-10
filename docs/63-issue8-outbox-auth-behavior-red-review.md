# 63 — Issue #8: real PostgreSQL authorization-barrier RED evidence and S2 test-review packet

**State: S1 partial behavioral RED candidate; independent S2 approval NOT GRANTED.** This is a deliberately failing business-security requirement exercised via the **existing production `PlatformOutboxDelivery`** and real PostgreSQL, not a mock worker, not a compilation error, and not a production security patch.

## Exact boundary and rationale

The platform transport currently accepts a trusted tenant UUID, claims an event from `platform.outbox_event` with real lease/fencing, and calls `Sender.send(Envelope)`. It has no knowledge of the CustomerAccount, operation grant, or the actor. The class documentation explicitly requires a trusted controller and intentionally does **not** claim to implement authorization. A future CustomerAccount background dispatch entrypoint MUST verify scope/operation grant **before** delegating to this generic transport.

`Issue8CustomerOutboxAuthorizationRedTest` creates a **real PostgreSQL** outbox event with a CustomerAccount-restricted `EXPORT` intent. The unguarded dispatcher is called with its existing public internal API. The current code reaches the sender and ACKs; the required Account+operation gate is absent. The expected failing assertion is `ISSUE8_MISSING_ACCOUNT_AUTH_BARRIER`. The test is **not** evidence that an existing CustomerAccount service leaked production information; no such service, grant store, export implementation or network sender exists yet. It demonstrates the exact missing trust-boundary integration.

The test uses real `keruenix_ci_login` for insertion, a separately restricted `keruenix_ci_dispatcher` role for claims, Liquibase-created Outbox tables and `FORCE ROW LEVEL SECURITY`. It does not mutate production code. The event payload contains an untrusted account selector, explicitly illustrating why that value cannot grant permission.

## Execution and isolation

- Test: `backend/src/test/java/kz/keruenix/platform/persistence/Issue8CustomerOutboxAuthorizationRedTest.java`
- CI wrapper: `scripts/ci_assert_issue8_outbox_auth_red.sh`
- Workflow: `.github/workflows/pr01-pg-foundation.yml`, dedicated step after current RFQ RED.
- Opt in only when `KERUENIX_ISSUE8_BEHAVIOR_RED=true` **AND** `KERUENIX_DB_URL=jdbc:postgresql:...`. Normal backend tests exclude this intentional failure.
- Accept exactly **1 targeted assertion failure / 0 errors / 0 skipped**, marker present, no compile/bootstrap failure; a green test or unrelated failure must fail CI.
- This is an expected **real-transport behavior RED**, unlike `API_ABSENT_RED` from future cache/job interfaces.

## Qualified versus blocked

| Security/transport oracle | State | Evidence or blocker |
|---|---|---|
| Existing Outbox PostgreSQL claim/fencing, single-tenant RLS | Existing regression PASS | `PlatformOutboxClaimIntegrationTest` |
| Existing transactional Outbox -> Inbox replay after consumer ACK loss | Existing regression PASS | `PlatformOutboxDeliveryIntegrationTest` |
| CustomerAccount-restricted event must not be sent by unguarded transport | **Expected behavioral RED candidate** | Issue #8 targeted assert against existing dispatcher |
| CustomerAccount authorization from *real DB-backed grant source*, including per-operation permission | **BLOCKED** | No approved relation model or authoritative grant repository; BR-03/DEC-R0-02, DEC-CA-01 unresolved |
| Revoke between enqueue/claim/send prevents protected effect | **BLOCKED** | Account-level dispatch guard and grant source absent |
| Cross-account job privilege, service delegation, artifact download | **BLOCKED** | DEC-CA-03/04 and production service entrypoint absent |
| Independent S2 Test Review | **PENDING** | Human QA/Security + domain approvers required |

## Review questions

1. Confirm responsibility: account/operation gate is on a restricted **caller/service port**, **not** on generic Outbox transport (which has no authenticated user). Do not break reusable Outbox transport.
2. Determine precisely when a job requires a fresh grant check; define who can generate service-initiated events and which events are non-sensitive.
3. Decide allowable authority lifecycle across transaction commit, queued processing, and irreversible external side effects. Must distinguish `DENIED`, `AUTH_UNAVAILABLE` and successful dispatched delivery.
4. Approve domain relationship/grants from BR-03/DEC-R0-02 and DEC-CA-01, then write the remaining **real PostgreSQL grant-backed** behavior RED. Avoid a test-only grant registry used to satisfy tests.
5. For tests to be qualified, require an exact-SHA CI log confirming expected assertion, no errors/skips, and preserved existing Outbox recovery regressions.
6. Request independent QA and Security review. **No author's own COMMENT is counted as independent S2 approval.**

**Hard gate:** no production grant schema, job engine, cache, Redis, separate worker or PR-04 domain implementation before the approved decisions and independent test review. PR #3 stays Draft.

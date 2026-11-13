# 69 — G1 RFQ Draft S1 executable test design / RED qualification checklist

**Status: S1 TEST DESIGN READY FOR INDEPENDENT REVIEW; EXECUTABLE AUTHORIZED RFQ RED NOT YET QUALIFIED.** 2026-11-13. Depends on [G0 business decision gate #11](https://github.com/alimbetov/KERUENIX/issues/11), [DEC-CA-01 #4](https://github.com/alimbetov/KERUENIX/issues/4), BR-03, DEC-R0-02. No production account-grant adapter, RFQ controller, migrations or S3 authorization exists yet. The existing [`RfqDraftRedContractTest`](../backend/src/test/java/kz/keruenix/platform/persistence/RfqDraftRedContractTest.java) is **preliminary**: a test-only grant registry and a missing MVC handler do not establish a valid production security RED.

## Test harness and qualified RED definition

1. Start a real disposable PostgreSQL 16/PostGIS database, run approved Liquibase migrations under separate migrator credentials, then application traffic under restricted runtime identity; never test against privileged schema-owner connection.
2. Use a trusted issuer-signed short-lived JWT for `alice` and `bob`; forged/expired/missing JWT cases separate. Do **not** use `mockUser` as account authorization evidence.
3. Use one provider tenant T1, two distinct customer accounts X and Y in T1, plus T2/X2 for tenant isolation. Create **real durable grants** for Alice/T1/X only and Bob/T1/Y only (subject to #4/#11). Disable authorization cache; DB primary is authoritative.
4. Create real RFQ rows through production REST handler only, unless a test explicitly tests migration/DB constraint. Query state using tenant-scoped JDBC and account predicate. Assertions must compare resource IDs and versions, not just row counts.
5. For each executable RED record source/test method, initial and final DB snapshot, response code and body, specific assertion message, zero skipped tests, exact code SHA, CI run URL, owner and approval state.
6. A true **behavioral RED** requires an authenticated request reaching the approved production command boundary, where the missing domain behavior causes a named assertion mismatch. A 403 from global denyAll, HTTP 404 from absent handler, Spring context error, test-only positive grant, compiler failure or arbitrary nonzero Maven exit is **not** a qualified production-domain RED.
7. Do not create production no-op handler solely to manufacture a RED. If the reviewed public port does not exist, label the suite `CONTRACT_UNWIRED` and hold S2 until the trusted boundary is approved, rather than claiming passed/failed behavior.
8. No user-supplied `tenantId`, `customerAccountId`, header, trace baggage, Outbox body or JWT private claim is self-authorizing. Every account operation requires a current persisted operation grant and resource ownership.
9. For parallel request tests, use separate HTTP client sessions and JDBC connections, coordinate with latches/barriers, verify persisted outcome; avoid sleeps and shared static account fixtures that leave pending cross-test events.
10. No test fixture may assume that a green Outbox wrapper means A-03/A-04 have been implemented: both remain targeted RED until independent #9 review and S3.

## Shared deterministic fixture plan

| Identifier | Organization and scope | Purpose |
|---|---|---|
| T1/X | Provider workspace T1, shipper CustomerAccount X | Alice permitted `RFQ_DRAFT_CREATE/READ/UPDATE` |
| T1/Y | Same provider workspace T1, other shipper CustomerAccount Y | Bob separately permitted to Y; must not access X |
| T2/Z | Independent provider tenant T2, shipper CustomerAccount Z | RLS cross-tenant negative case |
| Carol | Has valid JWT, **no** relevant operation grant | JWT-only permissions negative |
| Admin | Has administrative identity but **no** customer operation grant | Deny implicit cross-customer read |
| Grant outage | Primary DB authorization adapter fails/raises typed unavailable result | Fail closed, no protected response or write |

Use random UUID per test and teardown by isolated schema/database. Roles: `keruenix_ci_login` and `keruenix_ci_dispatcher` are test-only role names; never copy passwords into production configuration.

## G1-01…G1-12 Given / When / Then oracles

| ID | Given / When | Required Then (state+security+events) | Main S1 failure marker |
|---|---|---|---|
| G1-01 | Alice has current T1/X CREATE grant; valid mandatory cargo/origin/destination; POST Draft with new scoped key | HTTP 201; location and stable rfq ID; status DRAFT/version=1; tenant=T1, owner=X, actor=Alice; audit and **nonbinding** domain event committed atomically; zero Booking/Quote/Submit | `G1_01_AUTHORIZED_DRAFT_NOT_PERSISTED` |
| G1-02 | Two parallel identical POSTs under Alice/X with same idempotency key and canonical cargo | Exactly 1 persisted RFQ; same original rfq ID; result status/body according to accepted replay contract; no extra audit/outbox event | `G1_02_DUPLICATE_IDEMPOTENT_DRAFT` |
| G1-03 | Reuse original Alice/X key with changed cargo, unchanged authorization | HTTP 409 and stable error code; original payload/version unchanged; no new event | `G1_03_IDEMPOTENCY_PAYLOAD_CONFLICT_NOT_ENFORCED` |
| G1-04 | Bob has only Y grant in same tenant T1; GET/PATCH X's existing draft; list and count X | Fail without revealing resource existence or contents under selected 403/404 policy; zero X mutation; no X count/cursor leakage | `G1_04_SAME_TENANT_ACCOUNT_LEAK` |
| G1-05 | Valid Alice JWT plus body/header/account mismatch or Alice JWT claims manipulated; attempt CREATE under Y/T2 | No unauthorized X/Y/T2 write or event; mismatch/forgery denied at trusted boundary | `G1_05_UNTRUSTED_SCOPE_ESCALATION` |
| G1-06 | Alice can read X; admin revokes X READ grant in PRIMARY DB and commits audit; Alice retries same JWT | Next GET denied; no stale decision grants access; unrelated WRITE grant unaffected if policy permits | `G1_06_REVOKED_GRANT_REMAINS_EFFECTIVE` |
| G1-07 | Primary authorization read unavailable; Alice attempts valid CREATE | Fail closed; zero new aggregate/audit/outbox mutation; classified as auth dependency failure, not permissive fallback | `G1_07_AUTH_STORE_OUTAGE_FAIL_OPEN` |
| G1-08 | Two concurrent PATCH requests to same X draft with same version/ETag but differing cargo | Exactly one new revision; other conflict per version contract; final snapshot corresponds to winner only | `G1_08_LOST_UPDATE` |
| G1-09 | Inject controlled failure after real aggregate mutation and before audit/outbox commit | Transaction rolls back aggregate plus related audit/event; no orphan or partial effect | `G1_09_NONATOMIC_AGGREGATE_AUDIT_OUTBOX` |
| G1-10 | Alice has CREATE/READ/UPDATE, no binding operation grant; invoke Submit, Quote, Booking | No binding handler/action/event, no carrier data disclosure, no booking | `G1_10_DRAFT_ESCALATES_TO_BOOKING` |
| G1-11 | Reuse one real Hikari physical connection sequentially across T1/X then T2/Z | No stale tenant settings or account cross-contamination, tenant context resets on commit/rollback | `G1_11_POOLED_CONNECTION_SCOPE_LEAK` |
| G1-12 | Persist X Draft; restart application context; Alice GET with fresh JWT/current grant; Bob probes list/export | Alice obtains same durable snapshot and version; Bob cannot read or export X; no test-memory dependence | `G1_12_DRAFT_NOT_DURABLE_OR_EXPORT_LEAK` |

**Required complementary checks**: blank/null/negative quantity, unit normalization, overlong text and contact field input validation; attempt to mutate accepted status from Draft without approved state transition; idempotency key collision between X/Y and actors; revoke during retry; event digest and dead-letter correctness after #9 approval.

## Contracts requiring explicit decisions before compiling RED

| Blocker | Required choice | If missing |
|---|---|---|
| BR-03 / DEC-R0-02 / #11 | Legal entity ↔ provider tenant ↔ CustomerAccount mapping, optional carrier relationship and authorized party | No trusted resource resolution / no real grant table |
| DEC-CA-01 / #4 | Grant status, operation name, membership effective times, revision/epoch and current-read transaction semantics | No valid G1-01/04/06/07 auth oracle |
| G0-BR-04 | Required cargo fields, units, pickup time and PII bounds | No stable canonical request fingerprint |
| G0-BR-05 | Idempotency key scope, replay status/body, retention, If-Match vs 409/412, 403 vs 404 | No fixed G1-02/03/08 HTTP assertion |
| DEC-R0-03 | Meaning and legal authority of Submit, Quote, Booking | G1-10 remains deny only |
| Independent Outbox S2 #9 | Correct A-03 digest, poison event policies and external receiver | G1 audit/outbox may be tested as DB atomicity; no claim of qualified external dispatch |

## Engineering work items — only after owner decisions

1. S1a: write real-Postgres **grant-negative** cases G1-04…07/11 against the accepted `CustomerAccountAuthorization` port; distinct current-grant adapter and tenant scope. Ensure denial cannot be confused with missing handler or global denyAll.
2. S1b: write positive Draft behavior G1-01…03/08/09/12 through accepted HTTP API and explicit resource ownership. Capture expected RED signatures; reject arbitrary failures.
3. S1c: S2 independent QA/Security/DB review at exact SHA, followed by minimal S3 implementation in a dedicated Draft PR; keep PR #3 foundation stable.
4. S4: re-run regressions on real PostgreSQL, restart/in-flight failure injections, observability/audit and actual customer-save/reopen demonstration. Merge only after independent acceptance.

**Current verdict:** G1 S0/S1 test design **READY FOR REVIEW**; approval and executable real-authorized G1 RED **BLOCKED** pending owner decisions. This document does not add 12 new scenarios to the approved 132-count until existing register reconciliation.

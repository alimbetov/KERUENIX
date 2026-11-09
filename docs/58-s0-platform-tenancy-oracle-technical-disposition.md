# 58 — Platform/Tenancy S0 oracle review: technical disposition (2026-11-09)

**Stage:** S0 Scenario Design. **Disposition:** TECHNICAL_REVIEW_PROPOSED / HUMAN_APPROVAL_PENDING. **Scope:** PR-01, PR-02, PR-03C, PR-03, plus PR-04 safe RFQ Draft dependency. **No S1 RED claim, no S2 Test Review, no legal approval, no production feature activation.**

Sources: `51-s0-platform-tenancy-test-design-review.md`, `57-s0-completeness-audit.md`, `contracts/r0-s0-platform-tenancy-case-contracts.v1.json`, `contracts/r0-decision-readiness.v1.json`, `52-s0-commercial-test-design-review.md`.

## Technical review outcome

The existing 32-case design is sufficiently complete for a **focused technical oracle refinement**, but **not** for blanket S0 signoff. The 12 FOUND cases and 20 active/cross-owner cases retain their canonical IDs, PR owners and original GWT. This memo is a reviewer *proposal*, not a fabricated reviewer signature. A test must be compiled and runnable and fail on an unmet behavioral assertion (not a missing class/import), with exact SHA and real execution evidence.

| Case / boundary | Precise required oracle | Test level / execution | Reviewer disposition |
|---|---|---|---|
| FOUND-04 | Induce exception **after** aggregate + audit + outbox inserts and **before** commit. Query using an independent connection after rollback: all three absent for the unique command correlation ID. No external publication or 2xx acknowledgment. Control run commits all three with matching correlation and aggregate version. | PostgreSQL Testcontainers; transactional integration, post-rollback independent SELECT | Proposed technical oracle; confirm transaction API and auditing taxonomy |
| FOUND-09 | Run `ApplicationModules.verify()` for production modules; a separately compiled negative fixture with a deliberately forbidden direct repository dependency must fail **at module verification**, whereas the allowed named-interface fixture passes. Do not add a permanently broken import to production compilation. | Spring Modulith architecture test + negative fixture separate test configuration/module | Proposed technical oracle; reviewer must approve module metadata map |
| FOUND-10 | Cold empty DB migrate V1→V2, populated V1→V2, second migration run, checksum-mismatch halt, and restore/re-migrate. Validate retained sample row IDs/digests, constraint/index/RLS definitions and Liquibase history; runtime app principal cannot perform DDL. Distinguish migration role from application runtime role. | PostgreSQL/PostGIS + Liquibase Testcontainers; migration / restore | Proposed; specify golden V1 snapshot and measurable restore evidence |
| FOUND-12 | Validate lon ∈ [-180,180], lat ∈ [-90,90], finite numbers, SRID 4326; query geography meters (not geometry degrees), test near/just-outside boundary around a known distance with explicit tolerance. Prove A sees only A, B sees no A, and X cannot see Y geodata inside A through customer ABAC. No cross-account count/extent/facets. | PostGIS DB integration + API negative tests | Proposed; agree distance tolerance and scope for service jobs |
| FOUND-01/02/03/08/11 | Restricted DB role without BYPASSRLS, `FORCE RLS`, tenant context transaction-local across reused physical connection, server-resolved principal/grants (not header/body/JWT tenant authority). Account X/Y isolation within provider A for count/list/facets/export/cache. Invalid JWT 401; verified unauthorized request 403 or nondisclosing 404 by endpoint policy. | Security HTTP, RLS Testcontainers, ABAC access matrix | Proposed; explicit HTTP status mapping still needs owner/API review |
| FOUND-05/06/07 | Inbox dedup keyed by consumer+event ID and canonical digest; H1/H2 mismatch quarantined. Only active fencing-token holder may ACK. Crash after effect and before ACK delivers at least once but produces one logical effect. | Concurrent PostgreSQL, recovery fault injection | Proposed; event identity and side-effect boundary to be reviewed |
| CustomerAccount / TDD-SIM-05-G03-01…05 | No provider employee Membership derived from partner grant. Canonical CustomerAccount writer is proposed in Commercial only, never duplicated in Tenancy. Access is grant + resource + customer-account + tenant checked at every query; unrelated account X/Y denied. **Positive relationship activation remains DENY/HOLD** pending BR-03 and DEC-R0-02. | ABAC API + DB/data ownership, integration contract tests | Negative tests eligible; positive binding blocked |
| NEG-R0-001…008/040/043 | Last owner and self-approval safety; revoke affects new decisions with same still-valid JWT; no mass-revocation of colleagues; no secrets/contacts/margin/coordinates in support surfaces. Previously issued signed URL is not claimed instantly revoked absent dedicated policy. | Concurrent owner, revoke stream/export, log-redaction tests | Negative technical design eligible; in-flight/URL semantics need explicit review |
| PR-04 RFQ Draft / NEG-R0-011 | Safe draft operation only with verified account-scoped actor and no unapproved relationship inference. Idempotency identity = authenticated subject + tenant + CustomerAccount + operation + key; same canonical payload repeats with same draft ID, changed payload yields RFC9457 409 and leaves original cargo snapshot unchanged. A draft MUST NOT emit RFQ_SUBMITTED, QUOTE_ISSUED, BOOKING_CONFIRMED or other binding events. | API + PostgreSQL + Outbox; replay, wrong-account, cross-tenant | Proposed bounded S1 candidate after actor/grant fixture is approved; RFQ Submit blocked by DEC-R0-03 |

### Required negative assertions (not optional)

Every denied command checks **(1) HTTP ProblemDetail/error code, (2) no forbidden aggregate/audit/outbox/inbox mutation, (3) no external side effect**, with a query on an independent DB session after transaction completion. A denial may have a separate security telemetry record, but never a domain-success audit/event. Avoid a blanket assertion of *zero audit rows* if security denial auditing is intentionally supported.

Do not treat an HTTP `200` or data-less `404` alone as proof of tenant isolation; verify result sets, counts, facets, cursors, cache keys, exports, background job context and PostGIS search. Privileged SQL or an untrusted writable custom GUC is not sufficient authority.

### Safe executable S1 batch order (only after technical S0 oracle acceptance)

1. PR-01 `FOUND-04` rollback atomicity; `FOUND-09` module verification; `FOUND-10` Liquibase upgrade/drift; `FOUND-12` PostGIS meter + tenant/customer scope.
2. PR-01/02 `FOUND-01/02/03/08/11` and revoke/identity negative tests.
3. PR-03C/03 CustomerAccount data isolation + ownership/grant-negative contracts (no positive legal relationship activation).
4. PR-04 safe RFQ Draft: replay/collision, count visibility and nonbinding event assertion. Do **not** enable Submit, Quote, Booking or signatures.
5. Outbox/concurrency, owner safety and revocation failure injection; followed by separate S2 reviewer evidence.

**Gate for any S1 execution:** documented module lead and QA/Security reviewer acknowledgment of each selected oracle, exact error catalog decision, synthetic fixture, explicit outcome for unresolved BR/DEC, and an exact test-run SHA. This document alone is not that acknowledgment.

## Open decisions and required reviewers

- `BR-03`, `DEC-R0-02`: verified customer-provider relationship, canonical CustomerAccount writer. Domain + Security + commercial accountable approver.
- `DEC-R0-03`: RFQ Submit authority and boundary between DRAFT and binding request. Commercial + Legal.
- `BR-01/02/05`: Quote issue/accept/decline authority. Legal + customer representative.
- `BR-04`: privileged continuity action after subscription lapse. Legal + Security.
- `DEC-R0-07`: financial scope / margin visibility; payments remain excluded.
- Technical unresolved: endpoint-specific 401/403/404 + RFC9457 error codes; exact migration golden V1; PostGIS distance tolerance; owner-transfer transactional ordering; in-flight revoke semantics.

**Explicit preserved statuses:** 20/20 BR/DEC pending; 0 completed human Test Reviews; S0 proposed only; PR #1 Draft; no main merge; no payments.

# 59 — S1 corrective cycle evidence and S2 Test Review gate

**Status:** S1_CANDIDATE — **NOT S2 APPROVED**. This document is an audit checklist, not a release decision. Target PR: [#3](https://github.com/alimbetov/KERUENIX/pull/3), branch `test/s1-platform-tenancy-oracles`.

## Scope and isolation

- FOUND-04: transaction triplet (aggregate, audit, outbox) rollback / commit control with tested aggregate ID/version correlation. Synthetic fixture only; not a real PR-04 aggregate.
- FOUND-09: separate compilable forbidden import fixture, Spring Modulith verifier; production module graph must independently verify.
- FOUND-10: V1 migration; populated Outbox/Audit fixture, `pg_dump -Fc`, independent `pg_restore`; both source and restored database upgraded to V2; require identical data digest, changelog count and FORCE RLS. Independent checksum-drift DB and refusal of legacy Flyway auto-upgrade remain separate guards. Backup/restore qualification here is limited to a *disposable CI PostgreSQL instance*, not disaster recovery of production.
- FOUND-12: geography meters + tenant RLS are supported; invalid coordinate tests, CustomerAccount geographic read-model ABAC and per-service job scope remain **open**.
- CustomerAccount: synthetic signed-JWT -> test grant -> tenant JDBC -> same-tenant account-isolated list/count, cursor, export and facets, plus immediate revocation. These test-only endpoints and `audit_fact.subject_ref` are **not** production CustomerAccount writer, export, cache or API architecture.
- RFQ Draft: dedicated test-only signed JWT security matching `/api/v1/rfqs/**` allows **authenticated** draft path to be resolved through MVC, so missing handler cannot be confused with production `denyAll`. The same test-only chain explicitly denies `POST .../submit`. No fake success handler and no production endpoint are introduced. Idempotent draft and changed-cargo conflict behavior remain intentionally unimplemented RED.
- CI script `scripts/ci_assert_rfq_draft_red.sh` runs all four RFQ tests and only accepts the *exact* current expected missing-handler RED signature; any infra/compilation/context error must fail the job. An expected-RED classification is not a passing domain test.

## Exact SHA S1 gate (must attach actual CI logs, not assume)

1. Record PR head SHA immediately before review; check both `Backend Error Contract` and `PR-01 PostgreSQL Platform Foundation` were actually run **against that exact SHA** and both concluded success.
2. Verify FOUND-09 negative fixture detects a forbidden internal dependency, rather than a scanner/bootstrap exception.
3. Check real PostgreSQL integration section reports **zero skipped tests** and validates FOUND-04, FOUND-12, JWT/ABAC, Outbox and Inbox.
4. Confirm full FOUND-10 snapshot stage was executed; both V1->V2 upgrades and restore checks pass with *populated records*, correct IDs/payload, changelog count=2 and FORCE RLS. Ensure backup step is before V2 migration.
5. Confirm RFQ suite is executed (4 tests). The expected-RED wrapper must verify **two targeted missing-handler behavior failures, zero test errors; foreign-account and Submit denials must pass**; the legal Submit denial must pass. Do not treat an arbitrary nonzero exit as valid RED.
6. Verify no test-only positive authorization route is registered in production application packages; no main merge or business-domain implementation in PR #3.

## Open blockers for independent S2 Test Review

- S0 approvals from authorized module owners and QA/security; no human or legal authority approval can be inferred from CI.
- Contract choice for RFC 9457 response, RFQ Draft identifier, account-scoped idempotency canonical hash, persisted cargo snapshot and permitted non-binding events.
- Real CustomerAccount relationship semantics (BR-03, DEC-R0-02), same-account employee grants, provider visibility boundary, service jobs/cache/export policies.
- FOUND-12 lat/lon and SRID validation, meter tolerance specification, CustomerAccount geographic isolation and facet leakage.
- More comprehensive backup/restore consistency evidence including RLS policies, constraints, role privileges, and actual recovery runbook. This new CI test alone is not production DR acceptance.

**Decision:** retain `Draft`, no approval, no PR-04 domain implementation, no binding Submit/Quote/Booking, no Payments. 20 BR/DEC remain pending; they must be reviewed by designated owners. S2 starts only after exact-SHA evidence and independent test review.

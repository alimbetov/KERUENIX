# 44 — PR-01 TDD evidence: FOUND-02 nested transaction tenant isolation

**Date:** 2026-11-08 · **PR:** PR-01 / RD-01 · **Owner:** platform · **Status:** VERIFIED PARTIAL / NOT_QUALIFIED.

Contract: [FOUND-02 in R0 TDD Start Pack](36-r0-tdd-start-pack.md), [10-layer ТЗ](43-layer-by-layer-development-tz.md), [PR-01 machine acceptance](contracts/pr-acceptance-manifest.v1.json). This record reports a real RED→GREEN cycle but does **not** qualify the entire PR-01 or authorize any domain endpoint.

## 1. Given / When / Then

Given an outer `PlatformTenantTransaction.execute(Tenant-A)` uses a physical JDBC transaction, and an inner call uses Spring `TransactionTemplate` with `PROPAGATION_REQUIRED`.

When the nested call requests `Tenant-B` on the same physical connection, it must fail closed **before** changing PostgreSQL transaction-local `keruenix.tenant_id`. A nested call to Tenant A is permitted. If the outer operation fails, all its writes must roll back.

Additional oracle: Hikari maximum pool size **1**; capture `pg_backend_pid()` and assert the exact same PostgreSQL physical connection is reused across Tenant A → Tenant B → Tenant A, while no foreign rows can be read and the tenant setting is reset after commit.

## 2. Evidence: actual RED before implementation

- **Test-only commit:** [d9ed503050e9ed68e5ff71e095124d679ad0054e](https://github.com/alimbetov/KERUENIX/commit/d9ed503050e9ed68e5ff71e095124d679ad0054e).
- **RED CI:** [PostgreSQL Platform Foundation run 42467406336](https://github.com/alimbetov/KERUENIX/actions/runs/42467406336).
- Failure: `PlatformDatabaseIntegrationTest.nestedCrossTenantTransactionIsRejectedAndOuterWriteRollsBack` — `Expecting code to raise a throwable`. One failing real-PostgreSQL assertion proved that the original code switched tenant silently inside an existing transaction. This is a security regression, not a simulated or intentionally failing stub.

## 3. GREEN implementation and refactor

- **Fix commit:** [795d1d399bdf02481ef585f6fcee1fce62a061d5](https://github.com/alimbetov/KERUENIX/commit/795d1d399bdf02481ef585f6fcee1fce62a061d5). Before `set_config(..., true)`, the transaction helper reads existing tenant context; a conflicting active tenant raises `SecurityException`, so PostgreSQL transaction is rolled back. Nested calls with the same tenant remain allowed.
- **Test/refactor commit:** [1613180b277bcf365a0790da9204bb4373b7fa58](https://github.com/alimbetov/KERUENIX/commit/1613180b277bcf365a0790da9204bb4373b7fa58). Adds one-connection Hikari proof with `pg_backend_pid()` and RLS read assertions.
- **Exact-SHA GREEN PostgreSQL CI:** [run 42467668385](https://github.com/alimbetov/KERUENIX/actions/runs/42467668385).
- **Exact-SHA other CI:** [Backend Error Contract 42467668374](https://github.com/alimbetov/KERUENIX/actions/runs/42467668374), [TDD Roadmap Contract 42467668422](https://github.com/alimbetov/KERUENIX/actions/runs/42467668422).

## 4. Important limitations

The helper still accepts a UUID supplied by **trusted calling server code**. This TDD cycle does not authenticate a JWT, authorize a CustomerAccount, prevent arbitrary SQL from manually setting a PostgreSQL custom GUC, or provide a complete per-request permission boundary. Those are separate `FOUND-03`, `FOUND-08`, `FOUND-11` and PR-02/03/03C obligations.

RLS alone is not application authorization. This test used the CI PostgreSQL/PostGIS service and isolated Hikari pool, not a Java Testcontainers-managed PostgreSQL container; the requested Testcontainers qualification remains open.

**Not yet qualified:** `FOUND-05` broker crash→logical consumer effect, `FOUND-08` two-customer scope, complete `FOUND-09` negative module fixture, `FOUND-10` restore and release. Never promote PR-01 or RD-01 from this evidence alone.

## 5. Next TDD gate under current ТЗ

`FOUND-05` is a candidate for the next RED→GREEN cycle: committed Outbox event, crash after consumer effect but before publisher ack, replay through Inbox without duplicate logical side effect. This requires a real producer/consumer path, not merely a SQL claim helper. Alternatively the prerequisite `FOUND-03` trusted JWT→Tenant binding must be proven before activating HTTP business commands.

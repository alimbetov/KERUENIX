# KERUENIX Backend — error-handling bootstrap

This is **a minimal Java 21 / Spring Boot 4.1.2 bootstrap only**, not a working logistics backend or R0 release.

Includes:
- `ApiProblemFactory`: one RFC 9457 Problem Details contract shared by Spring MVC and Security filters.
- `ApiExceptionHandler`: MVC validation/framework/typed-domain/unknown error mapping with generic public details.
- `SecurityProblemHandler`: 401/403 before MVC, using the same public code registry and JSON contract.
- `ApiFallbackErrorController`: servlet `/error` dispatch when MVC/Security advice cannot handle an error.
- `RequestIdFilter`: server-generated UUID requestId, header and MDC.
- `SecurityConfig`: **fail-closed** `anyRequest().denyAll()`. No JWT/real user login, no Tenancy, no domain endpoints, no accidental public business route.
- `ErrorContractTest`, `SecurityErrorContractTest`, `ErrorCodeCatalogTest` and `FallbackErrorControllerTest`: **written; 15 error contract tests and the JSON/Java parity gate passed on commit `ac459923` (GitHub Actions #22); further revisions require exact-SHA verification**.

## Local build

Install JDK 21 and Maven 3.6.3+ and run:

```bash
mvn -f backend/pom.xml test
mvn -f backend/pom.xml verify
```

**Qualification:** GitHub Actions `Backend Error Contract` run #22 compiled and passed 15 JUnit tests plus the 21-code Java/JSON parity check on commit `ac459923` (0 failures/errors/skips). Later commits must be checked on their own SHA. Local Maven is unavailable in the execution container. These tests do not demonstrate PostgreSQL RLS or business-domain acceptance. Do not interpret these tests as security/RLS/business acceptance.

## PR-01 first PostgreSQL foundation slice (partial)

The repository now contains `src/main/resources/db/migration/V1__platform_outbox_inbox_rls.sql` and `db/admin/bootstrap_roles.sql`, plus a real PostGIS service job `PR-01 PostgreSQL Platform Foundation`. The SQL provides tenant-first compound keys for Outbox/Audit, a tenant-scoped Inbox, `FORCE ROW LEVEL SECURITY`, transaction-local tenant context and distinct NOLOGIN runtime/dispatcher capability roles. It does **not** create operational user credentials or enable application DB connectivity.

The GitHub Action runs `bash scripts/test_pr01_pg_foundation.sh` against PostgreSQL 16/PostGIS 3.7 with disposable credentials, checking absent tenant context, A→B connection reuse, forbidden foreign writes, same-UUID cross-tenant independence, audit/outbox/inbox rollback, Inbox uniqueness and geographic distances in meters. The runtime role has no superuser/DDL privileges; migration and role provisioning require a separate privileged step.

**This is only an initial SQL/CI slice**, not qualified PR-01: no Spring datasource/Flyway auto-migration, JWT binding, customer-account ABAC, dispatcher lease/replay, Modulith verification, backup restore or all `FOUND-01..12` implemented. The custom session parameter is untrusted unless exclusively set by server code after authenticated authorization within a database transaction. Do not expose any business endpoint on the basis of this smoke.

## Integration rules

The application **intentionally denies ordinary user-initiated routes** (servlet ERROR dispatch is permitted solely for safe error formatting) until a separate Tenancy/JWT feature introduces a tested `SecurityFilterChain` with explicit permissions and public health endpoints. Do not disable authentication to make a smoke test pass. Spring Security filter failures require their own entry point and denied handler, unlike MVC `@RestControllerAdvice`.

For R0 domain implementations, convert known aggregate guard failures to `DomainProblemException(ErrorCode.*)` only **after** server-derived subject/tenant/CustomerAccount checks. Catch recognized named SQL constraints inside the owning repository adapter, never map all `DataIntegrityViolationException` or foreign RLS failures to `409`. Keep the error catalog in [docs/contracts/api-error-catalog.v1.json](../docs/contracts/api-error-catalog.v1.json) synchronized with Java `ErrorCode`.

Outstanding acceptance:
- exact Maven compile and all JUnit tests;
- security filter + validation/error contract behavior on real Boot 4.1.2;
- Spring Modulith API boundary qualification;
- PostgreSQL Testcontainers/RLS and concurrency;
- real JWT/tenant authorization;
- full `/error` servlet dispatch and error response integration;
- propagation/localization and production metrics;
- legitimate idempotent application-level retry headers and job failure classification.

The repo workflow also checks Java ErrorCode parity with the JSON catalog before running Maven tests. No new business endpoints are available in this bootstrap.

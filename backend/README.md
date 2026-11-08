# KERUENIX Backend — platform foundation (in progress)

This is **a minimal Java 21 / Spring Boot 4.1.2 bootstrap only**, not a working logistics backend or R0 release.

Includes:
- `ApiProblemFactory`: one RFC 9457 Problem Details contract shared by Spring MVC and Security filters.
- `ApiExceptionHandler`: MVC validation/framework/typed-domain/unknown error mapping with generic public details.
- `SecurityProblemHandler`: 401/403 before MVC, using the same public code registry and JSON contract.
- `ApiFallbackErrorController`: servlet `/error` dispatch when MVC/Security advice cannot handle an error.
- `RequestIdFilter`: server-generated UUID requestId, header and MDC.
- `SecurityConfig`: **fail-closed** `anyRequest().denyAll()`. No production JWT issuer/grant configuration or live user login, no Tenancy aggregates or domain endpoints. JWT verification is exercised through a test-only route; production remains denyAll.
- `ErrorContractTest`, `SecurityErrorContractTest`, `ErrorCodeCatalogTest` and `FallbackErrorControllerTest`: **written; 15 error contract tests and the JSON/Java parity gate passed on commit `ac459923` (GitHub Actions #22); further revisions require exact-SHA verification**.

## Local build

Install JDK 21 and Maven 3.6.3+ and run:

```bash
mvn -f backend/pom.xml test
mvn -f backend/pom.xml verify
```

**Qualification:** GitHub Actions `Backend Error Contract` run #22 compiled and passed 15 JUnit tests plus the 21-code Java/JSON parity check on commit `ac459923` (0 failures/errors/skips). Later commits must be checked on their own SHA. Local Maven is unavailable in the execution container. These tests do not demonstrate PostgreSQL RLS or business-domain acceptance. Do not interpret these tests as security/RLS/business acceptance.

## PR-01 first PostgreSQL foundation slice (partial)

The repository now contains `src/main/resources/db/changelog/db.changelog-master.yaml` with PostgreSQL V1/V2 Liquibase changesets and `db/admin/bootstrap_roles.sql`, plus a real PostGIS integration job. This provides tenant-first compound keys for Outbox/Audit, tenant-scoped Inbox, `FORCE ROW LEVEL SECURITY`, transaction-local tenant context and separate NOLOGIN runtime/dispatcher capability roles. The application JDBC integration is tested under restricted credentials, but operational user provisioning and actual domain routes are not implemented.

The GitHub Action runs `bash scripts/test_pr01_pg_foundation.sh` against PostgreSQL 16/PostGIS 3.7 with disposable credentials, checking absent tenant context, A→B connection reuse, forbidden foreign writes, same-UUID cross-tenant independence, audit/outbox/inbox rollback, Inbox uniqueness and geographic distances in meters. The runtime role has no superuser/DDL privileges; migration and role provisioning require a separate privileged step.

**This is still PARTIAL PR-01**, not qualified: Spring JDBC, Liquibase, JWT signature tests with an isolated in-memory grant fixture, customer scope denial, Outbox transport replay, and RLS are tested. Persistent verified membership, real broker delivery, backup/restore and the entire `FOUND-01..12` suite remain incomplete. The custom session parameter is untrusted unless exclusively set by server code after authenticated authorization within a database transaction. Do not expose any business endpoint on the basis of this smoke.

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

## Spring Boot database profile (PR-01 work in progress)

Profile `platform-db` configures an application-only PostgreSQL JDBC connection
and a distinct privileged Liquibase migration connection; all secrets are supplied by
`KERUENIX_DB_*` environment variables. The base error test excludes JDBC/Liquibase
startup and keeps `denyAll` security unchanged. A dedicated GitHub Action creates
a disposable **second database**, applies V1 through Spring Boot/Liquibase and checks
the runtime user is not superuser, FORCE RLS, A/B tenant transaction reset, same
cross-tenant UUIDs, atomic rollback, Inbox changed-digest rejection and PostGIS.

`PlatformTenantTransaction` remains package-private: there is **no trusted
JWT → TenantAuthority bridge** yet and no REST business API. These tests cannot
be used to claim PR-02 or the complete PR-01 FOUND-01..12 suite is ready.

## Runtime privilege separation (PR-01 security gate)

The long-running `platform-db` profile has `spring.liquibase.enabled=false`
and requires ONLY `KERUENIX_DB_APP_*` credentials. Liquibase DDL runs in a **separate
short-lived migration job** with `platform-db-migrate-test`, never in
production application pods. CI verifies both a Spring/Liquibase-admin migration
process and an independent `RuntimeDatabaseProfileTest` that boots with the
migrator environment variables absent. The ephemeral test migrator must not be
taken as evidence of production bootstrap/rotation orchestration.

## Durable dispatcher claim/fencing baseline (PR-01 partial)

Liquibase `V2__outbox_claim_fencing.sql` adds a per-tenant, monotonic
`claim_token`, worker ownership, lease, retry timestamp, attempt count and
published timestamp to the existing transactional Outbox. Internal
`PlatformOutboxClaims` uses `FOR UPDATE SKIP LOCKED` to select one event,
commits claims before any potential network I/O, and checks owner/token/
unexpired lease on ack/retry. A separate restricted dispatcher role is used in
four concurrent real-PG tests. Stale workers cannot acknowledge or reschedule
an event taken over by another worker.

**Not a production dispatcher:** no broker publisher, tenant discovery
control-plane, poison/DEAD_LETTER policy, attempt backoff algorithm, metrics,
cross-system consumer integration or external delivery E2E has been delivered.
At-least-once delivery remains expected; the Inbox must protect logical
consumer side effects.

## Liquibase-only migration management

**Authoritative schema history:** `src/main/resources/db/changelog/db.changelog-master.yaml`, which includes two ordered PostgreSQL formatted-SQL changeSets in `db/changelog/changes/`. Spring Boot 4.1.2 uses `spring-boot-starter-liquibase`. Flyway migration files are removed from the runtime classpath.

CI proves initial migration on empty PostgreSQL/PostGIS, repeated Liquibase startup with no duplicate application, and upgrade from a separate database containing only Liquibase V1 to V2. Liquibase stores history and locks in `DATABASECHANGELOG` and `DATABASECHANGELOGLOCK`. The independent SQL smoke executes the same versioned SQL content, but it does not replace Liquibase migration testing.

Long-running profile `platform-db` explicitly has `spring.liquibase.enabled=false` and only application credentials. A separate `platform-db-migrate-test` profile lives under `src/test/resources` and is excluded from the production JAR; production requires a short-lived migration job with separate DBA-administered credentials.

**Legacy Flyway databases:** do not auto-run Liquibase on an existing populated Flyway schema, drop `flyway_schema_history` or blindly call `changelogSync`. A separate approved cutover must inventory schema and grants, snapshot/restore, map historical versions and verify each new changeSet against actual catalog state before formally recording a baseline. No such production cutover is claimed here.

RLS, tenant-first primary keys, deferred no-payments scope and separation of migration/runtime roles remain mandatory. All 26 PR acceptance entries remain `NOT_QUALIFIED`.

## TDD review checkpoint — FOUND-03/05/08/11

[Detailed RED → GREEN review record](../docs/45-pr01-found03-found05-found08-review-checkpoint.md).
The test-only `/__qualification/**` HTTP controller and RSA private test key are NOT
included in the production JAR. The production servlet `SecurityConfig` still
uses `denyAll`. `TenantScopeAuthorization` enforces that only a Spring Security
verified `JwtAuthenticationToken` plus a server-side grant source can select
Tenant+CustomerAccount; JWT tenant claims and attacker-supplied selectors alone
never grant access. No persistent source is shipped yet.

`PlatformOutboxDelivery` is a narrowly scoped at-least-once transport port:
an Outbox event may be re-sent after crash; the test consumer proves one logical
Inbox+Audit effect. There is still NO external broker adapter, lifecycle
scheduler, tenant discovery controller or operational DLQ. A sender is forbidden
inside an open business transaction.

All three milestones are evidenced by exact-SHA CI and the PR acceptance
manifest; PR-01 and all domain modules remain `NOT_QUALIFIED`.

# 36 — R0 TDD Start Pack: PR-00 and PR-01 (готовые задания разработчикам)

**Версия:** 1.0.0 · **Дата:** 2026-11-08 · **Статус:** `READY_FOR_ENGINEERING_REVIEW / IMPLEMENTATION NOT STARTED / CI NOT EXECUTED FOR DOMAIN`.

**Execution scope:** [35 — R0 Developer Handbook](35-r0-developer-handbook.md), [33 — Roadmap v1.4](33-tdd-development-roadmap-v1.md), [R0 Decision Contract](contracts/r0-delivery-contract.v1.json).

## 1. PR-00 — Scenario/ADR traceability qualification (owner: architecture)

**Objective:** produce code-ready first decisions while distinguishing accepted, proposed and intentionally denied workflows. PR-00 can close when BR-01..12 are honestly recorded as pending — a fake signoff is a blocking failure. This is not a legal/finance product acceptance.

### Work items

1. Create an ADR per disputed canonical resource: `Order` read-only composition versus aggregate; Commercial `CustomerAccount` versus Tenancy grants; custody `ProofReceipt` versus Documents package; Invoice/AR/AP ownership. Require reviewed rationale, alternative, risk, event contract and migration consequence.
2. For each [DEC-R0-01..08](contracts/r0-delivery-contract.v1.json), attach owner, `PENDING/APPROVED/REJECTED`, stage/PR gate, fail-safe rule, evidence link and reviewer authority. Do not keep identity documents or secrets in public repo.
3. Assign `USB → BSC → BR/ADR → AUTH → command owner → TDD-SIM/NEG → expected UI state` for the first `PR-02..05`; retain unapproved `customer:rfq:submit` as disabled.
4. Confirm `Order` is *proposed* derived read-only projection, with a stable customer-safe `orderRef` and no second writes.
5. Freeze the first synthetic test fixture (Tenant-A provider, Customer-X/Y same provider, Tenant-B, Carrier-C, 10 CargoUnits, revoked user, stale JWT/cache, two fleet bookings).

**Exit criteria:** no duplicate canonical writer, no unapproved elevated permission, unique IDs and stage DAG validated by CI, each R0 decision explicitly pending or evidence-backed approved. A document may be `DOC_QUALIFIED` while `BUSINESS_SIGNOFF=PENDING`.

## 2. PR-01 — Platform Foundation (owner: platform; real code required)

**Goal:** one Spring Boot Java21 runtime and true PostgreSQL/PostGIS persistence + tenant-scoped application access + atomic Outbox/Inbox + failing-first tests. Extend the existing RFC9457 error-only bootstrap; do not create arbitrary business controllers to demonstrate it.

### Minimum architecture

```text
backend/
  pom.xml                      # verified BOMs / Java21 / Enforcer / JaCoCo
  src/main/java/kz/keruenix/
    platform/errors/           # existing RFC9457
    platform/security/         # verified principal context / denyAll until auth ready
    platform/persistence/      # Flyway, tenant-scoped RLS connection policy
    platform/events/           # atomic Outbox publisher and Inbox dedup contract
    platform/evidence/         # future EvidenceBlobGateway port, no storage engine now
    tenancy/                   # module boundary only; business aggregate later PR-02
  src/main/resources/db/migration/
  src/test/java/kz/keruenix/
    architecture/             # Spring Modulith verification
    platform/rls/             # real Testcontainers PostgreSQL/PostGIS
    platform/outbox/          # atomic transaction/replay
    platform/security/        # session/header trust tests
```

This is a **proposed package layout**; packages are not existing code. Pick actual Spring Modulith, MapStruct, Flyway, Testcontainers compatibility from compile/run evidence; do not infer from a dependency matrix. Do not choose H2 as substitute for PostgreSQL RLS or exclusion constraints.

### Mandatory red-first cases

| ID | Given | When | Required Then / technical oracle |
|---|---|---|---|
| `FOUND-01` | app DB principal with no `BYPASSRLS`, tenant context unset | select protected row | deny/zero access according to policy, never all tenants |
| `FOUND-02` | Tenant-A uses pooled Connection-1, then Tenant-B obtains same physical connection | B queries A row | no A data; transaction-local tenant context reset proven |
| `FOUND-03` | trusted authentication context Tenant-A, request body/header claims Tenant-Z | command is invoked | request-supplied tenant ignored/rejected, DB write stays A or DENY |
| `FOUND-04` | app writes aggregate+audit+outbox | throw before DB commit | none of the three records persists |
| `FOUND-05` | DB commit succeeded, outbox dispatch dies before ack | restart dispatcher twice | exactly one logical consumer effect, durable event retained until ack |
| `FOUND-06` | inbox event id E already applied with payload digest H1 | reprocess same E with H2 | conflict/quarantine; no silently accepted mutation |
| `FOUND-07` | two worker instances claim same due job | simultaneous claim/reclaim | one fenced lease owner, no stale worker commit |
| `FOUND-08` | Tenant-A + Customer-X/Y share provider | X/Y queries same provider via app API | account-level ABAC still denies cross-customer; RLS tenant check alone is insufficient |
| `FOUND-09` | illegal module uses direct imported JPA repository from another module | Modulith `ApplicationModules.verify()` | build/test fails until boundary corrected |
| `FOUND-10` | schema migrations boot from empty DB, and from known previous schema | run Flyway upgrade | repeatable deterministic schema with no manual application superuser DDL |
| `FOUND-11` | invalid/expired or forged JWT actor and tenant headers | HTTP request | 401/403/404 ProblemDetail, no unverified tenant context or data |
| `FOUND-12` | PostGIS point proximity in lon/lat | `ST_DWithin` query with meter semantics | trusted SRID/geography units + tenant scope; invalid/foreign coordinate rejected |

`FOUND-08` may use a minimal **test-only** CustomerAccount grant policy adapter until PR-03, but must not claim the Commercial business relationship is implemented or introduce an unauthorized real endpoint.

### Data and transaction invariants

- **RLS** uses PostgreSQL production-like role, security migrations, transaction-scoped trusted tenant context, and explicit `SET LOCAL`/connection-pool leak assertions. Root/DDL role is not the runtime role.
- **Outbox** is persisted in same PostgreSQL transaction as business write and audit; producer sends no external event *before* commit.
- **Inbox** uses unique consumer/event and canonical payload hash; duplicate delivery is allowed, duplicate **business side effect** is not.
- **Idempotency** binds a logical key to authenticated subject/tenant/account, operation and canonical request hash. Changed payload returns RFC9457 `409`; don't cache foreign responses across tenants.
- **Migrations** have forward/upgrade test, unique/exclusion/check constraints and migration version in CI evidence. A new tenant-scoped table requires an RLS audit and a test for absent context.
- **Security** is deny by default. Spring Security filter 401/403 and MVC use the already implemented public error contract. No auto user signup or employee by domain.

### Deliverables and acceptance artifact

```text
PR-01
  ├─ Maven pom + dependency convergence report
  ├─ Spring Modulith verify and @ApplicationModuleTest
  ├─ Flyway migrations + least-privilege runtime role
  ├─ Testcontainers PostgreSQL/PostGIS tests FOUND-01..12
  ├─ scoped transaction API + Outbox/Inbox + durable dispatcher
  ├─ Docker Compose local profile, .env.example (no actual secrets)
  ├─ CI jobs and tests on exact SHA
  └─ qualification manifest with module/report/migration/SBOM links
```

**Don't mark PR-01 green on error-handler CI alone.** The current 15 RFC9457 tests are useful existing regression checks, not proof of Modulith/PG/tenant authorization.

## 3. PR acceptance manifest — copy into each subsequent implementation PR

```yaml
prId: PR-01
phaseId: RD-01
canonicalWriteOwner: platform
upstreamQualifiedPrs: []
implementationStatus: NOT_STARTED
businessSignoffStatus: NOT_REQUIRED_FOR_TECHNICAL_FOUNDATION
adrRefs: []
brRefs: []
scenarioRefs: []
tddCaseIds:
  - FOUND-01
  - FOUND-02
caseApplicability:
  APPLICABLE_APPROVED: []
  APPLICABLE_FAIL_CLOSED: []
  BLOCKED_PENDING_BR: []
  DEFERRED_WITH_RATIONALE: []
  NOT_APPLICABLE_WITH_REASON: []
checks:
  unit: NOT_RUN
  moduleBoundary: NOT_RUN
  realPostgresqlRls: NOT_RUN
  concurrencyAndOutbox: NOT_RUN
  apiSecurity: NOT_RUN
  browserRoleAcceptance: NOT_APPLICABLE_FOUNDATION
  migrationUpgrade: NOT_RUN
  restore: NOT_RUN
exactCommitSha: null
ciRunUrl: null
dbMigrationVersion: null
artifactDigest: null
reviewer: null
approvalEvidenceRef: null
```

**Qualification rules:** `GREEN` means tests really passed; `API_QUALIFIED` means approved API/DB/negative contracts on exact SHA; `USER_JOURNEY_QUALIFIED` additionally needs real multi-role UI; `BUSINESS_RELEASE_QUALIFIED` needs relevant BR signatures, restore/security and actual E2E. A line in this template is never proof on its own.

## 4. First business vertical after PR-01

`PR-02` verify user identity and tenant roles → `PR-03C` Commercial CustomerAccount relationship → `PR-03` Tenancy user/account grants → `PR-04` scoped RFQ DRAFT/query/inbox visibility → `PR-05` explicit SUBMIT permission, idempotent state transition and provider Inbox.

Required acceptances: Customer X can create a draft and see only own list/count; Customer Y in same provider cannot discover X; Sales sees permitted provider queue only; revoked EXC can no longer read or submit; `RFQ:submit` remains disabled until separate grant/policy acceptance; replay does not create duplicate RFQ or event. This is the **first customer-visible proof of modular correctness**, not a CRUD scaffolding milestone.

## 5. Open gates and what must NOT be implied

- `Order` and `CustomerAccount` decisions are **proposed ADRs**; the correct default is stop the affected irreversible schema/API write until reviewed.
- `BR-01..12` are **pending real stakeholder**; PR-00 documents statuses, not signatures.
- `DEC-R0-01..08` define design choices and safe defaults, not permission approval.
- Owner module APIs and events are part of an eventual integration contract; no runtime business endpoint is yet implemented.
- `FOUND-01..12` are **new proposed test specifications** outside the prior 132 existing R0 named test candidates. They do not increase the historical 132 count until implemented and traced in a separate machine acceptance bank.

**Exit of this start pack:** issue-ready PR-00 and PR-01 scopes, not executed PRs. After the first actual runtime, update test and coverage evidence without changing business truth based on a green mock.

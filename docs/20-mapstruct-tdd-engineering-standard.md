# 20 — Engineering Standard: MapStruct + TDD and Test Architecture

**Status:** ACCEPTED engineering direction by project owner (2026-11-07), design specification; **implementation/CI tests:** NOT STARTED. Applies to the existing 17 KERUENIX business modules; creates no new service or bounded context.

## 1. Decisions

- **MapStruct** is the default compile-time mapper for nontrivial DTO ↔ domain view/command ↔ persistence adapter conversions in Java 21 + Spring Boot; simple field-for-field one-liners may use explicit constructors. Mapping is not a substitute for validation, authorization, business rules or aggregate constructors.
- **TDD** is required for new and modified domain rules, aggregate transitions, authorization, idempotency, money calculations, reservation concurrency and failure/recovery rules. Follow **Red → Green → Refactor** with business invariants expressed as executable tests before implementation when practical. For migrations, integration adapters and exploratory performance work, write acceptance/integration tests early, use characterization tests for legacy behavior, and record deviations rather than pretending every code line was developed test-first.
- **Test pyramid, not test count:** fast JUnit 5 unit/property tests, Spring Modulith module boundary tests, Testcontainers PostgreSQL/PostGIS/RLS integration, typed API/event contract tests, focused E2E and load/recovery checks. Do not replace real-db concurrency tests with mocks.
- **Quality gate:** no merge for new business behavior unless required tests and existing regression suites are green on exact SHA; changed code coverage is diagnostic and risk-based, not a universal guarantee of correctness. No invented test metrics.

## 2. MapStruct conventions and boundaries

| ID | Rule | Evidence |
|---|---|---|
| MAP-001 | Mapper components belong to the owning module/adapter; no cross-module JPA entities in public APIs | Spring Modulith dependency verification |
| MAP-002 | For business-sensitive mappings use explicit `@Mapping`, `@BeanMapping(ignoreByDefault = true)` as appropriate and `unmappedTargetPolicy = ERROR` | Compile fails for unintended target fields |
| MAP-003 | Never map client-supplied tenantId, createdBy, state, price approval, ledger totals or permissions into writable aggregates through generic update method; those come from authorized command/domain policy | Mutation/privilege-escalation negative tests |
| MAP-004 | Keep Java 21 records for immutable commands/events/responses; map null, timezone, currency and nested fields intentionally | Unit tests for field, null and precision semantics |
| MAP-005 | Annotation processors pinned via Maven compiler plugin with MapStruct processor and Lombok binding only if Lombok is necessary; keep Lombok optional and avoid entity `@Data` | Clean CI compile, reproducible generated mapper |
| MAP-006 | Generated mappers must not perform I/O, security checks, database calls or business state transitions | Mapper review and architecture tests |

Sample conservative compile-time contract:

```java
@Mapper(componentModel = MappingConstants.ComponentModel.SPRING,
        unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface BookingViewMapper {
    @Mapping(target = "bookingId", source = "id")
    BookingView toView(BookingSnapshot source);
}
```

Do not adopt MapStruct for every class: domain aggregates with invariants must be constructed through domain factories/commands, not unconstrained generated setters. Avoid deep JPA graph mapping and accidental lazy-loading/N+1.

## 3. TDD workflow and testing strategy

1. **Before code:** define requirement ID, owning aggregate, legal transition, authorization, invariants, failure behavior and acceptance IDs.
2. **RED:** add a failing focused unit test for positive, negative, boundary and duplicate/concurrent behavior; for database guarantees add a failing Testcontainers integration test.
3. **GREEN:** implement the smallest correct domain rule or adapter meeting the test, keeping transaction/security ownership intact.
4. **REFACTOR:** improve design, mapping, observability and module encapsulation without changing verified behavior.
5. **QUALIFY:** `mvn verify` with the module/unit/security suite, real PostgreSQL/PostGIS tests for DB behavior, exact-SHA CI and linked evidence.

Mandatory technique by concern:
- **State machine:** transition table tests, guards, property-based invariant tests, expectedVersion and clock-driven expiry.
- **Tenancy:** 2–4 tenants, RLS direct SQL, stolen IDs, partner grant revoke, virtual-thread/context propagation and JDBC pool reuse.
- **Booking/Finance:** concurrent holds, idempotency collisions, money precision and allocations, outbox transaction rollback, stale messages.
- **Jobs/Workers:** lease expiry/fencing, crash before/after side effects, retry/DLQ, duplicate messages, Redis unavailable.
- **Tracking/GIS:** watermark, late GPS, `ST_DWithin`, partitions, spatial RLS.
- **Intelligence:** deterministic point-in-time fixtures, leakage and reproducibility tests before any ML training.

## 4. Recommended tools

- Java 21, Maven, JUnit Jupiter, AssertJ, Mockito for isolated collaborators, JaCoCo for coverage visibility.
- Spring Boot Test + Spring Modulith `ApplicationModules.verify()` and `@ApplicationModuleTest`.
- Testcontainers with real PostgreSQL/PostGIS; Flyway migration tests including permissions.
- MapStruct stable release compatible with the chosen compiler and Spring Boot; verify currently supported version/license/security before version lock.
- Optional jqwik or another property-based testing library only where it improves high-risk invariants. Do not mandate a new framework for trivial DTO mapping.
- Maven compiler annotation processor configuration; no Maven snapshot dependencies in release baseline.

## 5. Minimal definition of done

| ID | Mandatory acceptance |
|---|---|
| ENG-001 | Mapper compile detects unmapped security-sensitive fields / changes and generated mapping cannot over-post status or tenant |
| ENG-002 | Domain transitions are driven by red/green/refactor test evidence and boundary/negative cases |
| ENG-003 | Booking hold/race and payment/outbox behavior verified against **real** PostgreSQL, not in-memory mocks |
| ENG-004 | Module architecture test prevents dependency on another module's `internal` or repository |
| ENG-005 | Two-tenant RLS and PartnerGrant negative tests on exact SHA |
| ENG-006 | Flyway migration + rollback-in-transaction and event replay integration tests |
| ENG-007 | CI collects test reports and JaCoCo with risk-based review; no false promise that coverage % alone establishes correctness |
| ENG-008 | Failure injection and full Booking → POD → Finance-lite E2E qualify R0 release gate |

Priorities: **ENG-001..007 R0**, **ENG-008 before R0 release qualification**. A module's declared tests remain **planned** until exact-SHA evidence is recorded.

## 6. Anti-overengineering safeguards

Avoid a global mapping service, runtime reflection mapper, shared model DTO bag, heavyweight universal TDD framework, arbitrary 100%-coverage target and test-only abstractions with no production benefit. Use MapStruct for meaningful mapping boundaries and plain Java constructors where clearer. Test behavior/invariants, not generated MapStruct implementation details except for critical transformations.

## 7. Adoption plan

- **A0:** align module contracts and define mapping conventions, test fixtures and acceptance IDs.
- **A1:** configure Java 21 compiler, MapStruct, JUnit/JaCoCo, Spring Modulith tests, Testcontainers/PostGIS and CI.
- **A2:** implement Booking/CapacityReservation using TDD (including concurrency) and immutable public records mapped explicitly.
- **A3:** extend to Execution/POD/Finance-lite; E2E and crash recovery.
- **A4+:** expand property-based, performance and resilience tests where measured complexity justifies it.

See [19 — Architecture Hardening](19-architecture-hardening-priorities.md), [14 — Delivery Blueprint](14-modular-delivery-blueprint.md), [04 — Traceability](04-requirements-traceability.md).

## 8. User Story Book → TDD input contract

Use [21 — User Story Book](21-user-story-book.md) as source of actor-centered business scenarios. Only business-reviewed stories with tenant scope, main and negative flow, invariants and accepted `USB-*-AC-*` criteria can become `ACCEPTED_FOR_TDD`. Derive `TDD-USB-*` tests at unit, PostgreSQL concurrency/RLS and E2E levels as applicable. Draft stories are not executable specifications.

## 9. Role and approval policy TDD traceability

The first permission-driven TDD input is [22 — Role → Permission → Scope → Approval → Test](22-role-permission-scope-approval-matrix.md) and its [JSON](contracts/role-permission-scope-approval.v1.json). Map `AUTH-TEN-001..011` and `AUTH-COM-001..013` to tests after security/business acceptance. Red/Green/Refactor targets permission boundaries, SoD and quote version transitions, using actual Spring Security/tenant membership + PostgreSQL RLS integration where required. Compile-time MapStruct mapping cannot assign tenant, permissions or approval state from untrusted DTOs.

## 10. Access Governance v2 test-first specification

[24 — Reworked Roles / Scope / Approval / TDD](24-access-control-tdd-matrix-v2.md) and [v2 JSON](contracts/access-policy-matrix.v2.json) replace v1 as the source for new access policy TDD. The design defines 67 draft `AUTH-*` policy acceptances and 27 independent `AUTH-X-*` adversarial cases. First implement pure guard and approval logic using Red → Green → Refactor, then prove effective `CustomerAccount`/tenant/PartnerGrant scoping through Spring Security HTTP, PostgreSQL RLS/Testcontainers, async jobs, cache revocation and exact-SHA E2E tests. Preserve all prior IDs; no executed test status is implied.

## 11. Second security audit test selection

The current authorization design contract is v2.1. Start Red/Green/Refactor by proving read-only permission cannot call Quote decline, EXC viewer cannot sign, foreign CustomerAccount cannot list RFQ/orders, and concurrent incoming RFQ assignment respects expectedVersion. Then add Testcontainers RLS for composed portal reads, booking cancellation request state separation, membership revoke isolation, and verified Finance payment reconciliation. See `AUTH-X-019..027` in [24](24-access-control-tdd-matrix-v2.md). These are **planned tests** only, not passing CI.

## 12. User Story Book → cross-role Business Scenario Book → TDD

Current draft sources: [User Story Book v0.5](21-user-story-book.md) and [25 — Business Scenario Book](25-business-scenario-book.md). 18 newly DISCOVERED role-based stories are not approved. 11 `BSC-*` scenarios contain 38 proposed business acceptance criteria. Do not turn unapproved narrative into unit-test contracts: close actor, pricing/legal liability, current RLS context, event/cargo evidence, permission gaps and exact state transitions first. On approval map each `BSC-xxx-AC-nn` to production-code test `TDD-BSC-xxx-nn`, reusing `AUTH-*` for security and `LFC-*` for domain invariants; use PostgreSQL Testcontainers for resource concurrency/cargo/finance uniqueness and Modulith verification for ownership. No tests are implemented by these documents.

## 13. Role-process desk simulation → TDD case design

[26 — Role/Process Simulation](26-role-process-simulation-and-gap-audit.md) contains 42 **paper** role/process scenarios and 33 gap hypotheses with source owners, phase and expected negative outcome. Use [JSON contract](contracts/role-process-simulation.v1.json) to author `TDD-SIM-NNN` **only after** policy and business approval. Highest risk: real PostgreSQL concurrent resource holds, Quote expiry/authorization, driver offline custody replay after reassign/revoke, 8/10 partial POD cargo-unit conservation, bank allocation dedup, SaaS suspension during live Trip, and Sales-assisted RFQ source attribution. Mock tests alone cannot prove RLS, SQL exclusion or transaction atomicity. Measure implemented acceptance on exact SHA rather than labeling desk cases green.

## 14. Fourth-pass TDD bank: approved business truth versus planned test specs

The [R0 TDD Bank](28-r0-tdd-acceptance-bank.md) and [machine cases](contracts/r0-tdd-scenarios.v1.json) define **84 prospective** test cases: 60 blocker variants, 14 safety paths and 10 multi-role E2E. They are based on [12 business rule proposals](27-r0-blocker-policy-decisions.md), each needing [real stakeholder review](29-r0-business-acceptance-workshop-kit.md). MapStruct remains a DTO boundary tool; never use mapper generation to bypass subject/tenant, aggregate version or approval. `@Version` alone is insufficient for exclusive vehicle/time-slot capacity. Acceptance requires actual PostgreSQL/Testcontainers concurrency, RLS, event replay and field-leak tests on exact commit SHA. No tests are implemented or passed by drafting these contracts.

## 15. Negative tests must assert DB/Outbox/UI, not just HTTP 403

[30 — Negative & Failure Bank](30-negative-and-failure-scenario-bank.md) adds 48 high-risk fault cases to the existing 84 (132 planned), with 8 uncounted mixed-fault combinations. Every denied business command must verify absent forbidden DB writes, correct aggregate version/resource conservation, absence of false success Outbox/notifications, safe customer-carrier field projection, meaningful user-visible status and sanitized audit. Race/replay/revoke validation needs real PostgreSQL/Testcontainers, distinct JDBC connections, clock control and Outbox/Inbox; mocking exception responses or checking a 403 alone is not qualification. The prospective tests are **not implemented**; applicable business/legal decisions in [27](27-r0-blocker-policy-decisions.md) remain pending.

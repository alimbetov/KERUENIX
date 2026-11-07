# 19 — Architecture Hardening: Correctness, Reliability, Intelligence Readiness

**Status:** ACCEPTED architectural priorities (owner decision, 2026-11-07); requirements and acceptance plan only. **Version:** 1.0. **Code/CI qualification:** NOT IMPLEMENTED. Applies to the existing **17 business modules**; no new bounded contexts or mandatory services are introduced.

## 1. Decision

KERUENIX prioritizes:
1. **Correctness First:** ACID transactions, idempotency, concurrency, tenant-aware authorization/RLS, domain-owned state machines, transactional outbox/inbox.
2. **Operational Reliability:** durable platform jobs, failure/recovery, observability, performance budgets, resilient external integration, repeatable tests, backup/restore.
3. **Intelligence Ready:** trustworthy source facts, provenance, time semantics, data quality, immutable/tenant-safe ML projections and datasets. Do not launch a broad AI training platform before the first qualified freight lifecycle.

**Guardrail:** first qualify one complete transport between two isolated tenants from RFQ and quote through reservation, pickup, POD and auditable economic outcome. Advanced AI, marketplace, generalized rules engines, universal BPM, Kafka, mandatory Kubernetes and broad microservice decomposition are **not R0 requirements**. Dedicated workers or R2DBC only after evidence-based profiling and architecture review.

Chosen technical baseline: Java 21 LTS, Spring Boot + Spring Modulith, Spring MVC/JDBC + Virtual Threads, PostgreSQL + PostGIS with transaction-scoped RLS, Flyway, Testcontainers; Redis for optional cache/live notifications, never source of truth. Spring Boot release and third-party library versions require compatibility and security lock before code.

## 2. Architecture requirements — Correctness First

| ID | Priority | Requirement / owning boundary | Qualifying evidence |
|---|---|---|---|
| KX-ARC-COR-001 | R0 P0 | Command idempotency per tenant + operation + client request key; reject same key/different payload, avoid duplicate external effects; domain owner controls effect | Concurrent duplicate command + crash/retry, exactly one logical booking/payment outcome |
| KX-ARC-COR-002 | R0 P0 | Optimistic version checks on mutable aggregates; DB unique/exclusion/row locks for physical capacity; no cache-derived write guards | Competing reservation attempts, stale expectedVersion, valid capacity constraints |
| KX-ARC-COR-003 | R0 P0 | Tenant context from verified membership and resource grants, transaction-scoped `SET LOCAL`/equivalent for RLS; no caller-controlled tenant spoofing; no pool context leak | Multi-tenant HTTP/JDBC/job/event concurrency and reset tests |
| KX-ARC-COR-004 | R0 P0 | Aggregate state transition and durable outbox publication in same committed PostgreSQL transaction; inbox dedup and at-least-once consumer semantics | Rollback/no phantom event, publish crash/replay, consumer duplicates |
| KX-ARC-COR-005 | R0 P0 | Domain-owned typed state machines; guards, actors, audit and expectedVersion; process managers coordinate multi-owner outcomes | Booking/CapacityReservation/POD transition suites and compensation |
| KX-ARC-COR-006 | R0 P0 | UTC instants, injectable `Clock`, explicit business time zone for scheduling; expiry compares authoritative state and deadline at execution | Clock boundary, delayed expiry, race with confirmation |
| KX-ARC-COR-007 | R0 P0 | Immutable canonical evidence/provenance for legally or financially consequential transitions; owner controls authorization and retention | Pickup/POD evidence and invoice/payment cross-check, audit consistency |

## 3. Architecture requirements — Operational Reliability

| ID | Priority | Requirement / owning boundary | Qualifying evidence |
|---|---|---|---|
| KX-ARC-OPS-001 | R0 P0 | PostgreSQL-backed durable Job Engine: enqueue atomic with transaction or via outbox; bounded workers, retry/backoff, attempt fencing, cancellation and recovery | JOB-001..008 from [18](18-platform-jobs-state-machines-workflows.md) |
| KX-ARC-OPS-002 | R0 P0 | Timeout, bulkhead, retry classification and circuit breakers on external I/O; no unbounded virtual-thread fan-out | Fault injection: slow GPS/ERP, no API starvation or duplicate effect |
| KX-ARC-OPS-003 | R0 P0 | Structured logs + correlation, tenant-safe redaction, Micrometer metrics/traces, JDBC pool/queue/worker saturation; JFR for VT pinning | Observable end-to-end correlation and alert exercises |
| KX-ARC-OPS-004 | R0 P0 | Schema/event/OpenAPI contract versioning; Flyway forward-only migration checks and compatibility tests | N and N-1 event consumer/migration smoke, no unowned DB writes |
| KX-ARC-OPS-005 | R0 P0 | Repeatable two-tenant fixture and negative security cases; exact-SHA CI with PostgreSQL/PostGIS Testcontainers and architecture verification | Reproducible complete freight scenario and isolation suite |
| KX-ARC-OPS-006 | R0 P0 | Resource budget baseline: HikariCP limits, query plans/indexes, memory/CPU, job concurrency, external quota | Measured p95/p99/error and resource utilization, not invented SLA |
| KX-ARC-OPS-007 | R0 P0 | Backup/restore drills for PostgreSQL and referenced evidence; replay recovery for outbox/jobs; RPO/RTO agreed by deployment | Restore into isolated environment, verify business state/artifact hashes |
| KX-ARC-OPS-008 | R1 P1 | Tenant-aware cache, rate limiting and bounded features/quotas, with reliable invalidation and degraded-mode Redis outage | Tenant leakage tests, cache invalidation, Redis-failure smoke |
| KX-ARC-OPS-009 | R1 P1 | Retention/partition management, legal hold, archive/drop and measurable read-projection freshness | Partition late-arrival/retention tests + rebuild consistency |

## 4. Architecture requirements — Intelligence Ready

| ID | Priority | Requirement / owning boundary | Qualifying evidence |
|---|---|---|---|
| KX-ARC-INT-001 | R0 P0 **data contract only** | Fleet owns GPS; Execution owns actual pickup/delivery; Commercial/Finance own business money facts; source provenance, event/observed/received time and schema version recorded | Truth owner mapping and canonical event schema tests; GPS is not proof of POD |
| KX-ARC-INT-002 | R0 P0 **data contract only** | Define data quality gates for completeness, duplication, missing/outlier values, freshness and label confidence; do not block R0 on deployed training infra | Deterministic quality validation fixtures and report format |
| KX-ARC-INT-003 | R1 P1 | Tenant-authorized ML projections and point-in-time feature generation; immutable dataset manifest, snapshot cutoff, lineage and retention | INT-001, INT-003..005 and INT-010 |
| KX-ARC-INT-004 | R1 P1 | First measurable use case: ETA deterministic baseline vs one candidate model with temporal holdout and subgroup checks | INT-009 plus comparable MAE/P90/coverage results; shadow mode |
| KX-ARC-INT-005 | R2 P2 | Model approval, registry, canary/rollback, worker training quotas and drift monitoring only when validated pilot data justify them | INT-002, INT-006..008, INT-012..014 |

Original facts are not moved to Intelligence; no cross-tenant model training by default. Derived inference cannot authorize bookings, compliance, financial postings or POD. See [17](17-intelligence-special-module.md).

## 5. Delivery gates — what must be done now vs later

| Gate | Scope | Exit criterion |
|---|---|---|
| A0 — Design coherence | Catalog of 17 modules, ownership, ADRs, R0/P1 boundary, explicit command/event/time contracts | No unresolved owner for critical writes; traceability IDs linked |
| A1 — Tenant foundation | Java/Maven bootstrap, Flyway/PostGIS, 2-tenant identity/permissions, PostgreSQL RLS, JDBC+VT test profile | `mvn verify` + negative tenant isolation on exact SHA |
| A2 — Commercial & Booking | RFQ/quote + Fleet hold, idempotency, concurrency, state transitions, outbox and expiry job | Repeated and competing operations deterministic; no false confirmation |
| A3 — Execution & Finance-lite | Pickup/custody, Shipment, POD, documents, accounting evidence and tracking | One real E2E carriage, no GPS=POD or delivered=paid shortcut |
| A4 — Operational qualification | Failure injection, backup/restore, resource budgets, traceability, optional Redis outage | Exact-SHA CI evidence and agreed performance/restore thresholds |
| A5 — Intelligence pilot (after A3/A4) | Quality-controlled ML projection, ETA baseline/candidate, offline evaluation | Demonstrable improvement on representative holdout, no cross-tenant leakage |

**Definition of Ready:** owner/actor, source-of-truth, invariants, transaction boundary, tenant grants, DTO/event version, expected failure/retry, test IDs and scoped deliverable. **Definition of Done:** implementation + exact-SHA unit/integration/security/performance as applicable, migrations, monitoring and recovery evidence. Planned test ID is **not** an executed result.

## 6. Anti-overengineering policy

For each proposed technology demand: demonstrated problem, bounded ownership, alternatives, operating cost, failure modes, measurable acceptance and explicit exit/reversal plan. Prefer one deployable backend and small purpose-built abstractions. Never add new business modules to represent generic utilities. Adopt new broker, R2DBC, general BPM, custom rules engine, ML tooling, or microservice only on qualified evidence. Feature flags are configuration/limited rollout tools, not an excuse for permanent duplicated behavior.

## 7. Decisions and next work

**Agreed:** 17 modules unchanged; three priorities above; JDBC + Virtual Threads for transactional core; domain-owned business states, PostgreSQL authoritative Jobs/outbox; guarded Intelligence pilot.

**Open:** first paying persona/corridor, legal quote/financial policies, acceptance SLOs and load profiles, JobRunr vs minimal scheduler PoC, authorized data policy/labels for ML, production library-version locks.

**Next action:** close A0 as a documentation/contract consistency pass, then execute A1 tenant foundation and the A2 Booking/CapacityReservation vertical slice. No additional generic platform subsystems before these gates.

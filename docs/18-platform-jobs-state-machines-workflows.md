# 18 — Platform Jobs, State Machines & Process Orchestration

**Architecture decision:** selected for KERUENIX planning by project owner, 2026-11-07. **Specification:** v1.0 / DESIGN ONLY. **Implementation:** NOT STARTED; no tests or CI qualification. Deployment baseline: Java 21 + Spring Modulith, Spring MVC/JDBC + Virtual Threads, PostgreSQL RLS; Redis optional and non-authoritative.

## 1. Executive decision and boundaries

Adopt three **separate** facilities:
1. **Platform Jobs**: a shared durable scheduler/dispatcher for background work (delay, recurrence, retry, leasing, cancellation, recovery, observability), with PostgreSQL as authoritative storage. Prefer evaluating a supported PostgreSQL-backed library (JobRunr candidate) before implementing a custom engine. No final library choice until PoC proves atomic enqueue and operational requirements.
2. **State Machine Kernel**: minimal Java 21 reusable primitives for evaluating typed transitions, expected version and diagnostics. **Business states, guards, invariant enforcement and authoritative persistence remain in each owning module.** No global table storing all business states.
3. **Domain Process Managers**: application-level durable orchestration of cross-module operations using explicit commands/events, completion and compensation policies. Not a global state machine and not a blind distributed transaction.

These are **platform capabilities, not new bounded contexts** in the catalog of 17 business modules. The business module dependency list remains unchanged. Platform facilities MUST NOT import domain internals or perform SQL writes to business tables.

**Not interchangeable:** Event = completed fact; Outbox = durable intent to publish fact; Job = work to perform; State machine = permission to change aggregate state; Process manager = coordination between aggregate owners.

## 2. Physical placement (proposed)

```text
backend/src/main/java/kz/keruenix/
  platform/jobs/             JobSchedulerPort, JobDescriptor, JobExecutionContext, JobStatusQuery
      internal/              pgstore, leases, worker, recovery, telemetry, adapters
  platform/statemachine/     Transition, GuardResult, TransitionResult, TransitionPolicy
  platform/eventing/         publication registry, transactional outbox/inbox adapters
  booking/internal/          BookingStateMachine, BookingProcessManager
  fleet/internal/            CapacityReservationStateMachine, ReservationExpiryHandler
  execution/internal/        ShipmentStateMachine, DeliveryProcessManager
  finance/internal/          FinanceStateMachine, SettlementProcessManager
  intelligence/internal/     TrainingJobLifecycle (domain-owned), TrainingOrchestrator
  optimization/internal/     OptimizationJobLifecycle (domain-owned)
docs/contracts/platform-jobs.v1.json   # contract candidate, to implement after validation
```

Job engine technical records must be in `platform_jobs` or dedicated platform schema; business aggregate states in their owner schemas. A domain may schedule by typed public port; engine holds no domain repository references. No generic Java class-name payload deserialization / script execution.

## 3. Job contracts and execution guarantees

Job descriptor (conceptual): `jobId UUID, tenantId, ownerModule, type, schemaVersion, businessResourceRef, idempotencyKey, payloadRefOrBoundedPayload, runAt, priority, queue, deadline, attemptLimit, createdAt, correlationId, principalScope, policyVersion`.

On worker claim, issue `attemptId, leaseUntil, fencingToken` and validate authorized tenant, type and queue capacity. Tenant/principal permissions are **revalidated at execution**; original principal identity in payload is context/audit, not a perpetual authorization grant. Scheduler can execute authorized system-scoped maintenance jobs without impersonating end users; privileges separate and explicit.

Lifecycle (system technical state): `QUEUED -> CLAIMED -> RUNNING -> SUCCEEDED`; retry path `RUNNING -> RETRY_WAIT -> QUEUED`; terminal `FAILED, CANCELLED, EXPIRED, DEAD_LETTER`. Transitions for lease expiry/worker crash are reconciled by supervisor with attempt fencing; stale claimant cannot finalize or publish a result. Cancellation is cooperative and cannot roll back already committed external side-effects.

Reliability:
- PostgreSQL is durable source for job and attempt data. Persistent enqueue must be atomic with the initiating business transaction **or** use domain outbox and idempotent enqueue after commit. Never assume JobRunr enqueue and JPA save automatically share one transaction without proof.
- Claim via tested locking/atomic SQL (e.g. `FOR UPDATE SKIP LOCKED` for queue-like tables) with bounded batch, fairness by tenant and priority aging. This SQL is **not** substitute for booking resource locks.
- Define **at-least-once execution attempts**, not exactly-once effects. Every external action requires idempotency key, dedup/result record and compensating protocol when necessary.
- Retry only classified transient failures with exponential backoff + jitter and bounded retry budget. Permanent validation/auth failures go to explicit terminal/quarantine state; DLQ/manual replay requires authorized, audited operation.
- Timeouts are enforceable at I/O adapter and external worker level; blocking interrupt or worker death is not proof remote action was undone. Reconcile uncertain outcomes with provider-specific idempotency/status APIs.
- PostgreSQL maintenance/partition DDL requires a separate privileged operations worker and credentials; normal runtime job workers cannot DDL.
- Background jobs use bounded queues/active worker caps per type and tenant; no unlimited virtual-thread fan-out. I/O workers may use virtual threads; CPU-heavy Timefold/ML workers use bounded executors or isolated processes.
- Repeating schedules and timezone/DST semantics must be explicit (UTC storage, calendar timezone, catch-up or skip policy, overlap controls).
- Job data retention, legal hold, delete/export rights and poison-message quarantine are defined before launch.

**Redis:** optional acceleration for progress/counters/notifications; cache eviction or Redis outage cannot lose a confirmed job, state transition or evidence. Redis Streams only after transport benchmark and preservation of authoritative outbox semantics.

## 4. State machine ownership and correctness

Define pure `transition(currentState, command, context) -> Allowed(nextState,effectsIntent) | Denied(reason)`. Use Java 21 sealed interfaces, records, enums and exhaustive switch for typed contracts. Context includes authenticated actor/tenant, expectedVersion, event-time and rule-set version. Guard decisions do not directly publish side effects.

Owning application service transaction executes: (1) resolve tenant/auth, (2) load aggregate with optimistic version/necessary row locks, (3) evaluate typed guards and domain invariants, (4) mutate owner aggregate, (5) write immutable audit and outbox, (6) commit. If step fails, transition is not claimed completed. Persist meaningful rejected attempts in a separate security/diagnostic record where required; do not mutate aggregate for denied commands.

Existing [12 canonical lifecycle machines / 94 transitions](contracts/commercial-execution-lifecycle.v1.json) are the initial source specification. All string guard names must be mapped to tested predicate implementations and actor/permission matrices; current JSON is not executable proof. Multi-step states are not collapsed into a single global state table. State kernel is optional where simple aggregate methods suffice; prefer explicit domain code over an overgeneralized DSL/framework.

Expiry is a **job requesting a domain command**, not a direct status UPDATE: `ExpireCapacityHold(reservationId,expectedVersion,scheduledDeadline)` checks authoritative state and clock at execution. Late execution must not expire a subsequently confirmed hold. Similarly quote expiry and unpaid invoice reminder have separate policies.

## 5. Process managers / orchestration

Process managers live with the coordinating domain/application capability and own **only process state** (`processId, businessCorrelation, step, expectedVersions, deadlines, attempts, compensations`). Subordinate business records belong to their source modules.

Primary R0 process:
```text
QuoteAccepted
 -> BookingProcessManager requests Fleet hold
 -> capacity hold confirmed by Fleet
 -> Booking confirms against valid quote and reservation evidence
 -> BookingConfirmed -> Outbox -> customer/carrier notification jobs
 -> Execution pickup/custody events -> Tracking read projection
 -> POD accepted -> Documents verify -> Finance records obligations
```

Define whether each cross-module synchronous operation truly uses the same local JDBC transaction (and is intentionally part of shared commit) or crosses process/network boundary and therefore uses durable saga/compensation. In both cases only owner APIs may mutate owner aggregates. On failure: release/expire hold, invalidate provisional confirmation, mark exception, retry/reconcile external status; never silently mark delivered/paid.

The durable process manager is not a BPM engine by default. Evaluate orchestration framework only after explicit requirements for timers, human approval, parallel branches, visibility and operational scale exceed simple persisted process coordinators.

## 6. Multi-tenancy, safety and observability

- All job metadata/payload references tenant-scoped with RLS where applicable; no access from Tenant A to Tenant B. PartnerGrant revoke must block later sensitive job outputs and downloads.
- Workers use scoped service identity, typed allowed handlers, revalidated rights, safe schema version handling and integrity checks. Enforce limits on payload sizes and redact PII/secrets.
- Correlation and audit across `commandId -> aggregateVersion -> outboxEventId -> processId -> jobId -> attemptId`.
- Metrics: job queue lag p50/p95/p99, execution duration, retry/DLQ rates, lease expiry, heartbeat staleness, saturation per pool/tenant, process timeouts and compensation failures. JFR observes pinning and virtual-thread use.
- Disable/scale optional pools without taking down core booking/finance. Readiness/liveness distinguish worker degradation from core transactional availability.

## 7. Implementation gates and mandatory acceptance

| ID | Test (real persistence where necessary) | Gate |
|---|---|---|
| JOB-001 | Business rollback -> neither committed outbox nor actionable job | R0 |
| JOB-002 | DB commit followed by dispatcher crash -> job eventually enqueued exactly as one logical job | R0 |
| JOB-003 | Two workers claim same job -> one valid active lease/fence | R0 |
| JOB-004 | Worker dies after side-effect before ack -> replay cannot duplicate effect | R0 |
| JOB-005 | Lease expiry + stale worker completion -> stale attempt rejected | R0 |
| JOB-006 | Retry budget, permanent failure, DLQ and manual replay produce audit trail | R0 |
| JOB-007 | Tenant A cannot inspect/claim/mutate Tenant B jobs | R0 |
| JOB-008 | Redis unavailable -> committed jobs remain durable, degraded UI permitted | R0 |
| JOB-009 | Queue saturation/tenant quotas do not starve API or other tenants | R1 |
| JOB-010 | Timezone, DST, overlapping recurrence and late schedule semantics | R1 |
| SM-001 | All permitted/forbidden Booking and CapacityReservation transitions match predicates | R0 |
| SM-002 | ExpectedVersion collision rejects stale command without lost update | R0 |
| SM-003 | Late expiration cannot cancel confirmed hold; duplicate expiry is idempotent | R0 |
| SM-004 | State change, audit, outbox commit atomically; no phantom event on rollback | R0 |
| SM-005 | Two-tenant/partner-grant negative permission matrix, including async handler | R0 |
| WF-001 | Carrier rejects after provisional selection -> reservation safely released, Booking not falsely confirmed | R0 |
| WF-002 | Restart between steps -> persisted process resumes and converges without duplicate transitions | R0 |
| WF-003 | Document/POD evidence missing -> no delivered/financial-close false positives | R0 |

Qualification: unit + property-based state tests, Spring Modulith boundary tests, real PostgreSQL/Testcontainers RLS + concurrency, restart/failure injection, exact-SHA CI and audit traces. Benchmarks must compare library choice (JobRunr candidate vs minimal PG scheduler) using target workload. No claim of exactly-once arbitrary external effects.

## 8. Delivery sequence and review criteria

- **JSM-R0**: approve interfaces, state ownership, durability/permission decision and library PoC acceptance; no business-module count change.
- **JSM-R1**: minimal PostgreSQL durable job + booking reservation expiry, implement `JOB-001..008` and `SM-001..005`.
- **JSM-R2**: durable Booking process manager with failure compensation (`WF-001..003`), Modulith event bridge and monitoring.
- **JSM-R3**: integrate document/notification, optimization and ML queues with independent worker caps, quotas and scheduled operations.
- **JSM-R4**: performance/HA benchmark, restore drills, on-prem feature profile and optional Redis transport PoC.

Open library decision: JobRunr (or another maintained PostgreSQL-backed scheduler) is a **candidate**, not approved dependency. Check current license tier, multi-tenancy mechanics, transaction integration, lease/fencing behavior, monitoring and operational lifecycle. Keep public `JobSchedulerPort` independent of chosen framework.

**Decision record:** architectural direction ACCEPTED IN DESIGN by project owner; vendor/implementation details remain PROPOSED. No implementation or production qualification has occurred.

## 9. Relation to Architecture Hardening priorities

This platform design supports [19 — Architecture Hardening Priorities](19-architecture-hardening-priorities.md). Jobs, state machines and process managers remain technical capabilities, **not** new business modules. R0 implements only the minimum durable scheduling, concurrency and recovery needed by Booking/CapacityReservation; advanced worker orchestration follows measured demand.

# 17 — Intelligence Special Module: Historical ML, Training & Model Lifecycle

**Status:** PROPOSED / architecture review required. **Version:** 1.0. **Date:** 2026-11-07.
**Scope:** pooled SaaS, dedicated and on-prem KERUENIX. **Not implemented:** no Java code, migrations, trained models or CI qualification.
**Related:** [module boundaries](contracts/module-boundaries.v1.json), [data platform](15-data-platform-partitioning-postgis.md), [delivery blueprint](14-modular-delivery-blueprint.md).

## 1. Decision and ownership

Introduce exactly one **Spring Modulith business-support module** `kz.keruenix.intelligence`, dedicated to permitted historical ML projections, feature definitions/materialization, immutable datasets, training orchestration, experiment runs, model registry, inference, evaluation and monitoring. Its stable public APIs are `IntelligencePredictionApi`, `TrainingManagementApi`, `ModelRegistryQueryApi`, `IntelligenceEventIngestApi` (the last internal/system-authenticated, never public arbitrary event ingestion).

**Not owned:** original GPS history (Fleet), shipment events and POD (Execution), prices/payments (Commercial/Finance), optimizer job/score/constraints (Optimization), global raw tenant data, identity and business approvals. Only owner modules write their source-of-truth. Intelligence may store purpose-limited copies/projections with lineage, retention and tenant isolation. It does not authorize bookings, assert legal compliance, or mutate source domain aggregates.

**Optimization remains separate** (`optimization`, existing R1 module) and receives versioned predictions or immutable feature snapshots via API/events; Timefold remains in Optimization, not in Intelligence. Avoid direct cyclic dependency: Intelligence directly depends only on Tenancy. All other ingestion is via durable event contracts or inbound snapshot adapters owned by Intelligence, without imports of another module's internals. Optimization may depend on Intelligence exported API. Domain modules may consume prediction API later through explicit catalog adjustments; do not introduce dependencies in R0 that are not implemented.

## 2. Physical layout (proposed)

```text
backend/src/main/java/kz/keruenix/intelligence/
  package-info.java
  IntelligencePredictionApi.java
  TrainingManagementApi.java
  ModelRegistryQueryApi.java
  IntelligenceEventIngestApi.java
  internal/
    history/       # durable dedup, source provenance, retention
    features/      # feature definitions, point-in-time materialization
    datasets/      # immutable manifests and deterministic snapshots
    training/      # job state, leases, retries, callbacks
    registry/      # versioned models, provenance, approval, deployment
    inference/     # provider port and guarded online serving
    evaluation/    # baselines, backtesting, drift, bias, latency
    adapters/      # PostgreSQL, RustFS/S3, ONNX, external workers
workers/intelligence-training/     # independently deployable compute, optional Python
docs/contracts/intelligence-events.v1.json
docs/17-intelligence-special-module.md
```

The worker is **not** a second business source-of-truth. Worker has least-privilege scoped dataset access and signed job identity; its result is verified and finalized by the owning backend module. No DB superuser credentials or cross-tenant SQL credentials on worker.

## 3. Data ownership, storage and retention

PostgreSQL schema `intelligence` (not a PostgreSQL partition per module) uses separate migration ownership. Proposed tables:
- `source_event_registry`: `tenant_id, producer, event_id, schema_version, source_occured_at, received_at, payload_hash, object_ref, consent_scope, processing_status`; unique `(tenant_id,producer,event_id)`; record only needed, sanitized payload or secure reference; replay conflicts reject on different hash.
- `feature_definition`: versioned schema, input contract, owner, freshness, privacy class.
- `feature_snapshot`: `tenant_id, entity_scope, as_of_at, feature_definition_version, values_ref, source_watermark`; point-in-time values with validity intervals.
- `dataset_version`: dataset ID, tenant scope, feature/schema versions, frozen time window and cutoff, manifest SHA256, storage ref, classification, provenance, retention.
- `experiment_run`, `training_job`, `training_attempt`: parameters, seed, code/container digest, input hashes, status, heartbeats, budgets, metrics and errors (redacted).
- `model_version`: immutable model digest, model format, artifact location, dataset lineage, dependency/runtime compatibility, quality metrics.
- `model_deployment`: environment, use case, tenant/cohort scope, model version, approval, rollout, rollback pointer, optimistic version.
- `prediction_audit`: minimal protected prediction receipt, model/dataset/feature versions, request correlation, latency, baseline/quality observations; avoid raw PII.
- `drift_report`: statistical validation and operational alerts, sample sizes and version association.

Large Parquet datasets, training checkpoints and ONNX artifacts reside in RustFS/S3 with checksums, immutable versioned keys, encryption and IAM scopes; PostgreSQL records metadata, ACL, provenance and lifecycle. RustFS/S3 object existence **is not** proof of committed model; use staged upload → hash verify → transactional DB finalization → garbage collection of orphans.

Tenant scoped tables enforce RLS, composite tenant-aware references and per-transaction tenant context. Runtime role cannot bypass RLS. Shared cross-tenant models are prohibited by default; governed use requires explicit lawful/policy approval, documented allowed purpose, minimized/aggregated data, risk assessment, auditable lineage and isolation tests. Deduplicate before partitioning; partition `prediction_audit` or event history by time only at measured scale and subject to legal holds/retention. Dataset/model lineage must survive source-event retention by policy without leaking raw records.

## 4. Contracts and lifecycle

Events from Fleet / Execution / Finance are **versioned sanitized immutable envelopes**, published by the owning module through outbox; `IntelligenceEventIngestApi` validates producer identity, schema, tenant mapping, event identity, event time, rights and payload checksum; duplicate matching event is no-op; conflicting duplicate is quarantined. Projection lag is observable, replay idempotent, late/out-of-order events do not silently rewrite a frozen dataset.

```text
Domain event/outbox -> tenant policy -> dedup & history projection
 -> point-in-time feature generation -> frozen DatasetVersion
 -> TrainingJob -> worker claim/lease -> upload staging
 -> evaluation & acceptance -> model registry approval
 -> scoped rollout -> inference -> monitoring -> rollback/retire
```

Separate state machines:
- Dataset: `BUILDING -> VALIDATING -> FROZEN -> RETIRED` (errors `FAILED`).
- Training: `QUEUED -> CLAIMED -> RUNNING -> EVALUATING -> SUCCEEDED|FAILED|CANCELLED` with heartbeat expiration and bounded retries; unique idempotency key.
- Model: `REGISTERED -> EVALUATED -> APPROVED -> DEPLOYED -> RETIRED`; `REJECTED` possible after evaluation; approval is explicit, never a side effect of success.
- Deployment: `STAGED -> CANARY -> ACTIVE -> ROLLED_BACK|DISABLED` with compare-and-swap and previous known-good version.

Public inference request must include authorized context and use case, `asOf`/feature freshness, bounded timeout and idempotency/correlation; response includes `modelVersion`, `prediction`, units, `confidence/calibration when valid`, `asOf`, `featureWatermark` and `fallbackUsed`. No claim that all model types support calibrated confidence. If no qualified model, stale features or timeout: explicit typed unavailable/fallback result; never auto-approve movement, finance, compliance or safety decisions. Human/business policy remains authoritative.

## 5. Evaluation, leakage prevention and controls

- Build temporal train/validation/test splits with clear cutoff, group by shipment/vehicle/tenant where necessary, point-in-time joins and delayed labels. No future features, test-set tuning, or implicit cross-tenant mixing.
- Baseline for ETA: deterministic route provider / historical median segmented by corridor, not a random guess. Report MAE (minutes), P50/P90 absolute error, on-time calibration, coverage, per-region/tenant strata, cold start and drift. Ship only if agreed holdout thresholds beat baseline without significant subgroup regression.
- Optimization is evaluated separately: hard constraints **must never be violated**; compare Timefold solutions with deterministic baseline on matched seeded instances, total cost, feasible rate and timeout; version constraint model.
- Reproducibility: dataset SHA, feature version, training code commit/container digest, random seed, dependency lock, hyperparameters, runtime/CPU architecture and source watermark. Nondeterministic GPU runs require documented tolerance.
- Evaluate model/package safety (untrusted pickle prohibition for automatic production deserialization), checksum, allowed runtimes and malware/dependency checks. All payloads bounded; redact secrets and driver/customer identifiers.
- Define retention, subject-deletion propagation, dataset invalidation/retrain and model retirement for privacy or contractual revocation. Don't promise model unlearning without a validated process.
- Resource quotas: one tenant's training must not starve transactional traffic; queue limits, job cancellation, cpu/memory/GPU quotas, timeout, circuit breakers and separate worker pool. Training never runs in an API request thread.

## 6. Contractual integration map

| Producer/consumer | Mechanism | Data allowed | Not allowed |
|---|---|---|---|
| Fleet -> Intelligence | outbox events | sanitized vehicle observations and timestamps | unscoped GPS history reads |
| Execution -> Intelligence | events | confirmed milestones and outcomes | converting GPS candidate to delivery truth |
| Finance -> Intelligence | approved feature/event | permitted cost aggregates | raw bank/payment secrets |
| Intelligence -> Optimization | exported prediction API | versioned ETA/cost estimates | solver modifying model registry |
| Tracking/Commercial -> Intelligence | later approved prediction API | scoped ETA/risk view | bulk global tenant model access |
| Tenancy -> Intelligence | exported permission policy | tenant authorization decision | implicit permission from caller-supplied tenant ID |

## 7. Technology selection and deployment

R0: Java 21 / Spring Modulith, PostgreSQL RLS, object store and contract-first events only. R1: Tribuo or XGBoost for measured supervised baselines; ONNX Runtime Java for verified exported compatible models. `optimization` owns Timefold PoC. R2: Python/PyTorch training worker only if real model requirement warrants it. DJL and MLflow are **options to benchmark**, not mandatory default dependencies. Verify the actual compatible version matrix, JDK, Spring Boot, runtime licensing, transitive security and ONNX operator support before dependency lock.

No default GPU requirements. Backend runs with no model or worker deployed. SaaS, dedicated and on-prem use same contracts and can disable training/inference with explicit capability flags. No network call to third-party AI provider is required for first release.

## 8. Delivery roadmap and qualification

| Milestone | Scope | Acceptance |
|---|---|---|
| INT-R0 | boundaries, contracts, ownership & threat model | catalog has no cycles, no cross-module repository writes, signed-off RLS/consent rules |
| INT-R1.0 | ingestion + immutable history + dataset | two-tenant Testcontainers RLS, duplicate/conflicting/late event, point-in-time leakage and deterministic manifest |
| INT-R1.1 | optimization contract with Timefold PoC | no hard constraint violation; seeded benchmark better than baseline on agreed target |
| INT-R1.2 | ETA baseline + trained candidate | strict temporal holdout MAE and P90 vs baseline, no subgroup regression beyond agreed guardrail |
| INT-R1.3 | registry + ONNX | hash verification, approval gate, canary/rollback, incompatible engine rejected |
| INT-R2 | training worker, model monitoring | job crash/replay/lease expiry recovery, quotas, drift alerts, training reproducibility |
| INT-R3 | pricing/risk/advanced models | domain-owner review, contractual permission & shadow-mode acceptance |

**Mandatory acceptance cases (not executed yet):**
- INT-001 two tenants with same resource ID cannot query each other's events, datasets, models or predictions;
- INT-002 stale or malicious cross-tenant worker claim rejected;
- INT-003 duplicate event same hash no-op, different hash quarantine; replay after restart consistent;
- INT-004 late timestamp and time-window snapshot do not leak future information;
- INT-005 frozen dataset manifest byte-for-byte reproducible, mismatch blocks training;
- INT-006 worker crash after staged artifact leaves no published model; retry idempotent;
- INT-007 training success cannot automatically deploy unapproved model;
- INT-008 model checksum/runtime mismatch blocks inference;
- INT-009 timeout, stale feature, unavailable model -> typed fallback and no business side effect;
- INT-010 revoked consent/grant blocks new extraction and triggers retention/invalidation policy;
- INT-011 optimization never violates hard constraints and solver timeout preserves valid baseline;
- INT-012 model rollout CAS + rollback preserves previous approved model;
- INT-013 architecture verification checks module dependencies; API remains responsive under training load;
- INT-014 backup/restore reconstructs registry with referenced artifacts; orphan staging cleaned safely.

Qualification needs exact-SHA CI and linked evidence: unit, module boundaries, real PostgreSQL/Testcontainers, object storage integration, worker failure injection, benchmarks and security tests. **Draft spec != implemented != qualified.**

## 9. Decision log / open questions

1. Data policy owner: which commercial/GPS data may be retained for ML, by tenant and contractual purpose?
2. Legal basis and on-prem data egress: can model training happen outside dedicated installation? Default **no**.
3. Time-series volumes, p95 throughput and retention: partition strategy measured, not speculative.
4. ETA reference labels: actual arrival/POD event quality and tolerance; what constitutes a trustworthy label?
5. Baseline/guardrail thresholds: to be fixed from real pilot data before claiming ML improvement.
6. Model governance approvers, rollback SLO, and support for tenant-specific vs aggregated models.
7. Platform stack compatibility: chosen Spring Boot, Timefold, Tribuo, ONNX runtime and worker image security.

**Architectural recommendation:** accept module specification only after owner sign-off; implement a minimal vertical slice of `INT-R1.0` after tenancy/RLS qualified, not an all-in-one AI platform ahead of the first verified freight lifecycle.

## 10. Intelligence Ready priority and dependency on canonical truth

The accepted project priority is to capture **source-owned trustworthy facts first**, then implement point-in-time datasets and only subsequently deploy ML training/inference. See [19 — Architecture Hardening Priorities](19-architecture-hardening-priorities.md), specifically `KX-ARC-INT-001..005`. R0 requires data contracts and quality semantics, **not** a deployed training stack, a feature store service or a GPU. ETA model qualification is downstream of the proven tenant-isolated freight lifecycle and deterministic baseline.

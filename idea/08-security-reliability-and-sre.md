# 08 — Security, multi-tenant safety, reliability and operations

**Status:** architectural baseline. Numeric objectives are proposed pilot targets, not an existing SLA.

## Security threat model

Threats: cross-tenant horizontal privilege escalation; compromised driver phone; leaked signed document URL; GPS spoofing; external webhook replay; fraudulent fueling; admin overreach; malicious upload; stale roles/cached permissions; mis-scoped search and batch export.

**Controls:**
- Tenant context resolved from authenticated membership on each request and async job; no trust in client-provided tenant_id alone.
- Object-level authorization and partner collaboration grants; deny by default and recheck on download.
- PostgreSQL RLS + app-level filters + composite tenant-key invariants, including background workers and pooled connections.
- OIDC, MFA for privileged users, short-lived sessions/service credentials, scoped APIs and rotation.
- Secrets in secret manager or runtime secret injection, never committed to repo; encrypt at rest and in transit.
- Files scanned, MIME/size checked, hashes and allowed type policies; short-lived download URLs.
- Audit every sensitive read/export/approval, privilege change, price change, custody/finance event.
- Mask GPS and commercial data in logs; retain only required telemetry granularity/period.
- Security and privacy assessments for location tracking, drivers, cross-border transfers and local regulations.

## Reliability patterns

**Transactional outbox/inbox:** domain mutation and outgoing event in one database transaction, at-least-once delivery with idempotent consumers; no assumption of exactly-once external execution.

**Idempotency:** client idempotency keys scoped to tenant and operation, external event IDs, request fingerprints, dedup retention, durable result replay. Critical on booking, reservations, invoices, fuel imports and proof-of-delivery.

**Concurrency:** optimistic version/compare-and-set on quote approval, route modifications and resource assignment; reserve capacity with database constraints and expiry. Prevent double booking through durable reservation rules, not UI checks.

**Compensation:** explicit cancel/release workflows for partner booking and appointment changes; do not use DB transaction to promise atomicity across providers.

**Failure isolation:** circuit breakers per provider, tenant quotas, queue backpressure, retry budget and dead-letter queues. Long-running optimization is cancellable, bounded and isolated per tenant.

## Proposed SLO and recovery profile

| Measure | Proposed initial objective | Qualification |
|---|---|---|
| API availability | 99.9% monthly for core ordering | excludes agreed maintenance; pilot target only |
| Core read API p95 | <= 500 ms at measured reference load | excludes expensive routing/optimization jobs |
| Booking write response p95 | <= 2 s excluding external confirmation | async states must be explicit |
| GPS freshness | display age; warn if >120 seconds | varies by fleet/device and network |
| Recovery point objective | <= 15 minutes | requires WAL/PITR and verified operations |
| Recovery time objective | <= 4 hours | verify in restore game-day |
| Optimize job time | deadline and cancellation configurable | no unbounded solver jobs |

Do not market SLOs before load/restore and external provider tests.

## DR, backup and lifecycle

- Automated versioned database backups plus WAL/PITR and encrypted offsite storage; periodic restore with checksum and integrity checks.
- Object storage backups/replication and restore of tenant documents with keys.
- Defined ownership of schema migrations and rollback, expand/contract migration for zero-downtime changes.
- Per-tenant data retention policies, legal holds, export and deletion procedures; backup deletion limitations documented.
- Independent test/dev/prod configs and no production secrets in tests.
- Kubernetes possible after evidence; containerized single-instance/pilot deployment first is acceptable.

## Observability

OpenTelemetry traces, Micrometer/Prometheus metrics, structured logs with request_id, correlation_id, job_id and opaque tenant_id. Alerts for: tenant access denials anomalies, API error budgets, lagged outbox, backlog, stale GPS, failed imports, solver saturation, quote discrepancies, storage failure and backups. Do not put sensitive cargo or GPS coordinates into trace baggage.

## Required failure-mode / adversarial testing

1. Cross-tenant IDOR on read, edit, export, WebSocket, cache and document download.
2. Connection-pool session context survives failure -> still cannot see another tenant.
3. Duplicate webhook/refuel event/driver sync -> exactly one business effect.
4. Two dispatchers reserve same vehicle simultaneously -> one valid reservation.
5. DB commit succeeds and event publish fails -> outbox eventually delivers.
6. Traffic/GPS/ML provider unavailable -> explicit fallback with confidence downgrade.
7. Poison event / large payload / malicious file -> quarantined without compromising other tenants.
8. Partial disaster restore recovers consistent orders, documents and outbox.
9. Slow tenant optimization cannot starve other tenants' tasks.
10. Revoked partner cannot fetch future snapshots or signed documents.

## Release gates

Code scan + dependency/SBOM + secret scan; database migration smoke; tenant-isolation security suite; contract/integration tests; load tests with two or more tenants; staging restore rehearsal; exact-commit CI success; documented manual operational runbook.

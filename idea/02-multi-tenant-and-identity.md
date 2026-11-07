# 02 — Multi-tenancy, identity and inter-company collaboration

**Status:** architecture proposal. **Non-negotiable:** no cross-tenant data leakage.

## Terminology

- **Tenant:** SaaS subscription/security boundary; owns its configuration, quotas, audit and billing account.
- **Legal entity / organization:** company or branch operating inside a tenant; one tenant can manage multiple legal entities.
- **Partner organization:** external carrier, shipper or warehouse, normally owned by another tenant or only present as a directory contact.
- **Membership:** user, tenant, role(s), optional legal-entity scope, status and validity.
- **Collaboration grant:** explicit, narrow permission for another organization to access a specific shipment, trip task, document or milestone.

Customer users are not automatically tenant administrators. A platform operator has restricted support access, never permanent unrestricted visibility.

## Recommended tenancy model

**Start:** PostgreSQL shared database / shared schema with a mandatory tenant_id on tenant-owned rows, composite tenant-aware keys and PostgreSQL Row Level Security (RLS) as defense in depth. Application authorization remains required. System dictionaries may be global read-only tables.

**Enterprise option later:** dedicated database (and optionally isolated deployment), using the same domain contracts and a tenant database routing abstraction. Do not implement two persistence strategies before the first pilot, but avoid business logic depending on global shared identifiers.

### Isolation layers

| Layer | Required rule |
|---|---|
| Web/API | Resolve active tenant from authenticated membership, not from an arbitrary request header |
| Authorization | Verify role, tenant, legal-entity scope and resource ownership for every operation |
| Database | tenant_id not nullable; RLS and tenant-aware joins/FKs; deny unscoped queries |
| Cache | Keys include tenant and permission-sensitive scope; invalidate per-tenant |
| Object storage | Tenant-specific prefixes/buckets, access broker, short-lived signed URLs, server-side ownership checks |
| Events | Include tenant_id and event_id; consumer validates context, schema and authorization |
| Search/index/analytics | Tenant partition/filter; isolated query context; no arbitrary cross-tenant aggregation |
| Telemetry | Map device ownership and trip-sharing grants before exposing coordinates |
| Logs/traces | Tenant correlation by opaque identifier; redact personal, commercial and secret data |
| Exports/backups | Tenant-scoped export authorization and tested selective restore procedure |

For pooled JDBC connections, the transaction must set and safely clear the database tenant context; validate behavior under errors, reused connections, background tasks and migrations. Never treat a user-supplied tenant header as proof of authorization. Tenant-aware RLS alone does not solve cross-company workflows.

## Authentication and authorization

- OIDC/OAuth2 for users; verified JWT signature, issuer, audience, expiry and tenant membership.
- Users can belong to several tenants, choosing an active tenant through a validated server-side membership.
- Permission model: platform operator, tenant owner, tenant admin, dispatcher, planner, accountant, driver, customer, partner carrier, warehouse operator, auditor; use granular capabilities rather than fixed roles alone.
- Machine-to-machine: short-lived client credentials and scoped service permissions; no shared permanent universal API key.
- Enforce MFA for privileged accounts; rate limits, session revoke, invitation expiry and audit.
- Driver mobile access must be restricted to assigned tasks and permitted cargo/vehicle fields.

## Cross-company shipments

Example: Shipper tenant A orders from forwarder tenant B; carrier tenant C drives; warehouse tenant D receives. Each retains private rates, drivers, customers and finance. Share an explicit **shipment collaboration projection**, not all source records:

- Shipper: accepted quote, contractual milestones, delivery evidence.
- Forwarder: orchestration plan, provider status, commercial margin, customer commitments.
- Carrier: assignment, operational stops and cargo safety details; not forwarder's margin.
- Warehouse: appointment, relevant cargo handling and authorization status.
- Each party sees only necessary documents, with expiry and revocation of access.

Grant actions and disclosed fields are logged. Revoking access must stop future reads/downloads (already copied information cannot be retroactively erased).

## Billing and tenancy lifecycle

TenantProvisioning -> Trial/Active -> GracePeriod -> Suspended -> Export/DeletionPending -> Deleted, with safe read-only suspension rules and legally required retention. Billing dimensions candidates: active vehicles, planner seats, published jobs, GPS device count, optimization compute, map API usage, storage and integrations. Meter service usage per tenant with idempotent metering and spend caps; do not expose one tenant's billing records to another.

## Tenant safety test matrix (mandatory)

1. User A cannot read/write/export tenant B's order by UUID or guessed path.
2. A shared partner grant permits only the intended shipment fields.
3. Switching active tenant invalidates cached views and open socket subscriptions.
4. RLS blocks cross-tenant access even if an application query omits the predicate.
5. Background workers, migrations, scheduled jobs and retries cannot operate without explicit tenant context.
6. Signed object URL is tenant-bound, expiring and revoked as policy permits.
7. Every event, index and telemetry location respects scoped visibility.
8. Concurrent access and pooling never leak session state between tenants.

## Open policy choices

Data residency and retention by contract/jurisdiction; tenant BYOK requirement; exact billing units; third-party collaboration consent; customer support impersonation policy; formal data processing agreements and cross-border transfers. These require legal/security review before production.

## Incident rescue collaboration

When a failed vehicle needs external assistance, authorized partners may receive a narrowly scoped RescueRequest and submit offers. Reveal generalized pickup zone and cargo requirements initially; exact pickup location and custody documents only after confirmed contractual authorization. Preserve original tenant's customer identity, rates, margins and historical GPS confidentiality. See [14 — Rescue Network](14-emergency-recovery-subcontracting.md).

## Customer shipment tracking and visibility

A customer (shipper/consignee) may see only authorized shipment milestones and derived ETA, not full vehicle telemetry, the freight forwarder's purchase rates, drivers' personal details or other clients' stops. Guest tracking links, if enabled, must be narrow, expiring, revocable, backed by hashes of cryptographically random tokens and never become universal data permissions. Tracking API, SSE, cache, signed document access and notifications all enforce grants. See [19 — Customer Shipment Tracking](19-customer-shipment-tracking.md).

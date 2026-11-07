# 11 — Architecture Decision Register (ADR backlog)

All items are **proposed**, not ratified. Record decision owner, date, alternatives, consequences, migration path and decision status in dedicated ADR files when approved.

| ID | Topic | Recommended starting decision | Revisit trigger |
|---|---|---|---|
| ADR-001 | Product scope | Road-freight/mixed-fleet TMS first, multimodal model ready | Pilot proof and demand |
| ADR-002 | Architecture | Spring Boot modular monolith with explicit ports/events | Team and scaling evidence |
| ADR-003 | Tenancy | Shared PostgreSQL schema, tenant_id + RLS + app authorization | Enterprise contract/data residency |
| ADR-004 | Cross-company access | Scoped shipment collaboration grants/projections | Partner privacy/legal review |
| ADR-005 | Mapping/routing | Provider-neutral interface, test 2 candidates | Coverage, SLA, license |
| ADR-006 | Solver | Timefold optional Java optimizer; deterministic fallback | Version/license/performance review |
| ADR-007 | ML | Baseline first; Tribuo isolated behind predictor port | Verified labels/model uplift |
| ADR-008 | Integration | Transactional outbox + idempotent inbox | Provider reliability requirements |
| ADR-009 | Fuel | Normative calculation first, telemetry reconciliation later | Device data availability |
| ADR-010 | Files | RustFS/S3 via object storage interface, per-tenant authorization | Compliance/hosting constraints |
| ADR-011 | Hosting | Shared SaaS first; dedicated enterprise option later | Contractual isolation requirements |
| ADR-012 | Authorization | OIDC memberships, resource ABAC, scoped partner grants | Fine-grained policy growth |
| ADR-013 | Pricing | Versioned quote/cost snapshots with money precision | Tax/ERP mapping review |
| ADR-014 | Location | GPS observed vs inferred cargo location/custody separated | Multi-modal pilot |
| ADR-015 | Deployment | Containerized pilot with backup/observability | Verified demand for Kubernetes |
| ADR-016 | SaaS + Enterprise parity | One versioned logistics core supports pooled SaaS and dedicated/on-prem through configuration | Deployment pilot and enterprise requirements |
| ADR-017 | Emergency recovery and subcontract | Preserve the original order; create incident, approved replacement leg, scoped partner offer and cargo handover evidence | Carrier/insurer contract and operational pilot |

## Questions to settle before code

1. Who is the paying tenant: carrier, forwarder or shipper, and how do sub-brands/legal entities work?
2. Are companies allowed to bring their own clients and partner carriers without publishing them to a directory?
3. Which exact data fields can each party see during and after a shared shipment?
4. Does the customer require a binding fixed price, estimated price or hybrid contract?
5. Is the initial launch domestic Kazakhstan, cross-border, or both? Truck restriction and customs coverage differ.
6. Which provider has valid local live traffic, truck restrictions and usable data rights?
7. How does a customer receive proof of delivery and dispute it?
8. Which vehicle/driver and shipment telemetry fields are lawful/necessary to retain, and for how long?
9. What is source of truth for a carrier's real-time availability and capacity?
10. Which business costs are controllable by dispatcher vs finance and which approval limits apply?
11. What data is required to calibrate an ETA/fuel model without future leakage?
12. What availability and data-recovery guarantees can be afforded commercially?

## Decision template

    # ADR-NNN — Title
    Status: proposed / accepted / superseded
    Context: ...
    Decision: ...
    Alternatives: ...
    Consequences and tradeoffs: ...
    Security/privacy implications: ...
    Validation and rollback plan: ...
    Owner and date: ...

## Rejected shortcuts

- One shared administrator role for all companies.
- Global unique resource IDs as a substitute for tenant authorization.
- Blindly trusting tenant_id from an HTTP header or client token without membership.
- Hardcoded route-provider API calls in domain objects.
- Training ML before verified labels exist.
- Saying a customer's cargo is delivered merely because a truck reached its location.
- Applying automatic price changes without a versioned contractual acceptance event.
- Building independent billing, customs and banking modules before proving the logistics MVP.

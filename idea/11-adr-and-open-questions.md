# 11 — Architecture Decision Register (ADR backlog)

All items are **proposed**, not ratified. Record decision owner, date, alternatives, consequences, migration path and decision status in dedicated ADR files when approved.

**Current consolidated decision & risk tracker:** [docs/07 — Decisions and Risks](../docs/07-decisions-and-risks.md). `PROPOSED` remains the status of every ADR in this file until a real approval process is completed.

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
| ADR-018 | Warehouse stock truth | Transactional stock ledger + balance/reservation constraints, independent cargo owner and custody | Multi-owner transit warehouse pilot |
| ADR-019 | Yard/WMS/SVH boundaries | WMS+YMS interfaces in modular core, customs hold with verified release, hardware adapters | Warehouse operations and legal qualification |
| ADR-020 | Commercial lifecycle | Separate RFQ, conditional quote, offer, confirmed booking, delivery, documents and finance states | Expeditor workshop and pilot |
| ADR-021 | Financial exposure | Separate cost/margin from AR/AP, advances, credit limits and cash exposure; ERP can remain source of truth | Finance model and first-customer ERP integration |
| ADR-022 | Cargo classification and compatibility | Deterministic versioned rule engine, four-state decision, physical adjacency and jurisdiction/mode rules; ML cannot authorize | Approved legal/quality data and mixed-load pilot |
| ADR-023 | Customer shipment tracking | Shipment-centric permission-filtered timeline and ETA; vehicle GPS not proof of cargo custody, optional scoped guest link | Shipper/consignee privacy and pilot review |
| ADR-024 | Vehicle capability and capacity | Model tractor/trailer/body, payload and internal dimensions independently; specialized refrigerated/tank capabilities require verified equipment and legal compliance | Pilot fleet data and cargo classification review |
| ADR-025 | International identifiers & labels | GS1 identifiers/SSCC where legitimately issued, own UUID/LPN fallback, external code namespaces, EPCIS 2.0 adapter | GS1 issuer policy / label pilot |
| ADR-026 | Regulatory rule lifecycle | Jurisdiction/mode/date-specific source-versioned rules and required documents with expert approval; critical uncertainty fails closed | First real cross-border lane/legal opinion |
| ADR-027 | Customs and transport documents | Separate customs release, eCMR, TIR/eTIR and contract terms; no assumed official API | Approved provider/corridor compliance tests |
| ADR-028 | Documentation governance | `idea/` remains hypothesis and source; `docs/` carries consolidated draft requirements and release gates | Product-owner and domain-expert review |
| ADR-029 | Release 0 boundary | Road-freight E2E with tenant isolation, cargo safety, client tracking, POD and financial evidence; regulated integrations phased | Pilot contract/customer selection |

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

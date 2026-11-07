# 10 — Roadmap, MVP, pilot KPIs and acceptance

**Status:** proposal. Dates and effort are deliberately not promised before pilot resources are known.

## Phase 0 — foundations and discovery

**Needs-analysis gate:** before coding quote/booking workflows, qualify RFQ inputs, counterparty verification, contractual approval of changes, delivered-vs-invoiced-vs-paid states, and credit/cash exposure. The gaps and scenario acceptance are tracked in [16 — System Needs & Gap Analysis](16-system-needs-gap-analysis.md) and [17 — Day-in-Life Simulation](17-forwarder-dispatcher-day-simulation.md).


Deliverables: customer interviews and workflow mapping; benchmark representative routes; tenant threat model; data catalog; agreed business glossary; architecture decision records; provider proof-of-concept; test sample of completed trips.

**Gate:** two or more target companies validate workflows and are willing to participate in a pilot; validate availability of real traffic, GPS and rate inputs. If not, revise scope.

## Phase 1 — multi-tenant road-freight MVP

Scope:
- tenant registration, OIDC identities, membership and permission model;
- customer requests, order/quote/version/booking;
- owned and partner vehicle/driver directory, capacity assignment;
- 2–3 road route alternatives with restriction warnings and planned stop list;
- baseline ETA, fuel norm and itemized cost with price version;
- dispatcher route approval, changes and audit trail;
- one GPS adapter or simulator, latest position with freshness state;
- shipment milestones and proof-of-delivery evidence;
- plan vs actual kilometers/time/cost, basic customer and dispatcher UI.

**Not required for MVP:** AI training, nationwide truck legal data guarantee, own fuel depot equipment, automated customs clearance, rail/air/sea/drones, billing for public SaaS at scale.

## Phase 2 — operational efficiency

Rescue scenario: vehicle breakdown, manually approved internal reassignment and custody evidence; then opt-in trusted-carrier rescue offers, consent-based subcontract confirmation and route/cost recalculation. Complex marketplace matching and cross-installation federation come only after safety, authorization and contract tests. See [14 — Rescue Network](14-emergency-recovery-subcontracting.md).


Multi-order vehicle assignment, VRP stop optimization, automatic backhaul suggestions, partner availability workflow, traffic-aware departure planning, fuel card import and external AЗС reconciliation, driver offline sync, robust exception and alert handling.

## Phase 3 — cost and warehouse precision

Own fuel station ledger, CAN/tank sensor integration, maintenance, warehouse dock slots, temporary customs storage event integration where permitted, partner financial settlement, more sophisticated historical ETA and pricing calibration.

## Phase 4 — platform expansion

Optional Tribuo models when trained and measured; multi-tenant usage billing/quotas; dedicated enterprise deployment; multimodal legs (rail, sea, air), verified droning use cases only under required aviation approvals; marketplace offerings and integrations.

## Product KPIs

| KPI | Definition | Baseline |
|---|---|---|
| Quote preparation time | request receipt to documented quote version | measure from actual manual workflow |
| ETA MAE/p90 | error at prediction timestamp vs verified arrival | group by corridor/vehicle/provider |
| Vehicle empty-distance ratio | empty km / total actual km | compare equivalent periods |
| On-time delivery | delivered within agreed window | include exceptions and exclusions |
| Estimated cost error | |estimated−actual| / actual, eligible records | disclose missing actual cost |
| Dispatcher interventions | number and reason per 100 trips | monitor automation quality |
| Net contribution | revenue less explicitly defined attributed costs | same allocation rules |
| Tenant isolation defects | confirmed cross-tenant access | required zero in release qualification |

## Test fixture

Pilot reference dataset: 2 tenants, 10 trucks in total, 20 orders, at least 3 partner organizations, 2 warehouses, multiple cargo units, one route closure, one unavailable GPS, one fuel receipt replay and conflicting reservations. Include route through a facility with a time window and a trip with two different customers' cargo.

## Acceptance checklist (release-blocking)

- Each tenant's order, rate, invoice, telemetry, event stream and file inaccessible to other tenants without explicit grant.
- Authorized partner sees only the scoped collaboration projection; revocation is effective.
- Every accepted booking has a recorded confirmed reservation; duplicate request creates no duplicate booking.
- Simultaneous dispatchers cannot commit conflicting capacity allocations.
- Route warnings surface missing restriction data; forbidden routes cannot be auto-approved.
- Changing route creates a new plan version and recalculates ETA/cost, preserving baseline.
- GPS stale/offline state distinguished from a live observation; POD requires authorized evidence.
- Cost calculation reproducible with rate version/currency; actual expense does not rewrite historical quote.
- Provider outage degrades clearly; no silent fake precision.
- Outbox replay, duplicate webhooks, offline driver events and retry paths are idempotent.
- Backup/restore and database migration roll forward/rollback rehearsals completed in staging.
- Critical API security, load and exact-commit CI green before production launch.

## Pilot execution

1. Replay historical orders with timestamps and only data available at decision time.
2. Run shadow recommendations against manual dispatcher choices.
3. Review unsupported or unsafe routes with operational staff.
4. Enable assisted dispatch for agreed cases, with human confirmation.
5. Compare KPI outcomes and direct vendor/API operating costs.
6. Expand only after measurable quality and tenant isolation gates.

**Success criterion:** at least one evidence-backed improvement (quote time, ETA accuracy, cost or empty km) without regression in feasibility and security; set numeric business threshold with pilot participants before experiment.

## Warehouse Hub optional vertical slice and gates

To prove a 3PL transit warehouse, add a deliberately bounded pilot: 2 cargo owners at the same facility, 1 dock, 20 labeled pallets, ASN receipt, one discrepancy, putaway/cross-dock, concurrent pick attempt, outbound loading and custody handover. The Warehouse Hub is a modular extension of road-freight MVP, not a mandatory full WMS implementation before first logistics acceptance. Never ship regulated SVH functions without dedicated legal and operational qualification. See [15 — Logistics Hub / WMS](15-logistics-hub-wms-automation.md).

## Mandatory cargo compatibility gates

Cargo attributes and manufacturer/dangerous goods declarations are explicitly validated at RFQ/booking. First mixed-load or multi-owner warehouse pilot requires deterministic CargoCompatibilityPort, source/versioned rules, an unknown-data stop, vehicle-compartment and warehouse-zone restrictions, and adversarial tests for temperature mismatch, cross-contamination, dangerous goods uncertainty, false GPS/container compatibility, rescue re-handover and warehouse holds. See [18 — Cargo Classification & Compatibility](18-cargo-classification-and-compatibility.md).

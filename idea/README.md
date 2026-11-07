# KERUENIX — idea catalog

> **Status:** Discovery / concept, not production-ready specification.
> **Updated:** 2026-11-07

KERUENIX is a proposed **multi-tenant logistics operating platform** for carriers, freight forwarders, shippers and warehouse operators. Its core promise: plan feasible shipments, dispatch mixed fleets, monitor execution and explain planned versus actual cost.

## Read this catalog

| Document | Focus |
|---|---|
| [01 — Vision](01-vision-and-positioning.md) | Users, value proposition and scope |
| [02 — Tenancy](02-multi-tenant-and-identity.md) | Isolation, organizations, roles, data access |
| [03 — Domains](03-domain-model.md) | Orders, shipments, trips, cargo and movements |
| [04 — Operations](04-operational-workflows.md) | Booking, dispatch, custody, incidents |
| [05 — Optimization](05-routing-optimization-and-intelligence.md) | Routing, departure times, Timefold, Tribuo |
| [06 — Economics](06-pricing-fuel-and-settlements.md) | Pricing, fuel, cost, partners |
| [07 — Integrations](07-external-integrations.md) | Maps, GPS, ERP, WMS and customs |
| [08 — Reliability](08-security-reliability-and-sre.md) | Tenant safety, availability, audit and recovery |
| [09 — Architecture](09-reference-architecture.md) | Java/Spring Boot modular design and APIs |
| [10 — Delivery](10-mvp-roadmap-and-acceptance.md) | Phased delivery and acceptance tests |
| [11 — Decisions](11-adr-and-open-questions.md) | Proposed ADRs and unresolved choices |
| [12 — Competitive ideas](12-competitive-benchmark.md) | Patterns to learn from existing platforms |

## Concept rules

1. One **commercial order** is not necessarily one **physical shipment** or one **vehicle trip**.
2. Make the **tenant boundary** explicit at every read, write, event, cache key, file and export.
3. Optimize **only feasible plans**; route legality, capacity, driver rest and required custody events are hard constraints.
4. Separate **plan**, **forecast** and **fact**; preserve versioned explanations and audit history.
5. Ingest external GPS and traffic through replaceable adapters; avoid dependence on one vendor.
6. Launch with road freight and a controlled pilot; multimodal, autonomous drones and a public marketplace are future work.

**Documentation policy:** mark assumptions, decisions and experiments explicitly. Do not treat illustrative cost figures or unofficial road restrictions as authoritative.

**Next:** review the [MVP and acceptance](10-mvp-roadmap-and-acceptance.md) before implementing features.

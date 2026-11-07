# 12 — Competitive patterns and build-vs-integrate

**Status:** idea inventory, not a 2026 feature audit or independent vendor ranking. Recheck products, APIs, licenses and market terms in vendor discovery.

## What to learn

| Reference system | Product pattern worth learning | KERUENIX experiment |
|---|---|---|
| SAP Transportation Management | Commercial order / freight execution / settlement separation | Model quote, trip and invoice independently |
| Oracle Transportation Management | Multi-leg transport planning and costing | Reproduce explainable plan vs actual cost |
| PTV routing and optimization | Truck constraints and multiple-stop planning | Evaluate safe variants under windows |
| Wialon | GPS events, geofences, fuel and dispatch monitoring | Provide freshness and confidence-aware fleet view |
| Traccar | Ingest diverse GPS device protocols | Reuse telemetry gateway rather than reimplement |
| project44 / FourKites | Shipment-centric visibility, predictive milestones | Follow cargo across vehicle transfers |
| Transporeon | Carrier procurement and dock collaboration | Partner confirmation + appointment workflow |
| Geotab / Samsara | Vehicle telemetry and fleet operations | Normalize actuals and anomaly review |
| ATI.SU | Carrier exchange and trust workflows | Experiment with scoped offers and partner onboarding |
| HERE / 2GIS / other map APIs | Routing/traffic/geocoding services | Provider benchmark on target corridors |
| Timefold | Java constraint solver | Schedule vehicles and jobs with explainable restrictions |
| Tribuo | Embedded Java predictive models | Compare ETA/fuel estimates to deterministic baseline |

We borrow **business ideas and interoperable patterns**, not copyrighted source, proprietary data or unlicensed UI. A market benchmark needs product demos, legally obtained test accounts, API terms and controlled pilot evidence.

## Where to build ourselves

- Core shipment/order/custody domain;
- multi-tenant and inter-company permission model;
- versioned decision and cost engine;
- workflow of approval, plan/forecast/fact and exceptions;
- customer/dispatcher experience and pilot analytics.

## Where to integrate

- Maps/traffic/truck path calculation;
- GPS protocol support and third-party fleet telemetry;
- optimization solver engine;
- ERP/tax/accounting and payments;
- fuel cards/pump hardware;
- WMS/customs and other regulated documents.

## Vendor evaluation scorecard

Weighted scoring must be agreed per pilot customer. Candidate dimensions:
- truck routing legality/coverage in Kazakhstan;
- predicted ETA measured against actual trips;
- fresh road closures/traffic and data freshness semantics;
- API licensing, data retention and caching rights;
- integration contract stability;
- latency, rate limits and observed failure modes;
- operational support and local language/addresses;
- cost per 1,000 route calls or active tracked vehicle;
- privacy/data hosting requirements;
- fallback ability and lock-in exposure.

Record test cases, dates, vendor version, route sample and observed failures. Do not substitute website marketing claims for measured quality.

## Differentiation hypothesis

KERUENIX can unify feasibility, quote cost, dispatch exceptions and actual profitability per shipment for smaller regional operators that cannot adopt a heavy enterprise suite. Validate willingness to pay, configuration burden, vendor costs and support load in customer discovery.

## Initial benchmark artifacts

1. 30 documented routes including truck restrictions and facility entrances.
2. 20 trips with ETA baseline and observed timestamps.
3. 10 fuel ledger cases including duplicates and disputed anomalies.
4. Cross-tenant collaboration scenario with four parties.
5. Route-change comparison: ETA, cost delta, customer approval.
6. Complete quote-to-settlement audit trail.

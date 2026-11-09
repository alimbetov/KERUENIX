# 01 — Vision, customers and product boundaries

**Status:** proposed · **Version:** 0.1 · **Date:** 2026-11-07

## Mission

KERUENIX is a multi-tenant logistics operating platform: from customer request and costed options through dispatch, multimodal shipment execution, proof of delivery and actual profitability. It should explain **why** a plan is feasible, what it costs, and what changes if an incident occurs.

## Target customers and operating models

| Persona | Jobs to be done | Value |
|---|---|---|
| Cargo owner / shipper | Request, compare and track a shipment | Predictable price, ETA and evidence of delivery |
| Freight forwarder / 3PL | Buy transport, consolidate loads, coordinate partners | Margin and exception control |
| Carrier with owned fleet | Assign drivers and trucks, monitor utilization | Lower empty mileage and operational cost |
| Mixed-fleet operator | Combine owned capacity with subcontractors | Choose feasible and profitable fulfillment |
| Warehouse / temporary customs storage | Book docks, receive, hold and release cargo | Predictable load and custody trail |
| Enterprise account | Run multiple legal entities or branches | Shared governance with explicit permissions |

**Initial segment:** 1–3 Kazakhstan road freight operators, each with 5–50 vehicles and some subcontracted loads. This is a proposed pilot profile, not validated demand.

## Core outcomes

1. Quote a feasible service with cost breakdown, expiration and source/version of rate assumptions.
2. Choose a compliant route and departure window, including road closures, driver rules, stops and warehouse availability.
3. Assign owned or partner capacity without double booking.
4. Monitor vehicle, shipment and custody as separate concepts.
5. Recommend a safe change, show estimated time/cost delta, require approval where appropriate.
6. Reconcile actual kilometers, expenses, fuel and contractual settlement.
7. Learn from completed trips; never make model inference mandatory for safe operations.

## Distinctive value

**A decision-and-cost layer on top of transport execution:** compare alternatives for vehicle, route, departure, refueling and carrier with an auditable plan-vs-forecast-vs-fact record. This is a hypothesis to validate in pilot; not a claim that competing products cannot do it.

## Product boundaries

| Now: road freight MVP | Later: expand |
|---|---|
| Order, quote, booking, trip, route-plan versions | Marketplace and bidding at scale |
| Company-specific users, permissions, tenants | Sophisticated inter-company collaboration and settlement |
| One maps/traffic and one GPS adapter | Many providers and failover |
| Baseline costs, route alternatives, dispatch | Fleet-wide VRPTW, backhauls, AI predictions |
| Stops, simple fuel estimate and delivery evidence | Sensor-based fuel reconciliation and own fuel stations |
| Warehouse stop / appointment reference | Full WMS and temporary customs storage workflows |
| Data model for transport legs | Rail, sea, air, drones with separate regulatory qualification |

## Product principles

- Optimize profitability only **after** hard safety/legal constraints have been satisfied.
- Never silently change price, deadline, required cargo stop or shipper agreement.
- Distinguish estimated location from confirmed cargo custody.
- Make every recommendation explainable and reversible.
- Design for degraded operation: no traffic/GPS/model => clearly marked fallback, not invented precision.
- Do not replicate ERP, government customs or professional GIS software if interfaces suffice.

## Non-goals at MVP

Live control of driver steering; automatic drone operations; customs filing without certified integrations; guarantees based on unverified external data; payment settlement marketplace escrow; training neural networks before collecting reliable labels.

## Hypotheses and validation

H1: dispatcher quote time falls measurably compared with the current workflow.
H2: predicted ETA errors shrink after calibration, against a fixed baseline.
H3: return-load planning lowers empty kilometers without reducing on-time delivery.
H4: plan-vs-fact accounting changes quotes or dispatch choices.
H5: users pay for combined cost + routing + execution value, not for GPS alone.

Test in a time-limited pilot with historical and prospective trips; define experiment groups and costs beforehand. See the delivery and acceptance document.

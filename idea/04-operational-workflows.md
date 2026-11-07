# 04 — User journeys, dispatch and exception handling

**Status:** proposed end-to-end workflows.

## Journey A — shipper books a road shipment

1. Authenticated shipper selects active tenant/legal entity and enters origin, destination, cargo units, weight/volume, transport conditions, time window and optional insurance/customs requirements.
2. Validate addresses and road access separately from visual pin coordinates; store confidence of geocoding.
3. Pricing invokes routing alternatives and eligible owned/partner capacity; mark missing live availability and unknown external fees.
4. Return economical, fast and balanced options, each with scope, terms, validity and price confidence.
5. Customer accepts a versioned quote; booking service reserves resources atomically or requests carrier confirmation. Do not advertise a reservation until confirmed.
6. Dispatcher approves route, stops, safety/driver constraints and assignment.
7. Driver confirms pickup and custody with available online/offline evidence.
8. Device GPS updates vehicle location; shipment milestones are created only by authorized custody/scan/events.
9. Exceptions may propose alternate plans with ETA and cost delta, subject to approval and customer contract.
10. Proof of delivery captured; reconcile expenses, partner invoice, customer invoice and exceptions; close order.

## Journey B — dispatcher re-routes

Inputs: current vehicle position and freshness, approved route version, destination deadlines, closure information, cargo/vehicle limits, contractual constraints, fuel reserve, driver availability.

Decision procedure:
1. Detect significant deviation, road closure or deadline risk; debounce jitter.
2. Re-evaluate current route and viable alternatives from the latest confirmed position.
3. Filter illegal/infeasible alternatives (dimensions, weight, restrictions, driver rest, time windows, required stops).
4. Estimate updated ETA distribution, distance, fuel, tolls, stop delays and cost.
5. Show comparison and explanation; append recommendation record and source timestamps.
6. Dispatcher approves proposed change; check expected route version (optimistic concurrency) and invalidate stale suggestions.
7. Publish assignment update to driver; require acknowledgment for operationally significant route changes.
8. Notify customer only per contractual event rules and channel preferences.

If no feasible option exists, raise manual escalation; never fabricate a feasible route.

## Journey C — mixed fleet and partner capacity

- Candidate assignment requires confirmed availability; consider driver qualifications, vehicle profile, capacity, loading compatibility and carrier SLA.
- Separate estimated provider purchase price from customer sales price and internal operating expense.
- Capacity reservation requires expiry, idempotency and conflict handling.
- Partner sees only allocated operational details; customer sees contract-bound tracking, not carrier's confidential telemetry.
- Cancellation releases reservation and calculates contractual fee.

## Journey D — multi-stop / consolidated cargo

- Combine orders into one trip while preserving per-order milestones and per-cargo custody.
- Respect pickup-before-delivery precedence, incompatible goods, volume/weight profiles, delivery windows and facility rules.
- Allocate shared costs according to a declared and auditable method.
- Re-optimize only unlocked stops; preserve mandatory customs, recipient and booked warehouse appointments.

## Journey E — warehouse and temporary storage

Vehicle arrival -> gate check -> dock booking -> unload/load/stock transfer -> custody confirmation -> release clearance -> departure. Temporary customs storage adds controlled status and release checks. Regulatory workflows remain integration-specific pending jurisdictional validation.

## Journey F — no connectivity / degraded mode

Driver app queues signed operational events with stable UUIDs and local timestamps; server validates sequence and actor on sync, detects duplicates/conflicts, and never trusts client clock alone for settlement. Live map marks last observation with age and uncertainty. Routing without live traffic is explicitly labeled historical/static. Expired quote or missing provider capacity cannot be silently treated as confirmed.

## Human decision boundaries

Automatic: generate draft route, compute alternative, flag fuel mismatch, update non-contractual ETA.
Approval required: assignment changes with commercial impact, altering promised delivery window, deleting mandatory stops, adding unapproved carrier, modifying price, releasing customs-controlled goods.
Prohibited: bypass vehicle safety rules, auto-approve payments or evidence without authorization, use GPS alone as proof of delivery.

## UX surfaces

- Customer: request form, quote comparison, booking, shipment timeline, document center, issue messaging.
- Dispatcher: fleet map with data age, exception queue, trip board, editable versioned route, cost delta.
- Driver: assigned tasks, stop order, navigation handoff, online/offline scan and POD.
- Carrier partner: offer/accept assignment, task visibility, compliance documents, milestones.
- Warehouse: appointment calendar, arrival/exit and custody scans.
- Finance: price vs cost vs actual by order, trip, carrier and tenant.

## Acceptance scenarios

Two tenants use the same vehicle nickname and same customer reference: no leak. A closure triggers proposed route change with correct cost delta; old version remains audit-visible. A shipment transfers to another truck: tracking follows cargo custody not old truck. Offline pickup sync duplicate creates one custody event. Carrier rejects job: reservation released and new quote/assignment required.

## Journey G — vehicle breakdown and rescue subcontract

Driver or telemetry reports a verified issue; dispatcher checks safety and whether transfer is permitted. Planner selects safe handover facilities and searches replacement capacity first internally, then via consented partner offers. After approvals, reserve the selected partner, confirm cargo handover with evidence, create a replacement route leg and recalculate ETA and cost. Do not replace the commercial order or treat a accepted offer as completed physical transfer. For state machine, privacy and financial controls, see [14 — Rescue Network](14-emergency-recovery-subcontracting.md).

## Journey H — multi-owner logistics hub operations

Pre-advised inbound shipment -> dock slot -> gate/yard check-in -> actual SSCC/LPN scan -> discrepancy/quality checks -> putaway OR cross-dock -> stock ledger -> reserve/pick -> outbound loading manifest -> custody transfer -> gate-out -> charge reconciliation. Rescheduled vehicle ETA may change dock appointment but not actual stock/custody until confirmed scans. Holds, concurrent picks, offline duplicate events and mixed tenant-owned goods are mandatory adversarial cases. See [15 — Logistics Hub / WMS](15-logistics-hub-wms-automation.md).

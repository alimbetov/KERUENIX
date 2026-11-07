# 06 — Costing, pricing, fuel and settlements

**Status:** proposed accounting model. Accounting/tax treatment needs local expert review.

## Separate commercial vs operating numbers

- Quote/price: contractual amount and service scope offered to customer.
- Cost estimate: expected owned-fleet and external supplier direct + allocated overhead costs.
- Actual: posted fuel, driver time, tolls, vehicle costs, warehouse costs, subcontractor invoices and adjustments.
- Contribution margin and full profit: calculations with explicit allocation policy; not interchangeable.
- Customer invoice, carrier payable, payments, credit notes and disputes: financial lifecycle.

Do not calculate quote solely as distance multiplied by one universal rate.

## Cost dimensions

Distance (loaded/empty/return/deadhead), driving time, paid time, fuel and idle burn, driver compensation, depreciation/leasing, tires/maintenance, insurance, tolls, ferries, border permits, waiting, customs handling, warehouse/temporary storage, partner tariff, currency fluctuation, contingency and overhead. Freight details include cargo insurance, handling class and temperature constraints.

Treat fixed, variable and allocated costs distinctly. Some costs belong to a trip; others to shipment/order/stop. Preserve policy for splitting one shared trip among several shipments (weight-distance, volume-distance, pallets or activity-based; make configurable and reviewable).

Money must be BigDecimal with currency, tax category, effective dates and exchange-rate provenance. Record original invoice currency and converted reporting currency. Avoid mixing gross margin, markup and margin percent.

## Cost engine pipeline

1. Snapshot commercial obligations and cargo profile.
2. Snapshot route, expected kilometers, driving/idle/waiting hours and provider source timestamp.
3. Quote owned fleet vs carrier offers.
4. Derive fuel from vehicle-specific baseline and expected conditions; verify station availability.
5. Add fixed/variable/toll/handling/warehouse/partner and overhead items.
6. Add risk reserve or price confidence band where warranted.
7. Apply customer-specific pricing/contract rule and explicit approval thresholds.
8. Save immutable QuoteVersion and CostEstimate with formulas, rate card version and expires_at.
9. Recalculate only through new version, preserving history.
10. Post actual facts after delivery and reconcile discrepancies.

## Fuel management, from basic to advanced

### Phase 1: norms
Plan fuel = route distance * calibrated liters/100km / 100 + idle + auxiliary usage; factors by vehicle, weight, temperature and topography should be measured, not arbitrary.

### Phase 2: external stations and cards
Import transactions: provider ID, station ID, vehicle/driver or card attribution, product, liters, price, currency, timestamp, receipt reference. Dedupe by provider event + tenant, validate against authorized vehicle/card and GPS vicinity with tolerances. No proof of fraud from one mismatch alone.

### Phase 3: own fuel depots / stations
Fuel inventory ledger by tank, receipts, transfers, pump dispensing, inventory reconciliation, stock valuation, calibrated measurement and meter events. Assign responsibility and immutable audit. Integrate certified controllers and accounting systems rather than treating a GPS tracker as the legal metering device.

### Phase 4: tank sensors/CAN
Correlate fuel-level time series, refueling receipts, consumption and vehicle motion. Sensor bias, slope, delay, calibration and temperature affect readings; generate anomalies for human review with confidence and evidence.

## Refueling optimization

Given route, remaining fuel, tank capacity, reserve, expected usage, stations and prices, select feasible station stops minimizing purchased fuel + detour + driver waiting + access/toll costs. Respect opening hours, vehicle access, fuel contract constraints and uncertain price freshness.

## Partner settlement

Carrier offer -> accepted purchase order -> dispatch -> service evidence -> invoice matching -> variance dispute -> approval -> payment. Forwarder margin is private to its tenant; carrier sees only contractually scoped price and tasks.

## Reporting

Per order, trip, vehicle, route corridor, customer, partner and tenant: planned vs actual cost, realization, gross margin, fuel liters/100km, empty-distance %, deadhead, delay costs, warehouse waiting, chargeback and exceptions.

## Controls and tests

- Quote versions immutable; change requires new approval if threshold exceeded.
- Same external receipt imported twice posts once.
- Cross-tenant rate cards and invoices never resolve.
- No negative inventory unless explicitly authorized adjustment workflow.
- Currency conversion is reproducible from stored rate.
- Reconciliation of split shipments does not double count costs.
- Missing provider prices yield provisional offers, not false fixed guarantees.

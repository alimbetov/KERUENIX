# 07 — External systems and data contracts

**Status:** candidate integration catalog. Capability, licensing, coverage and prices must be validated for Kazakhstan and each target country.

## Integration principles

1. Use ports/adapters in the core, not vendor classes in Order/Trip domain.
2. Contract-test each adapter; store provider, version, query metadata, timestamps, confidence and licensing limits.
3. Rate-limit, time out, retry idempotently with jitter and circuit-break, never retry blindly after an uncertain booking/payment outcome.
4. Cache only if vendor terms allow; do not mix tenant-sensitive cache data.
5. Return degraded-mode indicators when live data is unavailable.
6. Track cost per tenant/provider/request, coverage and failure rate; configurable quotas and kill switches.
7. Version payloads and use inbound outbox/inbox-style dedup where supported.

## Provider matrix

| Need | Candidates | Initial approach |
|---|---|---|
| OSM road graph | OpenStreetMap + Valhalla | Prototype/static baseline; review OSM license and graph freshness |
| Truck routes/traffic | HERE, PTV, 2GIS and others | Test 2 providers with same Kazakhstan corridor scenarios |
| Maps UI | MapLibre or commercial SDK | Separate rendering from routing rights and data |
| Telematics protocol gateway | Traccar | Self-host optional; vendor GPS cloud adapter alternative |
| Fleet management | Wialon, Geotab, Samsara | Import GPS/fuel/vehicle events only with consent and API rights |
| Solver | Timefold Solver | Internal Java library behind optimization port |
| Prediction | Tribuo | Internal optional Java library, baseline fallback |
| ERP and finance | 1C and other ERP | Invoice and cost imports via secure adapter |
| WMS / gate | Facility WMS, dock scheduler | Appointments, arrivals and confirmed handoffs |
| Fuel providers | Fuel card operators, own pumps | Transaction registry/REST import and reconciliation |
| Customs/SVH | Authorized local platforms, brokers | Manual milestones first; regulated document exchange later |
| Partners/marketplaces | Carrier/shipper platforms and EDI | Explicit B2B integration, not scraping proprietary data |

Do not claim that every named vendor offers each capability in Kazakhstan. Separate routing constraints from regulatory certification.

## Common integration contracts

RouteProvider: route alternatives + traffic and truck restrictions.
GeocodeProvider: coordinates, precision, access point and provider evidence.
TrafficIncidentProvider: segment, validity interval, severity, restriction and updated_at.
TelematicsProvider: device registration, location events, sensor readings, event clock.
FuelTransactionProvider: refill item with dedup key, station/time/liters/price.
WarehouseProvider: facility, available appointment, confirmation, arrival/exit and cargo handoff.
DocumentProvider: create/verify evidence with access scope and checksum.

For provider events, track occurred_at and ingested_at; store original event ID and a payload checksum when permitted.

## Tracking trust model

- A GPS point must have device-to-vehicle assignment validity time and quality classification.
- A vehicle location is not shipment custody; show shipment-attributed location only while linkage is justified by pickup, loading and handover events.
- Data age displayed; position predicted beyond freshness threshold is labeled estimate.
- For partner fleet, share only trip-scoped observations, not entire historical route or other business clients.
- GPS spoofing, stale devices and impossible jumps generate review events, not automatic penalties.

## Resilience

- Provider outage: manual dispatch and static routing allowed with warning and approval; no false guaranteed ETA.
- Late/duplicate/out-of-order events: idempotent consumer and reconciliation.
- Inconsistent geocoding: manual facility coordinate confirmation.
- Request cost spike: tenant quotas and provider circuit breakers.
- Dependency lock-in: adapter contract compliance tests and saved baseline test corridors.

## Vendor due diligence checklist

Kazakhstan truck restriction coverage; future traffic prediction; API license/redistribution rights; personally identifiable location handling; data localization obligations; auditability; SLA; pricing; sandbox support; fallback; cancellation/rebooking semantics; bulk import; support of RU/KZ/EN place names.

## First provider acceptance

Take the same 20–50 road-corridor and last-mile cases, including known height/weight restrictions, warehouses and tolls. Record route legality flags, ETA variance, costs, latency, error behavior, licensing and operational response. Pick providers from evidence, not feature marketing.

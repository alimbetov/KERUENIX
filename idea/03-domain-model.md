# 03 — Canonical domain model and invariants

**Status:** conceptual; not a database migration.

## Separate the objects

| Entity | Meaning | Key invariants |
|---|---|---|
| Order | Customer commercial request/contract | Price, parties and deadline explicitly versioned |
| OrderLine | Goods/service obligations | Units, hazardous flags, declared value tracked |
| Shipment / Consignment | Physical collection of cargo moving together | Can split/merge; independently tracked |
| CargoUnit | Pallet, parcel or container with identifier | Custody and quantity conserved |
| TransportMovement | Planned movement from origin to destination | Contains ordered legs; linked to shipment(s) |
| TransportLeg | Road, rail, ocean, air or drone portion | Mode-specific constraints and handoffs |
| Trip | Actual resource execution, usually a vehicle tour | May serve many orders/shipments |
| TripAssignment | Driver, vehicle, trailer and validity window | No incompatible concurrent assignments |
| RoutePlanVersion | Immutable proposed/approved path | ETA, segments, traffic snapshot and author |
| RouteStop | Pickup, delivery, fuel, rest, service, border, warehouse | Time window, service time, mandatory flags |
| TripEvent | Observed execution event | Event time and receipt time both preserved |
| CustodyEvent | Who accepted/released cargo, where and when | Chain of custody auditable |
| QuoteVersion | Proposed price and terms | Cost inputs and expiration immutable |
| CostEstimate / ActualExpense | Planned vs incurred amount | Currency, allocation and provenance recorded |
| FuelTransaction | Pump, card or manual refueling evidence | Duplicate-source replay prevented |
| ProofOfDelivery | Signed/photographic/commercial delivery evidence | Permissions, retention and checksum |

A single order can yield multiple shipments; a shipment can move through multiple legs; a trip may carry cargo from multiple orders; a vehicle can be assigned to many trips across non-overlapping periods.

## Proposed lifecycle

Order: DRAFT -> REQUESTED -> QUOTED -> ACCEPTED -> BOOKED -> IN_EXECUTION -> DELIVERED -> SETTLED -> CLOSED. CANCELED and DISPUTED are explicit transitions, not silent field edits. External documents and financial obligations may remain after cancellation.

Trip: PLANNED -> ASSIGNED -> READY -> IN_PROGRESS -> COMPLETED -> RECONCILED. Additional states BLOCKED and CANCELED with reasons.

Shipment: REGISTERED -> READY_FOR_PICKUP -> IN_TRANSIT -> AT_TERMINAL -> DELIVERED; split/merge and custody events must not erase prior milestones. An order's delivery status is derived from all relevant shipment lines, not a single vehicle position.

## Example relationships

    Tenant -> LegalEntity -> Membership
    Tenant -> Orders -> OrderLines -> Shipments -> CargoUnits
    Shipments <-> TransportMovements -> TransportLegs
    Trips <-> TripAssignments -> Vehicle / Driver / Trailer
    Trips -> RoutePlanVersions -> RouteStops / Segments
    TransportLegs <-> Trips (for road legs)
    Shipments -> CustodyEvents -> Evidence
    Orders -> QuoteVersions -> CostEstimates
    Trips -> ActualExpenses / FuelTransactions

Every tenant-owned entity carries tenant_id. Cross-tenant collaborations use scoped reference/grant objects and replicated read-model projections; do not create foreign keys into another tenant's private tables.

## Event design

Domain event minimum fields: event_id, tenant_id, aggregate_id, aggregate_version, event_type, occurred_at, recorded_at, actor_id, correlation_id, causation_id, schema_version and payload. Publish via transactional outbox; consume idempotently with inbox/deduplication. Events are not a substitute for transactionally maintained invariants.

Examples: OrderRequested, QuoteAccepted, CapacityReserved, TripAssigned, RoutePlanApproved, VehiclePositionObserved, EstimatedArrivalChanged, CargoHandedOver, FuelTransactionImported, ProofOfDeliveryAccepted, ShipmentSettled.

## Temporal and location model

Use UTC for timestamps; persist original time zone and local appointment window for human display. Coordinate CRS and source accuracy must be explicit. Store predicted arrival distributions or intervals separately from observed arrival. GPS position is vehicle position, not proof of cargo custody.

## Multi-modal extension

Each TransportLeg has mode, operator, contracted capacity, origin/destination facility and milestone contract. Rail requires train/service identifiers; ocean requires voyage/port events; air requires flight/air waybill semantics; drone operations require dedicated regulation, permission and safety assessment. Do not force all modes into road RouteStop or Driver models.

## Integrity and privacy

Optimistic locking for edited plans and assignments; unique idempotency key per tenant/action; composite key constraints; custody quantity reconciliation; money represented in decimal minor units/BigDecimal plus currency; preserve snapshots of contract rates. No unsafe delete of evidence or finance records. Document retention and tenant deletion must be policy-driven.

## Emergency re-assignment and subcontracts

A breakdown may interrupt a Trip without canceling the commercial Order or physical Shipment. A RecoveryCase links the incident to the affected CargoUnits, approved alternative TransportLegs and a SubcontractAgreement. Reassignment requires verified CargoHandover and must preserve immutable custody history. See [14 — Rescue Network](14-emergency-recovery-subcontracting.md).

## Warehouse inventory and hub domain

WarehouseFacility, FacilityZone, BinLocation, HandlingUnit, StockMovement/Line, StockBalance, InventoryReservation, WarehouseTask, DockAppointment and CustodyHandover are separate from Trip, Shipment and CargoOwner. Ownership, actual custody and inventory visibility are independent. Stock changes through append-only correction movements with transactional balance/reservation checks; customs and quality holds block dispatch. See [15 — Logistics Hub / WMS](15-logistics-hub-wms-automation.md).

## Cargo compliance and segregation invariants

Commercial product category, dangerous goods classification, manufacturer handling profile, packaging, temperature and contamination risk are separate dimensions. A `CargoComplianceProfile` and versioned `CompatibilityAssessment` are linked to CargoUnit/Shipment; load/warehouse placement uses compartment/zone adjacency and time overlap. Hard legal rules cannot be bypassed by optimizer or dispatcher; unknown critical data does not mean compatible. See [18 — Cargo Classification & Compatibility](18-cargo-classification-and-compatibility.md).

## Customer-facing shipment status and projection

Customer tracking is a permission-filtered read model derived from Order, Shipment, TransportLeg, Trip, Custody and Delivery events, not an independent authoritative state. A Shipment may transfer between trucks or remain at a warehouse; vehicle location does not prove cargo custody. Store CustomerVisibilityPolicy, TrackingSnapshot, ShipmentMilestone and TrackingAccessGrant separately from raw GPS and financial data. See [19 — Customer Shipment Tracking](19-customer-shipment-tracking.md).

## Vehicle/trailer/body capability and capacity

Do not store vehicle capacity as a single payload_ton or volume_m3 flag. Model VehicleCombination, Body/Trailer, compartment dimensions, remaining physical capacity, pallet placements, axle loads and specialty capabilities for cold chain, bulk and regulated tanks. Driver/tractor/attached trailer configuration is time-versioned. See [20 — Vehicle Classification & Capacity](20-vehicle-classification-capacity-and-special-equipment.md).

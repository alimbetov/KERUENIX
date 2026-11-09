# 09 — Reference architecture and engineering conventions

**Status:** proposal for a Java-first system, intentionally modular before microservices.

**Deployment principle:** one product and codebase supports pooled multi-tenant SaaS and dedicated/on-premise installations; see [13 — Deployment Models](13-deployment-models.md). Keep tenant/resource authorization active even for a physically isolated installation.

## Technology options (final versions require compatibility check)

- Java 21, supported Spring Boot release, Spring Security/OIDC, JPA/JDBC with explicit tenant boundaries.
- PostgreSQL + PostGIS for transactional and spatial records, migrations with Flyway or Liquibase.
- Redis for bounded/tenant-scoped caches and temporary job controls, never the source of truth for reservations.
- RustFS/S3 object storage for documents and approved ML model artifacts; tested backup/restore.
- Next.js/React/TypeScript for customer/dispatcher/partner portals; Flutter for driver mobile app if operationally justified.
- Traccar or another telemetry adapter, maps/routing vendor adapter, Timefold-based optimization module; Tribuo optional predictor behind Java port.
- OpenTelemetry + Micrometer, structured logging, container builds, GitHub Actions CI.

Timefold/Spring Boot compatibility and vendor licenses must be verified against pinned versions before implementation. Do not include optional engines in the critical startup path.

## Deployment view

    Web / Partner portal / Driver app
                  |
             API gateway / WAF
                  |
       Logistics application (modular)
           |             |             |
     PostgreSQL       Redis         RustFS/S3
           |
      Outbox publisher -> message broker / workers
                             |
                     telemetry / optimization
                             |
               maps, GPS, fuel, WMS and ERP adapters

Broker selection (Kafka, RabbitMQ or Postgres-backed jobs) must follow measured workload and durability needs. A broker is not mandatory for the earliest single-instance prototype if persistent jobs/outbox are reliable.

## Modules (package ownership)

    keruenix/
      apps/api/
      modules/
        tenancy/           # organizations, membership, entitlements
        orders/            # offers and booking
        shipments/         # cargo and custody
        tracking/          # customer shipment timeline, ETA/read-model and visibility
        trips/             # assignments, stops, route plan versions
        dispatch/          # events and exceptions
        recovery/          # incidents, rescue offers, subcontract, cargo handover
        routing/           # provider-independent routing contracts
        optimization/      # constraints and solver adapter
        prediction/        # baseline, Tribuo and model registry
        cost/              # rates, costs, price, reconciliation
        fuel/              # norms, refuels, stations, depots
        warehouses/        # logistics hub / WMS entry point
        warehouse_inventory/ # stock ledger, reservations, counting
        yard_dock/         # gate, yard slots, docks and appointments
        warehouse_tasks/   # receiving, putaway, pick, cross-dock, ship
        integrations/      # supplier adapters and webhooks
        audit/             # sensitive actions and compliance
        identifiers/       # GS1, ISO container and external code namespaces
        regulatory/        # source-versioned country/mode rules & document checks
        labels/            # versioned GS1/internal templates and scanners
      clients/web/
      clients/driver/
      infra/
      idea/

Business modules communicate through explicit application APIs and domain events; avoid cyclic dependencies and direct access to another module's tables.

## Tenant persistence strategy

Central TenantContext comes from verified auth/membership. Domain service layers accept trusted context explicitly. Use tenant_id, composite constraints and RLS. Integration consumers and schedulers obtain tenant context from signed/validated event metadata, never from arbitrary message payload. Test pooled connection cleanup.

Global reference data (countries/currencies/mode enumerations) is read-only or curated; partner directory access is scoped and distinct from private tenant data.

## API conventions

REST endpoints versioned under /api/v1, standardized error format (Problem Details), explicit pagination and sort allowlists, request ids, ETags/expected versions and idempotency keys for dangerous writes. Examples:

- POST /api/v1/orders — create draft
- POST /api/v1/orders/{id}/quotes — request quote
- POST /api/v1/quotes/{id}/accept — accept with expected version and idempotency key
- POST /api/v1/trips/{id}/routes/evaluate — alternatives
- POST /api/v1/trips/{id}/routes/{version}/approve — explicit approval
- GET /api/v1/shipments/{id}/timeline — permission-filtered milestones
- POST /api/v1/driver/events — idempotent custody/activity sync

These are candidate URLs, not published contracts. Tenant is inferred from authorization context; never permit arbitrary path prefix to override current permissions.

## Async boundaries and consistency

A request to optimize many jobs returns durable job_id and state QUEUED/RUNNING/SUCCEEDED/FAILED/CANCELED. Worker loads authorized tenant snapshot, computes bounded result, revalidates version before proposed plan is surfaced. Commit only after approval and collision checks. Outbox drives notifications and derived tracking projections; idempotency ensures retries do not duplicate financial effects.

## Code-quality guardrails

- Domain objects independent of Spring and vendor SDKs.
- Database migrations immutable and reviewed; restrict raw SQL permissions and protect RLS.
- Separate test fixtures for tenant A/B, 1-to-many shipments and concurrent booking.
- Tests: unit, property-based constraints, integration Testcontainers Postgres, contract, E2E, load and chaos.
- Include SBOM, SAST, secrets scanning, dependency checks and exact-commit qualification.
- ADR per foundational choice; include alternatives and rollback.

## Build-first vertical slice

One tenant registers a company and driver; an order creates a quote; dispatch reserves a vehicle; routing produces an approved plan; a simulated GPS device sends a location; driver confirms delivery; cost reconciliation produces plan/actual. Then repeat concurrently with second tenant to prove isolation.

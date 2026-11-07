# 14 — Modular Delivery Blueprint: реализация R0a и дальнейшее расширение

**Версия:** 1.0 · **Дата:** 07.11.2026 · **Статус:** PROPOSED implementation plan.  
**Родитель:** [13 — Architecture Options](13-modular-architecture-options-v1.md).  
**Машинный каталог:** [contracts/module-boundaries.v1.json](contracts/module-boundaries.v1.json).  
**Текущий репозиторий:** к документации добавлен минимальный [backend error-handler bootstrap](../backend/README.md) (Spring Boot 4.1.2 / Java21); полноценные бизнес-модули, миграции, реальная аутентификация и подтверждённый CI ещё отсутствуют.

## 1. Форма репозитория

```text
KERUENIX/
├── README.md
├── idea/                              # гипотезы и отраслевая экспертиза
├── docs/                              # канонические требования/ADR/контракты
│   └── contracts/
├── backend/
│   ├── pom.xml                        # один основной Maven/Spring Boot artifact в R0
│   ├── src/main/java/kz/keruenix/
│   │   ├── KeruenixApplication.java
│   │   ├── platform/                 # jobs, state machine kernel, event/outbox infrastructure
│   │   ├── tenancy/
│   │   ├── commercial/
│   │   ├── fleet/
│   │   ├── cargo/
│   │   ├── compliance/
│   │   ├── booking/
│   │   ├── execution/
│   │   ├── tracking/
│   │   ├── documents/
│   │   ├── finance/\n│   │   ├── intelligence/             # ML history, datasets, training/model lifecycle (R0 design)\n│   │   └── optimization/             # constraint solving and Timefold (R1)
│   ├── src/main/resources/db/migration/
│   └── src/test/java/kz/keruenix/
├── apps/
│   ├── operations-web/                # экспедитор/диспетчер, React+TS
│   ├── customer-web/                  # shipment tracking (можно общий frontend на R0)
│   └── driver-web/                    # PWA/мобильный вид для пилота
├── deploy/
│   ├── compose/                       # Postgres, app, object-store optional
│   └── env.example                    # names, no real secrets
└── .github/workflows/
```

Это **предложение структуры**, папки/файлы реализации в репозитории пока не созданы. Для R0 можно объединить web apps в один React workspace с ролевыми маршрутами, чтобы не раздувать frontend.

## 2. Шаблон application module

```text
kz.keruenix.booking/
├── package-info.java            # @ApplicationModule и allowed dependencies
├── BookingApi.java               # публичный контракт для других модулей
├── BookingView.java              # публичный DTO/immutable snapshot
├── BookingConfirmed.java         # versioned public event
└── internal/
    ├── BookingApplicationService.java
    ├── Booking.java              # aggregate root, business invariants
    ├── BookingRepository.java
    ├── BookingPolicy.java
    └── BookingPersistenceAdapter.java
```

**Не экспортировать наружу:** JPA entity, repository, servlet controller implementation, SQL/native queries, internal mapping types. На уровне HTTP отдельный adapter/controller внутри модуля, контракт API versioned.

Модули могут иметь более подробную внутреннюю структуру `domain/application/adapter` при росте; не создавать три слоя и десятки интерфейсов для каждого простого DTO без причины.

## 3. Управление модульными контрактами

У каждого модуля:
- `owner` и *single writer* его данных;
- список публичных команд (API) и событий (events);
- `allowedDirectDependencies` только на чужие exported API;
- source of truth для aggregates/table ownership;
- tenancy/security/partner grants + cross-tenant visibility;
- failure/compensation, idempotency, consistency expectations;
- acceptance and observability requirements.

**Допустимые прямые связи** приведены в [JSON](contracts/module-boundaries.v1.json). Это **проектные ограничения**, не исполняемый plugin policy; при реализации нужно транслировать их в `@ApplicationModule(allowedDependencies=...)` и contract tests.

`booking` может вызвать `commercial`/ `fleet` через API и согласовать резервирование; `commercial` не зависит от `booking`. `tracking` потребляет подтверждённые события `execution`, но не управляет рейсом. `finance` слушает события коммерции и исполнения и ведёт собственные обязательства.

## 4. Модель транзакций и публикаций

**Local transaction:** один module owner atomic write + outbox record.  
**Cross module action:** command orchestration в application layer; direct DB write в чужие агрегаты запрещён даже в одном JDBC connection.  
**External Carrier/ERP:** idempotency + timeout + durable inbox/outbox and compensating actions.  
**Tracking:** eventual projection с watermark/source timestamp; не обещать строгую синхронность с GPS.  
**Payments/stock/reservations:** только проверенные атомарные ledger/constraints, асинхронный replay без double effect.

Для Event Publication Registry важны тесты сбоя listener/restart; для внешней доставки нужен проверенный outbox mechanism. Не включать Kafka только потому, что существуют события.

## 5. План реализации по PR

| Slice | Что реализовать | Блокирующее доказательство |
|---|---|---|
| P0 — Bootstrap | Maven/Spring Boot, Modulith, Testcontainers, Flyway, docker compose, config, health | `mvn verify`, архитектурная проверка, startup smoke |
| P1 — Tenant Foundation | Tenant/LegalEntity/membership, RBAC/ABAC, DB RLS и audit | Полная отрицательная матрица 2 tenant по HTTP и DB |
| P2 — Commercial & Fleet | RFQ, immutable QuoteVersion, Vehicle, atomic hold, Booking workflow | Expired quote, competing reservations, partner-scope denial |
| P3 — Cargo & Execution | Cargo profile, Trip, Shipment, Pickup/Custody, POD | GPS != delivery, partial POD and replay, safety constraints |
| P4 — Customer & Finance-lite | Tracking timeline + ETA freshness, document package, AR/AP/evidence | Customer scope, stale GPS, delivered != paid |
| P5 — R0a E2E | End-to-end one carriage with customer and carrier, failure injection | Exact SHA CI, own+partner fixtures, backup/restore smoke |
| P6 — Optional modules | Rescue, WMS, backhaul private board, optimizer | Domain-specific boundary, contract and acceptance suites |

P0–P5 — **порядок задач**, не длительности. Не следует начинать P6, пока не пройдена готовность P5, кроме отдельного эксперимента с чётким отказоустойчивым контрактом.

## 6. Карта R0a сценария

```text
[Customer Tenant B]
    RFQ request        -> commercial creates RFQ
    Quote accepted     -> commercial freezes QuoteVersion
[Expeditor Tenant A]
    Carrier selected   -> booking orchestrates fleet hold/confirmation
    Trip started       -> execution writes TripStarted
    Pickup confirmed   -> execution writes CustodyTransferred
    GPS observed       -> adapter records time-stamped observation
[Customer Tenant B]
    Tracking page      -> tracking read model, no other customer's trip data
    POD confirmed      -> execution validates cargo units/signatures
[Finance Tenant A]
    Invoice            -> finance own ledger, no fake PAID before payment
    Order summary      -> operational vs financial result separately
```

Все команды проверяют tenant/partner authorization. Даже если `Tenant B` — владелец груза, его роль не даёт доступ к закупочной цене `Tenant A`.

## 7. Профили поставки одного кода

| Profile | Runtime | Domain modules | Constraints |
|---|---|---|---|
| Pooled SaaS | Backend image + DB with strict RLS + per-tenant object-storage policy | One core build, licensing and route-policy flags | Scope/security tested, resource quotas |
| Dedicated | Same image, isolated DB+secrets | Same domain contracts | Dedicated deployment smoke |
| On-Prem | Same image and portable dependencies | No always-on SaaS control plane required | Backup/restore + intermittent connectivity |

Модули не должны зависеть от прямых URL облачной инфраструктуры. `@Profile` используется для **implementation adapters/config**, а не для изменения бизнес-правил в каждой среде.

## 8. Инженерные проверки на точном SHA

- **Architecture:** Spring Modulith verify + package import checks + no circular dependency.
- **Unit:** QuoteVersion immutable, booking guards, cargo/vehicle suitability.
- **Module integration:** `@ApplicationModuleTest` with legitimate mocks/fixtures for exported APIs.
- **Postgres integration:** Flyway on real PostgreSQL Testcontainers; RLS bypass, pool session leaks, concurrency, unique constraints, timestamps.
- **Event processing:** outbox retry, duplicate events, stale ordering, rollback after failed publish.
- **Security:** two independent tenants, partner grants, customer tracking, S3 evidence, negative authorization.
- **E2E:** R0a as in [docs/11](11-commercial-execution-acceptance-v1.md), exact SHA; no claims about real data from mocks.
- **Release:** reproducible container image, SBOM, secrets scan, health/readiness, backup/restore, docs, known limitations.

## 9. Факторы выделения microservice/worker

Для каждого кандидата `extractToWorker` фиксировать evidence:
- профиль CPU/memory/I/O и latency; необходимость отдельного autoscale;
- последствия падения относительно основного пути перевозки;
- объём и гарантии очереди (retries, deadlines, ordering, idempotency, DLQ);
- один владелец данных, миграционный план, contract version;
- observability and restore tested in production-like environment.

**Первая подходящая изоляция:** обработчик массовых GPS-событий или долгий route/Timefold optimizer.  
**Первая неподходящая изоляция:** Quote ↔ Booking ↔ Reservation, если нет доказанного распределённого обеспечения эквивалентной корректности.

## GIS / Storage Slice — дополнение к плану реализации

1. Сначала `PostGIS` и валидированные SRID/units в миграциях, два tenant, RLS + GiST `ST_DWithin` smoke; базовые геоточки можно добавить до реального GPS ingest.
2. `Fleet.current_position` — горячая read model; `Fleet.vehicle_position_event` — append-only, RANGE(time) partitions включать при реальном ingestion. Отдельный globally unique dedup registry нужен из-за ограничения PK/UNIQUE partitioned parent.
3. Только `Fleet` обновляет свои positions; `Tracking` строит собственный permission-filtered projection, `Execution` создаёт геозонные **candidate** события, но не POD по GPS.
4. `Partition Lifecycle Manager` — privileged operational job/extension с premake, late events, retries, retention/legal hold, backup/replay; прямое DDL у runtime app запрещено.
5. В каждом модульном PR: по [16 — Annex](16-module-storage-gis-addendum.md) определить `write/read/geo/partition/test` и пройти соответствующие `DATA/GEO` tests из [15](15-data-platform-partitioning-postgis.md).

## 10. Definition of Done первого PR

Есть исполняемый Spring Boot backend, бизнес-модули с `ApplicationModules.verify()` green, real PostgreSQL migrations и RLS, DTO/API contracts, docker compose, двухтенантный отрицательный тест, README запуска, CI green exact SHA и один вертикальный workflow. Наличие документов `docs/13`–`docs/14` **не означает выполнения этих критериев**.

**Решение на утверждение:** выбрать B (Spring Modulith logical modules) для R0 и E (modular core + workers) для развития; отложить C/D до реальных эксплуатационных сигналов.

## Intelligence — special module extension (proposed)

`intelligence` is a separate Spring Modulith module for tenant-safe historical ML projections, immutable datasets, training lifecycle, registry and inference. `optimization` remains owner of Timefold jobs and hard constraints. Training workers are separately deployable and cannot write another module's tables. The exact contracts, state machines, RLS boundaries and acceptance cases are in [17 — Intelligence Special Module](17-intelligence-special-module.md). The design is R0; execution starts after qualified tenancy and a usable first business vertical slice. Do not treat this section as implemented code.

## Platform Jobs / State Machines / Workflow standard

Selected architecture: [18 — Platform Jobs, State Machines & Workflows](18-platform-jobs-state-machines-workflows.md). Platform Jobs stores durable technical job state in PostgreSQL with bounded virtual-thread I/O workers, lease fencing, retry/recovery and tenant security. State Machine Kernel only standardizes transition evaluation; each module persists its own business lifecycle and guards. Cross-module coordination belongs to domain-specific durable Process Managers. Redis never owns confirmed jobs. First acceptance slice: expired Fleet capacity hold + Booking process manager with outbox, crash and two-tenant tests. JobRunr is a PoC candidate, not a locked dependency.

## Architecture Hardening priorities — mandatory implementation filters

Follow [19 — Architecture Hardening Priorities](19-architecture-hardening-priorities.md): (1) Correctness First, (2) Operational Reliability, (3) Intelligence Ready. The catalog stays at 17 business modules. Baseline: Java 21, Spring MVC/JDBC + Virtual Threads, PostgreSQL RLS, Outbox and durable Jobs; Redis is not authoritative. Gate A0 aligns contracts and owners; A1 establishes two-tenant foundation; A2 proves Booking + CapacityReservation concurrency/expiry; A3 establishes custody/POD/Finance-lite end-to-end; A4 qualifies failure/restore/metrics; A5 runs optional ETA ML pilot only with reliable data. Do not treat all 20 technology ideas as R0 dependencies. No new business module required for generic framework capability.

## Engineering baseline — MapStruct and test-driven development

Apply [20 — MapStruct + TDD Engineering Standard](20-mapstruct-tdd-engineering-standard.md) for all 17 existing modules. MapStruct is the default for nontrivial module-owned DTO mappings, with explicit sensitive fields and strict compile-time unmapped-target checking; simple constructor mapping is acceptable. Test new high-risk domain rules with Red → Green → Refactor and real PostgreSQL/Testcontainers for JDBC/RLS/concurrency. Foundation CI must include JUnit 5, Spring Modulith verification, Flyway integration tests, JaCoCo reports, and exact-SHA qualification. Do not conflate mapped DTOs with authorized domain commands or promise correctness based on coverage alone.

## Role-based User Story Book adoption

Develop [21 — User Story Book](21-user-story-book.md) in several passes: R0 actors and story seeds; commercial/booking; execution/POD; finance/tenancy/operations; later roles; approved scenarios → TDD tests. Keep `USB-*` story IDs stable and link `KX-*`, `LFC-*`, `ENG-*`. Do not add business modules or inflate R0 scope. Each implementation slice references reviewed user outcomes and adversarial/security acceptance.

## First access-policy architecture slice

Use [22 — Role Permission Scope Approval Matrix](22-role-permission-scope-approval-matrix.md) as R0 design candidate for Tenancy and Commercial. Implement only necessary built-in role templates, scoped permissions and a compact approval policy; no general-purpose IAM service or BPM engine. Begin with verified tenant owner bootstrap, admin delegation and scoped Commercial Quote issuance, exceptional approval and authorized customer acceptance. Demonstrate 24 documented draft `AUTH-*` outcomes through business review then TDD/real PostgreSQL Testcontainers, without claiming test execution at documentation stage.

## External Customer access and revised v2 Role Matrix

R0 must include the minimum authenticated external customer portal `EXC` and provider Tenant inbound RFQ window, customer-safe My Orders, quote acceptance by verified signatory, permission-filtered delivery monitoring/POD and minimal private completion-based review. Implement these as experiences/projections across existing domains, not a new module or writable duplicate Booking/Shipment table. Follow [24 — Access Governance v2](24-access-control-tdd-matrix-v2.md) and [23 — Customer Portal](23-external-customer-portal.md); historical [22 — v1 matrix](22-role-permission-scope-approval-matrix.md) is superseded. Separate scoped read guards from approval workflows. No new business module.

## Business Story Pass 2 — cross-role journey before new code

Use [25 — Business Scenario Book](25-business-scenario-book.md) to qualify role-based journeys and exceptions before implementation. 11 BSC scenarios cover customer/provider/carrier, booking, offline custody, tracking, partial POD, claims, finance, review, cancellation and access revocation; 38 proposed business acceptance outcomes. The [User Story Book](21-user-story-book.md) now has 58 stories (18 newly DISCOVERED). Implementation remains restricted to R0 vertical slices approved by real business owners, with independent `AUTH-*` policy review for proposed new commands; no new business modules or artificial workflow platform.

## Third-pass role/process walkthrough qualification

After 11 business narratives, [26 — Role/Process Simulation & Gap Audit](26-role-process-simulation-and-gap-audit.md) adds 42 desk simulations across all 22 role personas, including cross-tenant EXC, own tenant shipper, carrier, driver, receiver, Finance, Warehouse/Marketplace/ML (later) and two strategic exceptions: Sales-assisted RFQ and live transport during SaaS suspension. The JSON matrix is [here](contracts/role-process-simulation.v1.json). There are 33 gap hypotheses, not 33 new modules. Keep 17 module boundaries and 67 unchanged Access Governance v2.1 policies. Only approved R0 commands get authorization design/test code; R1/R2 personas stay deferred.

## R0 fourth-pass proposed policy and test qualification

Use [27 — 12 Blocker Decisions](27-r0-blocker-policy-decisions.md), [28 — TDD Acceptance Bank](28-r0-tdd-acceptance-bank.md), and [29 — Business Stakeholder Workshops](29-r0-business-acceptance-workshop-kit.md) to freeze business/legal permission and lifecycle contracts **before** code. Full planned catalog: 60 blocker tests + 14 R0 safety tests + 10 E2E cases = 84 planned, **zero executed**. No new business module, IAM service, generic BPM or Kafka is required. Sequence: signoff of relevant `BR-*` → TDD JUnit domain guard → real PG RLS/transaction races → Modulith contract/Outbox → customer/carrier E2E → exact-SHA CI. Missing approval/supplier/EDS/cash proof must never be inferred.

## Negative/failure acceptance prior to R0 code qualification

[30 — Negative and Failure Bank](30-negative-and-failure-scenario-bank.md) supplements the [84-case original TDD Bank](28-r0-tdd-acceptance-bank.md) with 48 fault-focused assertions across identity, CustomerAccount, Quote, Carrier, Capacity/Booking, Compliance, Custody, POD/Documents, Finance, SaaS, Jobs and disputes. Combined **132 designed test cases** plus eight cross-domain MIX fault sequences (uncounted). Prove state correctness, data absence/preservation, Outbox/Inbox event control and truthful UI status, not simply HTTP 403. All are planned, none executed; 17 business modules and 67 draft access policies remain unchanged.

## Error-handler bootstrap as first platform code slice

[31 — Unified RFC 9457 Error Standard](31-unified-error-handling-standard.md) provides shared machine codes and the first real [backend implementation skeleton](../backend/README.md): one Spring MVC/Security/servlet error contract, safe 400/401/403/404/409/422/500 responses, request IDs and contract tests. The first [Maven CI](../.github/workflows/backend-error-contract.yml) run on commit `0117f8dc` passed 13 error-only tests, with later edits requiring requalification on exact SHA. The scaffold defaults to `denyAll`; do **not** mistake it for Tenancy or drop this security boundary for convenience. No additional business module is created; full Spring Modulith module baseline and PostgreSQL RLS are the next engineering slices.

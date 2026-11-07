# 14 — Modular Delivery Blueprint: реализация R0a и дальнейшее расширение

**Версия:** 1.0 · **Дата:** 07.11.2026 · **Статус:** PROPOSED implementation plan.  
**Родитель:** [13 — Architecture Options](13-modular-architecture-options-v1.md).  
**Машинный каталог:** [contracts/module-boundaries.v1.json](contracts/module-boundaries.v1.json).  
**Текущий репозиторий:** в проверенной проектной ветке только документация; это план, а не работающий код.

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

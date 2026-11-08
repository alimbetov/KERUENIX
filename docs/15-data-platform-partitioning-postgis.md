# 15 — Архитектура хранения: Read Models, Partition Lifecycle и PostGIS

**Версия ТЗ:** 1.0 · **Дата:** 2026-11-07 · **Статус:** PROPOSED / awaiting architecture approval.  
**Источник:** [Модульная архитектура](13-modular-architecture-options-v1.md), [План реализации](14-modular-delivery-blueprint.md), [ТЗ по 16 модулям](16-module-storage-gis-addendum.md).  
**Сфера:** Multi-Tenant Cloud / Dedicated / On-Prem; один Spring Boot Modular Monolith и один физический PostgreSQL на инсталляцию. Документ не свидетельствует о созданных схемах/миграциях/тестах.

## 1. Цель, архитектурное решение

Разделить **владение записью**, **специализированное чтение** и **физическое масштабирование таблиц**:

1. **Write model / system of record** — модуль владеет агрегатом, бизнес-инвариантами, таблицами и миграциями; чужой JPA Repository, SQL UPDATE/INSERT и прямой доступ к private-схеме запрещены.
2. **Read model** — владельцем projection table может быть читающий модуль, который получает immutable snapshot/версионированные события от write-owner. Можно синхронно собирать лёгкий DTO через exported API; отдельная таблица создаётся **только при измеренной пользе** для фильтров/latency/другого permission scope.
3. **Physical partitioning** — физический способ хранения **внутри таблиц конкретного владельца**. Не включать partition by module или by tenant по умолчанию; отдельный SQL schema для модульного ownership не равно partition.
4. **PostGIS** — общее инфраструктурное расширение PostgreSQL; каждый business module владеет собственными геопространственными объектами. Не вводить «GIS-супермодуль», напрямую владеющий всеми позициями/маршрутами/складами.

**R0 decision:** включить PostGIS в провижининг и тесты; `fleet_current_position` как snapshot (если поставщик GPS выбран); `vehicle_position_event` как append-only история с RANGE-партициями по `observed_at`, когда в R0 включён реальный ingestion. Сложная автоматизация партиций может начинаться с idempotent maintenance job, `pg_partman` — только после подтверждения совместимости/доступности в каждом профиле.

**v1.7 product boundary:** `finance` contains no Invoice/Receivable/Payable/PaymentAllocation tables. External fiscal/payment data remains outside KERUENIX; older design examples are non-normative.

## 2. Модель данных и схематические примеры

### 2.1. Горячие данные / актуальное чтение

- `fleet.vehicle_current_position` (`tenant_id, vehicle_id, position_geog, observed_at, received_at, source_id, accuracy_m, event_id, quality_status, version`): **одна актуальная строка на Vehicle**, после проверки event sequence/occurred_at; геопозиция машины не равна местоположению груза после handover. Tenant + vehicle unique; B-tree для tenant/id и GiST для position.
- `tracking.customer_shipment_snapshot` (`tenant_id, shipment_id, customer_status, eta_window, event_watermark, observed_at, updated_at, allowed_visibility, projection_version`): отдельная **фильтрованная** read model. По умолчанию B-tree `(tenant_id, shipment_id)`, `(tenant_id, customer_status, updated_at)`; RLS + проверка grant до ответа.
- `execution.trip_route_version` содержит `geometry(LineString/MultiLineString,4326)` **при наличии фактической геометрии** и provenance/provider; `booking` не редактирует маршрут напрямую.
- `execution/warehouse` имеет подтверждённые геоточки отправки/доставки, терминалов и геозоны; indoor WMS rack/bin coordinates — **локальная система координат склада**, не фиктивный WGS84.

**Не партиционировать в R0:** `RFQ`, `QuoteVersion`, `Booking`, `CapacityReservation`, `HandlingUnit`, `DocumentPackage`, `customer_shipment_snapshot`, `vehicle_current_position`, `warehouse_current_stock`. Для них важнее PK/unique constraints, конкурентные блокировки, rollback, audit и быстрый доступ по tenant/resource.

### 2.2. История GPS / append-only

Концептуальная таблица:
- `fleet.vehicle_position_event(tenant_id, vehicle_id, source_id, external_event_id, event_id, observed_at, received_at, position geometry(Point,4326), speed, heading, accuracy, raw_payload_ref, ingestion_status)`.
- Рекомендуемое **первичное разбиение:** `RANGE(observed_at)`, UTC месяцы для низкой/средней нагрузки, дни/недели **только по измерению** p95/объёма/индексов. Использовать half-open интервалы. На пилоте вариант без partition допустим за feature flag, если объём мал, но contract, миграционный путь и тесты должны существовать.
- Основные запросы: `WHERE tenant_id=? AND vehicle_id=? AND observed_at>=? AND observed_at<? ORDER BY observed_at DESC LIMIT ?`. Query filter по ключу партиции нужен для pruning; пренебрегать этим нельзя.
- Индекс на каждой partition: B-tree `(tenant_id, vehicle_id, observed_at DESC)`; GiST по геометрии на исторических партициях **только** если есть доказанные пространственные аналитические запросы на историю, иначе индексный overhead не оправдан.
- Подтверждённый current position обновляется отдельно idempotent projector с контрольными `observed_at/event_seq/source_quality`; старое событие не переписывает новое.
- Для dedup across partitions `(tenant_id, source_id, external_event_id)` использовать **отдельный непартиционированный ingest registry с unique constraint** и transactional ownership, или иной доказанный глобальный механизм; не рассчитывать на `UNIQUE(event_id)` в RANGE-таблице, потому что PostgreSQL требует включить partition key в unique/PK partitioned parent. Регистру нужны TTL/retention и защита от повторов после purge; удалять dedup state раньше срока возможных повторов запрещено.
- Stable event UUID может храниться отдельно как identity без уникальности на partitioned parent; ссылки, требующие глобальной уникальности/FK, проектировать по composite key `(event_id, observed_at)` либо через identity/registry.

### 2.3. Кандидаты на партиционирование после замеров

| Данные | Владелец | Ключ/стратегия | Когда применять |
|---|---|---|---|
| Vehicle GPS event history | Fleet/Telemetry adapter | RANGE `observed_at` | R0 с реальным потоком или P1 при появлении нагрузки |
| Shipment milestone history | Execution | RANGE `occurred_at` (кандидат) | Когда растёт event volume / retention и надо реорганизовать хранение |
| Warehouse stock movement history | Warehouse | RANGE `occurred_at` (кандидат) | Только после проверки ledger/inventory invariants и queries |
| API/audit request log | Platform/Security | RANGE `recorded_at` (кандидат) | При подтверждённой ретенции и нуждах Compliance |
| Marketplace listing events | Marketplace | RANGE `created_at` (кандидат) | Позднее, при высокой частоте событий; **не активные объявления** |
| Tracking projection/event outbox | Tracking/Platform | Не партиционировать автоматически | Сначала DDL/indexes, bounded outbox, TTL/archival после ownership review |
| CommercialCostReport and capacity reservation | Finance/Fleet | **НЕ ПО УМОЛЧАНИЮ** | Лишь отдельный доказанный дизайн без потери глобальных инвариантов; AR/AP/Payments вне продукта |

**Запрет:** создавать отдельную партицию на каждого tenant или на каждый Java-модуль. Это приводит к росту числа partitions без преимуществ для запроса, усложняет migrations, backup/restore и cross-tenant policy. Физическое выделение Dedicated tenant — deployment choice, не таблица-партиция.

## 3. Автоматический Partition Lifecycle Manager

Приложение не должно создавать DDL на каждый GPS INSERT. Создание/удаление партиций — **привилегированная эксплуатационная операция**, отделённая от обычного app-role.

Предлагаемые состояния: `PLANNED → CREATED → VALIDATED → ACTIVE → RETENTION_ELIGIBLE → ARCHIVED/DETACHED → DROPPED`. Каждое действие — job ledger (timestamp, schema/table/partition, bounds, checksum/config version, operator, outcome). Схема:
1. Периодический single-writer maintenance (advisory lock) проверяет текущий UTC time и будущие окна.
2. `premake` будущих партиций (пилотный кандидат: текущая + 2 будущих месячных); DDL idempotent; все индексы, grants, RLS проверяются перед ACTIVE.
3. На запись outside available partition: **не терять событие**. Retry/dead-letter/quarantine + alert, backfill после появления partition; нельзя silent drop/подмену observed_at.
4. Отставшие сообщения со старым observed_at принимаются в ещё сохранённые партиции либо через контролируемую процедуру восстановления; TTL dedup обязателен.
5. Retention и archive: только после политики бизнеса/права, legal hold, backup verification и reconciliation. **Не detach/drop всю partition, если у tenants разные сроки хранения или действует legal hold внутри неё**. В этом случае selective deletion/архив с соответствующим аудитом или отдельный retention design.
6. Не удалять partition, содержащую финансовые/юридические свидетельства, пока retention и ссылки на evidence не подтверждены.
7. Метрики: `partition_premake_success`, `partition_missing_count`, `partition_count`, `partition_bytes`, `partition_late_event_count`, `partition_retention_backlog`, planner p95, locks/waits, ingest lag, dead letters.
8. Режимы: built-in declarative partitioning + `pg_partman` BGW **если установлен и разрешён** в SAAS/DEDICATED/ON_PREM; иначе privileged Kubernetes CronJob/systemd scheduler/PG scheduler через явные migrations. App API не должен требовать суперпользователя.

Не обещать «бесконечно автоматическую» ротацию без мониторинга, привилегий, retention owner и restore tests.

## 4. PostGIS: канонические типы и GIS API

### 4.1. Договор координат

- Canonical external coordinate reference: **WGS84 / SRID 4326**; во внешнем JSON/GeoJSON указывать longitude, latitude, а в UI подписывать широту/долготу. SQL `ST_SetSRID(ST_MakePoint(lon,lat),4326)`, `lon ∈ [-180,180]`, `lat ∈ [-90,90]`; проверка NaN/Infinity, невозможных скачков и timestamp.
- `geometry(Point,4326)` для хранения точек и geofence topology; `geometry(Polygon/MultiPolygon,4326)` для геозон, с `ST_IsValid`/ограничениями размера/сложности и review опасных геометрий.
- Для радиуса в **метрах** использовать `geography(Point,4326)` или явный `::geography` с соответствующим GiST functional index. Не использовать `ST_DWithin(geometry4326, point, 5000)` как 5000 метров (там градусы).
- Для поиска расстояния `ST_DWithin` (index-aware); для геозоны `ST_Covers(zone.geom, position.geom)`, если граница считается включённой; фиксировать семантику пограничных точек. Для общего пересечения — `ST_Intersects`; указывать SRID обеих геометрий.
- `ST_Transform` только при известной исходной CRS: нельзя применять `ST_SetSRID` как физическое преобразование координат.
- GiST indexes для frequently queried geography/geometries, B-tree tenant/time filters, composite query design и `EXPLAIN (ANALYZE, BUFFERS)` на realistic fixture; не вводить лишние GiST на все события.

### 4.2. GIS-возможности и их границы

| Use case | Владелец write/read | Точная семантика |
|---|---|---|
| Current vehicle on map | Fleet telemetry / Tracking projection | Последнее подтверждённое положение машины, freshness, visibility grants |
| Nearby available vehicle | Fleet query API + capacity state | `ST_DWithin` на актуальной позиции; **не** доказательство дорожной доступности или свободного ресурса |
| Geofence entry/exit | Execution/Facility with Fleet observations | Debounce, GPS accuracy, idempotent candidate event; геозона не означает POD/custody |
| Route geometry/history | Execution/Route adapter | `LineString` only with provider version, quality, route plan version |
| Warehouse/terminal polygons | Warehouse/Facilities | Валидные зоны, ворота, температурная зона отдельно от координат |
| Rescue nearest eligible carrier | Recovery + Fleet + Compliance | PostGIS shortlisting, затем документы, time windows, cargo compatibility and safe handover |
| Backhaul / marketplace discovery | Marketplace read model | Coarse permitted regions, privacy; no global raw GPS exposure |
| Jurisdiction/road constraints | Compliance/Regulatory | Spatial overlay лишь candidate constraint; юридический source/date required |

**PostGIS не является грузовым роутером.** Прокладка дороги и проверка реальной проходимости/разрешений — RoutingProvider и утверждённые правила, независимо от «кратчайшего расстояния» по GIS.

## 5. Multi-Tenant Security, PII и аудит GIS

- Все геометрические таблицы и read models хранят `tenant_id`, RLS + ABAC/PartnerGrant; фильтровать **до** возвращения карты/агрегатов, counts, tiles, errors и nearest list. Spatial join может пересечь чужие строки: явная проверка обеих сторон и E2E adversarial tests.
- Скрывать точные GPS-координаты водителя/клиента по договору и роли; external listing выдаёт approx zone, не pin точного местоположения; driver PII отдельно.
- M2M ingest имеет подтверждённого provider/vehicle/tenant binding; не доверять `tenantId` в payload GPS-провайдера.
- Archive/purge/tenant deletion и signed evidence retention учитывают региональные обязанности хранения и legal hold.
- `SET LOCAL` tenant context с гарантированным transaction boundary, app role без bypass RLS; проверять access к child partitions напрямую, grants и owner privilege.

## 6. Требования к миграциям и производительности

**Migrations:** `CREATE EXTENSION IF NOT EXISTS postgis` выполняется отдельным provisioning/migration шагом под правами, совместимыми с Managed PG; schema creation, domains/checks, GiST/B-tree indexes, RLS policies, grants; smoke `SELECT postgis_version()` и GIS query. Не требовать суперпользовательских прав у app-role.

**Partition manager:** таблица/конфигурация `partition_policy`, per-table `strategy, interval, premake, retention, last_checked, owner`, and safe scheduler; manage migrations with Flyway. `pg_partman` optional dependency with fallback, not app bootstrap hard-requirement.

**Read projections:** `read_model_version, source_event_id, source_aggregate_version, watermark, last_rebuild_at`; update idempotently using owning module service; rebuild-from-events verifies counts/checksum; strong consistency needed for Reservation, Payment and stock -> **не опираться на eventually consistent read model для write guard**.

**Benchmarks:** synthetic scenarios at 10k/100k/1M events per relevant workload, rather than fixed unmeasured SLA; capture p50/p95/p99, query plans, partitions scanned, CPU, memory, index size, write amplification; compare partition ON/OFF and GiST ON/OFF with same fixtures. Establish target SLO only after pilot measurements.

## 7. Acceptance tests: DATA / GEO / RLS

| ID | Что проверяет | Gate |
|---|---|---|
| DATA-01 | Новая partition возникает до наступления следующего UTC окна, DDL idempotent | P0 GPS |
| DATA-02 | late/old/future GPS, отсутствующая partition: no silent loss, quarantine + alert, replay success | P0 GPS |
| DATA-03 | duplicate external GPS ID через разные partitions: ровно один бизнес-эффект | P0 GPS |
| DATA-04 | EXPLAIN показывает partition pruning при фильтре `observed_at` и `tenant_id` | P0/P1 |
| DATA-05 | Real PG rejects global `UNIQUE(event_id)` on date partition parent, correctness handled by dedup registry | P0 |
| DATA-06 | Retention with two tenants and legal hold never drops protected rows/partition | P0 |
| DATA-07 | RLS + child-partition direct SELECT + pool switch tenant A→B cannot expose A | P0 |
| DATA-08 | Streaming/out-of-order GPS events never regress current_position and TrackingSnapshot | P0 |
| DATA-09 | Read projection backfill/rebuild yields same allowed state, respects source watermark | P0 |
| DATA-10 | Slow projection cannot grant capacity booking/payment/stock authorization | P0 |
| DATA-11 | Backup/restore + schema migration+partition index works in SaaS and On-Prem profiles | P0/P1 |
| GEO-01 | Valid (lon,lat,4326) point, reject swapped/out-of-range/invalid CRS | P0 |
| GEO-02 | `ST_DWithin(geography)` radius in meters and spatial index plan valid | P0 |
| GEO-03 | Geofence polygon boundary counts as inside for `ST_Covers`; verify point-on-boundary | P0 |
| GEO-04 | Polygon invalid/self-intersection input rejected or safely normalized with versioned evidence | P0 |
| GEO-05 | Spatial search excludes other tenant even if their truck is closer | P0 |
| GEO-06 | GPS 2h old flagged STALE; no fake LIVE or derived cargo custody | P0 |
| GEO-07 | Nearby vehicle search never implies legal road ETA/cargo eligibility | P0 |
| GEO-08 | Warehouse/Rescue transfer rebinds cargo to new leg; old truck location not exposed as cargo | P1 |
| GEO-09 | Geometry of routes includes source/provider/version and does not override road compliance | P1 |
| GEO-10 | GeoJSON/coordinate input guards against excessively complex shapes and large radii | P0 |

**Любой P0 тест в этом списке — planned**, не исполнен. Реальная Testcontainers-реализация требует образа PostgreSQL с PostGIS и проверенного `pg_partman` профиля при использовании.

## 8. ADR / границы релизов

**ADR-036 (proposed):** separate write models and per-module read projections; no direct cross-module DB read; read projection never used for critical write authorization.  
**ADR-037 (proposed):** selective time-based partitioning only for high-volume event history; automatic maintenance under privileged job, no partition per module/tenant by default.  
**ADR-038 (proposed):** PostGIS 4326 with explicit geometry/geography, GiST and two-tenant geospatial authorization; no implied legal truck routing.

R0 must **support PostGIS** with e2e geographic smoke and proper data model. GPS partitioning becomes mandatory when live GPS is turned on; if R0 pilot has manual milestone tracking, the partitioned telemetry implementation may be developed in the telemetry slice, not a prerequisite for basic RFQ.

## 9. Первоисточники и подтверждённые технические ограничения

- PostgreSQL 18 [declarative partitioning, pruning, unique/PK constraints, operational drawbacks](https://www.postgresql.org/docs/current/ddl-partitioning.html).
- PostGIS [spatial indexes and index-aware functions](https://postgis.net/documentation/faq/spatial-indexes/).
- PostGIS [ST_DWithin](https://postgis.net/docs/ST_DWithin.html) (geography distance measured in meters).
- PostGIS [ST_Covers](https://postgis.net/docs/ST_Covers.html) (includes polygon boundary).
- pg_partman [extension/automatic maintenance](https://github.com/pgpartman/pg_partman) (availability needs per-deployment check).

**Статус:** DRAFT. No SQL/JPA/CI implementation is claimed.

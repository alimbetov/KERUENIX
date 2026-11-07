# 16 — Дополнение к ТЗ всех 16 модулей: Read Models, Partitioning & GIS

**Версия:** 1.0 · **Дата:** 2026-11-07 · **Статус:** PROPOSED / техническое уточнение существующих ТЗ.  
**Основное ТЗ:** [docs/15 — Storage and GIS](15-data-platform-partitioning-postgis.md).  
**Машинный контракт:** [storage-gis-module-contract.v1.json](contracts/storage-gis-module-contract.v1.json).  
**Модули и направления зависимостей:** [module-boundaries.v1.json](contracts/module-boundaries.v1.json).

## 1. Обязательное приложение к техническому заданию любого модуля

Каждому модулю в реализации нужен паспорт `ModuleDataProfile`:
- `module_id`, `business_owner`, `single_writer`, `tables_and_migrations`, `data_classification`, `access_model`;
- `write_invariants`, `transaction_boundaries`, `idempotency_keys`, `outbox/inbox`, `retention/legal_hold`;
- `read_model_names`, `source_events`, `projection_version/watermark`, `consistency_guarantee`, `rebuild/backfill`, `freshness_SLO`;
- `geo_types`, `SRID/units`, `spatial_index`, `index-aware query`, `privacy policy`, `mapping/road-routing source`;
- `partition_policy` only if justified by measured retention/access pattern, including `partition_key`, interval, indexes, dedup, premake, late events, purge/backups;
- тесты: unit model + module boundary + Testcontainers PG/PostGIS + RLS/ABAC + concurrency/replay + explain analyze + smoke on exact SHA.

**Важно:** write guard не может опираться на устаревший `ReadModel`. Critical bookings, stock, money, cargo legality проверяются по авторитетному агрегату/таблицам в правильной транзакции.

## 2. Матрица по каждому бизнес-модулю

| Модуль | Главная Read Model | Partition Strategy | PostGIS / Geo | Gate |
|---|---|---|---|---|
| `tenancy` (R0) | AccessDecision cache optional, never stale grant authorization | none | coordinates in partner grants cannot authorize raw GPS | TEN-GEO-01 cross-tenant spatial query denied; TEN-DATA-01 direct child partition RLS denied |
| `commercial` (R0) | RFQ pipeline and quote-search indexes; optional filtered quote list | none | pickup/delivery locations are typed references, not geo truth | COM-DATA-01 quote acceptance unaffected by stale projection |
| `fleet` (R0) | vehicle_current_position, available-capacity projection, spatial nearest shortlist | vehicle_position_event RANGE(observed_at) when GPS ingestion enabled | Point(4326)/geography near vehicle; GiST, stale quality | FLT-GEO-01 nearest eligible truck respects tenant and freshness; FLT-DATA-01 duplicate/late GPS |
| `cargo` (R0) | filtered product/handling-unit catalog, no replica of stock ledger | none | cargo stops reference approved facility positions; not owner of global route | CAR-DATA-01 no duplicate HU on replay; CAR-GEO-01 no fabricated storage GPS |
| `compliance` (R0) | versioned compatibility lookup, explainable assessment by rule set | none, assessment audit may be candidate after measurements | point/polygon overlap for legal/geofence candidate only; no auto-legal approval | CMP-GEO-01 missing jurisdiction rule => NEEDS_REVIEW; CMP-DATA-01 replay stable decision |
| `booking` (R0) | booking pipeline/due upcoming departures | none; exclusivity remains indexed DB constraint | customer pickup/delivery refs, never direct write to route geometry | BKG-DATA-01 stale read model cannot confirm; BKG-GEO-01 geo-near does not book |
| `execution` (R0) | trip board, shipment checkpoints/route metadata | shipment event history: later RANGE(occurred_at) candidate | route geometry(LineString,4326); geofence arrival is provisional | EXE-GEO-01 geofence != POD; EXE-DATA-01 event replay maintains cargo custody |
| `tracking` (R0) | shipment customer timeline/ETA/watermark; indexed by tenant and Shipment | snapshot NO; archive of notices only after measurements | geometry must be privacy-filtered and recent; no full truck history | TRK-GEO-01 old truck after transfer hidden; TRK-DATA-01 stale watermark labelled |
| `documents` (R0) | document checklist read model by shipment; filtered customer list | none | geo metadata optional, cannot prove signature or physical delivery | DOC-DATA-01 no document authority from uploaded GPS |
| `finance` (R0) | AR/AP aging and profitability projections, reconciliation snapshots | none for financial source of truth | geo only as reference for pricing/route cost, no own spatial truth | FIN-DATA-01 delayed read model cannot mark payment settled |
| `optimization` (R1) | candidate vehicle proximity and schedule eligibility projection | Job history candidate only after high volume | PostGIS preliminary shortlist, routing provider verified travel feasibility | OPT-GEO-01 straight-line near candidate rejected if road/legal unsafe |
| `recovery` (R1) | nearby partner/capacity with masked zone | none | ST_DWithin to shortlist, rescue availability/legal checks mandatory | RSC-GEO-01 replacement cargo custody verified before tracking switch |
| `warehouse` (R1) | occupancy, stock balance, dock availability/yard map | historical stock movements candidate, not active balance | valid Polygon(4326) yard/dock geofence; indoor aisle/rack local CRS | WMS-GEO-01 boundary logic; WMS-DATA-01 legal hold blocks pickup despite projection |
| `marketplace` (R2) | geo coarse heatmap, backhaul discovery and privacy-filtered feed | listing events candidate only, not active listing | coarse regions/precision by grants, avoid exact GPS of carrier | MKT-GEO-01 query doesn't disclose competitor raw location |
| `regulatory` (R2) | country/mode/route overlay and applicability cache | none, version retention by legal policy | spatial overlay only under approved legal source/version | REG-GEO-01 border crossing without confirmed rule not auto-allowed |
| `saas-control` (R1) | aggregated tenant-specific usage and operating costs | usage event history only if measured | geospatial usage quota without exposure of driver PII | SAS-DATA-01 quota flag never disables mandatory tenant security |

**Детали ownership каждого модуля** и точные тестовые IDs сохранены в [JSON-контракте](contracts/storage-gis-module-contract.v1.json). Каждый модуль должен включать и применять общее ТЗ `docs/15`, а не копировать свои partition scripts в другие модульные схемы.

## 3. Модель архитектурных контрактов

`ReadModelProjectionPort` — only updater of its owning projection; `GeoQueryPort` — context-specific typed read; `PartitionMaintenancePort` — privileged operational interface (не публичный бизнес API). Эти имена предварительные. Без необходимости не создавать отдельный deployable `gis-service` или `partition-service`.

Рекомендуемый функциональный pipeline:

```text
GPS Provider Event → validated ingest (tenant/source binding + dedup)
     ├── append-only Fleet vehicle_position_event (time partitions)
     └── idempotent Fleet current_position projector
                    ├── Fleet nearest vehicle query (PostGIS)
                    ├── Execution geofence arrival candidate (not POD)
                    └── Tracking customer-visibility projection (scoped)
```

Защита от cross-tenant leakage работает на каждом шаге. `Tracking` не получает бессрочное право видеть все автомобили, а `Execution` не переписывает `Fleet` telemetry при изменении маршрута.

## 4. Порядок исполнения изменений (проектный backlog)

| Slice | Реализация | Тест/доказательство | Blocking |
|---|---|---|---|
| GEO-P0 | PostgreSQL + PostGIS provision, versioned migration/health | `GEO-01…05` real PostgreSQL integration | Перед использованием геозон |
| DATA-P0 | Tenant RLS и schema ownership, два tenant GIS fixture | `DATA-07`, `GEO-05`, direct partition access and pool reset | До API с GPS |
| DATA-P1 | Fleet current_position + append-only GPS and global idempotency registry | `DATA-02,03,08` | Когда появляется реальный GPS |
| DATA-P2 | Declarative RANGE partitions + idempotent premake/late replay | `DATA-01…06` и recovery smoke | До масштабирования GPS |
| DATA-P3 | Tracking projection, event watermark, rebuild and document scope | `DATA-09,10`, `TRK-GEO-01` | До клиентского tracking |
| GEO-P1 | Fleet radius search, geofences, route geometry | `GEO-02,03,04,06,07`, EXPLAIN | До Nearby/Rescue |
| R1/R2 | Warehouse/Marketplace geo overlays и исторические partition sets по нагрузке | `GEO-08…10`, tenant/privacy and retention tests | По реальному потреблению |

Под `GEO-P0` и `DATA-P0` подразумеваются **этапы работы**, не полная геофункциональность R0. Параметры interval/premake/retention — настраиваемые и проходят ревью конкретного клиента/deployment.

## 5. Аудиторские риски и необходимые решения

| Риск | Последствие | Норматив проектирования |
|---|---|---|
| Unique key только по `event_id` в RANGE-партиции | Дубли across partitions | Отдельная global dedup table / корректный composite key |
| Too many tenant/day partitions | Планирование и RAM деградируют | Число partition по workload; не one-tenant-one-partition |
| Automatic DROP on retention | Потеря чужих held/legal данных | Per-tenant retention/legal hold-aware archive; evidence |
| Read model drives financial status | Двойная выплата/бронь | Critical guard только по source of truth |
| GIS geometry degrees mistaken for meters | Ошибочный подбор близких машин | `geography` для метров и `ST_DWithin` |
| Unscoped spatial join | Disclosure координат других tenants | RLS + ABAC + negative GIS tests |
| No GPS/old GPS | Fake realtime/ETA | Freshness + UNKNOWN, no fabricated position |
| GPS geofence used as delivered | Ложный POD | Custody/POD evidence separately |
| Missing PostGIS in On-Prem | Migration/startup failure | Preflight extension, version policy, local installation validation |

## 6. Qualification for per-module READY

`DESIGNED` если есть owner + write/read ownership, data migration, GIS semantics, tests and decision approvals.  
`IMPLEMENTED` только после кода/DDL и обновлённых API/contracts.  
`QUALIFIED` после real PG/PostGIS/RLS + module test, query-plan proof (где имеется partition/GiST), replay, backup/restore and exact-SHA CI.

**До появления исходного кода все 16 модулей имеют статус PROPOSED.** Настоящий acceptance требует реального теста в среде, а не анализа JSON.

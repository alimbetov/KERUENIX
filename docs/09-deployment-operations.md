# 09 — Deployment, Security & Operations

**Статус:** DRAFT · **Версия:** 0.2.

## Поддерживаемые варианты поставки

| Profile | Расположение данных | Оператор |
|---|---|---|
| `SAAS_POOLED` | Shared app/DB, tenant_id + RLS, scoped object storage | KERUENIX SaaS |
| `DEDICATED` | Клиентская БД/runtime, собственные secrets и объектное хранилище | KERUENIX/MSP |
| `ON_PREM` | Локальный runtime/БД/файлы, возможна отсутствие связи с cloud | Enterprise-клиент/подрядчик |

**Один domain-core и версии API**, отдельные runtime configuration/tenant provisioning. Dedicated-установка может содержать несколько legal entities/tenants по согласованной модели. Не удалять RLS и permission checks в ON_PREM просто потому, что физически одна компания.

## Config taxonomy

| Application config | Connection config | Secrets |
|---|---|---|
| service port, logging level, feature flags, quota, job concurrency | DB URL, Redis host, GPS/map gateway URLs, S3 endpoint, IAM issuer | DB password, S3 secret, API keys, JWT/signing keys |
| Не секретно | Часто чувствительно, контролировать распространение | Secret manager/env injection only |

Пример концептуальных имён: `KERUENIX_DEPLOYMENT_MODE`, `KERUENIX_TENANCY_STRATEGY`, `DATABASE_URL`, `OBJECT_STORAGE_ENDPOINT`, `OIDC_ISSUER_URI`. Это не готовый конфигурационный контракт; реальные имена фиксируются по коду. `.env.example` хранит только имена и безопасные заглушки.

## Tenant-aware reliability

- Transactional outbox/at-least-once + idempotency, дедуп webhook/сканирования/событий исполнения.
- Optimistic version + atomic resource availability для VehicleCapacity, WarehouseStock и финансируемых команд.
- Event and cache keys содержат tenant scope, проверенную membership и resource permission.
- Для RLS в pooled JDBC проверить корректную установку/сброс контекста в каждом transaction, включая ошибки, pooling и фоновые джобы.
- Секреты/ключи/сигнатуры отделены от метаданных; документальные ссылки имеют кратковременные права.
- Поддержка offline driver/WMS events через строго подтверждаемую сервером сверку, без ложного «принято» от локального терминала.

## Доступность и аварийное восстановление

Предварительные инженерные **кандидаты**, не действующий SLA:
- Core API availability: 99.9% monthly при определённых исключениях.
- Read API p95 ≤500ms на согласованном эталонном наборе; оптимизация выполняется асинхронно.
- DB RPO ≤15 минут, RTO ≤4 часа **только если сценарии восстановления фактически квалифицированы**.
- Stale GPS, неработающий ML/provider не блокируют безопасное ручное исполнение, но уменьшают уровень уверенности в ETA.
- Нужны PITR, объектные backups, проверка tenant-selective export/restore, audit retention.

## PostGIS & partition lifecycle operations

R0 migration preflight проверяет доступность `postgis` extension и права installation на SAAS_POOLED, DEDICATED, ON_PREM без использования суперпользовательских прав application runtime. `pg_partman` **опционален**: для каждого deployment проверить поддержку/версию и альтернативный privileged schedule (не DDL на каждый запрос). Контроль ошибок создания будущих partitions, late events и failure-mode recovery; сохранять job ledger, retries, alerts, per-tenant/legal-hold retention. Никакого автоматического DROP partitions без документированного owner approval.

Измерять `p95/p99` GIS query, число scanned partitions, maintenance lag, ingest backlog, index size, autovacuum/locks, RLS negative-test failures. Backup/restore проверяет parent + child partitions, spatial indexes, extension version и read projection rebuild. Прямой доступ к child tables и leaks connection-pool RLS тестировать на реальном PostgreSQL. Полные требования и тесты: [15 — Data Platform](15-data-platform-partitioning-postgis.md).

## CI/CD и приёмка эксплуатации

1. Check formatting, tests, SAST/dependency/secret scans and SBOM.
2. Integration Testcontainers PostgreSQL/PostGIS (RLS/security, migrations, transaction consistency).
3. Adapter contract tests для map/GPS/warehouse/ERP.
4. 2+ tenant E2E security suite, external share revocation, no leak via SSE/cache/files.
5. Controlled load/timeout, concurrent booking, invoice/stock replay.
6. Build pinned container images (AMD64/ARM64 только когда проверены), health/readiness, image SBOM/signature.
7. Deployment smoke на `SAAS_POOLED` и `ON_PREM` профилях с одинаковым функциональным контрактом.
8. Restore game-day, rollback migrations/feature flags, incident runbook.
9. Exact SHA qualification, владельцы и список известных ограничений.

## Security/privacy

Location and personal data require legal basis, retention schedule and least-privilege disclosure. Enterprise support access is temporary, attributable and approved. Для Client Tracking не делать публичный GPS URL из SSCC. Tenant deletion and backups require documented contractual/retention policy.

## Open choices

OIDC vendor, DB routing strategy, object storage encryption/KMS, queue transport, secrets provider, logging stack, production support ownership, tenant billing, regional residency, upgrade policy and compatibility matrix for Java/Spring/Timefold.

**См.:** [System Architecture](02-system-architecture.md), [Security concept](../idea/08-security-reliability-and-sre.md), [Deployment models](../idea/13-deployment-models.md).

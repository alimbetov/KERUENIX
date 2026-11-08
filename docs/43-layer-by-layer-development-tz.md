# 43 — KERUENIX: ТЗ разработки по архитектурным слоям (R0 → R1 → R2)

**Дата:** 2026-11-08 · **Версия ТЗ:** 1.0 · **Статус:** `DESIGN / EXECUTION READY WHERE NOT SIGNOFF-BLOCKED`.

**Источники истины:** [Roadmap v1.7](contracts/tdd-development-roadmap.v1.json) задаёт 26 PR и зависимости; [Module Boundaries](contracts/module-boundaries.v1.json) — 17 владельцев; [Acceptance Manifest](contracts/pr-acceptance-manifest.v1.json) — фактическую квалификацию; [Decision Ledger](contracts/r0-decision-readiness.v1.json) — BR/DEC; [машинный контракт этого ТЗ](contracts/layered-development-plan.v1.json) — разбиение по слоям. При конфликте выигрывают продуктовая граница NO PAYMENTS, реально принятые BR/ADR, Module Boundaries и Roadmap; этот документ не меняет права пользователей.

## 1. Обязательная модель поставки

- **R0:** один Java 21 / Spring Boot 4.1.2 / Spring Modulith 2.1.2 modular monolith, 10 запланированных доменных модулей R0 (полный прикладной код ещё не реализован), Postgres/PostGIS и **Liquibase-only**. Остальные 7 модулей — R1/R2/design, не ранний rollout.
- **Внутри каждого PR:** требование → доменный инвариант → команда/транзакция → Liquibase/Postgres → REST/DTO → UI (если требуется) → отрицательные тесты → exact-SHA CI → qualification evidence.
- **Схемы:** один canonical writer на ресурс; ни один модуль не пишет чужую таблицу, public API другого модуля или versioned events — единственные договорные точки зависимости.
- **Default DENY:** пока JWT, права CustomerAccount и внешние юридические документы не подтверждены — не открывать submit/accept/confirmed/pickup/POD/review.
- **Вне R0:** любые Payment/PAID/SETTLED, банковские callbacks, AR/AP и собственные официальные бухгалтерские/налоговые документы. Finance — commercial costing и внешняя opaque-ссылка.
- **Никаких лишних сервисов:** Kafka, универсальный BPM, Kubernetes, отдельные workers и ML не обязательны без измеренной необходимости. R1/R2 не могут блокировать первую работающую перевозку.

## 2. Протокол разработки каждого PR

**Definition of Ready:** (1) actor/action/resource/tenant/customer scope; (2) владелец агрегата и канонических данных; (3) положительные и отрицательные AC; (4) BR/DEC/ADR status и fail-closed поведение; (5) transaction/idempotency/version; (6) границы SQL/API/UI; (7) выбранные тесты и критерии сбоя.

**Red → Green → Refactor:** сначала failing unit/property/API/security/real-PG тест применимого инварианта; затем минимальная реализация; затем рефакторинг без ослабления gates. Mock не считается доказательством RLS/concurrency, standalone SQL не доказывает полноценную авторизацию.

**Definition of Done:** traceability + tests + миграции + signed approvals для применимых переходов + real integration + UI E2E (если required) + exact SHA + reviewer + release artifacts. `IMPLEMENTED` ≠ `QUALIFIED`; 0/20 BR/DEC принято на дату документа, реестр ожиданий нельзя автоматически переводить в APPROVED.

**Дисциплина Liquibase:** каждый новый changeSet с устойчивым `id/author/path`, неизменяемый после применения, checksum validation; отдельный миграционный процесс с DDL credentials. Runtime role никогда не мигрирует DB. Для legacy Flyway обязателен отдельный approved baseline/cutover, нельзя без проверки создавать второй migration ledger поверх готовой схемы.

## 3. Архитектура зависимостей

```text
Customer/Operations/Carrier/Driver/Admin UI
             ↓
API (REST, DTO, validation, auth, RFC 9457)
             ↓
Application (commands, queries, transaction boundary)
             ↓
Domain (aggregate, invariants, state machines)
             ↕
PostgreSQL/PostGIS (Liquibase + RLS + data owner)
             ↕
Outbox/Inbox — Durable Jobs — Domain Process Managers
             ↕
External ports (EDS, evidence storage, GPS, carrier, accounting ref)

Across all layers: scope/security, tests, tracing, CI, audit, recovery.
```

## 4. Подробное ТЗ по каждому слою

### L0 — ТЗ, анализ и управление контрактами

**Владелец:** architecture · **Релиз:** R0-R2 · **PR:** PR-00, PR-01, PR-02, PR-03C, PR-03, PR-04, PR-05, PR-06, PR-06S, PR-07, PR-08, PR-09, PR-10V, PR-10, PR-11, PR-12, PR-12C, PR-13, PR-14, PR-15, PR-16, PR-16R, PR-17, PR-18, PR-19, PR-20.

**Цель:** Описывать пользовательскую ценность, отрицательные сценарии и документированное право совершить действие до реализации.

**Результаты:**
- User Story → Business Scenario → BR/DEC/ADR → API/command owner → negative tests → UI states
- Реестр утверждения с доказательством полномочий подписанта
- Версионированный acceptance manifest для каждого PR

**Работы:**
1. Связать 26 PR с однозначными владельцами, фазами, тестами и состояниями
2. Зафиксировать 12 BR и 8 DEC как PENDING до реальных согласований
3. Провести W1-W5 и задокументировать юридические/коммерческие разрешения
4. Запретить автоматический перевод документационного CI в бизнес-approval

**Обязательные тесты:** Проверки уникальности и полного покрытия PR/BR/DEC; Mutation tests: удаление blocker, замена owner, нарушение DAG, ложный approval.
**Готовность:** Для каждого реализуемого PR есть actor, resource, source of truth, positive/negative AC; Отказные и необратимые переходы не открываются без принятого BR/DEC.
**Запрещено:** Выдавать техническое решение за юридическое согласование.

### L1 — Presentation, UX и offline workflow

**Владелец:** frontend · **Релиз:** R0 · **PR:** PR-02, PR-03C, PR-03, PR-04, PR-05, PR-06, PR-06S, PR-07, PR-10V, PR-10, PR-11, PR-12, PR-12C, PR-13, PR-14, PR-15, PR-16, PR-16R, PR-17, PR-18, PR-19, PR-20.

**Цель:** Ролевой React/TypeScript workspace и проверяемые UI-состояния, без самостоятельного утверждения бизнес-команд.

**Результаты:**
- Customer, Operations, Carrier/Driver, Administration роли/маршруты
- UI для RFQ, Quote, Booking, Trip, partial POD, Documents, CommercialCost
- Адаптивность и offline-очередь driver pickup/POD с подтверждённым replay

**Работы:**
1. Согласовать frontend baseline, state management, дизайн-систему и browser E2E
2. Построить UI сразу с соответствующим API PR, а не отдельным финальным этапом
3. Отображать PENDING, DENIED, EXPIRED, CONFLICT, stale и retry без ложного SUCCESS
4. В offline режиме хранить проверяемые локальные команды и не менять серверные custody-факты без ACK

**Обязательные тесты:** Component tests, browser E2E по ролям и доступу Customer-X/Y; Offline duplicate/out-of-order/revoke tests на реальном backend.
**Готовность:** Для каждого PR с uiAcceptance.required есть тестируемый пользовательский экран и E2E evidence; Без backend ACK интерфейс не заявляет завершение юридически значимого действия.
**Запрещено:** Предполагать что GPS, локальная отметка или upload URL равны POD/подписанному оригиналу.

### L2 — REST API, DTO, MapStruct и контракты ошибок

**Владелец:** backend-api · **Релиз:** R0 · **PR:** PR-01, PR-02, PR-03C, PR-03, PR-04, PR-05, PR-06, PR-06S, PR-07, PR-08, PR-09, PR-10V, PR-10, PR-11, PR-12, PR-12C, PR-13, PR-14, PR-15, PR-16, PR-16R, PR-17, PR-18, PR-19.

**Цель:** Детерминированные контрактные границы, не несущие доменной логики и утечек.

**Результаты:**
- Версионированный OpenAPI, request/response Java records
- Явные MapStruct mappings для чувствительных полей
- RFC 9457 machine codes, фильтрация, sorting, cursor pagination

**Работы:**
1. Создать command/query endpoints только после доменных AC
2. Установить лимиты input, sorting allowlist, paging и validation
3. Не маппить клиентский tenantId, actor, version, approval и margin непосредственно в aggregate
4. Совместимость контрактов N/N-1, ошибки 400/401/403/404/409/422/500

**Обязательные тесты:** MVC + API contract + negative authorization tests; Никаких побочных записей в БД/Outbox при отказе HTTP.
**Готовность:** DTO и OpenAPI согласованы с UI и Application слоями; Никакие entity и скрытые коммерческие поля не раскрываются наружу.
**Запрещено:** Размещать условия подтверждения Booking внутри Controller или mapper.

### L3 — Application, транзакционные use cases

**Владелец:** backend · **Релиз:** R0 · **PR:** PR-02, PR-03C, PR-03, PR-04, PR-05, PR-06, PR-06S, PR-07, PR-08, PR-09, PR-10V, PR-10, PR-11, PR-12, PR-12C, PR-13, PR-14, PR-15, PR-16, PR-16R, PR-17, PR-18, PR-19.

**Цель:** Оркестрировать команды, доступ, версии, идемпотентность, транзакции, audit и outbox.

**Результаты:**
- Типизированные commands, queries, handlers, ports
- Схемы транзакций и compensating transitions
- Контракты idempotencyKey, expectedVersion, correlationId

**Работы:**
1. Выполнить authorize(actor, action, resource, scope) до доменного перехода
2. Разрешить право из проверенного principal/grant, а не tenant header
3. Commit domain aggregate + audit + outbox атомарно
4. Повтор с тем же idempotencyKey и другим payload отвергать конфликтом

**Обязательные тесты:** Command property/unit suites + PostgreSQL concurrency; Crash before/after commit, rollback и idempotency replay.
**Готовность:** Повтор команды приводит ровно к одному логическому эффекту; Некорректный и неавторизованный запрос не изменяет данные/аудит событий состояния.
**Запрещено:** Использовать внешние HTTP вызовы в длинной транзакции.

### L4 — Domain, агрегаты и инварианты перевозки

**Владелец:** module-owners · **Релиз:** R0 · **PR:** PR-02, PR-03C, PR-03, PR-04, PR-05, PR-06, PR-07, PR-08, PR-09, PR-10V, PR-10, PR-11, PR-12, PR-12C, PR-13, PR-14, PR-15, PR-16, PR-16R, PR-17.

**Цель:** Хранить правила предметной области независимо от HTTP, SQL, React, провайдерских SDK.

**Результаты:**
- Канонические агрегаты и ownership 10 модулей R0
- Value Objects: Money, HandlingUnit, Weight, GeoPosition, TimeWindow, DocumentHash
- Typed state transitions с actor/guard/expectedVersion

**Работы:**
1. Развести Quote.ACCEPTED, Capacity.CONFIRMED, CarrierCommitment и Booking.CONFIRMED
2. Запретить двойную резервацию ресурса, потери единиц груза и ложный полный POD
3. Сохранять UNKNOWN compliance в HOLD без автоматического allow
4. Соблюдать правило no-payments: только CommercialCostReport и внешняя opaque-ссылка

**Обязательные тесты:** State machine transition tables, property invariants и отрицательные случаи; Несогласованная стоимость, stale version, 8/10 custody и safety UNKNOWN.
**Готовность:** Каждое правило выражено исполняемым тестом владельца агрегата; Нет второго canonical writer того же бизнес-факта.
**Запрещено:** Прятать бизнес-инварианты только в SQL, UI или event subscriber.

### L5 — Outbox, Inbox, durable jobs и process managers

**Владелец:** platform · **Релиз:** R0 · **PR:** PR-01, PR-04, PR-05, PR-06, PR-07, PR-10, PR-11, PR-12, PR-12C, PR-13, PR-14, PR-15, PR-16, PR-17, PR-18, PR-19.

**Цель:** Атомарные события, безопасный replay и долговечные межмодульные бизнес-процессы.

**Результаты:**
- PostgreSQL Outbox/Inbox с tenant-scoped claim/lease/fencing
- Typed publisher, subscriber, retries/dead-letter и heartbeats
- Booking/Capacity процесс с persisted state и компенсациями

**Работы:**
1. Закончить реальный dispatcher, не ограничиваясь SQL claim
2. Проверять fencing token и authority при выполнении, а не только при enqueue
3. Публиковать только committed события; consumer idempotent
4. Добавить метрики lag/poison/lease expiry и recovery процедуры

**Обязательные тесты:** Concurrent SKIP LOCKED, crash after effect before ACK, stale lease; Retry, revoked worker, poison event, process compensation.
**Готовность:** Нет потерянных committed событий и двойного логического эффекта при replay; Долгоживущий Booking-процесс восстанавливается после рестарта.
**Запрещено:** Считать at-least-once равным exactly-once transport; Redis — единственный authoritative job store.

### L6 — PostgreSQL, Liquibase, RLS, PostGIS и read models

**Владелец:** data-platform · **Релиз:** R0-R1 · **PR:** PR-01, PR-02, PR-03C, PR-03, PR-04, PR-05, PR-06, PR-06S, PR-07, PR-08, PR-09, PR-10V, PR-10, PR-11, PR-12, PR-12C, PR-13, PR-14, PR-15, PR-16, PR-16R, PR-17, PR-18, PR-19, PR-20.

**Цель:** Версионированная схема и строгое владение данными, географическая корректность и восстановление.

**Результаты:**
- Liquibase master YAML + immutable formatted-SQL changeSets по owner
- Schema/data grants: migration/admin separate from application and worker
- PostGIS SRID4326/geography meter semantics, domain read projections
- Partition lifecycle только для обоснованных высокочастотных данных

**Работы:**
1. Поддерживать empty DB, upgrade N-1→N, checksum и повторное применение без побочных эффектов
2. Доказать RLS для Tenant-A/B и Customer-X/Y, transaction-local scope и pool reuse
3. Изолировать migrations от runtime credentials, no superuser/BYPASSRLS app
4. Проверять indexes, EXPLAIN, read model freshness, replay/backfill
5. Для GPS истории измерить партиционирование и обеспечить late-event/retention/legal hold

**Обязательные тесты:** Real PostgreSQL/PostGIS+Liquibase, RLS negative, constraint/concurrency; Upgrade/restore, duplicate UUID across tenants, geographic units, slow queries.
**Готовность:** Переход N-1→N доказан на данных, backup/restore воспроизведён; Нет cross-tenant leak, публичных DDL прав или разрыва domain/outbox атомарности.
**Запрещено:** Повторно менять применённый Liquibase changeSet; автоматически базировать Flyway-управляемую БД.

### L7 — Внешние интеграции, ЭЦП и доказательства

**Владелец:** integrations · **Релиз:** R0 · **PR:** PR-06S, PR-11, PR-13, PR-14, PR-15, PR-16, PR-17, PR-19.

**Цель:** Изолировать внешние провайдеры через порты и верифицировать юридические доказательства.

**Результаты:**
- NCA/NCALayer signing port с server-side certificate/authority validation
- Object storage verified original receipt, checksums, retention/legal hold
- GPS normalized ingestion, carrier exchange, external accounting reference

**Работы:**
1. Для каждого провайдера задать timeout/retry/idempotency и typed error states
2. Никогда не принимать URL как доказательство оригинала POD
3. Сохранять точные байты, хеш, юридический контекст и полномочия подписанта
4. Допускать ЭЦП юридически значимых документов только после signoff для профиля

**Обязательные тесты:** SIG-01..18, wrong signer/wrong bytes/replay/expired/revoked cert; Missing object, duplicate callback, stale GPS, timeout and compromised URL.
**Готовность:** Реальный integration smoke принят отдельно от mock; Юридически значимый эффект требует проверенного оригинала и утверждённого правила.
**Запрещено:** Считать подписанный файл фактом оплаты; допускать неопределённые carrier commitments.

### L8 — Identity, RBAC/ABAC и безопасность нескольких компаний

**Владелец:** security-tenancy · **Релиз:** R0 · **PR:** PR-01, PR-02, PR-03C, PR-03, PR-04, PR-05, PR-06, PR-06S, PR-07, PR-08, PR-09, PR-10V, PR-10, PR-11, PR-12, PR-12C, PR-13, PR-14, PR-15, PR-16, PR-16R, PR-17, PR-18, PR-19, PR-20.

**Цель:** Не допустить доступа к чужой организации, CustomerAccount, документу, рейсу или цене.

**Результаты:**
- JWT issuer/audience/signature/expiry trust binding
- Tenant/LegalEntity/Membership/PartnerGrant/CustomerAccount authorization
- Transaction-scoped RLS, revocation-aware access, SoD/worker identity

**Работы:**
1. Запретить доверие к tenantId из body/header без проверки
2. Разрешать ресурс с учётом provider+customer account и разных ролей одного человека
3. Ревалидировать grants после revoke и в фоне, не полагаться на warm cache
4. Негативно проверить UUID enumeration, COUNT/OFFSET leak, signed URL и cross-tenant Outbox

**Обязательные тесты:** AUTH-X, two-tenant two-customer HTTP→DB, pooled connection; Revocation, self-approval denial, signed URL after revoke.
**Готовность:** Нет cross-tenant/customer leakage на HTTP, DB, event, read model и UI; DenyAll не снимается без доказанного end-to-end права.
**Запрещено:** Фиктивный principal из непроверенного JWT claim; broad worker superuser role.

### L9 — TDD, CI/CD, DevOps, наблюдаемость и пилот

**Владелец:** quality-release · **Релиз:** R0-R2 · **PR:** PR-00, PR-01, PR-02, PR-03C, PR-03, PR-04, PR-05, PR-06, PR-06S, PR-07, PR-08, PR-09, PR-10V, PR-10, PR-11, PR-12, PR-12C, PR-13, PR-14, PR-15, PR-16, PR-16R, PR-17, PR-18, PR-19, PR-20.

**Цель:** Каждый PR имеет проверяемые gate и доказательства именно по его SHA, с безопасным выпуском.

**Результаты:**
- JUnit/AssertJ + Modulith + Testcontainers/PG + API/UI E2E
- CI exact SHA, SBOM, build digest, container, secrets separation
- Metrics/traces/logs, restore drill и Pilot UAT signed evidence

**Работы:**
1. Не мерджить бизнес-поведение без required P0/negative tests
2. Мерить p95/p99, Outbox lag, DB locks, partition maintenance и error budget
3. Выполнить реальный smoke staging + restore drill на релизном артефакте
4. Отделить R0 delivery от неподтверждённых RX-01..03/AI/Marketplace

**Обязательные тесты:** SAST/SCA, regression, recovery, backup restore, release digest; Full cross-role E2E: separate 8/10 partial versus verified 10/10 completed.
**Готовность:** PR acceptance manifest имеет реальный test report, SHA, reviewer и BR/DEC refs при необходимости; No-go при любом незакрытом P0 дефекте, отсутствии legal signoff или неуспешном restore.
**Запрещено:** Выдавать docs-only CI или mock-only успех за production-ready.

## 5. Поэтапный план с зависимостями

| Волна | PR-срезы | Выходной gate |
|---|---|---|
| W0 — Foundation | `PR-00`, `PR-01` | CI документации и частичная база не открывают бизнес-переходы; все FOUND-01..12 остаются отдельным gate |
| W1 — Identity & Accounts | `PR-02`, `PR-03C`, `PR-03` | Tenant + CustomerAccount grants и revoke проверены с двумя клиентами в одном provider |
| W2 — Safe drafts and catalogues | `PR-04`, `PR-08`, `PR-10V` | Draft RFQ, CargoProfile и Fleet registry доступны без binding Booking/Quote |
| W3 — RFQ commercial and signing foundation | `PR-05`, `PR-06`, `PR-06S`, `PR-09` | Submit, QuoteVersion, NCA/EDS platform и compliance проходят свои gated contracts |
| W4 — Contract and capacity commitment | `PR-07`, `PR-10`, `PR-11`, `PR-12`, `PR-12C` | Никакой BookingConfirmed без подписанного согласия, допустимого груза и capacity hold |
| W5 — Transport execution and proof | `PR-13`, `PR-14`, `PR-15`, `PR-16` | Pickup/POD доказательства, 8/10 partial и документы проверены в offline/replay сценариях |
| W6 — Economics and operational resilience | `PR-16R`, `PR-17`, `PR-18` | Private review только после verified completion; CommercialCost без банковских операций |
| W7 — Full E2E and release | `PR-19`, `PR-20` | 2 tenant E2E, approved BR/DEC, restore drill, exact release artifact, zero known P0 |

Объединение в одну волну означает последовательность PR внутри неё, а не разрешение игнорировать их DAG. Параллельно работать можно только на не зависящих от ещё не квалифицированных операциях; документальные и technical-safe deny-only срезы не активируют подпись или Booking.

## 6. Матрица всех 26 PR × архитектурные слои

| PR | Phase | Канонический владелец | Обязательные слои | UI | Блокирующие BR |
|---|---|---|---|---|---|
| PR-00 | RD-00 | architecture | L0, L9 | Нет | — |
| PR-01 | RD-01 | platform | L0, L2, L5, L6, L8, L9 | Нет | — |
| PR-02 | RD-02 | tenancy | L0, L1, L2, L3, L4, L6, L8, L9 | Да | — |
| PR-03C | RD-02 | commercial | L0, L1, L2, L3, L4, L6, L8, L9 | Да | BR-03 |
| PR-03 | RD-02 | tenancy | L0, L1, L2, L3, L4, L6, L8, L9 | Да | BR-03 |
| PR-04 | RD-03 | commercial | L0, L1, L2, L3, L4, L5, L6, L8, L9 | Да | — |
| PR-05 | RD-03 | commercial | L0, L1, L2, L3, L4, L5, L6, L8, L9 | Да | — |
| PR-06 | RD-04 | commercial | L0, L1, L2, L3, L4, L5, L6, L8, L9 | Да | BR-05 |
| PR-06S | RD-04 | platform | L0, L1, L2, L3, L6, L7, L8, L9 | Да | — |
| PR-07 | RD-04 | commercial | L0, L1, L2, L3, L4, L5, L6, L8, L9 | Да | BR-01, BR-02, BR-05 |
| PR-08 | RD-05 | cargo | L0, L2, L3, L4, L6, L8, L9 | Нет | — |
| PR-09 | RD-05 | compliance | L0, L2, L3, L4, L6, L8, L9 | Нет | BR-08 |
| PR-10V | RD-05 | fleet | L0, L1, L2, L3, L4, L6, L8, L9 | Да | — |
| PR-10 | RD-05 | fleet | L0, L1, L2, L3, L4, L5, L6, L8, L9 | Да | BR-07 |
| PR-11 | RD-06 | commercial | L0, L1, L2, L3, L4, L5, L6, L7, L8, L9 | Да | BR-06 |
| PR-12 | RD-06 | booking | L0, L1, L2, L3, L4, L5, L6, L8, L9 | Да | BR-06, BR-07 |
| PR-12C | RD-06 | booking | L0, L1, L2, L3, L4, L5, L6, L8, L9 | Да | BR-11 |
| PR-13 | RD-07 | execution | L0, L1, L2, L3, L4, L5, L6, L7, L8, L9 | Да | BR-09 |
| PR-14 | RD-07 | execution | L0, L1, L2, L3, L4, L5, L6, L7, L8, L9 | Да | BR-10 |
| PR-15 | RD-08 | tracking | L0, L1, L2, L3, L4, L5, L6, L7, L8, L9 | Да | — |
| PR-16 | RD-08 | documents | L0, L1, L2, L3, L4, L5, L6, L7, L8, L9 | Да | — |
| PR-16R | RD-08 | commercial | L0, L1, L2, L3, L4, L6, L8, L9 | Да | — |
| PR-17 | RD-09 | finance | L0, L1, L2, L3, L4, L5, L6, L7, L8, L9 | Да | — |
| PR-18 | RD-10 | platform | L0, L1, L2, L3, L5, L6, L8, L9 | Да | BR-04 |
| PR-19 | RD-11 | cross-functional | L0, L1, L2, L3, L5, L6, L7, L8, L9 | Да | — |
| PR-20 | RD-12 | release | L0, L1, L6, L8, L9 | Да | — |

У каждого PR есть минимум L0 (трассируемость) и L9 (evidence/CI), а в доменных срезах дополнительно L2/L3/L4/L6/L8. Если требует UI — L1 обязателен; если интеграция — L7. **Столбцы являются планом работ, не признаком их выполнения.**

## 7. Сквозные safety и release gates

| ID | Проверяемое требование | Как подтверждать |
|---|---|---|
| G01 | No business action without trusted identity and scope | JWT issuer/audience/signature + CustomerAccount ABAC + PostgreSQL RLS HTTP→DB |
| G02 | Correctness first under concurrency and replay | Domain transition + audit + Outbox atomic; capacity/exclusive locks; Inbox idempotence |
| G03 | Legal/signing truth | Real NCA signing/authority/revocation and approved applicable BR/legal evidence |
| G04 | Custody conservation | 10/10 and 8/10 separate branches; no GPS-derived POD; replay quarantine |
| G05 | Liquibase safe migration and recovery | Empty + V1→V2 + idempotent apply + N-1→N upgrade + backup/restore; forbid legacy Flyway auto-baseline |
| G06 | UI/contract integration | Required UI on actual backend + HTTP/contract and denied/expired/revoked states |
| G07 | Performance/operational readiness | Measured SLO + stage load + telemetry + restore drill + audit of maintenance |
| G08 | No payments in R0 | No payment route/table/bank webhook/AR/AP or PAID/SETTLED state |

### Reference E2E: одна реальная перевозка

Включает 2 независимых tenants и 2 CustomerAccounts в одном provider: RFQ Draft → provider Inbox → immutable Quote → EDS authority → customer accept → compliance → exclusive capacity/carrier → Booking → Pickup 10 HandlingUnits → POD **8/10 остаётся partial** → два остаточных HandlingUnits получают доказанный disposition → legal documents → commercial cost report без платежа. Отдельная ветка verified **10/10** допускает один private review; 8/10 — не допускает.

Fault injection на этапах commit, lease, broker ACK, offline replay, revoke grant, object-storage failure, cache staleness и backup restore. E2E требует фактического UI и HTTP→DB/Outbox evidence, не только unit mocks.

## 8. R1/R2: отложенные модули и критерий включения

| Модуль | Фаза | Правило запуска |
|---|---|---|
| intelligence | R0_DESIGN_R1_IMPLEMENT | После R0 pilot, отдельный owner/ADR/BR и измеренная ценность |
| optimization | R1 | После R0 pilot, отдельный owner/ADR/BR и измеренная ценность |
| recovery | R1 | После R0 pilot, отдельный owner/ADR/BR и измеренная ценность |
| warehouse | R1 | После R0 pilot, отдельный owner/ADR/BR и измеренная ценность |
| marketplace | R2 | После R0 pilot, отдельный owner/ADR/BR и измеренная ценность |
| regulatory | R2 | После R0 pilot, отдельный owner/ADR/BR и измеренная ценность |
| saas-control | R1 | После R0 pilot, отдельный owner/ADR/BR и измеренная ценность |

Не расширять MVP универсальным AI, marketplace, warehouse или банкингом; сначала green user journey и эксплуатационные измерения.

## 9. Приоритет следующей инженерной итерации

1. **PR-01:** закрыть FOUND-01..12 (Liquibase upgrade/replay/restore, реальные auth→RLS и Outbox dispatcher integration); не считать прошлый частичный CI полным.
2. **PR-02/03C/03:** trusted JWT, membership, CustomerAccount, grants/revoke и отрицательные Customer-X/Y тесты.
3. **PR-04:** первый сквозной UI/API/PostgreSQL RFQ DRAFT, без неутверждённого submit.
4. **PR-06S:** параллельный EDS signing PoC с real verifier, без разрешения юридически значимых переходов до BR/legal acceptance.

**No-go:** релиз или `QUALIFIED` запрещён при открытых обязательных бизнес-решениях, P0 leakage, duplicate booking, custody loss, отсутствующем restore, неверной миграции или неуспешном UI E2E.

# 05 — MVP Roadmap & Qualification Gates

**Продуктовое изменение:** [38 — EDS / No Payments](38-r0-eds-signing-no-payments.md), [39 — Technical + Business Review](39-r0-technical-business-review.md). **R0 не включает платежи, бухгалтерский реестр, ЭСФ и банковские API.** 11 исторических банковских TDD-кейсов RETIRED, текущие испытания `PAY-ABS-01..06` и `SIG-01..18`. Реальные бизнес-модули, NCA SDK и Testcontainers ещё не квалифицированы.

**Статус:** DRAFT v0.2. Это последовательность разработки и приёмки, а не обещание сроков.

**Модульный implementation blueprint:** [docs/14](14-modular-delivery-blueprint.md). Для R0 рекомендуется один Spring Boot business runtime со Spring Modulith, PostgreSQL/Flyway, отдельными логическими контекстами с verified API и CI architecture checks; не требуется 10 отдельный deployable services. Изоляцию GPS bulk/optimizer worker вводить по результатам нагрузки.

**Data/GIS qualification:** добавить [PostGIS + Read Models + GPS partition architecture](15-data-platform-partitioning-postgis.md) в foundation. Для `R0` достаточно PostGIS provisioning, корректного spatial smoke, RLS и ограниченного metadata/ETA projection. Автоматическое партиционирование GPS обязательно **с реальным потоком телеметрии**; если первый MVP работает на ручных этапах без GPS, отложить физические partitions до GPS ingestion slice, но сохранить контракт и тест-план. Не партиционировать все коммерческие таблицы.

## Audited R0 TDD Delivery Roadmap

[33 — TDD Roadmap v1.7](33-tdd-development-roadmap-v1.md) and [34 — Technical Audit](34-tdd-roadmap-technical-audit.md) define **13 R0 stage gates**, 26 independently testable PR outcomes and real RLS/Outbox/Modulith, cross-role API+UI and exact-SHA qualification. R0 events and retries begin at RD-01, **not** at late RD-10. Each irreversible operation is fail-closed until the applicable BR signoff. No stage is deemed complete from this planning document, and no migration, booking, custody or finance integration is qualified yet.

## Error-handling foundation qualification (handler CI passed; domain tests pending)

The platform has an initial [Java21/Spring Boot4.1.2 unified error-handler scaffold](../backend/README.md) and a [GitHub Actions Maven verification workflow](../.github/workflows/backend-error-contract.yml). [31 — RFC 9457 standard](31-unified-error-handling-standard.md) defines the shared `ProblemDetail` contract for REST, Spring Security `401/403`, and servlet `/error` fallback. **Important:** the code is an error-only bootstrap with deny-all business security; it is NOT an authenticated Tenancy implementation or a complete application. 15 handler contract tests and Java/JSON parity passed on commit `ac459923` (GitHub Actions #22); future changes need requalification on exact SHA. Before merging to production: run exact-SHA Maven CI and 401/403/error fallback contract tests; then prove PostgreSQL RLS/Booking/Finance negative effects in their owning modules.

## Clear R0 developer contract and product completeness

The implementation entry point is [35 — R0 Developer Handbook](35-r0-developer-handbook.md), with [DEC-R0-01..08](contracts/r0-delivery-contract.v1.json) and [36 — PR-00/01 TDD Start Pack](36-r0-tdd-start-pack.md). R0 includes independently qualified Fleet registry (`PR-10V`), customer cancellation REQUEST and safe review (`PR-12C`), and **private verified-service feedback** (`PR-16R`); public ratings, fraudulent automatic delivery and unverified settlement remain excluded. All three new PRs are design only, so a successful document check cannot qualify the customer journey.

## Product slice R0 — минимальная доказуемая перевозка

**Customer-facing access clarification:** Include a minimal authenticated **External Customer Portal** for customers without their own paid tenant (provider-scoped relationship), customer My RFQs/My Orders, separately authorized QuoteVersion accept, shipment timeline/POD, pre/post-delivery issue reporting and private verified-service review; also provider Tenant `Incoming RFQs` with guarded assignment/clarification. [23 — Portal](23-external-customer-portal.md), [24 — Access Matrix v2](24-access-control-tdd-matrix-v2.md). This is a frontend/API experience across existing 17 modules, not a new authoritative booking source. Reviews must not be public marketplace ratings in R0.


**Сначала только автомобильные перевозки по выбранному тестовому коридору Казахстана, типовые грузы с полностью описанным профилем**. Регулируемый опасный груз и международная декларация не входят в автоматический R0; отсутствие нормативных сведений должно блокировать соответствующую операцию.

В R0 реализуем:
1. Multi-tenant onboarding для двух компаний, роли/объектное разделение, scoped partner references.
2. RFQ с проверкой полноты, версионированная цена, приём заказа и подтверждение наличия транспорта.
3. Основной реестр Vehicle + Trailer/Body (масса, м³, размеры/вместимость, документы, доступность) и CargoProfile.
4. Order → Shipment → Trip → RoutePlanVersion, остановки и корректные события погрузки/доставки.
5. Один provider routing/geocoding или контролируемый симулятор с явным source; planned ETA и фактические timestamps не смешивать.
6. Customer shipment timeline, ETA with data freshness, статус ошибки, доступ к подтверждённому POD.
7. Базовая себестоимость/закупка/продажа, план/факт и отдельные финансово-документальные статусы.
8. Идентификаторы внутреннего HandlingUnit; внешние typed IDs без притворства GS1-регистрацией; базовые ограничения грузового соседства и legal hold.
9. Transactional outbox, idempotency, audit, Testcontainers+RLS, обоснованное резервирование ресурсов.
10. Контейнеризованный Cloud-пилот + повторяемый локальный standalone smoke для проверки того же доменного контракта.

**Упрощения допустимы:** ручная квалификация контрагента, ручной финансовый статус при наличии evidence, одна машина на первый Shipment, без публичного marketplace и без настоящего eCMR/KEDEN integration. Упрощение должно быть явно обозначено.

## Negative/failure readiness gate (design only)

[30 — Negative/Failure Scenario Bank](30-negative-and-failure-scenario-bank.md) supplements [28 — TDD Bank](28-r0-tdd-acceptance-bank.md): **84 + 48 = 132** planned cases (8 `MIX-*` compound sequences outside this count). No tests have yet run. First pilot must prove negative outcomes at **database state + Outbox/Inbox + UI projection**, not only deny HTTP requests; high-risk intersections include stale JWT/customer grants, capacity expiry/parallel holds, offline custody replay, 8/10 POD, signature revocation/authority and replay, PAY-ABS payment-function absence, SaaS continuity and supplier withdrawal. Business/legal approvals remain gatekeepers before confirming irreversible transitions.

## R0 Blocker and TDD acceptance gate (design only)

Before marking business logic `READY_FOR_IMPLEMENTATION`, review [27 — Twelve R0 Blockers](27-r0-blocker-policy-decisions.md) with real [29 — Stakeholder Workshop](29-r0-business-acceptance-workshop-kit.md). Every blocker has a technical fail-safe proposal, but **no real business/legal approval is recorded**. [28 — R0 TDD Bank](28-r0-tdd-acceptance-bank.md) supplies 84 designed, not executed tests: 60 blocker, 14 R0 safety, 10 cross-role. Any signature/payment/compliance ambiguity fails closed. Current repository state is documentation-only in this scope; no exact-SHA Java/PG/CI evidence is claimed. Deferral of R1/R2 features does not waive the 14 safety paths.

## Role-simulation safety review (draft)

Prior to R0 implementation, prioritize [26 — Role/Process Simulation & Gap Audit](26-role-process-simulation-and-gap-audit.md): 42 paper-simulated cases; 33 candidate gaps (including 12 blockers for the affected operations). R0 must NOT infer client acceptance from a phone-entered RFQ and must have an explicit safe policy for ongoing cargo/evidence when SaaS billing is suspended. Simulations are **not** CI/DB tests; sign-off and actual code acceptance remain pending. Do not pull deferred R1/R2 workflows into first pilot.

## Business Scenario Book Gate (draft)

Prior to R0 code and release qualification, select and review the critical vertical slice from [25 — Business Scenario Book](25-business-scenario-book.md): customer onboarding/RFQ → quote approval/accept → capacity hold/Booking → offline pickup → verified POD → document/finance evidence, with cancellation and authorization-negative coverage. Keep 18 additional stories in [User Story Book](21-user-story-book.md) as **DISCOVERED**, not new unconditional R0 scope. Missing policies require security review and approval before implementation. Later R1 warehouse/notifications/executive reporting must not block first reproducible transport.

## Commercial & Execution v1: обязательный Gate R0

Новый проектный стандарт [Lifecycle v1](10-commercial-execution-lifecycle-v1.md) разделяет 9 активных транспортно-документальных state machines (3 прежних финансовых автомата переведены в архив) и ресурсную/договорную/финансовую ответственность. В Release 0 должны быть реализованы основные happy path и безопасные error branches **RFQ → QuoteVersion → CarrierOffer/own capacity → Reservation → Booking → Trip → Shipment/POD → DocumentPackage → Invoice/AR/AP reconciliation**. Отдельные предложения подрядчика допускается заменить own-fleet сценарием, но при этом тест **CarrierOffer vs Booking** всё равно должен быть проверен на pilot fixture.

**Блокирующие проверки:** просроченная цена не принимается; нет подтверждённой машины — нет Booking.CONFIRMED; рейс не доказывает pickup; частичная доставка не закрывает всё; документы не отмечаются complete без проверки; платёжных механизмов и статусов PAID/SETTLED нет в KERUENIX; проверяется ЭЦП и документ; отмена после старта не удаляет custody. Дополнительная матрица: [11 — Lifecycle Acceptance](11-commercial-execution-acceptance-v1.md).

До sign-off реальными владельцами процессов это **проектная база тестов**, не утверждённое бизнес-ТЗ.

## Разграничение TMS и Freight Exchange

DELLA-подобная открытая биржа не входит в R0. Для R0 достаточно учитывать свободную вместимость собственных машин и заявки/предложения проверенного партнёра внутри существующего Commercial & Booking контуров. Stage 0 после базового E2E — доска внутренних возможностей догруза/backhaul; Stage 1 — закрытая сеть доверенных перевозчиков; Stage 2 — опциональная публичная биржа только после ликвидности и антифрода. **Нельзя допустить**, чтобы новый MarketplaceListing был источником истины вместо `RFQ/CarrierOffer/CapacityReservation/Booking`. См. [idea/27 — Freight Exchange](../idea/27-freight-exchange-load-board-and-backhaul.md).

## Что делать после R0

| Релиз | Содержание | Gate |
|---|---|---|
| R1 — Commercial/Exception | Расширенные переговоры, claims resolution, cancellation tariffs, сложные partial returns/split workflows, уведомления; **минимальный безопасный partial POD 8/10 обязателен уже в R0** | Full day-in-life E2E |
| R2 — Multi-Load & Rescue | Несколько заказов на машину, Timefold, возвратные грузы, внутренняя замена/проверенные партнёры | Feasibility + no custody-loss |
| R3 — Warehouse Hub | ASN, scan/SSCC, ledger, cross-docking, dock scheduling, charging | Stock balance + custody + tenant safety |
| R4 — Regulated Corridors | Правила ADR/ТН ВЭД/CMR/eCMR/eTIR по конкретной стране и виду, интеграция официальных статусов | Экспертное approval + юридический/операционный пилот |
| R5 — Scale / Intelligence | Enterprise packaging, широкая сеть партнеров, ML ETA/fuel, multi-mode | Load, restore, privacy, business KPI |

**Порядок R1–R4 может меняться по платящему пилоту**, но нельзя пропускать необходимые P0 контракты безопасности/доменной модели.

## Пилотный набор

- Tenant A: экспедитор с 8 собственными/привлечёнными транспортными ресурсами.
- Tenant B: грузовладелец; партнёр C и склад D (в пилоте могут иметь limited projections).
- 20 синтетических или согласованно обезличенных заказов; минимум 10 машин разных типов.
- Несколько продуктов/паллет, 1 отклонение веса, 1 задержка склада, 1 неисправность, 1 частичная доставка, 1 дубль GPS, 1 просроченный документ и 1 конфликт двойного резерва.
- Не выполнять регулируемую операцию, если утверждённый нормативный набор отсутствует.

## Qualification gates

| Gate | Что проверяется | Блокирующий критерий |
|---|---|---|
| G0 — Domain | Инварианты Order/Shipment/Trip, state transitions, финансы/документы | Неполное согласование business lifecycle |
| G1 — Security | 2+ tenant, partner grants, RLS, file, search, cache и event policy | Любая cross-tenant утечка |
| G2 — Data integrity | Replay, concurrent booking, cargo split/merge, partial POD, idempotency | Double booking, double-stock, потеря custody |
| G3 — Safety & compliance | Cargo/vehicle profile, route legality warnings, holds, class ambiguity | Автоматический ALLOW при UNKNOWN/запрете |
| G4 — End-to-end | RFQ → Quote → Booking → Pickup → GPS/ETA → POD → Cost/Finance | Невозможно воспроизвести процесс по audit |
| G5 — Deployment/SRE | Backup/restore, migrations, diagnostics, source loss, secrets | Не восстановить целостность и tenant isolation |
| G6 — Business | Пилот и KPI до/после, поддержка, стоимость карты/SMS/GPS | Не доказана польза или непредсказуемая эксплуатация |

Сценарии должны выполняться на точном SHA с логами; прохождение mock-интеграций **не заменяет** реальный provider smoke там, где он требуется для обещаний пользователям.

## Чего не делать до первого пилота

Не строить полноценный «AI логиста», автоматический customs broker, полноценную биржу перевозчиков, роботизированный склад и сложную микросервисную платформу одновременно. Не обучать модель до достоверных timestamped данных. Не выдавать маркетинговые показатели ETA/тонн/кубатуры за сертификационные.

## Выходные артефакты первого implementation PR

Реальные миграции/тестовые данные, порты и контракты, docker compose, runtime `.env.example` (без секретов), README локального запуска, unit/integration tests, tenant isolation suite, E2E сквозного заказа и CI job. Согласованная версия Java/Spring Boot/Timefold фиксируется после PoC.

**См.:** [Requirements](04-requirements-traceability.md), [Operations](09-deployment-operations.md), [Legacy roadmap](../idea/10-mvp-roadmap-and-acceptance.md).

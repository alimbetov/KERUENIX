# 05 — MVP Roadmap & Qualification Gates

**Статус:** DRAFT v0.2. Это последовательность разработки и приёмки, а не обещание сроков.

## Product slice R0 — минимальная доказуемая перевозка

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

## Commercial & Execution v1: обязательный Gate R0

Новый проектный стандарт [Lifecycle v1](10-commercial-execution-lifecycle-v1.md) разделяет 12 агрегатных state machines и ресурсную/договорную/финансовую ответственность. В Release 0 должны быть реализованы основные happy path и безопасные error branches **RFQ → QuoteVersion → CarrierOffer/own capacity → Reservation → Booking → Trip → Shipment/POD → DocumentPackage → Invoice/AR/AP reconciliation**. Отдельные предложения подрядчика допускается заменить own-fleet сценарием, но при этом тест **CarrierOffer vs Booking** всё равно должен быть проверен на pilot fixture.

**Блокирующие проверки:** просроченная цена не принимается; нет подтверждённой машины — нет Booking.CONFIRMED; рейс не доказывает pickup; частичная доставка не закрывает всё; документы не отмечаются complete без проверки; платёж не ставится paid без доказанного поступления; отмена после старта не удаляет custody. Дополнительная матрица: [11 — Lifecycle Acceptance](11-commercial-execution-acceptance-v1.md).

До sign-off реальными владельцами процессов это **проектная база тестов**, не утверждённое бизнес-ТЗ.

## Что делать после R0

| Релиз | Содержание | Gate |
|---|---|---|
| R1 — Commercial/Exception | Переговоры/доп.условия, claims, cancellation, частичные доставки, оповещения | Full day-in-life E2E |
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

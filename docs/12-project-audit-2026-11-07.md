# 12 — KERUENIX: системный, продуктовый и технический аудит

**Дата аудита:** 2026-11-07 · **Версия:** 0.1 · **Статус:** аналитическое заключение (не acceptance и не юридический аудит).  
**Аудируемая ветка:** `docs/idea-multitenant-foundation` @ `81c7b56178ded9ef705224b7c442a756a7607ae0`; base `main`.  
**Метод:** inspection GitHub tree and docs, candidate JSON state machines, consistency and architecture review, public market context (BNS and DELLA). Не проверялись build/CI, работа API, эксплуатация, реальная безопасность, нормативные наборы, клиентские интервью и прибыльность.

## Executive conclusion

**Стратегический потенциал высокий, реализационная готовность нулевая.** Repo branch содержит 45 обычных файлов — Markdown+JSON документация, **ни одного файла приложения, миграции БД, теста, контейнерной сборки или CI**. В `main` — только исходный `idea/README.md`. Draft PR #1 открыт, идеи и требования не объединены в main.

KERUENIX должен позиционироваться как **Logistics Operations OS для перевозчика/экспедитора**, где коммерческие обязательства связываются с исполняемым рейсом, custody, клиентским tracking и финансовым результатом. Публичная биржа — дальнейшее расширение, не стартовый продукт.

## 1. Scope и фактическая готовность

| Направление | Концептуальное состояние | Реализация/доказательства | Вывод |
|---|---|---|---|
| Позиционирование | Характеризуется сегментами и ценностью | Ни одного подтверждённого платящего пилота | Discovery |
| Multi-Tenant/Dedicated/On-Prem | Хорошее описание модели прав | Нет DB RLS/API/test/federation smoke | Design only |
| Commercial Lifecycle | 12 candidate state machines / 94 transitions | Нет исполняемых guard, API и процесса sign-off | Design only |
| Cargo/Vehicle safety | Есть профиль/классификации/правила | Нет approved regulatory dataset, тех. проверки | Design only |
| Route/ETA/Dispatch | Есть provider ports и time-dependent концепция | Нет provider benchmarks, GPS event ingestion, E2E | Design only |
| Client tracking | Shipment-centric/permission-filtered проекции | Нет runtime, event pipeline и UI | Design only |
| WMS/YMS | Stock ledger/dock/cross-dock проработаны | Нет схемы и concurrency tests | Out of R0 |
| Rescue/subcontract | Incident/custody/economics | Нет договорных approvals и e2e | Stage later |
| Finance | Plan/fact, sale vs buy, AR/AP | Нет источника истины, double-entry rules, matching | Critical discovery gap |
| Freight Exchange | DELLA benchmark/FTL/PTL/LTL/backhaul | Нет ликвидности, KYB, антифрода и marketplace code | Do not launch open first |
| International regulatory | GS1/HS/TNVED/UN/ADR/CMR/eTIR versioned docs | Нет validated live rule sets/official integrations | No regulatory promises |
| SRE/CI | Proposed observability, RPO/RTO, images | Нет restore/build/monitoring evidence | Not production-ready |

**Нельзя** интерпретировать разработанные test cases как прошедшие тесты, а `PROPOSED` ADR — как утверждённые решения.

## 2. Рыночная и бизнес-модель

- Стартовый клиент: **экспедитор/перевозчик с собственными + привлечёнными машинами, которому недоступна дорогая интегрированная IT-система**.
- Painkiller: меньше неверных обещаний клиенту, меньше простоя и потерянных документов, контроль маржи и платежных рисков, клиентский Shipment Tracking.
- Альтернатива: Excel + телефон/мессенджеры + GPS-провайдер + DELLA/ATI.SU + отдельная бухгалтерия. Конкурентное преимущество KERUENIX должно **измеряться**, а не декларироваться.
- Выход на рынок по этапам: один вертикальный TMS/Finance-lite/Tracking → приватная партнёрская сеть → безопасный догруз/backhaul → открытая биржа только при достаточной ликвидности.
- Продажа «одной ERP для всех» рискованна: у перевозчика, экспедитора, склада и грузовладельца разные buyer/user и SLA. Сегменты надо выделять в продуктовые пакеты, не создавать все интерфейсы R0.
- Потенциальная цена: subscription + usage limits (vehicles, users, GPS, SMS, route API), enterprise separate; нужна **unit economics**: `ARPU - variable provider cost - support cost - hosting cost - payment costs` и CAC, churn, cost-to-serve. Значения пока отсутствуют.
- Рыночные свидетельства: BNS Казахстана описывает рост услуг транспорта и складирования, но **не доказывает спрос на KERUENIX**. DELLA — существующая контактная биржа, где стороны договариваются напрямую, а не конкурентный заместитель всех функций TMS.

## 3. Сильные архитектурные решения — сохранить

1. **Shared modular core**, не стартовать с микросервисной сетки.
2. **Order ≠ Shipment ≠ Trip ≠ TransportLeg ≠ HandlingUnit**; позволяет перегрузку, частичную доставку и разную контрактную ответственность.
3. **Shipment-centric customer tracking**; GPS vehicle не является POD/custody.
4. **QuoteVersion ≠ CarrierOffer ≠ Reservation ≠ Booking**.
5. **CargoCompatibilityPort + VehicleCapabilityPort** как hard constraints; Timefold после feasibility, Tribuo позже для прогнозов.
6. **Tenant/LegalEntity/PartnerGrant** как отдельные измерения, а не «все пользователи одного Cargo имеют доступ».
7. **Versioned evidence**, outbox/inbox, idempotency, audit.
8. Внешние идентификаторы GS1/HS/TNVED/UN/ISO6346 как типизированные namespaces, внутренний UUID не выдаётся за GS1 SSCC.
9. **Warehouse stock ledger и legal hold** отдельно от состояния перевозки.
10. Сменные порты для GPS/routing/customs, регуляторные правила с датой и экспертным review.

## 4. Блокирующие и серьёзные gaps

### A-01 — нет implementation foundation (Critical, P0)

Нет Java/Spring Boot проекта, migration strategy, domain modules, API contracts, security tests, DevOps. **Action:** отдельная ветка `feat/foundation-r0` от согласованного baseline main, application skeleton, PostgreSQL/Flyway, Testcontainers, GitHub Actions quality/security, docker compose, runtime config and minimum runbook.

### A-02 — продуктовая сегментация и платящий клиент не подтверждены (High, P0)

`Product Charter` предполагает одновременно carrier, 3PL, warehouse, shipper, SaaS owner и marketplace. **Action:** 3–5 интервью с реальными компаниями разного размера, выбрать один paying persona, одно главное workflow, одну логистическую полосу и KPI/готовность платить. Интервью не заменять виртуальным экспертным советом.

### A-03 — канонические state machines не являются executable spec (Critical, P0)

JSON: 12 machines, 94 transitions; позитивно, что состояния отделены. Но `guard` — строка без формального языка/предиката, нет версии API/event schema, прав каждой команды, бизнес-владелец и доказательство не связаны программно; нет orchestrator rollback и contract tests. **Action:** утверждённые команды/guards/actor permissions, exception types, versioned events и тесты на переходы/отказы, прежде чем встраивать в persistence.

Конкретные edge cases:
- `BOOKING.CONFIRMED` после отказа перевозчика до выезда не имеет явного `REBOOKING/ON_HOLD` в state machine; текст говорит о `BookingException`, но transition/compensation contract не определён.
- `SHIPMENT.RETURNED` может включать доставленные ранее единицы: нужна derived per-unit disposition и отдельный customer status, иначе виден неверный итог.
- `CARRIER_OFFER.SELECTED` terminal — это лишь бизнес-выбор, но последующий отказ/withdraw партнёра моделируется только в другом aggregate; cross-aggregate consequence нужен в одной согласованной saga.
- `Order.operationalComplete` и `financiallyClosed` объявлены derived, но нет формально утверждённых предикатов/разрешённых случаев с открытым Claim.
- Invoice immutable и payable/receivable требуют отдельного `PaymentTransaction/Allocation/Adjustment` контракта с multi-currency precision, accrual/cash provenance.

### A-04 — Multi-Tenant security не квалифицирован (Critical, P0)

Партнёры должны иметь право на конкретный груз и необходимые поля, но ни source of truth policy, ни fallback/revocation для stream/cache/object storage не реализованы. **Action:** tenant auth from IdP + membership, ABAC/resource ownership, PostgreSQL RLS, negative test suite 2–4 tenant, signed docs with short TTL, audit grants, token revocation. Роль водителя и юридическое право распоряжаться машиной — **разные полномочия**.

### A-05 — Commercial/Finance модели недостаточно для реального операционного цикла (Critical, P0)

Не утверждены binding vs conditional quote, стоимость отмен, документы, credit limit, авансы, disputed charges, source of truth Invoice/AR/AP/Payment. **Action:** сначала выбрать ERP adapter or finance-lite ledger и сквозной денежный пример; запрещать `PAID` из ручной отметки без reference/evidence. Логика invoice/credit notes и налоговые правила страны должны проверяться финансистом.

### A-06 — физические ограничения требуют реальных источников (High, P0/P1)

Правила тоннажа/оси/прицепа/паллето-геометрии, товарного соседства, температура, опасные грузы не подтверждаются одним map API и названием типа кузова. **Action:** выбрать пилотные классы обычных грузов, 10 реальных профилей машин, 30 маршрутов, проверка базы ограничений, hard block для неутверждённых опасных/температурных сценариев.

### A-07 — R0 перегружен (High, P0)

Первая версия описывает Quote/Booking/Shipment/POD/Finance, Multi-Tenant, безопасность, Cloud+standalone, cargo/vehicle compliance, routing/ETA и более сложные трёхсторонние расчёты. В R0 **вынести**: сложный WMS/YMS, автономную биржу, eCMR/eTIR/KEDEN, ML, полноценную AR/AP ERP, сложное многогрузовое 3D/bin packing и расширенные Enterprise deployment workflows.

**Предлагаемый R0a:** 2 tenants; 1 domestic corridor; standard packaged cargo; 1 shipment = 1 assigned trip; own fleet + 1 trusted carrier fixture; RFQ/Quote/accepted/confirmed vehicle; tracked milestones + ETA provenance; POD; cost/revenue estimate, invoice/payment status with evidence; secure runtime + integration smoke. Единая кодовая база оставляет возможность dedicated/On-Prem, но промышленную поддержку обеих моделей нельзя обещать по одному локальному smoke.

### A-08 — Marketplace/DELLA cold start, антифрод и права (High, P1/P2)

Для public marketplace нужна ликвидность с двух сторон, проверенные объявления, KYB, антифрод, спор/модерация, платежные правила и юридическая роль площадки. Начать с внутренней `CapacityOpportunityBoard` и `TrustedPartnerListing`. Не строить сторонний Della scraper: API/условия требуют отдельного разрешения.

### A-09 — Compliance registry пока справочник ссылок (High, P1)

Правила HS/TN VED, ADR, СВХ и гос.маркировки требуют source/effective date, expert approval, test cases и права использования dataset. Не заявлять юридически достоверное разрешение из одного JSON-каталога. **Action:** real lane/cargo review, versioned data sources, `NEEDS_REVIEW` при неизвестном обязательном правиле.

### A-10 — Data contracts/SRE/качество отсутствуют в реализации (High, P0)

Измеряемые SLO/RPO/RTO предлагаются, но не подтверждены. **Action:** p95 load profile, restore drills, outbox replay, retry policies, observability, runbooks, SBOM, exact SHA gates. Не считать документальные acceptance 20/36 тестов успешно выполненными.

### A-11 — документационное противоречие (Low, P0 editorial)

`docs/07-decisions-and-risks.md` говорит «все ADR-001…ADR-027», а `idea/11-adr-and-open-questions.md` перечисляет уже **ADR-001…ADR-032**. Это навигационная и управленческая ошибка; исправить индекс до реализации.

## 5. Целевая модель поставки — recommended scope

### Product core / R0a

```text
Customer Portal / Expeditor Console / Driver light-view
                    ↓
 Identity + Tenant + Partner Scopes
                    ↓
  Commercial (RFQ, Quote, Booking, reservation)
                    ↓
  Shipment + Cargo + Trip + RoutePlan + Custody
                    ↓
  Tracking projection + Delivery/POD
                    ↓
  Finance-lite (sale/buy/cost, evidence-based invoice/AR)
                    ↓
  Outbox + Audit + Security + SRE
```

**Не делать бизнес-модуль «marketplace» source of truth:** Listing → Offer → existing CarrierOffer → Reservation → Booking. Сложные правила безопасности не должны зависеть от цены. Внимание к очередности: safe quote guard, safe allocation, safe pickup, reliable tracking, correct settlement.

### Минимальные приложения и среда

- Backend: Java 21 + Spring Boot (версии зафиксировать в PoC), bounded modules + ArchUnit/контрактные тесты.
- PostgreSQL/PostGIS + миграции + RLS; Redis optional for cache/rate limits, **не** источник истины.
- RustFS/S3 для POD/документов с scoped access; не обязательно подключать до первого сквозного smoke, но предусмотреть port.
- React/Next.js операторский UI + клиентский tracking; для водителя на первом пилоте допускается mobile web/PWA вместо большой Flutter app, если подтверждение приемки/POD можно проверить на реальном устройстве.
- Интеграции через ports/adapters: 1 maps provider и 1 GPS source (или явно помеченный simulator в R0a). Качество ETA/законность маршрутов проверяются позже на реальных данных.
- GitHub Actions + Testcontainers: exact-SHA quality/security/acceptance; optional public status dashboard после внедрения.

## 6. Порядок реализации и критерии выхода

| Приоритет | Slice | Выход/блокирующий тест |
|---|---|---|
| P0-0 | Business sign-off: buyer, quote legality, POD, financial owner, tenant grants | ADR decisions; владельцы и контрактные правила |
| P0-1 | Project scaffold + Identity + Tenant | App boots, 2 tenants with deny matrix, Flyway/CI green |
| P0-2 | RFQ → QuoteVersion → CarrierOffer → CapacityReservation → Booking | Acceptance expired quote, double hold, unauthorized partner |
| P0-3 | Vehicle/Cargo → Trip/Shipment → Pickup/Delivery | Custody facts, partial POD, unknown cargo hard block |
| P0-4 | Shipment tracking + ETA freshness + customer evidence | No leakage, stale GPS safe, 1 source/adapters |
| P0-5 | Finance-lite + audit/notifications + R0 E2E | Quote vs cost, invoice/payment separate, no double posting |
| P0-6 | Staging release/restore and pilot | 20 orders/10 vehicles, resilience and user KPI report |
| P1 | Partial loads, backhaul opportunities, Rescue internal | Segment capacity, contract rights, cost delta |
| P1/P2 | Trusted partner load board, WMS-lite, country-specific regulations | Adversarial tests + buyer demand |
| P2+ | Open marketplace, advanced WMS, complex customs, Tribuo ML | Liquidity, compliance, proven ROI |

**Рекомендация по веткам:** сначала принять/согласовать документационные ADR, затем ветка `feat/foundation-r0` под реализацию; не размещать production-код в `docs/idea-multitenant-foundation` и не считать Draft PR готовым к merge лишь потому, что документация большая.

## 7. Пилотный E2E — точная последовательность

1. `Tenant A` создаёт запрос `RFQ`; `Tenant B` как заказчик/грузовладелец принимает версионированную цену.
2. Менеджер выбирает собственную либо подтверждённую машину; физическая `CapacityReservation` создаётся эксклюзивно и только затем `Booking.CONFIRMED`.
3. Логист утверждает простой RoutePlan, проверяет Truck/Cargo physical legality and warehouse access.
4. Водитель подтверждает реальный pickup/состояние CargoUnit отдельно от `Trip.STARTED`.
5. Диспетчер видит last known GPS/time и ETA; клиент — privacy-filtered Shipment milestones. Устаревший GPS не обозначается как live.
6. Получатель принимает cargo (в тесте одна частичная поставка) с POD; документы проверяются отдельно.
7. Финансист видит customer sales amount, purchase cost, advances, documents and unpaid receivable; не считает оплаченной неоплаченную доставку.
8. В тесте second tenant пытается читать чужие цены, GPS и POD; все запросы блокируются.
9. Обрабатываются duplicate events/optimistic concurrency и provider timeout; E2E выполняется на exact SHA.
10. Итог: восстановление после отказа и auditable cost and delivery evidence; клиент может самостоятельно проверить Shipment.

## 8. Критерии бизнес-эффекта: измерить, не обещать

- Median/p90 время от RFQ до подтверждённой Booking.
- Доля доставок в обещанное окно + точность ETA с меткой свежести.
- Доля заказов с полным и своевременным POD.
- Валовая/вкладная маржа по подтверждённому заказу: expected vs actual, отдельно cash flow.
- Утилизация машин по маршрутам, empty-km, задержки у ворот.
- Количество звонков клиента «где груз» на 100 отправок.
- Отказ / отмены / просроченные предложения / претензии, качество документации.
- Tenant support cost, subscriptions/usage, variable maps/GPS/storage/SMS expenses, monthly gross margin of SaaS.
- Open marketplace (later): active qualified listings, match→booking conversion, stale-listings %, fraud and cancellation rate.

Никаких числовых ROI/SLA/MarketShare утверждений без pilot baseline.

## 9. Итоговое архитектурное заключение

**GO** на контролируемый Spring Boot R0 foundation после согласования коммерческих границ и первых бизнес-владельцев.  
**NO-GO** на промышленный релиз, гарантию опасных/международных грузов, автоматическую таможню, открытый marketplace, обучение AI и полноценную WMS до реальных контрактов/данных/испытаний.

**Самое выгодное изменение сейчас:** не добавлять новые крупные модули, а реализовать одну доказуемую перевозку — с двумя tenant, бронью, custody, клиентским трекингом и правильным денежным результатом. Это превратит архитектуру из набора перспективных документов в работающую основу логистической системы.

## Внешние источники (контекст, не сертификация)

- Бюро национальной статистики Казахстана, раздел транспорт/складирование, 2026: https://stat.gov.kz/ru/industries/business-statistics/stat-transport/
- Della Kazakhstan: https://della.kz/ru-KZ
- Della Kazakhstan terms: https://www.della.kz/terms/

**Следующие артефакты:** согласованные P0 ADR, issue backlog по `KX-LFC` и `KX-TEN`, минимальный executable Spring Boot foundation и квалифицированный R0 smoke.

## Addendum — Data Platform / Read Models / GIS design (07.11.2026)

После данного аудита подготовлено [ТЗ по PostGIS и партиционированию](15-data-platform-partitioning-postgis.md), [дополнение по 16 модулям](16-module-storage-gis-addendum.md) и [машинный контракт](contracts/storage-gis-module-contract.v1.json). **Это проектная mitigation**, а не исправление в коде: нет доказанных RLS/partition pruning/GiST/latency или restore tests. При первом implementation PR обязательны real PostGIS/Testcontainers tests и гарантии no stale critical write guards.

# 07 — Open Decisions, Risks and Next Actions

**Статус:** DISCOVERY · **Дата:** 07.11.2026. Все ADR-001…ADR-038 в `idea/11` остаются **PROPOSED**, если нет отдельного подписанного утверждения.

**Свежая оценка архитектурных и продуктовых рисков:** [Project Audit — 2026-11-07](12-project-audit-2026-11-07.md). Он фиксирует блокеры и не означает их устранения.

## Архитектурные приоритеты — согласовано для проектирования

**Решение владельца проекта (07.11.2026):** сохранить 17 бизнес-модулей, не создавать новые bounded contexts ради платформенных механизмов. В первую очередь: **Correctness First** (транзакции, идемпотентность, tenant isolation, state machines, outbox), **Operational Reliability** (jobs, восстановление, observability, тесты, ограниченная конкурентность), **Intelligence Ready** (правильная история фактов, provenance, data quality и подготовка к ML без преждевременного запуска AI-платформы).

Содержание, требования `KX-ARC-*`, acceptance и roadmap: [19 — Architecture Hardening Priorities](19-architecture-hardening-priorities.md). Это согласованное направление, **не** готовый код, юридическое утверждение бизнес-правил или пройденные CI-тесты.

## Access Governance v2 — текущий проектный стандарт

Первый role/permission security review выявил недоопределённость внешних заказчиков, доступа к `My Orders`, входящих заявок Tenant, отзывов, роли независимого Finance Approver, прав POD и реальных scopes/approval. Обновлённый [Access Governance v2.1](24-access-control-tdd-matrix-v2.md) с [machine contract](contracts/access-policy-matrix.v2.json) теперь является базой для дальнейшего TDD-проектирования. После повторного аудита v2.1 содержит 67 проектных policy entries и 27 adversarial scenarios; требуется согласование полномочий подписанта, лимитов, и юридического статуса отзывов до реализации. v1 сохранён исторически; тесты не выполнялись.

## Business scenario and role walkthrough — third audit

[User Story Book](21-user-story-book.md) now holds 80 unique draft/discovery stories; [Business Scenario Book](25-business-scenario-book.md) retains 11 cross-role narratives; [Role/Process Simulation](26-role-process-simulation-and-gap-audit.md) adds 42 desk walkthroughs, representing all 22 role personas in at least one process. There are 33 gap candidates, including 12 business/security/legal blockers for their impacted R0 actions. **Not exhaustive**, not actual user simulation, code or CI. Specifically requires sign-off on external customer authority, carrier agreement, offline custody, finance truth, and live shipment continuity if tenant billing suspends. Do not convert discovery candidates into unreviewed R0 features or expand from 17 business modules.

## Fourth review: 12 blocker design proposals versus stakeholder approvals

[27 — Proposed R0 Blocker Decisions](27-r0-blocker-policy-decisions.md) specifies fail-safe contracts for the 12 blocking business/legal/security gaps from [26](26-role-process-simulation-and-gap-audit.md). Technical specification exists, but **business/legal approvals remain pending**. The [28 — TDD Bank](28-r0-tdd-acceptance-bank.md) contains 84 planned cases, [29 — Workshop Kit](29-r0-business-acceptance-workshop-kit.md) prepares five stakeholder sessions; none of these represent actual test runs or signed agreements. Keep all affected irreversible actions deny/pending until the applicable actor, source/evidence and operating policy is verified.

## Новое архитектурное решение — модульная стратегия

**Рекомендуемый выбор (ещё не ACCEPTED):** один Spring Boot backend + Spring Modulith business modules для R0, впоследствии isolated background workers для GPS, routing, notifications. Сравнение альтернатив и критерии экстракции: [13 — Architecture Options](13-modular-architecture-options-v1.md). Декомпозиция и gate implementation: [14 — Delivery Blueprint](14-modular-delivery-blueprint.md).

| Код | Что необходимо утвердить | Владелец |
|---|---|---|
| MOD-DEC-01 | Spring Modulith package-level, single Maven build для R0 или сразу Maven multi-module | Architect + backend lead |
| MOD-DEC-02 | Границы Booking/Capacity (один атомарный владелец reservation) | Fleet + dispatch + architecture |
| MOD-DEC-03 | Data ownership и tenancy/partner grants для внешних интеграций | Security + architect |
| MOD-DEC-04 | Event publication/outbox delivery model и recovery | Platform/SRE |
| MOD-DEC-05 | Условия выделения workers и автономная работа On-Prem | Platform + enterprise owner |

## Принятое направление: Platform Jobs & State Machines (07.11.2026)

**Выбрано владельцем проекта для архитектурной реализации:** PostgreSQL-backed shared Job Engine, общий небольшой Java 21 State Machine Kernel и отдельные domain-owned Process Managers. Не создавать глобальную таблицу бизнес-состояний и не увеличивать каталог из 17 бизнес-модулей. Redis не является durable job store. См. [18 — Platform Jobs, State Machines & Workflows](18-platform-jobs-state-machines-workflows.md).

**Открыто до implementation gate:** сравнить JobRunr и минимальный PG scheduler; доказать transaction/outbox enqueue, lease fencing, RLS, at-least-once/idempotency и recovery. Ни библиотека, ни production readiness пока не утверждены.

## Data Platform / GIS решения для утверждения

| Код | Решение | Владелец |
|---|---|---|
| DAT-DEC-01 | `GPS VehiclePosition` source of truth и idempotency registry для partitioned history | Fleet + Architecture |
| DAT-DEC-02 | Retention per tenant/legal hold, permitted archive/drop policy | Compliance + Security + DBA |
| DAT-DEC-03 | `pg_partman` vs privileged scheduled DDL per Cloud/On-Prem profile | DBA/SRE |
| DAT-DEC-04 | Mandatory PostGIS versions/extensions, GIS provider, GIS query budgets | Backend + DBA |
| DAT-DEC-05 | Read-model watermark/freshness/rebuild and no critical write guards | Module owners + QA |
| DAT-DEC-06 | Privacy precision, partner geo access and geofence event semantics | Security + Logistics |

См. [15 — Data Platform](15-data-platform-partitioning-postgis.md) и [16 — Module Annex](16-module-storage-gis-addendum.md). Требуется real PostgreSQL/PostGIS PoC; декларативный JSON не подтверждает performance/tenant isolation.

## Критические решения

| ID | Что утвердить | Кто принимает | Почему блокирует |
|---|---|---|---|
| DEC-01 | Первый платящий сегмент и 2 компании-пилота | Product owner | Определяет ценность и границы MVP |
| DEC-02 | Первый коридор и грузовые категории | Product + logistics | Ограничивает карты и регуляторные наборы |
| DEC-03 | Contract / RFQ / Quote / Booking lifecycle | Экспедитор + Legal | Нельзя обещать цену/наличие машины без оснований |
| DEC-04 | Разграничение shipper/forwarder/carrier/warehouse | Architect + Security + Legal | Cross-tenant collaboration требует scope |
| DEC-05 | Коммерческая ответственность при Rescue и субподряде | Legal + Finance | Liability/insurance/согласия |
| DEC-06 | Документы и POD для конкретной страны/груза | Legal + Operations | Сроки, статус и closure |
| DEC-07 | Подключаемый routing/GPS provider, покрытие KZ | Integration lead | ETA/ограничения и цена API |
| DEC-08 | Фактические Vehicle/Trailer/Cargo attributes | Fleet + Quality | Невозможен безопасный подбор |
| DEC-09 | Source of truth for invoices/AR/AP/ERP | Finance | Нельзя оценить cash gap и margin |
| DEC-10 | Ответственность за правовые RuleSet и частоту обновления | Legal + Compliance | Нельзя объявлять опасные грузы разрешёнными |
| DEC-11 | Модель тарифов SaaS и usage caps | Product + Finance | Риск отрицательной юнит-экономики |
| DEC-12 | Поддерживаемые Cloud/On-Prem профили и SLA | Platform + Security | Разные операционные риски |
| DEC-13 | Отображение GPS/ETA клиенту и partner rights | Security + Logistics | Privacy/customer confidence |
| DEC-14 | Нужен ли SSCC issuer или только импорт | WMS/GS1 owner | Нельзя печатать GS1 код без правомерного выделения |

## Вопросы для утверждения Lifecycle v1

| Код | Решение | Бизнес-владелец |
|---|---|---|
| LFC-DEC-01 | Binding или conditional quote до подтверждения машины? | Коммерческий руководитель + юрист |
| LFC-DEC-02 | Момент обязательств перевозчика/поставщика и точная семантика `SELECTED` | Экспедитор + договорной юрист |
| LFC-DEC-03 | Подтверждение ресурсов: машина, водитель, прицеп, складские окна, сроки холда | Логист + fleet |
| LFC-DEC-04 | Кто подтверждает pickup/POD и юридическая сила доказательств | Operations + юридический представитель |
| LFC-DEC-05 | Физическое закрытие при partial delivery/return и claim | Экспедитор + клиент + финансы |
| LFC-DEC-06 | Source of truth и процесс Posting для invoice, AR/AP, advances и payments | Главный бухгалтер/финансовый контролёр |
| LFC-DEC-07 | Credit limits, скидки, дотации, approvals и separation of duties | Finance + Security |
| LFC-DEC-08 | Права раскрытия заказчику информации о подрядчике, маршруте и задержке | Security + коммерческий отдел |

**Документы:** [Commercial & Execution Lifecycle v1](10-commercial-execution-lifecycle-v1.md) · [LFC tests](11-commercial-execution-acceptance-v1.md). До рассмотрения на реальном workshop всё `PROPOSED`.

## Дополнительные продуктовые решения — Freight Exchange

| Код | Решение | Владелец |
|---|---|---|
| MKT-DEC-01 | Публикация: только закрытая сеть или отдельная публичная биржа? | Product + Commercial |
| MKT-DEC-02 | Driver vs carrier operator: полномочия на публикацию и заключение договора | Legal + Security |
| MKT-DEC-03 | Право на догруз поверх эксклюзивного FTL и изменение SLA | Contract owner + Logistics |
| MKT-DEC-04 | Порог полезности по уменьшению пустого пробега и incremental margin | Finance + Operations |
| MKT-DEC-05 | Есть ли официальное разрешение на использование API/данных внешних бирж? | Partnerships + Legal |
| MKT-DEC-06 | KYB, контрагентский риск, ответственность самой площадки и монетизация | Product + Legal + Finance |

См. [idea/27 — DELLA benchmark & Freight Exchange](../idea/27-freight-exchange-load-board-and-backhaul.md).

## Реестр основных рисков

| Код | Риск | Воздействие | Предохранитель |
|---|---|---|---|
| R-01 | Неполные коммерческие обязательства | Высокое | RFQ/contract/versioned approvals |
| R-02 | Утечка данных между компаниями | Критическое | RLS + policy + isolation suite |
| R-03 | Ошибочная безопасность груза/транспорта | Критическое | Approved rules + hard DENY + expert review |
| R-04 | Неверная/устаревшая геодорожная информация | Высокое | Provenance + manual review + provider benchmark |
| R-05 | Ложная отгрузка или lost custody | Высокое | HandlingUnit scan + explicit transfer |
| R-06 | Cash gap несмотря на «положительную прибыль» | Высокое | AR/AP, advances, credit policy |
| R-07 | Зависимость от одного платного provider | Среднее/высокое | Ports/adapters + quotas |
| R-08 | Пустое/недостаточное качество данных ML | Среднее | Baseline first, no legal ML decisions |
| R-09 | Enterprise отличается от Cloud по поведению | Высокое | Same release, contract suites, config |
| R-10 | Недействительные маркировка/таможенные документы | Критическое | Typed IDs + official sources + human legal sign-off |
| R-11 | Слишком широкий MVP | Высокое | Release 0 slice + acceptance gates |
| R-12 | Недостаточное тестирование восстановления | Высокое | Restore drills and audited outbox replay |

## Следующие проектные результаты

1. Провести реальный workshop с экспедитором, логистом, диспетчером и бухгалтером. Проверить сценарии `idea/17`.
2. Зафиксировать Commercial & Execution Lifecycle как state machines с юридическими/финансовыми основаниями и правами.
3. Принять ADR по tenancy, bounded contexts, deployment и source of truth, прежде чем писать общий backend.
4. Согласовать двусторонний Provider PoC для грузовых ограничений по первому коридору.
5. Подготовить каталог обязательных документов и грузовых профилей только для первого пилота.
6. Реализовать R0 в отдельном PR с Testcontainers, multi-tenant isolation suite и E2E smoke.
7. После фактической приёмки решать очередность Rescue, Warehouse, ML и международных интеграций.

## Definition of Decision

Решение имеет `owner, date, assumptions, alternatives, chosen option, legal/security consequences, cost, acceptance evidence, rollback plan`. Без этого таблица ADR остаётся *backlog*, а не утверждённой архитектурой.

**Источники:** [ADR proposals](../idea/11-adr-and-open-questions.md), [System gap analysis](../idea/16-system-needs-gap-analysis.md), [MVP](05-mvp-qualification.md).

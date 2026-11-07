# 07 — Open Decisions, Risks and Next Actions

**Статус:** DISCOVERY · **Дата:** 07.11.2026. Все ADR-001…ADR-032 в `idea/11` остаются **PROPOSED**, если нет отдельного подписанного утверждения.

**Свежая оценка архитектурных и продуктовых рисков:** [Project Audit — 2026-11-07](12-project-audit-2026-11-07.md). Он фиксирует блокеры и не означает их устранения.

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

# 25 — KERUENIX: консолидация идей и проектной документации v0.2

**Дата:** 07.11.2026 · **Статус:** DRAFT — сводный документ по `idea/00–24`; не доказательство реализации или юридического соответствия.

## 1. Что уже покрыто проектными идеями

| Направление | Подтверждено на уровне идеи | Подробные исходники |
|---|---|---|
| Продукт и клиенты | Малые перевозчики без IT-парка + крупные Enterprise, экспедиторы, грузоотправители, склады | [01](01-vision-and-positioning.md), [13](13-deployment-models.md) |
| SaaS/Enterprise | Одна кодовая база, tenant isolation, scoped inter-company collaboration | [02](02-multi-tenant-and-identity.md), [08](08-security-reliability-and-sre.md), [13](13-deployment-models.md) |
| Коммерческий процесс | RFQ, Quote, booking, ответственность, споры, доставка/финансы | [04](04-operational-workflows.md), [06](06-pricing-fuel-and-settlements.md), [16](16-system-needs-gap-analysis.md), [17](17-forwarder-dispatcher-day-simulation.md) |
| Транспорт/маршруты | GPS, пробки/ограничения, ETA, тяжесть/ось/кубатура, холодовая цепь и цистерны | [05](05-routing-optimization-and-intelligence.md), [20](20-vehicle-classification-capacity-and-special-equipment.md) |
| Cargo safety | Опасные, пищевые, фарма, товарное соседство, режимы, упаковка | [18](18-cargo-classification-and-compatibility.md) |
| Rescue Network | Поломка, подбор замены, субподряд, безопасная передача и расходы | [14](14-emergency-recovery-subcontracting.md) |
| WMS/YMS Hub | ASN, ворота, SSCC, адреса хранения, ledger, Cross-Dock, СВХ | [15](15-logistics-hub-wms-automation.md) |
| Клиентский трекинг | Отслеживание конкретного Shipment, milestone, ETA, POD, privacy | [19](19-customer-shipment-tracking.md) |
| Международный учёт | GS1 GTIN/SSCC/GLN, ISO контейнер, HS/TN VED, UN, EPCIS, этикетки | [22](22-global-cargo-identification-and-marking.md) |
| Правила и эксперты | Дорожные/опасные/таможенные/хранение, source versions, виртуальные review personas | [21](21-expert-council-logistics-compliance.md), [23](23-cross-border-regulatory-compliance-registry.md), [24](24-international-cargo-simulation.md) |
| Intelligence | Timefold как оптимизатор, Tribuo для будущих прогнозов, deterministic fallback | [05](05-routing-optimization-and-intelligence.md) |

## 2. Что изменилось в версии 0.2

Теперь единые **продуктовые и системные требования** отделены от гипотез. Новая [документация](../docs/README.md) содержит:
- [Продуктовую стратегию](../docs/01-product-charter.md);
- [Архитектуру](../docs/02-system-architecture.md);
- [Canonical Domain и lifecycle](../docs/03-domain-lifecycle.md);
- [Трассируемую матрицу требований](../docs/04-requirements-traceability.md);
- [Release 0 и qualification](../docs/05-mvp-qualification.md);
- [Стандарты и нормативное управление](../docs/06-standards-compliance-governance.md);
- [Открытые решения и риски](../docs/07-decisions-and-risks.md);
- [Глоссарий](../docs/08-glossary.md);
- [Развёртывание и SRE](../docs/09-deployment-operations.md).

**Статусы:** исходные идеи `idea/` — концепции; `docs/` — консолидированные Draft требования, но не утверждённые ADR и не реализация. Противоречия фиксировать в реестре решений.

## 3. Утверждения, которые пока нельзя делать

- «Платформа готова к промышленному использованию».
- «Автомаршрутизатор гарантирует все ограничения дорог Казахстана».
- «Подтверждены разрешения на ADR/габаритный/международный рейс по одной категории».
- «Наш код SSCC соответствует GS1» без выделенного правомерного номера/проверки.
- «Подтверждено автоматическое таможенное оформление KEDEN/eTIR/eCMR».
- «Партнёр автоматически несёт ответственность после принятия оферты».
- «Положительная маржа означает полученные деньги».
- «Позиция автомобиля означает местоположение груза после перегрузки».

## 4. Главные инженерные инварианты

1. `Order`, `Shipment`, `CargoUnit/HandlingUnit`, `Trip`, `TransportLeg` — разные сущности.
2. `tenant`, `legalOwner`, `custodyHolder`, `carrier`, `warehouseOperator` и `subcontractor` — разные роли.
3. Customer Tracking строится на подтверждённых событиях груза; GPS — вспомогательный сигнал с меткой свежести.
4. Транспортная вместимость = масса + геометрия + секции/кубатура + оси + разрешения + фактическая доступность.
5. CargoCompatibility и RegulatoryRules — hard constraints; неопределённость не является разрешением.
6. Товарные и транспортные стандарты не смешивают GTIN/SSCC/UN/HS/TNVED/контейнер.
7. При Rescue Shipment сохраняется, custody фиксируется, изменяется физический leg/trip и экономический план.
8. Warehouse Stock Ledger не может формировать отрицательные остатки/двойные резервы.
9. План, прогноз, подтверждённый факт, юридическое обязательство и денежный платёж хранятся отдельно.
10. Java/Spring доменное ядро переносимо между SaaS и Enterprise без форка бизнес-логики.

## 5. Что ещё недоучтено

| Риск / пробел | Необходимое решение |
|---|---|
| Экспедиторские переговоры и контракты | Утвердить квалификацию RFQ, quote negotiation, carrier confirmation, ограничения полномочий |
| Обязательные документы и финансовый учёт | Выполнить отдельный workflow AR/AP, POD, актов и претензий |
| Проверка реального перевозчика/страховки | Согласовать KYB, документы, сроки, проверки |
| Дорожные ограничения Казахстана | Измерить на pilot corridor через 2 независимых провайдера + экспертный обзор |
| Правомерное выделение SSCC | Решить: импорт GS1-кодов или собственная лицензия/issuer процесс |
| Customs и опасные грузы | Нужны реальные профильные специалисты, конкретная страна и нормативные versioned datasets |
| Между Cloud и On-Prem | Нужен тест согласованного API/расхождений/асинхронного обмена |
| SLA и стоимость SaaS | Рассчитать юнит-экономику карты/GPS/SMS/объектов, определить владельца инфраструктуры |
| Слишком широкий MVP | Формально заморозить R0 road-freight/General Cargo и определить критерии перехода |

## 6. Приоритет следующей работы

**Сначала:** принять отдельные решения по пилоту, Commercial Lifecycle, tenancy и безопасности, данным груза/транспорта, документам и финансовому источнику истины. Далее — минимальный вертикальный slice с подтверждёнными событиями, customer tracking и расчётом фактических затрат.

**Затем:** проверить WMS Lite, внутреннее Rescue, Timefold и международные правила по выбранному грузовому коридору; допускается смена порядка под конкретного платящего пилотного клиента, но без отмены safety и privacy gate.

Полный список см. [решения и риски](../docs/07-decisions-and-risks.md), [requirements](../docs/04-requirements-traceability.md), [MVP](../docs/05-mvp-qualification.md).

## 7. Как принимать новые идеи

Для каждой идеи:
`Problem → Persona → Real Event → Current workaround → Proposed capability → Permission/data → Safety/Legal → Cost/Impact → Priority → Acceptance → Owner`.

Проверять новой ролью в виртуальном совете и отдельно живым профильным специалистом для действующих норм. Не смешивать полезную бизнес-гипотезу с готовой регуляторной автоматизацией.

**Последовательность для нового PR:** обновить соответствующий `idea/NN`, скорректировать `docs/04`, `docs/03` или `docs/05` по необходимости, создать/обновить ADR, проверить ссылки и приложить evidence с SHA. Без независимого approval нет статуса `ACCEPTED`.

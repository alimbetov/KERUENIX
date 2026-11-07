# KERUENIX — каталог проектных идей

**Версия каталога:** 0.2 · **Обновлено:** 7 ноября 2026 · **Статус:** обсуждение / discovery, не утверждённое техническое задание.

**[Начать: краткая концепция на русском](00-brief-ru.md)** · **[Единая проектная документация](../docs/README.md)** · **[Сводка v0.2](25-consolidation-v0.2.md)**

KERUENIX — многоклиентская платформа управления логистикой: коммерческий заказ, выбор транспорта, маршруты, диспетчеризация, GPS, грузы, склады, топливо, себестоимость и контроль исполнения. Главная идея — оптимизация **допустимого и выгодного** движения груза, а не просто отображение машин на карте.

## Комплект документов

| Файл | Содержание |
|---|---|
| [00 — Краткая концепция (RU)](00-brief-ru.md) | Суть и главные проектные решения |
| [01 — Vision](01-vision-and-positioning.md) | Клиенты, позиционирование, гипотезы, границы |
| [02 — Multi-tenancy](02-multi-tenant-and-identity.md) | Изоляция компаний, роли, права, партнёрский доступ |
| [03 — Domain Model](03-domain-model.md) | Order, Shipment, Trip, Leg, Cargo, Cost |
| [04 — Workflows](04-operational-workflows.md) | Клиент, логист, диспетчер, водитель, склад |
| [05 — Intelligence](05-routing-optimization-and-intelligence.md) | Маршрутизация, выезд, Timefold и Tribuo |
| [06 — Cost & Fuel](06-pricing-fuel-and-settlements.md) | Цена, себестоимость, АЗС, план/факт |
| [07 — Integrations](07-external-integrations.md) | Карты, GPS, ERP, WMS, АЗС, партнёры |
| [08 — Security & SRE](08-security-reliability-and-sre.md) | Tenant isolation, надёжность, аудит, резервирование |
| [09 — Architecture](09-reference-architecture.md) | Java/Spring Boot, модули, API, данные, события |
| [10 — Roadmap & Tests](10-mvp-roadmap-and-acceptance.md) | MVP, фазы, пилот, обязательные проверки |
| [11 — ADR Backlog](11-adr-and-open-questions.md) | Предложенные решения и открытые вопросы |
| [12 — Benchmark](12-competitive-benchmark.md) | Идеи SAP, Oracle, Wialon, PTV и других систем |
| [13 — Deployment Models](13-deployment-models.md) | Cloud SaaS, Dedicated и Enterprise/On-Prem из одного кода |
| [14 — Rescue Network](14-emergency-recovery-subcontracting.md) | Аварийный перехват груза, поиск замены и субподряд между компаниями |
| [15 — Logistics Hub / WMS](15-logistics-hub-wms-automation.md) | Автоматизация въезда, складского учёта, перегрузки, СВХ, ворот и отгрузки |
| [16 — System Needs & Gap Analysis](16-system-needs-gap-analysis.md) | Системные потребности, разрывы бизнес-процессов, требования и приёмка |
| [17 — Day-in-Life Simulation](17-forwarder-dispatcher-day-simulation.md) | Симуляция рабочего дня экспедитора, логиста, диспетчера и финансов |
| [18 — Cargo Classification & Compatibility](18-cargo-classification-and-compatibility.md) | Классы грузов, товарное соседство, правила перевозки и хранения, нормативные профили |
| [19 — Customer Shipment Tracking](19-customer-shipment-tracking.md) | Клиентские статусы, ETA, этапы маршрута, трекинг груза и защита данных |
| [20 — Vehicle Classification & Capacity](20-vehicle-classification-capacity-and-special-equipment.md) | Грузоподъёмность, кубатура, рефрижераторы, цистерны, бензовозы, ограничения загрузки |
| [21 — Logistics Standards Council](21-expert-council-logistics-compliance.md) | Виртуальное заседание экспертов: международная логистика, дорожные правила, таможня, WMS, безопасность |
| [22 — Global Cargo Identification](22-global-cargo-identification-and-marking.md) | Международная маркировка, GS1 SSCC/GTIN/GLN, штрихкоды, контейнеры и события EPCIS |
| [23 — Cross-border Regulatory Registry](23-cross-border-regulatory-compliance-registry.md) | Правила Казахстана, ЕАЭС, ADR, CMR, TIR/eTIR, таможня и документы |
| [24 — International Cargo Simulation](24-international-cargo-simulation.md) | Четыре сценария квалификации международных грузовых операций |
| [25 — Consolidation v0.2](25-consolidation-v0.2.md) | Общая карта идеи, принятые к проектированию направления и следующие решения |
| [standards/identifier-catalog.v0.1.json](standards/identifier-catalog.v0.1.json) | Machine-readable namespace catalog, валидация форматов и источники |
| [standards/external-identifier.schema.json](standards/external-identifier.schema.json) | JSON Schema для записи внешнего идентификатора с issuer/verified/evidence |

## Неизменные правила дизайна

1. Один заказ может включать несколько грузовых партий и транспортных участков; один рейс может обслуживать несколько заказов.
2. Tenant определяет границу данных: она должна соблюдаться в API, PostgreSQL/RLS, кешах, файлах, событиях и мониторинге.
3. Между компаниями передаются только специально разрешённые данные по конкретной перевозке.
4. Безопасность транспорта и выполнение договорных ограничений важнее расчётной экономии.
5. План, прогноз, фактические события, деньги и история версий не подменяют друг друга.
6. Внешние карты/GPS/АЗС подключаются через заменяемые адаптеры.
7. Непроверенные дорожные данные и недоступные ML-модели не должны создавать ложных гарантий.
8. Старт — проверяемый MVP для автомобильной логистики, расширение на мультимодальность позже.

## Как работать с материалами

- **Idea:** новая гипотеза или возможность, требующая проверки.
- **Proposed:** вариант решения с анализом альтернатив.
- **Accepted ADR:** утверждённое архитектурное решение.
- **MVP Task:** реализуемая задача с проверяемыми критериями.
- **Verified:** подтверждено CI/интеграционным тестом/реальным пилотом на конкретной версии.

Данные о поставщиках и демонстрационные экономические числа не считать сертифицированными, юридически обязательными или универсальными для Казахстана.

**Начать реализацию рекомендуется с:** [единого реестра требований](../docs/04-requirements-traceability.md), [канонической доменной модели](../docs/03-domain-lifecycle.md) и [R0 qualification plan](../docs/05-mvp-qualification.md).

**Приоритет источников:** `docs/` объединяет текущие проектные требования и границы релизов, а `idea/` хранит подробные гипотезы и первоначальные варианты. Расхождения оформляются как открытые решения, а не молча считаются утверждёнными.

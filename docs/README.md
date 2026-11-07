# KERUENIX — единая система проектной документации

**Documentation baseline:** v0.2 · **Дата:** 2026-11-07 · **Статус:** DRAFT / Discovery.  
**Этот каталог — синтез требований**, `../idea/` — подробное описание гипотез, исходных предложений, сценариев и нормативных ссылок.

## Рабочие документы

| № | Документ | Ответ на вопрос | Состояние |
|---|---|---|---|
| 01 | [Product Charter](01-product-charter.md) | Для кого и ради чего создаём продукт? | Draft |
| 02 | [System Architecture](02-system-architecture.md) | Как разделены модули, доверие и данные? | Draft |
| 03 | [Domain Lifecycle](03-domain-lifecycle.md) | Какие реальные сущности и состояния? | Draft |
| 04 | [Requirements & Traceability](04-requirements-traceability.md) | Что система обязана делать и как проверить? | Draft |
| 05 | [MVP & Qualification](05-mvp-qualification.md) | Что войдёт в первый рабочий релиз? | Draft |
| 06 | [Standards & Compliance](06-standards-compliance-governance.md) | Кто поддерживает правила, маркировку и документы? | Draft |
| 07 | [Decisions & Risks](07-decisions-and-risks.md) | Какие вопросы блокируют проектирование? | Draft |
| 08 | [Glossary](08-glossary.md) | Что значат ключевые бизнес-термины? | Draft |
| 09 | [Deployment & Operations](09-deployment-operations.md) | Как Cloud и Enterprise используют один код? | Draft |
| 10 | [Commercial & Execution Lifecycle v1](10-commercial-execution-lifecycle-v1.md) | Каковы команды, состояния, инварианты, согласования и исключения? | Proposed / review |
| 11 | [Lifecycle Acceptance & Simulation](11-commercial-execution-acceptance-v1.md) | Как проверить коммерческий и операционный цикл? | Test plan |
| 12 | [Project Audit — 2026-11-07](12-project-audit-2026-11-07.md) | Состояние кода, технические разрывы, риски, R0a и план реализации | Audit / Draft |
| JSON | [Lifecycle State Machines](contracts/commercial-execution-lifecycle.v1.json) | Машинно-читаемый контракт допустимых переходов (12 агрегатов) | Proposed |
| 25 | [Сводка изменений идей v0.2](../idea/25-consolidation-v0.2.md) | Что уточнили и что ещё нужно доказать? | Draft |
| 26 | [Lifecycle gaps and decisions](../idea/26-commercial-execution-lifecycle-risks.md) | Коммерческие риски, исключения и бизнес-вопросы | Proposed |
| 27 | [Freight Exchange & Backhaul](../idea/27-freight-exchange-load-board-and-backhaul.md) | Биржа грузов и машин, догрузы, обратные рейсы, DELLA benchmark | Idea / Proposed |

## Источники концепций

| Группа | Документы в `idea/` |
|---|---|
| Бизнес и операции | [01](../idea/01-vision-and-positioning.md), [04](../idea/04-operational-workflows.md), [16](../idea/16-system-needs-gap-analysis.md), [17](../idea/17-forwarder-dispatcher-day-simulation.md) |
| Безопасность, tenancy и установка | [02](../idea/02-multi-tenant-and-identity.md), [08](../idea/08-security-reliability-and-sre.md), [13](../idea/13-deployment-models.md) |
| Домен, ресурсы и алгоритмы | [03](../idea/03-domain-model.md), [05](../idea/05-routing-optimization-and-intelligence.md), [06](../idea/06-pricing-fuel-and-settlements.md), [20](../idea/20-vehicle-classification-capacity-and-special-equipment.md) |
| Груз и исполнение | [14](../idea/14-emergency-recovery-subcontracting.md), [15](../idea/15-logistics-hub-wms-automation.md), [18](../idea/18-cargo-classification-and-compatibility.md), [19](../idea/19-customer-shipment-tracking.md) |
| Международные стандарты и правила | [21](../idea/21-expert-council-logistics-compliance.md), [22](../idea/22-global-cargo-identification-and-marking.md), [23](../idea/23-cross-border-regulatory-compliance-registry.md), [24](../idea/24-international-cargo-simulation.md), [JSON catalog](../idea/standards/identifier-catalog.v0.1.json) |
| Первичный roadmap и ADR | [10](../idea/10-mvp-roadmap-and-acceptance.md), [11](../idea/11-adr-and-open-questions.md) |

## Управление изменениями

- **Idea / Hypothesis:** предположение; требуется интервью, доказательство или эксперимент.
- **Draft Requirement:** требование с тестируемым критерием; ещё не утверждено владельцем процесса.
- **Accepted Requirement:** подтверждено ответственным и имеет владельца, границы и критерий приёмки.
- **Accepted ADR:** отдельное подписанное архитектурное решение, альтернативы и последствия.
- **Implemented:** код существует, но не обязательно соответствует требованиям.
- **Qualified:** проверено тестами и конкретным commit SHA/средой, есть ссылки на результаты.
- **Production-ready:** дополнительно проверены эксплуатация, безопасность, восстановление, нормативная применимость и поддержка.

Документы `docs/` **не могут автоматически менять** статус ADR с `PROPOSED` на `ACCEPTED`. Регуляторные данные и лицензионные таблицы активируются только через независимое подтверждение.

## Definition of Ready для реализации требования

Названы бизнес-владелец и актор, входные данные и валидация, события и состояния, tenant/partner permissions, ошибка и компенсация, граница P0/P1, acceptance IDs и обязательный источник правового правила (если нужно).

## Definition of Done для разработки

Есть реализация в точном SHA; unit + integration + permission/security tests; migration/backfill; contract test при внешнем API; audit/observability; документация изменений; воспроизводимый smoke; проверка на Cloud и соответствующих изолированных профилях.

**Следующая обязательная задача:** провести **бизнес-приёмку подготовленного [Commercial & Execution Lifecycle v1](10-commercial-execution-lifecycle-v1.md)** с реальными экспедиторами, логистами, перевозчиком, юристом и финансистом. До sign-off статус документа — PROPOSED; 12 state machines и 94 перехода являются проектным кандидатом, а не действующей реализацией.

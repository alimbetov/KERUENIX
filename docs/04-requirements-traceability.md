# 04 — Requirements & Traceability Matrix

**Версия:** 0.2 · **Статус:** DRAFT. Здесь нет реализованных/приёмочно закрытых требований.  
**Приоритет P0:** обязательно проработать для безопасного ядра/первого пилота; конкретный функционал может быть ограничен реализацией Release 0. P1 — расширение после первого вертикального процесса. P2 — дальнейшее развитие.

## Общая матрица

| ID | Требование | Приор. | Доказательство / тест | Источник |
|---|---|---|---|---|
| KX-TEN-001 | Identity, tenant, membership, роли и field/object policy | P0 | Два tenant не читают чужие ресурсы, в т.ч. документы и кеш | [02](../idea/02-multi-tenant-and-identity.md) |
| KX-TEN-002 | Межорганизационный доступ с ограниченным scope | P0 | Партнёр видит только свою часть Shipment | [02](../idea/02-multi-tenant-and-identity.md) |
| KX-DEP-001 | Один код для Cloud и Dedicated/On-Prem | P0 | Domain/security contract тесты в двух профилях | [13](../idea/13-deployment-models.md) |
| KX-COM-001 | RFQ с обязательными полями, уточнениями и ответственным | P0 | Нет binding quote при критически неполных данных | [16](../idea/16-system-needs-gap-analysis.md) |
| KX-COM-002 | Неизменяемые версии коммерческого предложения и условий | P0 | Истёкшую версию нельзя молча принять | [04](../idea/04-operational-workflows.md) |
| KX-COM-003 | Переговоры и подтверждение коммерческого согласия | P0 | Изменённый вес/адрес → новая версия approval | [17](../idea/17-forwarder-dispatcher-day-simulation.md) |
| KX-COM-004 | Проверка подрядчика, транспортных документов и страховки | P0 | Недействительный профиль блокирует твёрдое бронирование | [16](../idea/16-system-needs-gap-analysis.md) |
| KX-OPS-001 | Разделить Order, Shipment, CargoUnit, Leg, Trip | P0 | Перегрузка не создаёт новый коммерческий заказ | [03](../idea/03-domain-model.md) |
| KX-OPS-002 | Подтверждённая резервация транспорта без конфликта | P0 | Две конкурирующие команды → одна резервация | [10](../idea/10-mvp-roadmap-and-acceptance.md) |
| KX-OPS-003 | Версии маршрутов, стопов и ETA с подтверждением | P0 | Предыдущая утверждённая версия доступна | [05](../idea/05-routing-optimization-and-intelligence.md) |
| KX-OPS-004 | GPS freshness, офлайн и источник каждого события | P0 | Старое наблюдение не называется live-позицией | [19](../idea/19-customer-shipment-tracking.md) |
| KX-OPS-005 | Принятие, частичная выдача и POD по грузовым единицам | P0 | Частичный POD ≠ DELIVERED | [19](../idea/19-customer-shipment-tracking.md) |
| KX-OPS-006 | Обработка исключений, отмен и возвратов | P0 | Отказ получателя/срыв окна не стирает прошлые факты | [17](../idea/17-forwarder-dispatcher-day-simulation.md) |
| KX-VEH-001 | VehicleCombination и паспорт грузоподъёмности/объёма/геометрии | P0 | 8т проходит по массе, но не по двери → отклонить | [20](../idea/20-vehicle-classification-capacity-and-special-equipment.md) |
| KX-VEH-002 | Рефрижератор/цистерна/секции/оборудование как capabilities | P1 | Нет охлаждения/совместимого танка → отказ/Review | [20](../idea/20-vehicle-classification-capacity-and-special-equipment.md) |
| KX-CAR-001 | CargoComplianceProfile и проверка недостающих атрибутов | P0 | Неизвестный класс опасности → NEEDS_REVIEW | [18](../idea/18-cargo-classification-and-compatibility.md) |
| KX-CAR-002 | Товарное соседство и совместимость погрузки/хранения | P0 | Несовместимые режимы в одном отсеке → запрет | [18](../idea/18-cargo-classification-and-compatibility.md) |
| KX-CAR-003 | Невозможность обойти нормативный DENY | P0 | Обычный ручной override отклонён | [18](../idea/18-cargo-classification-and-compatibility.md) |
| KX-TRK-001 | Клиентский Shipment timeline + ETA provenance | P0 | Клиент видит только свою отправку и допустимые события | [19](../idea/19-customer-shipment-tracking.md) |
| KX-TRK-002 | Карта/уведомления/гостевые ссылки c privacy и expiry | P1 | Ссылка с истёкшим сроком ничего не выдаёт | [19](../idea/19-customer-shipment-tracking.md) |
| KX-FIN-001 | Расчёт цены, затрат, план/факт, отдельные buy/sell ставки | P0 | Quote воспроизводим по тарифной версии | [06](../idea/06-pricing-fuel-and-settlements.md) |
| KX-FIN-002 | AR/AP, предоплата, credit exposure и статус документов | P0 | Deliver не превращает Invoice в Paid | [16](../idea/16-system-needs-gap-analysis.md) |
| KX-FIN-003 | Спорные суммы и претензии с доказательствами | P1 | Счёт субподрядчика не оплачивается вслепую | [06](../idea/06-pricing-fuel-and-settlements.md) |
| KX-WMS-001 | Stock ledger, резервы и owner/custody | P1 | Нет double-pick, нет выдачи customs HOLD | [15](../idea/15-logistics-hub-wms-automation.md) |
| KX-WMS-002 | Dock slots, ASN, cross-dock и задания | P1 | Поздняя машина не создает фиктивную приёмку | [15](../idea/15-logistics-hub-wms-automation.md) |
| KX-RSC-001 | Внутренняя замена транспорта по инциденту | P1 | Order/Shipment остаются прежними | [14](../idea/14-emergency-recovery-subcontracting.md) |
| KX-RSC-002 | Trusted partner subcontract, approval и custody | P1 | Никто не получает cargo без подтверждённого handover | [14](../idea/14-emergency-recovery-subcontracting.md) |
| KX-ID-001 | Typed external IDs, GS1/ISO/HS/UN, hash/issuer evidence | P0 | Префиксы, checksum, namespaces не смешиваются | [22](../idea/22-global-cargo-identification-and-marking.md) |
| KX-ID-002 | SSCC/GS1-128 и внутренний LPN fallback | P1 | Не выдаём UUID за действующий SSCC | [22](../idea/22-global-cargo-identification-and-marking.md) |
| KX-REG-001 | Действующие правила country/mode/date и source version | P0 | Нет AUTO ALLOW из невалидного/отсутствующего rule set | [23](../idea/23-cross-border-regulatory-compliance-registry.md) |
| KX-REG-002 | Документальный checklist для выбранного коридора/груза | P1 | Без подтверждённых документов нет регулируемого выпуска | [23](../idea/23-cross-border-regulatory-compliance-registry.md) |
| KX-REG-003 | Таможенный HOLD и доказуемый release | P1 | Untrusted webhook не снимает HOLD | [23](../idea/23-cross-border-regulatory-compliance-registry.md) |
| KX-INT-001 | Заменяемые карты/GPS/ERP/WMS/EDI порты | P0 | Нет маршрутизатора → управляемая деградация | [07](../idea/07-external-integrations.md) |
| KX-INT-002 | EPCIS 2.0 и межинсталляционный обмен | P2 | Интероперабельность проверяется schema/contract tests | [22](../idea/22-global-cargo-identification-and-marking.md) |
| KX-ML-001 | Детерминированный baseline и optional Timefold | P1 | Solver timeout → безопасное ручное решение | [05](../idea/05-routing-optimization-and-intelligence.md) |
| KX-ML-002 | Tribuo models, registry, drift and rollback | P2 | Неверная модель не влияет на юридическое разрешение | [05](../idea/05-routing-optimization-and-intelligence.md) |
| KX-SRE-001 | Audit, idempotency, outbox и контроль конкуренции | P0 | Дубликаты events не удваивают stock/booking | [08](../idea/08-security-reliability-and-sre.md) |
| KX-SRE-002 | Backup, restore, metrics, SLO and incident runbooks | P0 | Staging restore, no cross-tenant leakage | [08](../idea/08-security-reliability-and-sre.md) |
| KX-PLT-001 | Tenant provisioning, plans, quotas, metering | P1 | Изоляция затрат/лимитов tenant, без смешивания счетов | [13](../idea/13-deployment-models.md) |

## Lifecycle v1 — дополнение к матрице требований

**Источник:** [Commercial & Execution Lifecycle v1](10-commercial-execution-lifecycle-v1.md), [проверки LFC-001…LFC-036](11-commercial-execution-acceptance-v1.md). Это Draft требования, тесты ещё не выполнялись.

| ID | Требование | Приор. | Acceptance evidence |
|---|---|---|---|
| KX-LFC-001 | RFQ может требовать уточнения; квалификация не равна акцепту | P0 | LFC-002 |
| KX-LFC-002 | QuoteVersion неизменяем, акцепт ограничен сроком и версией | P0 | LFC-003,004,010 |
| KX-LFC-003 | CarrierOffer.SELECTED не подтверждает CapacityReservation | P0 | LFC-005,006 |
| KX-LFC-004 | Booking.CONFIRMED только при акцепте условий + ресурсном confirmation | P0 | LFC-005…008 |
| KX-LFC-005 | Trip.STARTED не подтверждает pickup Shipment | P0 | LFC-011,012 |
| KX-LFC-006 | DeliveryAttempt/POD по каждой CargoUnit, включая partial/rejected | P0 | LFC-013,014,035 |
| KX-LFC-007 | DocumentPackageVersion отдельно от Shipment и Invoice | P0 | LFC-020,027 |
| KX-LFC-008 | Invoice, AR, AP, payment/advance и финансовое закрытие раздельны | P0 | LFC-021…026,028 |
| KX-LFC-009 | Отмена, сбой перевозки и смена перевозчика через exception/compensation | P0 contract / P1 Rescue automation | LFC-016,018,019,034 |
| KX-LFC-010 | Tenant/role protection, expectedVersion, idempotency and event replay | P0 | LFC-007,008,014,017,022,029,032,033,036 |

## Отдельная матрица критических владельцев

- **Product owner / эксперт-экспедитор:** COM, OPS, TRK.
- **Транспортный специалист:** VEH, routing и ограничение дороги.
- **DGSA/Quality:** CAR, опасные/пищевые/температурные грузы.
- **Customs/legal:** REG, международные документы и release.
- **WMS owner:** WMS и складское хранение.
- **Finance owner:** FIN, договоры и AR/AP.
- **Security/platform owner:** TEN, DEP, SRE, идентификация/доступ.

Требования, затрагивающие несколько ролей, считаются `NeedsCrossReview` до подписания экспертами.

## Acceptance status

Все тесты в таблице — **планируемые**. Ни unit, ни интеграционный, ни юридический тест не выполнен этой документацией. Для каждого требования будущая задача должна хранить: `requirement_id → user story → API/entity → test_case → CI run/exact SHA → owner approval`.

**См.:** [Qualification plan](05-mvp-qualification.md), [Simulation day](../idea/17-forwarder-dispatcher-day-simulation.md), [International simulation](../idea/24-international-cargo-simulation.md).

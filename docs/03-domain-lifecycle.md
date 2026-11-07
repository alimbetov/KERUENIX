# 03 — Canonical Domain & Lifecycle

**Статус:** DRAFT · **Версия:** 0.2. Каноническое разделение понятий требуется принять до создания таблиц.

## Основные бизнес-сущности

| Сущность | Смысл | Инвариант |
|---|---|---|
| `Tenant` | Подписчик и граница безопасности | У каждой приватной записи есть авторизованный владелец |
| `LegalEntity` | Юридическое лицо или филиал | Может быть несколькими в одном tenant |
| `PartnerGrant` | Обоснованное право другого участника | Только shipment/document/action scope, срок и аудит |
| `RFQ` | Запрос на расчёт, может быть неполным | Не является твёрдым обязательством |
| `QuoteVersion` | Предложение цены и условий | Версионируется, имеет срок действия |
| `CarrierOffer` | Коммерческое предложение перевозчика | Не равно резервированию машины |
| `Booking` / `CapacityReservation` | Подтверждённые ресурсы | Нет двойного бронирования |
| `Order` | Коммерческий заказ и контракт | Может включать несколько Shipment |
| `Shipment` | Физическая партия груза | Остаётся той же при замене авто |
| `HandlingUnit` / `CargoUnit` | Паллета/место/контейнер, возможный SSCC | SSCC не заменяет внутренний UUID |
| `TransportMovement` / `TransportLeg` | Передвижение груза по участкам | Каждый участок имеет mode/operator |
| `Trip` | Фактический рейс транспортного средства | Один рейс обслуживает несколько заказов |
| `VehicleCombination` | Машина+прицеп+кузов/секции/оборудование | Масса, объём и допускаемая нагрузка независимы |
| `RoutePlanVersion` | Версия маршрута и временного плана | Одобренная версия неизменна |
| `CargoComplianceAssessment` | Проверка соседства, опасности и хранения | Применимость нормативов, источник и версия |
| `CustodyHandover` | Доказательство передачи физического владения | GPS не подтверждает передачу |
| `WarehouseStockLedger` | Журнал движения складских единиц | Остатки/резервы под транзакционным контролем |
| `RecoveryCase` | Срыв перевозки и замена исполнителя | Не создаёт новый Order |
| `DeliveryEvidence/POD` | Принятый груз и документы | Подтверждается по CargoUnit, включая частичный приём |
| `Invoice/Receivable/Payable` | Денежные обязательства | Invoice, cash receipt, settlement — разные состояния |
| `TrackingSnapshot` | Клиентское представление фактов | Производная, permission-filtered проекция |

## Разделение жизненных циклов

**Commercial:** `RFQ_DRAFT → NEEDS_INFO → QUOTED → NEGOTIATING → ACCEPTED → CAPACITY_PENDING → BOOKED`. При отсутствии подтверждённой машины статус не должен быть `BOOKED`.

**Order:** `CREATED → CONFIRMED → IN_EXECUTION → FULFILLED → CLOSED`, с отдельными отменой и спором.

**Shipment/Cargo:** `REGISTERED → READY_FOR_PICKUP → PICKED_UP → IN_TRANSIT → AT_HUB/TRANSFER → OUT_FOR_DELIVERY → DELIVERED / PARTIALLY_DELIVERED`. В зависимости от процессной модели `AT_HUB` и `IN_TRANSIT` могут повторяться; это события/участки, не обязательно линейный enum.

**Trip:** `PLANNED → ASSIGNED → STARTED → COMPLETED/INTERRUPTED`, затем `RECONCILED`.

**Warehouse:** `EXPECTED → RECEIVED → STORED/STAGED → LOADED → DISPATCHED`, а quality hold/customs hold/reservation ведутся параллельно.

**Finance:** `COST_ESTIMATED`, `INVOICE_ISSUED`, `PARTIALLY_PAID`, `PAID`, `DISPUTED` и `SETTLED` относятся к разным обязательствам. Доставка не меняет автоматически эти состояния.

**Tracking:** client status — *derived read model* от фактов Shipment, Warehouse, Trip, Rescue; никогда не source of truth.

## Правила операций

1. `QuoteAccepted` не означает `CapacityConfirmed`; подтверждать оба события отдельно.
2. Сумма веса/объёма без геометрии/осевой нагрузки/положения паллет не гарантирует физическую вместимость.
3. Совместимость грузов и хранения зависит от опасности, санитарии, упаковки, температуры, конфигурации отсека и действующей нормы.
4. Груз на таможенном или качественном HOLD не выдаётся по обычному разрешению диспетчера.
5. При Rescue новый Trip/Leg, но старый Shipment и ID HandlingUnit, сохранение истории custody.
6. Клиент не видит чужих заказов и всех остановок одного Truck.
7. Клиентский статус «доставлено» требует подтверждения всех причитающихся грузовых единиц.
8. Ошибочные складские движения корректируются проводками, не бесследным редактированием.
9. Оригинальный Quote и расходы на Recovery/простой/претензии не смешиваются.
10. Внешний код (SSCC, GTIN, TNVED, UN, ISO6346) типизирован и не подменяет ни право доступа, ни статус официального документа.

## События

Формат: `event_id, tenant_id, aggregate_type, aggregate_id, aggregate_version, event_type, occurred_at, received_at, actor/source, correlation_id, causation_id, payload_schema_version, evidence_refs`.

Примеры: `RFQQualified`, `QuoteAccepted`, `CapacityReserved`, `CargoClassified`, `LoadPlanValidated`, `CargoHandedOver`, `TripInterrupted`, `RescueOfferAccepted`, `WarehouseReceived`, `ShipmentPartiallyDelivered`, `PODApproved`, `InvoiceMatched`, `PaymentAllocated`.

## Граница ответственности и трёхсторонняя ситуация

Четыре независимые компании могут участвовать в одном Shipment: грузовладелец, экспедитор, перевозчик, склад. Право собственности, custody, право дать поручение, коммерческая ответственность и доступ к полям — **не одно и то же**. Права выдаются ограниченно и фиксируются отдельными событиями/договорными ссылками.

**Детали:** [Business workflows](../idea/04-operational-workflows.md), [Cargo rules](../idea/18-cargo-classification-and-compatibility.md), [Vehicle](../idea/20-vehicle-classification-capacity-and-special-equipment.md), [Identifiers](../idea/22-global-cargo-identification-and-marking.md).

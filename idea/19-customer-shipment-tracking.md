# 19 — Customer Shipment Tracking: клиентский портал маршрута и процесса доставки

**Версия:** 0.1 · **Дата:** 07.11.2026 · **Статус:** предложенные требования, интерфейсы и критерии приёмки, без production-реализации.  
**Приоритет:** P0 для первого сквозного сценария доставки.

## 1. Потребность клиента

Клиент логистической компании должен самостоятельно получать ответ на вопросы:
- Принят ли мой заказ, и подтверждена ли перевозка?
- Где находится **мой груз**, что уже выполнено и какое событие ожидается дальше?
- Когда прибудет груз, насколько достоверен прогноз, есть ли задержка и что делает перевозчик?
- Где подтверждение приёма/передачи/доставки, какие грузовые единицы затронуты?
- Кому написать по проблеме или согласовать изменение условий?
- Если автомобиль заменили, как проследить дальнейшее движение груза без потери истории?

Пользователь не должен видеть полную GPS-историю водителя, другие грузы на том же автомобиле, внутреннюю стоимость закупки, маржу экспедитора, чужие документы и персональные данные без законного и договорного основания.

## 2. Три уровня доступа и отображения

| Уровень | Для кого | Возможности |
|---|---|---|
| Authenticated customer portal | Клиент как tenant/user с membership и scoped Order/Shipment grants | Список своих заказов и отправок, полный допустимый timeline, документы, сообщения, заявки на изменения |
| Scoped shipment sharing link (опционально) | Получатель/уполномоченный контакт без аккаунта | Минимальный статус одной отправки, ETA, окно доставки и допустимые документы; configurable без точных координат |
| Carrier/dispatcher internal | Перевозчик/экспедитор при своих полномочиях | Подробное исполнение, источник GPS, предложения маршрута, технические инциденты, согласования; приватные поля недоступны клиентскому API |

**Безопасность sharing link:** случайный криптографический токен, в БД хранится только хеш; цель/срок/объект/скоуп, revocation, по возможности одноразовое подтверждение или дополнительная аутентификация для чувствительных данных. Токены не должны попадать в analytics/referrer/logs, URL previews, историю публичного поиска. Rate limiting, HTTPS, минимальные данные, noindex, privacy-sensitive Cache-Control; никакого “достаточно UUID в ссылке”.

Право просмотра проверяется **каждый раз** по клиенту/контракту, shipment и разрешённым полям. Если ссылка утекла или доступ отозван, новые запросы должны быть отклонены; ранее скачанное содержание отозвать невозможно. Driver и грузовладелец могут быть разными компаниями.

## 3. Что показывает клиент

### Обязательные данные (MVP)

1. Номер заказа и отдельные идентификаторы отправок/партий — один Order может содержать несколько Shipment.
2. Маршрут: место отправления и назначения, промежуточные согласованные логистические пункты; точные адреса по разрешениям.
3. Status timeline: подтверждённый заказ, перевозчик назначен (при согласовании), ожидание погрузки, груз принят, в пути, прибыл в терминал/склад, передан следующему перевозчику, прибывает, частично/полностью доставлен, POD готов; события не должны “перескакивать” без объяснения.
4. Текущий `customer_status`, время и источник последнего **подтверждённого** события.
5. ETA `predicted_at`, диапазон/уровень уверенности и `last_location_observed_at` отдельно.
6. Задержка/изменение маршрута: клиентский статус, пересчитанный ETA и необходимость согласования.
7. Грузовые единицы: план, факт pickup, факт delivery, недостача/повреждение/частичный приём с разрешёнными деталями.
8. Документы: приемка, транспортные документы по договору, Proof of Delivery, акты замечаний и разрешённые вложения.
9. Контакт/тикет обращения, доступный уполномоченным лицам.
10. Раздельные состояния выполнения доставки и документального/финансового закрытия (последнее обычно доступно только уполномоченному заказчику).

### Расширения

- Карта: местоположение автомобиля/контейнера только если груз реально с ним связан по custody, телеметрия свежая и есть разрешение на показ. В противном случае последняя подтверждённая контрольная точка и честное сообщение об отсутствии live-координат.
- Ограничение геометрии: можно показывать этапы/коридор/крупную зону, не полную текущую трассу или точные остановки.
- Подписка на push/email/SMS/мессенджер через подтверждённый канал, preferences, SLA и quiet hours; без секретных коммерческих/GPS сведений в push.
- Список нескольких отправок по заказу, частичный POD, мультимодальные сегменты (road/rail/air/sea), температура/качество — только разрешённые контракты и сведения.

## 4. Shipment-centric модель, не vehicle-centric

`Order` — коммерческий договор/заказ; `Shipment` — физически отслеживаемая партия; `CargoUnit` — паллета/контейнер; `TransportLeg` — участок; `Trip` — движение машины; `VehicleObservation` — сигнал от устройства; `CargoCustodyEvent` — подтверждение нахождения или передачи груза.

Построение клиентского статуса происходит из проверенных `ShipmentMilestone` и custody/delivery событий. Текущее предполагаемое местоположение допускается выводить по `VehicleObservation` **только при действительной связке shipment↔trip и отсутствующем подтверждённом handover на другую машину/склад**.

GPS не является документом приёма или доставки. Геозона может стать `ARRIVAL_SUSPECTED`, но не `DELIVERED` без разрешённого подтверждения.

### Публичные статусы (проекция UI)

| customer_status | Источники |
|---|---|
| REQUESTED | RFQ/order submission, ещё нет подтверждённой перевозки |
| CONFIRMED | Booking подтверждён, транспорт/условия зафиксированы |
| AWAITING_PICKUP | Подтверждён график отправки, груз ещё не передан |
| PICKED_UP | Cargo custody scan/подписанное подтверждение |
| IN_TRANSIT | Активный leg/trip, cargo связан с этим участком |
| AT_HUB | Фактическая приёмка на терминале или складе |
| TRANSFERRING | Груз передаётся между исполнителями с доказательством |
| OUT_FOR_DELIVERY | Финальный подтверждённый участок выполняется |
| PARTIALLY_DELIVERED | Подтверждена лишь часть CargoUnit |
| DELIVERED | Подтверждение доставки всех обязательных грузовых единиц |
| DELIVERY_EXCEPTION | Отказ получателя, повреждение, недостача, возврат, другая проблема |
| ON_HOLD | Ожидание обязательного разрешения/документа/решения клиента |
| RECOVERY_IN_PROGRESS | Исполнение прервано, выполняется безопасный поиск замены |

OrderState, TripState, ShipmentState, DocumentState и InvoiceState остаются независимыми. Customer_status — derived read-model, не источник истины. `DELIVERED` не подразумевает `PAID` или `CLOSED`.

## 5. ETA и наблюдаемость

Сохранять `estimated_arrival_start/end`, `computed_at`, `input_version`, `provider`, `confidence`, `traffic_freshness`, `last_observed_location_at`, `display_policy`.

- Недостаточная точность ETA: показывать широкий диапазон или `ETA_UNAVAILABLE`, а не искусственное точное время.
- Устаревший GPS: карта показывает «последнее подтверждённое местоположение в HH:MM», либо скрывает положение; не называть это real-time.
- Отсутствует GPS у партнёра: milestone-tracking по подтверждениям, ручной check-in или EDI; никаких фиктивных координат.
- Текущее транспортное средство при Rescue меняется: timeline и ShipmentID сохраняются, новая транспортная связь подтверждается custody.
- В случае задержки причиной для клиента становится классифицированный код/разрешённое описание, а не персональная переписка персонала.
- Для международных/мультимодальных участков ETA/исходные события по leg могут быть разного качества; помечать источники отдельно.

## 6. Жизненный цикл изменения маршрута и оповещений

1. Трафик/GPS или водитель создаёт сигнал о проблеме.
2. Диспетчер проверяет и утверждает событие `TripException`.
3. Routing Engine сохраняет новую `RoutePlanVersion` и ETA.
4. Политика `CustomerVisibilityPolicy` решает, что можно показать клиенту и требуется ли согласование.
5. `ShipmentTrackingProjector` обновляет customer-visible status/timeline и `TrackingSnapshot` с версией.
6. `NotificationOutbox` отправляет событие один раз на подтверждённый канал (at-least-once технически, dedup по semantic key).
7. Если клиент должен согласовать изменение договорного срока/адреса/цены, запрос на approval остаётся отдельным процессом. Визуальное уведомление не означает согласие.

## 7. Предлагаемые доменные структуры и API

Сущности:
- `ShipmentMilestone` (canonical event, owner, source, actual/planned, event_time);
- `TrackingSnapshot` (tenant_id, shipment_id, version, derived status, ETA, safe location visibility, events watermark);
- `CustomerVisibilityPolicy` (per tenant/account/contract/shipment field and geometry policies);
- `TrackingAccessGrant` (account/member or hashed external share token, scopes, expiry, revoked_at);
- `TrackingSubscription` (channel, verified recipient, event types, opt-in, language);
- `TrackingNotification` (event dedupe id, template/version, delivery state);
- `TrackingException` (client-safe category, severity, approved message);
- `TrackingDocument` (linked proof, checksum, access category).

Draft API contracts (versioning and rights to be validated):
- `GET /api/v1/customer/shipments` — only authorized list.
- `GET /api/v1/customer/shipments/{id}/tracking` — derived status + ETA + permitted location.
- `GET /api/v1/customer/shipments/{id}/timeline` — authorized milestones.
- `GET /api/v1/customer/shipments/{id}/documents` — authorized document list.
- `POST /api/v1/customer/shipments/{id}/subscriptions` — verified notification prefs.
- `GET /api/v1/customer/shipments/{id}/events` — SSE authenticated stream, alternative polling.
- `GET /track/{token}` — optional, narrow, expiring guest view; no raw token in logs/analytics.

All commands use authenticated tenant membership and/or scoped external grant. No arbitrary `tenant_id` field from customer-supplied request authorizes access. SSE/WebSocket renew auth, verify rights on reconnect, handle revocation and never stream events of another tenant.

## 8. Архитектура и реализация Java/Spring Boot

`ShipmentTrackingProjector` consumes events from `Orders`, `Shipments`, `Trip`, `Warehouse`, `Rescue` and `POD` through durable transactional outbox/inbox. Idempotent projection stores last processed event and aggregate_version, tolerates out-of-order delivery through ordering/rebuild strategy, and avoids claiming live data without source timestamps.

`tracking-api` serves normalized `TrackingSnapshot` from PostgreSQL. `Redis` can cache tenant/permission-scoped recent snapshots; never cache public URL token authority incorrectly. SSE/WebSocket optional; MVP can poll with conditional requests/ETag to reduce load. Notification worker is isolated and rate-limited; payload follows field policy. `RustFS/S3` stores POD/documents behind authorized broker/expiring signed URL.

Strong isolation point: tracking projection is owned by the shipment's authorized parties and may include fields derived from another tenant's private Trip **only under explicit collaboration grants**. Physical GPS provider must not bypass field policy.

## 9. Customer UX: pages

- **My Shipments:** filters (all/new/in transit/exception/delivered), order references, ETA freshness, account, origin/destination.
- **Shipment Detail:** milestone timeline, approved route checkpoints, ETA band, last update; map only when allowed and data fresh.
- **Exceptions:** delay, reason class, next expected update, contact/approval action.
- **Documents:** shipping note, handover records, POD, claims/quality discrepancy where authorized.
- **Notifications:** email/SMS/push preferences; verified contact channels; no broad public sharing by default.
- **Mobile-friendly link:** QR/URL for authorized recipient with minimal data and expiry.

Localization KZ/RU/EN for statuses, timezone-aware time representation and accessibility. Customer must not need fleet telematics expertise to read the statuses.

## 10. Simulated user scenarios

**TRK-01: normal delivery** — CONFIRMED → PICKED_UP → IN_TRANSIT → OUT_FOR_DELIVERY → DELIVERED + POD.

**TRK-02: partial delivery** — 2 of 3 CargoUnits delivered; `PARTIALLY_DELIVERED` not `DELIVERED`.

**TRK-03: breakdown rescue** — truck A stopped; `RECOVERY_IN_PROGRESS`, then confirmed cargo handover, truck B receives cargo, original ShipmentID and history preserved. No disclosure of all other loads of truck B.

**TRK-04: warehouse transfer** — shipment AT_HUB while at Warehouse D; vehicle A leaves, new leg begins on truck C; client must not follow empty truck A.

**TRK-05: stale telematics** — GPS 15 minutes old, ETA uncertainty widened, client sees stale label and last known checkpoint.

**TRK-06: partner without GPS** — only confirmed milestones and conservative ETA; no invented map pin.

**TRK-07: delayed arrival** — ETA change propagates, reason category and consent request where contractual commitment changed.

**TRK-08: cargo quality hold** — cargo reaches warehouse but is held; no false “delivery completed”.

**TRK-09: canceled order** — tracker shows cancellation and status closure policy, no public GPS exposure after it.

## 11. Acceptance / adversarial tests

1. Two tenants have the same order number: cross-tenant tracking cannot leak through direct ID, search, link, SSE, cache, document URL or notification.
2. Shipper's access revoked -> future API/stream/file attempts denied.
3. Guest link expired/revoked/brute-forced -> no data; token absent in logs/referrer/analytics.
4. Carrier's truck carries two customers' shipments -> each sees only their cargo, not other customers, stops or pricing.
5. Cargo unloaded at hub while truck continues -> tracker no longer associates shipment with former truck.
6. After vehicle rescue, milestone history preserved and new vehicle visibility only after custody transfer.
7. Duplicated/out-of-order GPS/events do not regress status or create duplicate notifications.
8. No GPS / stale data is labeled; no fake live map.
9. Partial POD cannot mark all cargo delivered.
10. Incidents, cancellations and holds do not disappear when ETA is recalculated.
11. Customer cannot edit dispatcher route or partner price; can initiate authorized approval/request.
12. One tenant's pricing, customer contracts and drivers' personal data never appear in client-visible payloads.
13. On-Prem partner sync delay visible with updated_at; later sync reconstructs event order.
14. High-volume SSE reconnect and polling obey tenant quotas and do not overload route provider.
15. Tracking documents download respects tenant and field-level grants even through expiring URL.
16. KZ/RU/EN, timezones and source timestamps render correctly across browser/mobile.
17. Notifications have opt-in/consent and idempotent dedup; no other client's references in messages.
18. Status derived from confirmed cargo custody, never just geofence or vehicle ETA.

## 12. MVP и этапы

**P0 MVP:** customer portal authenticated, shipper order list, shipment timeline, ETA with freshness, basic exception label, authorized POD, responsive mobile page, polling; basic cross-tenant grant tests. Ability to track shipment without GPS via events is mandatory.

**P1:** optional scoped expiring links, map with location privacy and stale indicators, event notifications, partial deliveries, warehouse and rescue projections, support tickets and approvals.

**P2:** SSE/WebSocket, personalized milestones/notifications, temperature/condition events, multimodal timeline and detailed confidence bands; analytics and SLA reporting.

**P3:** proactive ML ETA warnings, customer-configurable webhooks/EDI, white-label tracking portals, dedicated/On-Prem federation with explicit event contracts.

## 13. Open decisions

1. Will a shipper always have an account or must no-login shipment links be provided to recipients?
2. What exact location precision may be disclosed at which stage and to which customer?
3. Should subcontractor name/vehicle plate/driver contact be visible? Default no; contract/policy governs.
4. Does tracking show finance/document closing or only physical delivery for each client role?
5. How long are location, timeline and document data retained?
6. Which notification channels must be supported in Kazakhstan pilot, and who pays for SMS costs?
7. Can recipient request delivery rescheduling through portal, and whose approval is binding?

**Recommendation:** MVP shipping status + confirmed milestones + ETA freshness. Map and public link are valuable, but should not be prerequisites for a reliable first release.

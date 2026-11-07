# 11 — Commercial & Execution v1: Acceptance, Test Matrix & Simulation

**Статус:** TEST PLAN / DRAFT · **Дата:** 07.11.2026. Ни один тест из этого файла не выполнялся.  
**Контракты:** [Lifecycle v1](10-commercial-execution-lifecycle-v1.md) и [Machine-readable transitions](contracts/commercial-execution-lifecycle.v1.json).

## 1. Цели

Доказать, что на одном заказе можно воспроизвести:
- согласование обязательств между грузовладельцем, экспедитором и перевозчиком;
- подтверждение ресурса без двойного бронирования;
- перевозку и доказанную передачу конкретных грузовых единиц;
- документальное и финансовое закрытие отдельно от физического;
- безопасные отказы и компенсации на всех этапах;
- изоляцию двух tenants и межкомпанийный scoped access.

Успех mock E2E не заменяет реальный provider smoke и нормативную квалификацию.

## 2. Пример сквозного сценария LFC-001

**Данные — синтетические:** экспедитор `Tenant-A`, грузовладелец `Tenant-B`, подрядчик `Tenant-C`; доставка `Almaty → Astana`, 10 паллет обычного груза, 8 000 кг, согласованный срок. Цены приведены только для арифметической проверки, не являются рыночными.

| Шаг | Команда и источник | Ожидаемые состояния | Доказательство |
|---|---|---|---|
| 1 | Customer submits RFQ | RFQ: `SUBMITTED` | actor, tenant, cargo and route |
| 2 | Expeditor validates | RFQ: `QUALIFIED` | critical cargo/vehicle fields completed |
| 3 | Expeditor issues quote at 620 000 KZT | QuoteVersion: `ISSUED` | snapshot, expiry, currency, approved conditions |
| 4 | Customer accepts exact version | QuoteVersion: `ACCEPTED` | acceptance evidence + version |
| 5 | Supplier offers 430 000 KZT | CarrierOffer: `OFFERED` | supplier terms, expiry |
| 6 | Expeditor selects supplier | CarrierOffer: `SELECTED` | procurement choice, NOT capacity confirmation |
| 7 | Planner holds then confirms vehicle | Reservation: `HELD → CONFIRMED` | no conflict, partner ack, active compliance |
| 8 | Booking confirm | Booking: `CONFIRMED` | accepted terms + confirmed resources |
| 9 | Driver starts trip; pickup signed | Trip: `STARTED`; Shipment: `IN_CUSTODY` | two separate event types |
| 10 | Tracking shows progress | `IN_TRANSIT` derived milestone | not necessarily live GPS; freshness explicit |
| 11 | Consignee receives all cargo | DeliveryAttempt: `ACCEPTED`; Shipment: `DELIVERED` | 10/10 CargoUnit, POD |
| 12 | Documents checked | DocumentPackage: `COMPLETE` | mandatory evidence, signatures |
| 13 | Invoice issued, receivable created | Invoice: `ISSUED`; Receivable: `OPEN` | finance refs, due date |
| 14 | Customer pays verified amount | Receivable: `SETTLED` | matched cash allocation |
| 15 | Supplier invoice approved and paid | Payable: `SETTLED` | separately approved/allocated |
| 16 | Order closing | derived operational/financial closure | audit, claims/adjustments policy |

**Экономика (условная):** 620 000 KZT клиенту − 430 000 KZT подрядчику − 65 000 KZT дополнительных ожидаемых затрат = 125 000 KZT ожидаемой прямой разницы до других расходов/налогов/претензий. Предоплата 50% подрядчику = 215 000 KZT; положительная ожидаемая маржа **не** гарантирует положительный cash flow.

## 3. Негативные и adversarial тесты

| ID | Сценарий | Ожидаемый результат | Приоритет |
|---|---|---|---|
| LFC-002 | RFQ без веса/опасности/адреса погрузки | NEEDS_INFO; нет binding Quote | P0 |
| LFC-003 | Quote истёк в момент акцепта | optimistic/atomic check, `EXPIRED`, акцепт отвергнут | P0 |
| LFC-004 | Клиент принимает прошлую quote version | REJECT/409, новая версия и явный consent | P0 |
| LFC-005 | Есть Accepted Quote, нет машины | Booking `RESOURCE_PENDING`, клиент не видит confirmed | P0 |
| LFC-006 | CarrierOffer selected, партнёр отказался | Capacity не подтверждается, supplier exception; поиск нового | P0 |
| LFC-007 | Два диспетчера держат один truck/time window | Только один HELD/CONFIRMED, второй conflict | P0 |
| LFC-008 | Подмена `tenantId` в HTTP/асинхронном событии | DENY, аудит, нет чужих цен/ресурсов | P0 |
| LFC-009 | Нет разрешённой совместимости грузов | Trip READY запрещён; NEEDS_REVIEW/DENY | P0 |
| LFC-010 | Загрузили 12 т вместо заявленных 10 т | Hold/reassess/cargo+contract amendment; old Quote immutable | P0 |
| LFC-011 | Trip started, водитель не подтвердил Pickup | Shipment всё ещё READY_FOR_PICKUP | P0 |
| LFC-012 | GPS в точке доставки, POD отсутствует | Не DELIVERY_ACCEPTED, Shipment не DELIVERED | P0 |
| LFC-013 | 8 из 10 паллет подтверждены | PARTIAL; 2 units unresolved, no full delivered | P0 |
| LFC-014 | Повторный offline POD 5 раз | Ровно один факт приёмки/аллокации quantity | P0 |
| LFC-015 | Груз в складском или customs HOLD | Нет release/dispatch, даже если клиент просит | P0 |
| LFC-016 | Vehicle breakdown + rescue | Old Trip INTERRUPTED, new Leg/Trip; Shipment ID и custody сохраняются | P1 |
| LFC-017 | Подрядчику открыли доступ к Shipment | Только его работа и условия, не sales rate/маржа | P0 |
| LFC-018 | Booking cancelled до старта | Release reservation + cancellation charge policy; no ghost trip | P0 |
| LFC-019 | Прекращение Booking после Trip STARTED | TERMINATED_WITH_EXCEPTION + cargo disposition, не обычный CANCELLED | P0 |
| LFC-020 | POD доставлено, акт не подписан | Shipment delivered, DocPackage not COMPLETE, finance close blocked | P0 |
| LFC-021 | Клиент оплатил 50% | Receivable PARTIALLY_SETTLED, outstanding balance and due date | P0 |
| LFC-022 | Повторное банковское событие | Только одна PaymentAllocation | P0 |
| LFC-023 | Подрядчик предъявил спорный surcharge | Payable APPROVAL_REQUIRED/Dispute, не автовыплата | P0 |
| LFC-024 | Клиент не заплатил 30 дней | AR OVERDUE flag; shipment remains delivered | P0 |
| LFC-025 | Предоплата подрядчику до перевозки | Advance recorded, Payable settlement and service fact separate | P0 |
| LFC-026 | Изменение стоимости курса/налога после quote | Original snapshot reproducible; revision requires new version | P0 |
| LFC-027 | DocumentPackage REJECTED, повторная подача | Revised documents, immutable audit, reviewed package | P0 |
| LFC-028 | Кредит-нота на выпущенный invoice | Original invoice immutable, adjustment linked, AR balance recomputed | P1 |
| LFC-029 | Late out-of-order event после delivered | No state regression; reconciliation/audit event | P0 |
| LFC-030 | Disconnect Cloud↔On-Prem during carrier confirm | No false confirmed Booking; retry/status sync | P1 |
| LFC-031 | Customer tracking external link revoked | Deny timeline/documents, event stream stops | P1 |
| LFC-032 | Same CargoUnit attached to two active custody holders | Reject or reconciliation; no silent duplicate | P0 |
| LFC-033 | Payment initiated by dispatcher without finance right | DENY before ledger change | P0 |
| LFC-034 | Клиент отменил заказ после pickup | Exception/return, no direct terminal cancel | P0 |
| LFC-035 | Partial delivered + remaining returned | Per-unit reconciliation, correct aggregate final disposition | P0 |
| LFC-036 | Same idempotency key with altered payload | 409, no second effect | P0 |

## 4. Property-based invariants

1. **Resource exclusion:** for an indivisible vehicle/driver/trailer capacity slot, overlapping confirmed reservations must be ≤1 unless approved shared-load configuration explicitly supports it.
2. **Cargo conservation:** for each identified CargoUnit quantity, pickup quantity must equal sum of currently held, accepted delivered, returned and incident-disposed quantities (with verified corrections), never negative.
3. **No premature delivery:** `Shipment.DELIVERED` implies validated POD/custody evidence for all mandatory units; GPS-only evidence never satisfies it.
4. **Money precision:** `sum(confirmed allocations) + outstanding = adjusted due` per currency/ledger; duplicates do not change sum.
5. **Price integrity:** a CustomerQuoteVersion after ISSUED cannot be mutated in-place.
6. **Tenant safety:** every command, event handler, cached read and file request uses verified tenant/party resource scope.
7. **State monotonicity:** late events do not regress recognized states; corrective business facts create new versions/compensations.
8. **Legality:** DENY or critical UNKNOWN cannot be transformed into route/cargo approved status without valid applicable legal resolution.
9. **Document truth:** PACKAGE.COMPLETE requires required checklist with verified evidence; no upload-only automatic complete.
10. **Closure truth:** operationalComplete, documentComplete, invoiceIssued, paid and financiallyClosed remain independent.

## 5. Test data and pipeline

- Two independent tenants, one shipper and one carrier, optionally warehouse and 3PL.
- 20 synthetic Orders with repeated customer reference numbers and intentionally clashing capacity.
- Two vehicles (one specialized/incompatible), 10 identified CargoUnits, route plans, loading and custody events.
- Quote versions with expiry boundary; sample advance, due date, partial payment and disputed surcharge.
- PostgreSQL Testcontainers with RLS; transactional outbox and inbox replay.
- Unit state-transition tests generated from JSON candidate contract; invariant/guard tests must use **production code** once available.
- REST/GraphQL (if chosen) contract tests, async eventual consistency, WebSocket/SSE privacy and signed document access.
- E2E on exact Git SHA with backend database and real or explicit mock provider; check Cloud and supported Enterprise profile.
- Store evidence: `requirementId, LFC-testId, branch, sha, date, runtime profile, logs, test result, reviewer`.

## 6. Business acceptance workshop

Рекомендуемые участники: экспедитор, логист, диспетчер, представитель перевозчика, бухгалтер/финконтролёр, юрист по транспортным договорам и архитектор безопасности.

На встрече разобрать по ролям:
1. Кто в конкретном договоре принимает цену и право на субподряд?
2. Когда заказчик слышит слова «машина подтверждена»?
3. Кто имеет право принять груз и какой POD допустим в КЗ?
4. Когда можно выставить счёт, какие документы и когда считается долг?
5. Когда можно закрыть сделку с недовозом, возвратом или открытой претензией?
6. Кто подтверждает банковский платёж и кому принадлежит финансовая книга?
7. Как действовать при перегрузке, сорванном рейсе, таможенном HOLD?
8. Какие поля видит заказчик, перевозчик, склад в каждом шаге?

**Критерий принятия документа:** задокументированные владельцы, согласованные статусы/guards/ответственность, signed-off сценарии R0 и подтверждённые исключения. До этого `Commercial & Execution Lifecycle v1` остаётся **PROPOSED**, не ACCEPTED.

**Связи:** [Requirements](04-requirements-traceability.md), [MVP](05-mvp-qualification.md), [Operations scenario](../idea/17-forwarder-dispatcher-day-simulation.md).

# 10 — Commercial & Execution Lifecycle v1

**Статус:** PROPOSED / business-review required · **Версия контракта:** 1.0 · **Дата:** 07.11.2026.  
**Назначение:** единая модель коммерческого, операционного, документального и финансового жизненных циклов для KERUENIX.  
**Машинно-читаемая нормативная часть проекта:** [contracts/commercial-execution-lifecycle.v1.json](contracts/commercial-execution-lifecycle.v1.json).  
**Приёмка:** [11 — Acceptance & Simulation](11-commercial-execution-acceptance-v1.md).

> Это проектная спецификация, а не утверждённое юридическое/бухгалтерское правило и не реализованный backend. Договорные последствия и финансовые документы должны быть проверены юристом и финансистом пилотного клиента.

## 1. Зачем нужен этот документ

Логистическая компания не продаёт «точку на карте». Она принимает коммерческое обязательство, проверяет возможность доставки, резервирует транспорт, перемещает конкретные грузовые единицы, получает доказательства выполнения, выставляет/принимает документы и рассчитывается с заказчиком и подрядчиком. Это **не один enum статусов**.

### Каноническая модель

```text
  Customer RFQ → Customer QuoteVersion → Customer acceptance
                               │                     │
  Carrier request → CarrierOffer│                     ▼
                     │         └────────────→ Booking (resource pending)
                     ▼                              │
               CapacityReservation ←────────── Resource confirmation
                     │                              │
                     └────────→ Booking(CONFIRMED) ─┘
                                      │
                        Trip / TransportLeg / Shipment
                                      │
            Pickup/Custody → DeliveryAttempt/POD
                                      │
                      DocumentPackageVersion
                                      │
               Invoice / Receivable / Payable / Payments
                                      │
                       Operational & financial close
```

Схема показывает связи, а не строгую синхронную последовательность: водитель может ещё ехать, когда уже возникли аванс и payable; документы, оплата, инциденты и претензии могут идти параллельно. **Customer Quote accepted** не равно **Carrier confirmed** и не равно **CapacityReservation confirmed**.

## 2. Четыре независимые границы ответственности

| Граница | Контур | Источник истины | Запрещённая подмена |
|---|---|---|---|
| Коммерческое обещание | RFQ / QuoteVersion / Order terms | Версия подписанных/принятых условий | Прайс провайдера не заменяет договор |
| Физическое исполнение | Booking / Trip / Shipment / TransportLeg / Custody | Подтверждённые ресурсные и грузовые события | GPS/ETA не заменяет принятие груза |
| Документы | DocumentPackage / DeliveryEvidence / POD | Проверенные исходные документы, их версии и подписи | Фото/QR не означает юридическую комплектность |
| Денежные обязательства | Invoice / Receivable / Payable / PaymentAllocation | ERP или локальный финансовый реестр, указанный в политике | Доставка не равна оплате, маржа не равна cash balance |

`Order` связывает эти контуры и показывает агрегированную бизнес-картину. `Order.customerStatus` и `Order.progress` — **производные проекции**, не авторитетная глобальная state machine.

## 3. State machines v1 — канонические состояния

Каждый агрегат имеет свою версию, tenant scope, действия и события. Разрешённые переходы полностью перечислены в JSON-контракте.

### 3.1. RFQ — Request for Quotation

`DRAFT → SUBMITTED ⇄ NEEDS_INFO → QUALIFIED → CLOSED_QUOTED`, альтернативно `REJECTED` / `CANCELLED`.

- `DRAFT`: клиент заполняет предварительную заявку.
- `SUBMITTED`: заявка отправлена экспедитору.
- `NEEDS_INFO`: требуются уточнения (груз, масса, дата, адрес, температурный режим, разрешения).
- `QUALIFIED`: получены данные, достаточные для указанного класса операции и правила расчёта.
- `CLOSED_QUOTED`: создана как минимум одна выпущенная версия предложения; наличие новых версий дальше не переписывает RFQ.
- `REJECTED/CANCELLED`: причина, актор и время сохраняются.

**Guard:** без достаточных свойств груза, способа погрузки, маршрута и обязательных документов нельзя выдавать ложное `Binding Quote`. При недостающих второстепенных данных допускается `INDICATIVE` с явно обозначенными допущениями и отсутствием гарантии.

### 3.2. Customer QuoteVersion — предложение экспедитора клиенту

`DRAFT → [INTERNAL_REVIEW] → ISSUED → ACCEPTED | DECLINED | EXPIRED | SUPERSEDED | WITHDRAWN`.

- Содержит `quoteId + versionId`, currency, налоги/оговорки, service scope, cargo snapshot, customer commitment, expected delivery window, assumptions, rate cards, versioned cost estimate, expiration и approval policy.
- Поля после `ISSUED` не изменяются. Для изменения веса, погрузки, адреса, стоимости, срока или существенных условий создаётся новый QuoteVersion.
- `INTERNAL_REVIEW` требуется при превышении ценового/кредитного лимита полномочий.
- `ACCEPTED` подтверждает коммерческое согласие с **конкретной** версией. Если обещание обусловлено подтверждением машины, это обязательно записано в тексте условий; без такого положения юридический риск требуется рассмотреть отдельно.
- `EXPIRED` не может стать `ACCEPTED` без новой версии. Конкурентный акцепт и истечение должны проверяться атомарно.

### 3.3. CarrierOffer — предложение стороннего перевозчика

`REQUESTED → OFFERED → SELECTED | REJECTED | EXPIRED | WITHDRAWN` либо `DECLINED` ещё на запросе.

- Отдельно хранит доступную перевозчиком машину/комбинацию, действительность тарифа, окно подачи, требуемое оборудование, условия предоплаты, страховку, срок оферты и источник подтверждения.
- `SELECTED` означает **выбор для последующего резервирования**, а не заключённый договор или фактическое присутствие грузовика.
- Для собственного транспорта CarrierOffer необязателен — применяется собственная CapacityReservation.
- При неподтверждённых документах, разрешениях или опасной категории не переходить к `SELECTED` без соответствующего compliance approval.

### 3.4. CapacityReservation — ресурсный резерв

`REQUESTED → HELD → CONFIRMED → CONSUMED`; альтернативы `REJECTED`, `RELEASED`, `EXPIRED`.

- `HELD`: временное, атомарно эксклюзивное удержание ресурса на интервал.
- `CONFIRMED`: владелец транспорта/ответственный подтвердил наличие ресурса и выполнение установленных условий.
- `CONSUMED`: связанный Trip стартовал; резерв не «свободен» после начала рейса.
- Время истечения применяется к `HELD`; `CONFIRMED` нельзя освобождать без проверки, не стартовал ли рейс.
- Конкурирующие бронирования одной машины/водителя/прицепа на пересекающиеся периоды: **строго одно подтверждение**; для shared capacity нужны отдельные формализованные правила консолидации.

### 3.5. Booking — согласованное выполнение услуги

`RESOURCE_PENDING → CONFIRMED → IN_EXECUTION → EXECUTION_FINISHED`. Варианты: `CANCELLED` до исполнения, `TERMINATED_WITH_EXCEPTION` при специальном закрытии уже начатого процесса.

`CONFIRMED` возможен только при:
1. `Customer QuoteVersion.ACCEPTED` для действующих условий или иной зафиксированной договорной основе;
2. `CapacityReservation.CONFIRMED` по всем необходимым обязательным ресурсам и положительном подтверждении Carrier/Own Fleet;
3. доступном законном и физически допустимом Cargo/Vehicle/Route configuration;
4. полученных обязательных согласованиях заказчика/экспедитора;
5. актуальном tenant/partner agreement и минимальном комплекте документов, необходимом именно для бронирования.

Если выбранный подрядчик сорвался **до выезда**, ранее подтверждённую Booking нельзя делать видимо «по-прежнему подтверждённой» без фиксации исключения и повторного контроля; создаются `BookingException`, новый резерв и согласование, если изменились договорные условия.

### 3.6. Trip — движение конкретного автомобиля

`PLANNED → ASSIGNED → READY → STARTED → COMPLETED`. Если автомобиль сломался: `STARTED → INTERRUPTED → CLOSED_INTERRUPTED`, затем отдельный `RecoveryCase` и новый Trip/Leg.

- `READY`: проверены машина+прицеп, водитель, груз, габариты, совместимость, документы, окна, маршрут и оборудование.
- `STARTED`: подтверждён фактический старт; возникает факт использования ресурса.
- `COMPLETED`: рейс завершён; **не** означает доставку всех Shipment и финансовый расчёт.
- `INTERRUPTED`: инцидент, текущее место и грузовые единицы, безопасность и необходимые меры.
- Для закрытия прерванного рейса нужен зафиксированный custodian и disposition оставшегося груза.

### 3.7. Shipment — физическая партия

`REGISTERED → READY_FOR_PICKUP → IN_CUSTODY → PARTIALLY_DELIVERED → DELIVERED` либо `RETURNED/CLOSED_WITH_EXCEPTION/CANCELLED` по допустимому сценарию.

- `IN_CUSTODY` включает множество событий `IN_TRANSIT`, `AT_HUB`, `TRANSFER`, `CROSS_DOCK`; это **milestones и TransportLeg**, а не необходимость менять состояние Shipment при каждой перегрузке.
- `PARTIALLY_DELIVERED` означает, что часть единиц принята; оставшиеся не должны считаться доставленными. Можно организовать последующие delivery attempts или возврат/закрытие исключением.
- `RETURNED` — завершённое распоряжение недоставленными единицами; если часть доставлена ранее, это сохраняется на уровне CargoUnit и delivery evidence (агрегатный статус не стирает факт частичной доставки).
- `DELIVERED` возможен только при подтверждении всех обязательных единиц/количеств (или допустимом согласованном договорном изменении объёма).
- Любая передача другой машине/складу создаёт `CustodyHandover` с evidence, а не новую Shipment.
- `CLOSED_WITH_EXCEPTION` требует документированного disposition недоставленных/спорных единиц; претензия может оставаться открытой отдельно.

### 3.8. DeliveryAttempt / POD

`PLANNED → ARRIVED → EVIDENCE_PENDING → ACCEPTED | PARTIAL | REJECTED | DISPUTED`. Спор проходит отдельное разрешение и может завершиться результатом `ACCEPTED/PARTIAL/REJECTED`; `FAILED` означает безуспешную попытку без принятого POD.

- `ARRIVED` — подтверждение прибытия/ручная верификация, **не** доставка.
- В `EVIDENCE_PENDING` проверяются получатель/полномочие, номера и количество CargoUnit, подписи/электронное подтверждение, фото/акт, время и место.
- При `PARTIAL` формируется разница и новая DeliveryAttempt для остатка.
- При `REJECTED/DISPUTED` создаётся Exception/Claim и, при необходимости, ReturnAuthorization.
- После завершённого POD новые претензии не должны бесследно редактировать его — создаются новые версии доказательств/ClaimCase.

### 3.9. DocumentPackageVersion

`OPEN → COLLECTING → REVIEW_PENDING → COMPLETE`; при отказе `REVIEW_PENDING → REJECTED → COLLECTING`.

- Список обязательных документов составляется по стране, виду транспорта, товару, договору, ролям и состоянию.
- `COMPLETE` означает, что **конкретная версия** обязательного пакета проверена уполномоченным лицом; позднее требование/поправка создаёт новую версию.
- Подтверждённый POD не равен пакету бухгалтерских/таможенных документов.
- Неполный пакет влияет на возможность фин.закрытия, а в регулируемой перевозке — на возможность release, если документ обязателен для данной операции.

### 3.10. Invoice, Receivable, Payable и фактические Payments

**Invoice:** `DRAFT → ISSUED` или `VOIDED` (только невыпущенный черновик). Выпущенный документ **не редактируется**; изменения через корректирующие документы, credit note/новую версию по применимым правилам.

**Receivable:** `OPEN → PARTIALLY_SETTLED → SETTLED` или `WRITTEN_OFF` с отдельным finance approval.

**Payable:** `PENDING_VERIFICATION → APPROVAL_REQUIRED/APPROVED → OPEN → PARTIALLY_SETTLED → SETTLED` либо `REJECTED` при проверке.

- `PaymentTransaction`, `PaymentAllocation`, `Advance`, `CreditNote`, `Claim`, `Dispute` — **отдельные объекты/операции**, а не «статусы доставки».
- `OVERDUE` и `DISPUTED` для AR/AP — **ортогональные признаки**, вычисляются по due date и claim; не разрушать основной автомат.
- Платежи сверяются с подтверждённым банковским/учётным фактом; смена `Paid` вручную без доказательства не означает поступившие деньги.
- Сумма проведённых аллокаций не может превышать допустимую непогашенную сумму с учётом подтверждённых корректировок и переплат; валюта, курс, копейки и налоги явно определены.
- **Advance** подрядчику до перевозки не означает, что услуга исполнена; это финансовое обязательство/предоплата с отдельной сверкой.
- В R0 допустим локальный упрощённый финансовый статус с evidence или проверенный ERP adapter; **не требуется создавать всю бухгалтерию**.

## 4. Роли, полномочия и SoD

**Канонический реестр access и approval policies:** [24 — Access Governance v2](24-access-control-tdd-matrix-v2.md), включая `AUTH-COM-001..013` и строгие различия `quote:draft`, `quote:issue`, `quote:approve_exception`, `quote:accept` и `carrier_offer:select`. Полномочия оцениваются с tenant/legal-entity/assignment/PartnerGrant scope, policy limit и Separation of Duties. Это матрица для бизнес-проверки, не утверждённые юридические обязанности.


| Действие | Инициатор | Обязательное право/подтверждение |
|---|---|---|
| Создать/уточнить RFQ | Клиент, sales, экспедитор по полномочию | Own customer/tenant scope |
| Выпустить клиентский Quote | Sales/экспедитор | Commercial policy/finance approval при лимитах |
| Принять Quote | Уполномоченное лицо заказчика | Конкретная неистёкшая версия, доказательство акцепта |
| Выдать CarrierOffer | Перевозчик-партнёр | Partner grant, проверка компании/документов |
| Принять выбор подрядчика | Экспедитор/закупщик | Selection permission; partner не видит клиентскую маржу |
| Зафиксировать CapacityReservation | Fleet planner / подтверждающий перевозчик | Право распоряжаться конкретным ресурсом, атомарная проверка |
| Подтвердить Booking | Booking service / ответственный | Customer acceptance + resource + legal gates |
| Начать Trip/подтвердить Pickup | Водитель/уполномоченный оператор | Assignment + cargo handling evidence + checks |
| Изменить обещанный срок/адрес/цену | Commercial owner + уполномоченный клиент | New version/amendment, не обычный GPS update |
| Подтвердить Delivery/POD | Получатель/уполномоченный агент | Право приёмки, проверенное доказательство |
| Подтвердить документы | Document controller/legal | Document matrix, право просмотра и подписи |
| Согласовать платёж / списание | Finance approver | Разделение инициатора и утверждающего по лимитам |
| Снять customs/quality HOLD | Профильный разрешающий орган/роль | Evidence-based procedure, не dispatcher override |

**Separation of duties:** создатель коммерческого изменения не должен обходить finance approval; инициатор выплаты и её утверждающий — раздельные полномочия по утверждаемому лимиту. Tenant boundary действует в каждом workflow, подписанном событии, webhook и файле.

## 5. Cross-aggregate orchestration и consistency

### Quote → Booking

1. У клиента есть `QuoteVersion.ACCEPTED`.
2. Создаётся `Booking.RESOURCE_PENDING` с теми же `orderId, quoteVersionId, termsHash`.
3. Выбирается собственный resource или `CarrierOffer.SELECTED` и создаётся `CapacityReservation.REQUESTED`.
4. Резерв проходит `HELD → CONFIRMED`; внешний партнёр даёт подтверждение по защищённому каналу.
5. Повторно проверяются контракт, совместимость, документы, лимиты, дата и ресурсный conflict.
6. `Booking.CONFIRMED` + event. До этого клиент видит `Awaiting carrier confirmation`, а не `Confirmed`.
7. Если любой шаг отклонён/истёк — rollback/compensating `release`, поиск нового ресурса или изменение договорного предложения.

**Cross-service:** не обещать распределённую ACID-транзакцию с API перевозчика; saga/process manager + outbox, idempotency and reconciliation. Внутри одного PostgreSQL владельца ресурсов применять транзакционный conditional write/exclusion constraints по интервалам.

### Pickup → Shipment → Customer Tracking

`Trip.STARTED` не переводит `Shipment` в `IN_CUSTODY`: нужен подтверждённый `CargoHandover/Pickup`. Грузы могут идти несколькими Trip и через Hub. Клиент видит статус своего Shipment, разрешённые milestones, ETA и свежесть источника; GPS автомобиля после выгрузки **не** означает перемещение груза.

### Delivery → Documents → Finance → Closure

- `Shipment.DELIVERED` наступает при доказанной доставке; `DeliveryAttempt.ACCEPTED` может относиться лишь к части CargoUnit.
- `DocumentPackageVersion.COMPLETE` оценивается независимо, иногда позже.
- `Invoice.ISSUED` фиксирует документ/обязательство, а `Receivable.SETTLED` — проверенные аллокации платежей.
- `Order.operationalComplete` определяется по disposition всех Shipment и обязательных exceptions.
- `Order.financiallyClosed` требует утверждённой сверки AR/AP, корректировок и claim policy. Если договор допускает закрытие с открытой претензией, отображается исключение и отдельный claim lifecycle.

## 6. Исключения и компенсации

| Case | Что произошло | Разрешённое действие | Что нельзя делать |
|---|---|---|---|
| EX-01 | Клиент отменил RFQ/не принял цену | Cancel/expire quote, сохранить причину | Создать финансовый обязательный заказ без акцепта |
| EX-02 | Перевозчик отказался до выезда | Release reservation, выбрать новую offer/проверить price amendment | Оставить невыполнимое Booking.CONFIRMED |
| EX-03 | Изменился вес/кубатура при погрузке | Cargo discrepancy, compliance + price reapproval | Молча править accepted QuoteVersion |
| EX-04 | Закрытие дороги / GPS stale | New RoutePlanVersion, предупредить клиента, пометить доверие ETA | Обозначить estimated as actual/approved |
| EX-05 | Поломка автомобиля | Incident triage, safe handover, rescue/subcontract approvals | Передать груз до подтверждения полномочий/custody |
| EX-06 | Частичная доставка | Per-unit POD, outstanding balance of units, new attempt/return | Пометить весь Shipment delivered |
| EX-07 | Получатель отказался | DeliveryException + storage/return, approvals | Автоматически возвращать без юридического поручения |
| EX-08 | Документы отклонены | REJECTED → COLLECTING, новую ревизию | Удалять старый подписанный документ |
| EX-09 | От клиента нет оплаты | AR overdue + collection, credit policy | Менять операционный статус доставки |
| EX-10 | Спорный invoice подрядчика | AP approval withheld, Dispute/ClaimCase | Автоматически оплачивать по GPS/счёту |
| EX-11 | Повторный webhook/POD/scanner | Один эффект по идемпотентности и версиям | Дублировать custody/финансовую проводку |
| EX-12 | Таможенный/quality HOLD | Hard block release; документальное подтверждение | Снять блокировку через сервисный backdoor |

**Cancellation после начала рейса** — не просто `Booking.CANCELLED`: требуется `TERMINATED_WITH_EXCEPTION` и документированный disposition груза, компенсация затрат, обязательства перед клиентом и подрядчиком.

## 7. Контракт события и жизненный цикл команд

Каждая команда несёт `tenantContext` (доверенная сессия), `aggregateId`, `expectedVersion`, `idempotencyKey`, `actorId`, `commandId`, `correlationId` и обоснование/evidence при необходимости.

- Не доверять `tenant_id` из произвольного поля HTTP или webhook без проверки партнёрского scope.
- Повтор с тем же idempotency key и тем же payload возвращает сохранённый результат; повтор с другим payload — conflict.
- Переход авторизован только из разрешённого состояния, при выполнении guard и `expectedVersion`; при гонке — `409 CONFLICT` и явное повторное чтение/ручной выбор.
- Audit/outbox event append-only: `eventId, tenantId, aggregateType/id/version, eventType, occurredAt, recordedAt, actor/source, correlationId, causationId, schemaVersion, evidenceRefs`.
- Out-of-order external events не регрессируют Booking/Shipment, а проходят inbox/dedup/reconciliation; возникновение юридически значимого факта требует доверенного источника.
- Event publisher не сообщает клиенту полную финансовую историю или исходный GPS; для клиента создаётся permission-filtered проекция.

### Ключевые доменные события

`RfqSubmitted`, `RfqNeedsClarification`, `RfqQualified`, `CustomerQuoteIssued`, `CustomerQuoteAccepted`, `CarrierOfferSelected`, `CapacityHeld`, `CapacityConfirmed`, `BookingConfirmed`, `TripStarted`, `CargoPickedUp`, `CustodyTransferred`, `TripInterrupted`, `ShipmentPartiallyDelivered`, `ShipmentDelivered`, `PodAccepted`, `DocumentPackageCompleted`, `InvoiceIssued`, `CustomerPaymentAllocated`, `SupplierPayableApproved`, `SupplierPaymentAllocated`.

Названия events — проектные. Договориться о `eventType`, schema/version, causation и partner projection до публикации публичного API.

## 8. R0 vs расширенная платформа

### Release 0 — только необходимый вертикальный процесс

- 2 tenants, own/one external carrier, RFQ, quote version, accept, hold/confirm capacity, booking confirmation, Trip + single Shipment с CargoUnit, pickup custody evidence, simple route/ETA, basic delivery attempt/POD, document checklist, customer Invoice + payment status, supplier cost, closure checklist.
- Аварии/погрузочные расхождения/частичная выдача поддерживаются **как безопасная ветка exceptional flow**, но полноценный автоматический Rescue/claims/ERP не обязателен.
- Допустима ручная финансовая сверка с учётной ссылкой; запрещена фиктивная банковская оплата.
- Опасные/таможенные операции не включаются в пилот без утверждённого regulatory dataset.

### Later releases

Contract negotiation cockpit, сложные скидки и тендеры, consolidated loads, backhaul, Rescue партнёрская сеть, WMS ledger/cross-dock, eCMR/eTIR/KEDEN по официальной интеграции, сложные AR/AP matching и Tribuo ML.

**Не путать:** P0-доменная безопасность обязательна с начала, но P0 не означает полнофункциональный UI для всех будущих модулей в R0.

## 9. Решения, требующие утверждения перед кодом

1. Акцепт `QuoteVersion` влечёт фиксированную обязанность исполнить или условное подтверждение наличия ресурсов? Нужна договорная формулировка.
2. Какие поля RFQ обязательны в каждом грузовом классе и для какого вида маршрута?
3. Кто имеет право изменять цену/срок/адрес и где пределы полномочий без customer approval?
4. Что фактически означает `CarrierOffer.SELECTED` в договорной модели и когда возникает purchase order?
5. Что считается ресурсом: собственная машина, связка тягач+прицеп, водитель, субподрядный лот, слот склада?
6. Какие документы позволяют начать рейс, сдать груз, выставить счёт и закрыть заказ?
7. Какой источник истины у Invoice, Receivable, Payable, Payment? Встроенная упрощённая система или ERP?
8. Как закрывается Shipment при смешанном `частично доставлен + остаток возвращён`? Зафиксировать external customer status и экономическую ответственность.
9. Можно ли закрыть Order с открытой претензией, и при каких делегированных правах?
10. Какие сведения о партнёре/водителе/договоре видит заказчик и получатель?

**Связи:** [Domain](03-domain-lifecycle.md) · [Requirements](04-requirements-traceability.md) · [MVP](05-mvp-qualification.md) · [Gap analysis](../idea/16-system-needs-gap-analysis.md) · [Acceptance](11-commercial-execution-acceptance-v1.md).

# 25 — Business Scenario Book: KERUENIX (pass 2, domain-first)

**Status:** PROPOSED / business workshop and security review required. **Version:** 0.1, 2026-11-07. **Scope:** R0 functional happy paths and adversarial exceptions, plus clearly marked R1 optional flows. **Implementation:** no backend, UI, migrations, tests or CI claimed.

**Why this book exists:** [User Story Book](21-user-story-book.md) owns actor-centred outcomes and stable story IDs. This document owns multi-actor **business narratives** that cut across several stories and domain aggregates, and maps to [Access Governance v2.1](24-access-control-tdd-matrix-v2.md), [Lifecycle v1](10-commercial-execution-lifecycle-v1.md) and [Lifecycle acceptance plan](11-commercial-execution-acceptance-v1.md). Do not invent new aggregate status enums in this book; named transitions are candidates from current lifecycle, subject to business validation.

## A. The real product: three workspaces, one shipment

| Workspace | Who | Their job to be done | What must not be exposed |
|---|---|---|---|
| Customer Portal | External Customer, customer signatory, consignee | RFQ, My RFQs/My Orders, quote decision, scoped tracking/POD, issue, review | Provider margin, supplier buy rate, all other clients' orders/GPS |
| Forwarder Tenant | Tenant Admin, Sales, Approver, Procurement, Planner, Dispatcher, Document Controller, Finance | Incoming RFQs, commercial commitments, sourcing, dispatch, custody/finance closure | Other tenant records; privileged approval if not granted |
| Carrier workspace | Carrier Manager and assigned driver | Scoped carrier offer, capacity acknowledgement, assigned transport and custody evidence | Forwarder sell price, other carriers and unrelated customers |

**Important distinct identities:** External Customer without a paid tenant is a scoped `CustomerAccount` member of an authorized business relationship, not an employee of the forwarding Tenant. A customer with its own `TENANT-B` needs a verified cross-company grant. `SHP` and `EXC` are different personas and permissions. `RCV` can be guest/single delivery-attempt receiver, never receives company-wide scope automatically.

## B. End-to-end business narrative

```text
Provider Tenant onboards CustomerAccount/External Customer
    → EXC submits RFQ; Sales sees Incoming RFQ; requests clarification
    → Commercial creates immutable QuoteVersion; independent approval if exceptional
    → Authorized customer signatory accepts exact unexpired QuoteVersion
    → Procurement requests CarrierOffer; Fleet holds & confirms capacity
    → Booking CONFIRMED (only after all mandatory proofs)
    → Dispatcher assigns Trip; driver records pickup/custody, including offline replay
    → Tracking provides filtered & freshness-aware milestones/ETA
    → Receiver records full/partial/refused POD; exceptions/cargo disposition remain explicit
    → Documents reviewed; Invoice/AR/AP and bank reconciliation independently processed
    → Verified completed service eligible for PRIVATE feedback; open issue/claim independent
```

**No false shortcuts:** `Quote.ACCEPTED ≠ Booking.CONFIRMED`; `CarrierOffer.SELECTED ≠ Capacity.CONFIRMED`; `Trip.STARTED ≠ Shipment.IN_CUSTODY`; `GPS geofence ≠ POD`; `DELIVERED ≠ paid`; `Approved Payable ≠ Bank Settled`.

## C. Scenario catalog (11 scenarios)

| Scenario | Business outcome | Main actors | Gate |
|---|---|---|---|
| `BSC-001` | Первичное подключение клиента к Tenant | TEN → EXC → SAL | R0 |
| `BSC-002` | Внешний RFQ → входящие заявки Tenant → уточнение | EXC → SAL | R0 |
| `BSC-003` | Версионирование Quote, независимое approval и акцепт | SAL → APR → EXC/SHP | R0 |
| `BSC-004` | Закупка перевозчика, capacity hold и подтверждение Booking | PRC → CAR → PLN/DSP | R0 |
| `BSC-005` | Подтверждение pickup и custody в условиях офлайн | DSP → DRV → consignor | R0 |
| `BSC-006` | Мониторинг ETA, задержка и операционное исключение | DSP → EXC | R0 |
| `BSC-007` | Частичная доставка, отказ, повреждение и претензия | DRV → RCV → DSP → EXC | R0 |
| `BSC-008` | Документы, счёт, спорная доплата и реальный расчёт | DOC → FIN → FAP | R0 finance-lite |
| `BSC-009` | Обоснованный отзыв после услуги и реакция Tenant | EXC → SAL | R0 minimal / R1 response |
| `BSC-010` | Отмена, сорванный перевозчик и замена ресурса | EXC → DSP → CAR/PLN | R0 safety |
| `BSC-011` | Изменение прав на фоне операций и безопасное восстановление | TNO/TEN → SUP/Jobs | R0 security |

## BSC-001 — Первичное подключение клиента к Tenant

**Priority:** R0. **Actors:** TEN → EXC → SAL. **Stories:** USB-TEN-005, USB-EXC-001.

**Preconditions:** Tenant-A активен; CustomerOrg-X проверена, представитель приглашён; CustomerOrg-Y не имеет доступа

**Main business flow:**
1. Администратор Tenant-A создаёт ограниченное приглашение конкретному пользователю CustomerOrg-X без роли сотрудника Tenant-A
2. Адресат проходит проверку приглашения, принимает условия доступа, выбирает provider/customer-account scope
3. Клиент видит My RFQs/My Orders только в рамках relationship; Sales видит нового клиента в своём контуре

**Domain state and source-of-truth:** Invitation PENDING → ACCEPTED; customer-account grant ACTIVE; не создаётся provider Membership

**Evidence:** invitation token digest, actor/customerOrg/provider IDs, expiry, acceptance audit

**Alternative/negative flows:** Просроченный токен, другой пользователь, общий email-домен, повторное принятие, отзыв собственных прав

**Proposed acceptance (Given/When/Then business outcomes):**
1. `BSC-001-AC-01` — Given подтверждённый invite, When адресат принимает, Then создан только customer-account grant без provider staff membership
2. `BSC-001-AC-02` — Given CustomerOrg-Y, When пользователь подставляет Order UUID X, Then доступ запрещён без утечки полей/количества
3. `BSC-001-AC-03` — Given invite expired или повторный nonce, When activate, Then отказ или идемпотентное прежнее состояние

**Existing planned security/lifecycle test references:** AUTH-TEN-012, AUTH-EXT-001, AUTH-X-001,015,017. These IDs are *planned*, not green tests.


## BSC-002 — Внешний RFQ → входящие заявки Tenant → уточнение

**Priority:** R0. **Actors:** EXC → SAL. **Stories:** USB-EXC-002, USB-EXC-003, USB-SAL-003, USB-SAL-006.

**Preconditions:** Клиент имеет CUSTOMER_REQUESTER; Tenant-A имеет команду Sales

**Main business flow:**
1. EXC оформляет заявку: маршрут, окна, единицы груза, физические параметры, контакт и особые условия
2. Commercial атомарно фиксирует SUBMITTED RFQ с idempotency key; provider увидит очередь входящих, клиент — My RFQs
3. Уполномоченный Sales назначает ответственного в разрешённом филиале, проверяет обязательные поля
4. При нехватке данных Sales запрашивает уточнение; клиент исправляет и повторно подаёт
5. После валидации RFQ достигает QUALIFIED; следующий шаг — только отдельный QuoteVersion

**Domain state and source-of-truth:** RFQ DRAFT → SUBMITTED → NEEDS_INFO → SUBMITTED/QUALIFIED согласно утверждённым переходам

**Evidence:** cargo snapshot, provider/customer account, actor, idempotency hash, assignment version, qualification reason

**Alternative/negative flows:** Неполный вес/класс, повторный submit, попытка назначить другого филиала, конфликт двух Sales, изменение существенных полей после quote

**Proposed acceptance (Given/When/Then business outcomes):**
1. `BSC-002-AC-01` — Given заполненный RFQ, When клиент повторяет тот же запрос с тем же ключом, Then существует один логический RFQ
2. `BSC-002-AC-02` — Given неуказанный критический грузовой параметр, When Sales проверяет заявку, Then NEEDS_INFO и binding quote невозможен
3. `BSC-002-AC-03` — Given два Sales назначают одного RFQ, When конкурируют expectedVersion, Then один commit, второй conflict без потерянного update
4. `BSC-002-AC-04` — Given CustomerOrg-Y, When читает My RFQs X, Then DENY

**Existing planned security/lifecycle test references:** AUTH-EXT-002,014,015, AUTH-COM-014,018,019, AUTH-X-022,023, LFC-002,036. These IDs are *planned*, not green tests.


## BSC-003 — Версионирование Quote, независимое approval и акцепт

**Priority:** R0. **Actors:** SAL → APR → EXC/SHP. **Stories:** USB-SAL-002, USB-APR-001, USB-APR-002, USB-EXC-004.

**Preconditions:** RFQ QUALIFIED; бизнес-политика ставок и полномочий согласована пилотной компанией

**Main business flow:**
1. Sales создаёт QuoteVersion DRAFT со снапшотом цены, валюты, грузовых условий, окон и срока действия
2. При превышении лимита Commercial направляет точную версию на независимое утверждение, автор не утверждает своё исключение
3. После разрешённого issue формируется immutable ISSUED version с конкретными условиями
4. EXC Viewer может читать версию; только отдельно подтверждённый Customer Signatory вправе принять эту неистёкшую версию
5. Commercial фиксирует ACCEPTED; Booking пока RESOURCE_PENDING, машина ещё не подтверждена

**Domain state and source-of-truth:** QuoteVersion DRAFT → INTERNAL_REVIEW (при необходимости) → ISSUED → ACCEPTED/DECLINED/EXPIRED/SUPERSEDED

**Evidence:** quoteId/versionId, approved amount/currency, who approved, terms hash, expiry, customer acceptance evidence

**Alternative/negative flows:** Самоутверждение, новый адрес/масса, устаревшая версия, expiration race, отзыв предложения, клиента без signatory grant

**Proposed acceptance (Given/When/Then business outcomes):**
1. `BSC-003-AC-01` — Given viewer без signer, When accept quote, Then DENY
2. `BSC-003-AC-02` — Given EXC с signer и актуальной версией, When accept, Then ACCEPTED без Booking.CONFIRMED
3. `BSC-003-AC-03` — Given author=approver для исключения, When approve, Then DENY даже при двух ролях
4. `BSC-003-AC-04` — Given quote expired или SUPERSEDED, When acceptance races expiry, Then только одна допустимая транзакция

**Existing planned security/lifecycle test references:** AUTH-COM-005..008, AUTH-EXT-005..006, AUTH-X-005,006,019,025, LFC-003,004,005,026. These IDs are *planned*, not green tests.


## BSC-004 — Закупка перевозчика, capacity hold и подтверждение Booking

**Priority:** R0. **Actors:** PRC → CAR → PLN/DSP. **Stories:** USB-PRC-001, USB-PRC-002, USB-CAR-001, USB-CAR-002, USB-PLN-002, USB-DSP-001.

**Preconditions:** QuoteVersion ACCEPTED; груз/маршрут и легальность одобрены; проверенный carrier/own-fleet

**Main business flow:**
1. Procurement запрашивает CarrierOffer у допущенного партнёра, скрывая sell price и маржу
2. Carrier Manager OFFERED/DECLINED; экспедитор выбирает подходящий предложенный ресурс
3. Fleet удерживает атомарный HELD по интервалу/оборудованию, проверяет конфликты и совместимость
4. Carrier/own-fleet подтверждает ресурс → CapacityReservation.CONFIRMED
5. Booking через доменный guard проверяет accepted terms, подтверждённые ресурсы, compliance/документы → CONFIRMED

**Domain state and source-of-truth:** CarrierOffer REQUESTED → OFFERED → SELECTED (не резерв); CapacityReservation REQUESTED → HELD → CONFIRMED; Booking RESOURCE_PENDING → CONFIRMED

**Evidence:** supplier offer version, resource/interval, cargo/vehicle compatibility, approvals, reservation id, confirmation ack

**Alternative/negative flows:** CarOffer истёк/отозван, аварийный hold, недоступный водитель, неподходящий кузов, параллельные резервы, отсутствие согласия carrier

**Proposed acceptance (Given/When/Then business outcomes):**
1. `BSC-004-AC-01` — Given CarrierOffer SELECTED, When no valid capacity confirmation, Then Booking remains RESOURCE_PENDING
2. `BSC-004-AC-02` — Given 2 competing holds for exclusive vehicle/time, When concurrent commit, Then ≤1 succeeds
3. `BSC-004-AC-03` — Given compliance DENY/critical UNKNOWN, When booking confirm, Then DENY
4. `BSC-004-AC-04` — Given carrier offer withdrawn before hold, When try booking, Then supplier exception and alternate selection

**Existing planned security/lifecycle test references:** AUTH-COM-009..011, AUTH-FLT-001..002, AUTH-BKG-001, AUTH-X-016, LFC-006,007,009. These IDs are *planned*, not green tests.


## BSC-005 — Подтверждение pickup и custody в условиях офлайн

**Priority:** R0. **Actors:** DSP → DRV → consignor. **Stories:** USB-DSP-001, USB-DRV-001, USB-DRV-002.

**Preconditions:** Booking CONFIRMED; водитель/машина назначены; CargoUnit identities и список погрузки определены

**Main business flow:**
1. Диспетчер назначает рейс и фактического водителя с допустимой конфигурацией
2. Trip проходит PLANNED → ASSIGNED → READY → STARTED; это ещё не pickup
3. Водитель фиксирует фактический груз/количество/состояние, подтверждение передачи и observedAt
4. При отсутствии связи локальная операция сохраняется и повторно передаётся с устойчивым event key
5. Execution фиксирует custody после серверной валидации; клиент получает milestone с правильным временем

**Domain state and source-of-truth:** Trip STARTED отдельно от Shipment IN_CUSTODY; custody ledger по единицам

**Evidence:** CargoUnit IDs/quantities, giver/receiver attestations, observedAt/receivedAt, stable event ID, evidence hash

**Alternative/negative flows:** Отсутствует подтверждение выдающей стороны; дубль offline replay; неверная единица; out-of-order pickup; отменённый водитель

**Proposed acceptance (Given/When/Then business outcomes):**
1. `BSC-005-AC-01` — Given Trip.STARTED but no handover evidence, When external customer views progress, Then pickup not confirmed
2. `BSC-005-AC-02` — Given offline duplicate replay, When connection restores, Then one custody effect
3. `BSC-005-AC-03` — Given wrong driver/units, When upload, Then DENY and incident log

**Existing planned security/lifecycle test references:** AUTH-EXE-001..002, LFC-010,011,029,032. These IDs are *planned*, not green tests.


## BSC-006 — Мониторинг ETA, задержка и операционное исключение

**Priority:** R0. **Actors:** DSP → EXC. **Stories:** USB-DSP-002, USB-DSP-005, USB-EXC-005.

**Preconditions:** Shipment active, provider/customer relationship valid; tracking data can be delayed

**Main business flow:**
1. Tracking получает санкционированные milestones/показания, сохраняет observedAt/receivedAt/source
2. Диспетчер видит последнее наблюдение с age и признаками качества, не выдуманное live GPS
3. При задержке или отклонении создаётся отмеченное оператором исключение и действие для ответственного
4. Клиент видит разрешённый ETA/status и корректный stale indicator; provider internal route, margin and foreign drops hidden

**Domain state and source-of-truth:** Shipment operational truth unchanged by ETA prediction; exception is separate case/milestone

**Evidence:** watermark/freshness, source, last known milestone, alert reason/ack, notification decision

**Alternative/negative flows:** GPS offline 6h, неверный geofence, чужой PartnerGrant отозван, канал уведомлений не работает

**Proposed acceptance (Given/When/Then business outcomes):**
1. `BSC-006-AC-01` — Given stale GPS, When client opens order, Then ETA marked stale or unavailable and not live
2. `BSC-006-AC-02` — Given GPS geofence arrival, When no POD, Then Shipment not DELIVERED
3. `BSC-006-AC-03` — Given revoked customer grant, When stream refreshes, Then deny future protected updates

**Existing planned security/lifecycle test references:** AUTH-EXT-007, AUTH-TRK-001, AUTH-X-007, LFC-012,029,031. These IDs are *planned*, not green tests.


## BSC-007 — Частичная доставка, отказ, повреждение и претензия

**Priority:** R0. **Actors:** DRV → RCV → DSP → EXC. **Stories:** USB-RCV-001, USB-RCV-002, USB-EXC-010.

**Preconditions:** Shipment in custody; delivery attempt bound to authorized recipient

**Main business flow:**
1. Получатель подтверждает идентификаторы единиц, количество, состояние и подписывает доказательства
2. Для 8/10 единиц создаётся DeliveryAttempt.PARTIAL и Shipment.PARTIALLY_DELIVERED, а 2 остатка остаются под custody
3. Непринятые единицы требуют follow-up DeliveryAttempt, возврата или отдельного документированного disposition
4. Клиент вправе заявить damage/claim до или после закрытия доставки; оператор назначает ответственного и фиксирует resolution
5. Подтверждённый POD не редактируется задним числом; корректировки и claim версионируются

**Domain state and source-of-truth:** DeliveryAttempt ACCEPTED/PARTIAL/REJECTED/DISPUTED; Shipment PARTIALLY_DELIVERED, остаток IN_CUSTODY/RETURNED/CLOSED_WITH_EXCEPTION

**Evidence:** quantity reconciliation, POD signer authority, photo/evidence hash, rejection reason, current cargo custodian

**Alternative/negative flows:** 8/10 ошибочно как complete, неизвестный recipient, duplicate POD, несогласованные возвраты, поздняя претензия

**Proposed acceptance (Given/When/Then business outcomes):**
1. `BSC-007-AC-01` — Given 8/10 accepted, When completion command, Then Shipment not DELIVERED
2. `BSC-007-AC-02` — Given recipient not authorized, When POD submit, Then DENY
3. `BSC-007-AC-03` — Given partial POD, When customer reports damage, Then issue created without rewriting signed POD
4. `BSC-007-AC-04` — Given duplicate signature callback, When replay, Then one accepted delivery effect

**Existing planned security/lifecycle test references:** AUTH-EXE-003, AUTH-EXT-016..017, LFC-013,014,015,035. These IDs are *planned*, not green tests.


## BSC-008 — Документы, счёт, спорная доплата и реальный расчёт

**Priority:** R0 finance-lite. **Actors:** DOC → FIN → FAP. **Stories:** USB-DOC-001, USB-DOC-002, USB-FIN-001, USB-FIN-002, USB-FIN-003, USB-FAP-001.

**Preconditions:** Есть verified delivery evidence; договорные условия и финансовые документы доступны уполномоченным

**Main business flow:**
1. Documents собирает требуемый пакет и проводит REVIEW_PENDING → COMPLETE только после проверки
2. Финансист формирует документированный Invoice/AR/AP с версией условий; документация и финансовый статус независимы
3. Поставщик присылает доплату: сумма не применяется автоматически, проверяются согласование и происхождение
4. Финансовый утверждающий санкционирует payable, но одобрение не является фактом банковского перевода
5. Finance сопоставляет подтверждённый bank/ERP reference, учитывает частичные оплаты/авансы и уникальность allocations

**Domain state and source-of-truth:** DocumentPackage COMPLETE; Invoice ISSUED; Receivable OPEN/PARTIALLY_SETTLED/SETTLED; Payable APPROVAL_REQUIRED/APPROVED/OPEN/SETTLED; Payment отдельно

**Evidence:** package version, invoice ref, approved payable request, bank/ERP transaction and allocation IDs, currency/tax

**Alternative/negative flows:** Reject package, disputed surcharge, duplicate bank event, partial settlement, bank outage, customer late payment

**Proposed acceptance (Given/When/Then business outcomes):**
1. `BSC-008-AC-01` — Given delivered Shipment without verified Documents, When finance closes, Then document-complete not implied
2. `BSC-008-AC-02` — Given payable approved but no bank transaction, When UI renders, Then not shown Settled
3. `BSC-008-AC-03` — Given duplicate payment callback, When allocation processed, Then sum unchanged
4. `BSC-008-AC-04` — Given disputed surcharge, When payable approval attempted, Then configured dispute guard blocks automatic payment

**Existing planned security/lifecycle test references:** AUTH-DOC-001, AUTH-FIN-001..004, AUTH-X-024, LFC-021..028. These IDs are *planned*, not green tests.


## BSC-009 — Обоснованный отзыв после услуги и реакция Tenant

**Priority:** R0 minimal / R1 response. **Actors:** EXC → SAL. **Stories:** USB-EXC-006, USB-SAL-005, USB-SAL-004, USB-EXC-013.

**Preconditions:** Delivery service status verified by Execution and eligible for private feedback; customer relationship active

**Main business flow:**
1. Commercial получает trusted evidence о выполненной услуге, выдаёт eligibility с привязкой к booking/customerAccount
2. Уполномоченный customer feedback actor оставляет оценку и необязательное пояснение без доступа к чужим услугам
3. Один логический отзыв по eligible service, уникальный ключ + идемпотентность
4. Provider Sales видит свой private review; ответ или модерация (R1) добавляются отдельно, оригинал не стирается

**Domain state and source-of-truth:** Review eligibility/feedback is own Commercial record; не влияет на POD, Booking, Finance

**Evidence:** completion source/event, author customerAccount, service reference, rating, version, audit

**Alternative/negative flows:** Не завершена услуга, подвязан чужой заказ, повтор, спорная доставка, попытка провайдера редактировать негатив

**Proposed acceptance (Given/When/Then business outcomes):**
1. `BSC-009-AC-01` — Given no verified completion, When review submit, Then DENY
2. `BSC-009-AC-02` — Given eligible completed service, When concurrent same-account submissions, Then one review
3. `BSC-009-AC-03` — Given provider staff, When overwrite customer rating, Then DENY; reply append-only only by permission

**Existing planned security/lifecycle test references:** AUTH-EXT-009,011, AUTH-COM-017, AUTH-X-008,018. These IDs are *planned*, not green tests.


## BSC-010 — Отмена, сорванный перевозчик и замена ресурса

**Priority:** R0 safety. **Actors:** EXC → DSP → CAR/PLN. **Stories:** USB-EXC-009, USB-DSP-003, USB-DSP-004, USB-CAR-002.

**Preconditions:** Accepted quote and Booking may be confirmed or in execution; contract cancellation policy not yet fully signed

**Main business flow:**
1. Клиент отправляет request-only отмену с причиной; это не обновляет Booking автоматически
2. Booking owner проверяет состояние, окно, фактический custody, ответственность/штрафы и необходимые согласования
3. Если поставщик сорвался до старта, Logistics получает supplier exception и пытается заново подобрать/подтвердить capacity
4. Если Trip уже STARTED, простое CANCELLED запрещено: execution exception, возврат/RecoveryCase и финансовое урегулирование

**Domain state and source-of-truth:** Request separate from Booking state; before execution CANCELLED by guard; in execution TERMINATED_WITH_EXCEPTION if allowed

**Evidence:** cancel request, receivedAt, Booking version, resource release/compensation, approvals, replacement proof

**Alternative/negative flows:** Отмена в момент старта, отказ carrier после confirmed, late expiry job, double cancellation, invoice/payment already issued

**Proposed acceptance (Given/When/Then business outcomes):**
1. `BSC-010-AC-01` — Given Booking.CONFIRMED, When EXC sends cancel request, Then Booking remains CONFIRMED until approved decision
2. `BSC-010-AC-02` — Given Trip.STARTED, When try direct Booking.CANCELLED, Then DENY and exception workflow
3. `BSC-010-AC-03` — Given failed carrier before start, When replacement resource not confirmed, Then client cannot see falsely confirmed replacement

**Existing planned security/lifecycle test references:** AUTH-EXT-013, AUTH-BKG-002..003, AUTH-X-020, LFC-005,006,034. These IDs are *planned*, not green tests.


## BSC-011 — Изменение прав на фоне операций и безопасное восстановление

**Priority:** R0 security. **Actors:** TNO/TEN → SUP/Jobs. **Stories:** USB-TEN-001..005, USB-SUP-001.

**Preconditions:** Приглашённый Customer/partner and staff may have active sessions, cache entries and in-flight jobs

**Main business flow:**
1. Tenant Admin отзывает сотруднику роль или точечный CustomerAccount grant в допустимых рамках
2. Обновляется canonical authorization и аудит, сессионные данные перестают разрешать новые действия
3. Сервисные обработчики с отложенным запуском проверяют собственную сервисную область и действующие ограничения, не используют старый user token
4. Support видит только обезличенный job metadata и выполняет разрешённый идемпотентный replay

**Domain state and source-of-truth:** AccessGrant ACTIVE → REVOKED; бизнес Shipment/Booking сами по себе не удаляются

**Evidence:** revoke actor, resource scope, policyVersion, audit, job attempt/event id

**Alternative/negative flows:** Warm Redis cache, presigned URL TTL, потеря worker, Tenancy RLS pool leakage, support inspect denied

**Proposed acceptance (Given/When/Then business outcomes):**
1. `BSC-011-AC-01` — Given revoked grant, When customer makes new protected call, Then DENY despite cache
2. `BSC-011-AC-02` — Given stale job with revoked user delegated action, When executed, Then no stale privilege elevation
3. `BSC-011-AC-03` — Given support role, When read job payload with financial details, Then redacted/denied

**Existing planned security/lifecycle test references:** AUTH-TEN-008..013, AUTH-X-007,009,010,014,027. These IDs are *planned*, not green tests.



## D. Missing business questions and decision log

| ID | Why it matters | Proposed business interview owner | Status |
|---|---|---|---|
| DEC-BSC-01 | Who may issue legally binding quote acceptance on behalf of CustomerOrg without an independent KERUENIX tenant? | Customer executive + legal | OPEN |
| DEC-BSC-02 | Who takes financial responsibility when carrier refuses after customer accepted price but before capacity confirm? | Forwarder commercial + legal | OPEN |
| DEC-BSC-03 | Which cargo/vehicle constraints must block route/assignment vs permit controlled exception? | Compliance + dispatcher | OPEN |
| DEC-BSC-04 | Who must attest pickup/POD, which forms qualify for the pilot corridor and which proofs may be captured offline? | Logistics + consignee + legal | OPEN |
| DEC-BSC-05 | How to calculate charge/compensation for late cancellation and replacement vehicle? | Operations + commercial + finance | OPEN |
| DEC-BSC-06 | Can customer receive review eligibility on partial delivery or active dispute? Standard R0 defaults pending, claims remain possible. | Customer + operations | OPEN |
| DEC-BSC-07 | What bank/ERP evidence is accepted as transaction truth; how to handle advance and overpayment? | Finance + accounting | OPEN |
| DEC-BSC-08 | Does contract require notification SLA, and what happens to the user when SMS/email is not available? | Customer support + legal | OPEN |
| DEC-BSC-09 | How long are POD, review and GPS evidence retained; can users request access/export/delete? | Security/privacy/legal | OPEN |
| DEC-BSC-10 | Can a carrier be granted limited access without its own paid Tenant for R0 pilot? | Carrier business owner + tenancy owner | OPEN |

A scenario is **BUSINESS_REVIEWED** only after actors, preconditions, exception ownership, evidence/tenant visibility and user-visible outcomes have been acknowledged by the relevant business parties. Formal implementation planning additionally requires exact state-machine transition guards, contract field names and test dataset.

## E. TDD derivation plan and minimum qualifying dataset

- Each `BSC-NNN-AC-NN` is a **draft business acceptance**, not an implemented JUnit test. `USB-...` records user benefit; `AUTH-*` proves identity/scope; `LFC-*` proves domain invariants; `TDD-BSC-...` is assigned after business review to actual tests.
- TDD first: quote version/expiry/SoD; cancellation request vs actual booking cancellation; exclusive Fleet capacity hold; custody replay; partial POD cargo conservation; payment allocation idempotency; customer+provider authorization; private eligible review.
- Real PostgreSQL/PostGIS Testcontainers for multi-tenancy RLS and concurrency; Spring Modulith boundary verification; HTTP/JSON and negative field-level assertions; simulation of Redis/network/worker outages.
- Synthetic fixture: Provider Tenant-A with CustomerOrg-X + CustomerOrg-Y (neither own tenant), optional separate Shipper Tenant-B, Carrier Tenant-C, forbidden Tenant-Z; 2 vehicles and one overlapping slot; 10 CargoUnits; two quote versions, one expired, one exception; offline duplicate pickup; 8/10 partial POD and remaining 2 returned; one payable surcharge, advance and duplicate payment reference.
- First vertical acceptance priority: `BSC-001 → BSC-002 → BSC-003 → BSC-004 → BSC-005 → BSC-007 → BSC-008`. Prove one complete safe transport, then add tracking alert/review/recovery depth. No broad role/permissions UI builder in R0.

## F. Scope discipline

This is the **second-pass R0 business story elaboration**, not evidence that 11 workflows have been built. Later Warehouse, Marketplace, Intelligence and executive dashboards remain **R1/R2** and are not prerequisites to the pilot. Permission matrix v2.1 is not automatically expanded by new story proposals: any new endpoint capability requires a scoped policy/test entry after business/security approval. No new business modules, broker, BPM engine or ML platform is introduced here.

## G. Third-pass role simulation and missing variants

[26 — Role/Process Simulation & Gap Audit](26-role-process-simulation-and-gap-audit.md) complements the 11 BSC business narratives with **42** desk walkthroughs, **22** role personas, **33** identified process/policy gaps and a separate [JSON scenario matrix](contracts/role-process-simulation.v1.json). It is NOT evidence of UI/API execution or business approval.

**Critical additional realistic variants:** provider staff captures a phone/email RFQ on behalf of customer but cannot forge customer consent (`SIM-42`); active Shipment/Trip retains safe custody and evidence continuity when SaaS subscription is suspended (`SIM-41`); customer quote decline and company signatory power are distinct; own fleet does not need fake CarrierOffer; physical pickup can fail due mismatched cargo; original custodian cannot be overwritten on driver replacement; receiver missing means failed attempt, not delivered; verified bank facts are different from payment approval.

**Next review:** use [User Story Book v0.7](21-user-story-book.md) with 80 proposed/draft stories. The current [Access Governance v2.1](contracts/access-policy-matrix.v2.json) is **still 67 policies**. Add an `AUTH-*` policy only after the specific business action and legal/security ownership are accepted. The 33 findings are proposed gaps; no new implementation/CI results are claimed.

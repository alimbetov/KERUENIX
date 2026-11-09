# 26 — Role-by-Process Simulation & Coverage Gap Audit

**Date:** 2026-11-07 · **Status:** `DESIGN SIMULATION / NOT EXECUTED` · **Version:** 1.0.
**Machine-readable scenarios:** [contracts/role-process-simulation.v1.json](contracts/role-process-simulation.v1.json).
**Input sources:** [User Story Book v0.7](21-user-story-book.md), [Business Scenario Book](25-business-scenario-book.md), [Access Governance v2.1](24-access-control-tdd-matrix-v2.md), [canonical lifecycle](10-commercial-execution-lifecycle-v1.md), [planned lifecycle acceptance](11-commercial-execution-acceptance-v1.md).

## 1. Executive verdict

**Are all role/process variants covered? NO.** The existing design covers the main economic path (RFQ → Quote → CarrierOffer → capacity → Booking → pickup → POD → finance), but does not yet define every legal authority, operational exception, customer-entry mode, data grant or payment/contract compensation. The risk is **premature implementation**, not merely a small role catalog.

**What was done:** paper-run **42** role scenarios with failure alternatives and expected domain truth; check the participation of **22** role personas; identify **33** candidate gaps with actionable owners and priority; expand User Story Book with **22 newly discovered** stories (20 operational + 2 strategic), bringing the total to **80**; keep **67** existing v2.1 security policies until reviewed — missing permissions are **not implicitly allowed**.

**What was NOT done:** live business-actor interview, Java/Flutter/UI simulation, database transaction, integration, security penetration test, real customer sign-off, financial/legal approval or CI. Passing a paper scenario does not certify correctness. No finite catalog can enumerate every combination; this audit supplies a **risk-prioritized basis for future test design**, not absolute coverage.

## 2. Actors represented — role/process matrix

The role appearing in a scenario proves only its **participation**, not the completeness of its permissions or all workflows.

| Code | Persona | Primary cases | Counterparty cases | Release coverage | Sample |
|---|---|---:|---:|---|---|
| `PSA` | Платформенный супер-администратор | 2 | 0 | R0_MUST, R0_EXCEPTION_RISK | SIM-01, SIM-02 |
| `TNO` | Владелец Tenant | 2 | 2 | R0_MUST, R0_EXCEPTION_RISK | SIM-03, SIM-41 |
| `TEN` | Администратор Tenant | 2 | 3 | R0_MUST, R0_EXCEPTION_RISK, R1 | SIM-04, SIM-34 |
| `EXC` | Внешний клиент | 10 | 9 | R0_MUST, R0_EXCEPTION_RISK, R1 | SIM-06, SIM-07 |
| `SHP` | Грузовладелец со своим Tenant | 1 | 0 | R0_EXCEPTION_RISK | SIM-05 |
| `SAL` | Экспедитор/продажи | 4 | 7 | R0_MUST, R0_EXCEPTION_RISK | SIM-08, SIM-09 |
| `APR` | Согласующий цену | 1 | 0 | R0_MUST | SIM-12 |
| `PRC` | Закупщик перевозки | 1 | 1 | R0_MUST, R0_EXCEPTION_RISK | SIM-15 |
| `CAR` | Представитель перевозчика | 1 | 3 | R0_EXCEPTION_RISK, R0_MUST, R2 | SIM-16 |
| `PLN` | Логист | 2 | 1 | R0_EXCEPTION_RISK, R0_MUST | SIM-17, SIM-18 |
| `DSP` | Диспетчер | 2 | 10 | R0_MUST, R0_EXCEPTION_RISK | SIM-20, SIM-26 |
| `DRV` | Водитель | 3 | 2 | R0_EXCEPTION_RISK, R0_MUST, R1 | SIM-23, SIM-24 |
| `RCV` | Получатель | 2 | 1 | R0_EXCEPTION_RISK, R0_MUST | SIM-27, SIM-28 |
| `DOC` | Контролёр документов | 1 | 0 | R0_MUST | SIM-30 |
| `FIN` | Финансист | 1 | 2 | R0_MUST, R1 | SIM-31 |
| `FAP` | Утверждающий платежи | 1 | 0 | R0_MUST | SIM-32 |
| `SUP` | Поддержка платформы | 1 | 0 | R0_EXCEPTION_RISK | SIM-35 |
| `COM` | Compliance | 1 | 0 | R0_MUST | SIM-19 |
| `WHS` | Склад | 1 | 0 | R1 | SIM-36 |
| `OWN` | Руководство Tenant | 1 | 1 | R1, R2 | SIM-37 |
| `MKT` | Marketplace | 1 | 0 | R2 | SIM-39 |
| `MLS` | ML/Data steward | 1 | 0 | R2 | SIM-40 |

**Identity warning:** these are `user personas`, not automatically granted roles. `EXC` can separately be Viewer, Requester, Signatory, Feedback Author. Provider `TEN` cannot assign platform permissions. Carrier may represent a separate tenant. Assigned driver and delivery receiver do not receive blanket provider membership. SaaS operator is control-plane and cannot directly read company finance/cargo/GPS.

## 3. Simulation catalog — 42 paper walk-throughs

Synthetic participants: **Tenant-A** freight forwarder, CustomerOrg-X and CustomerOrg-Y without subscription, **Tenant-B** shipper with own tenant, **Tenant-C** carrier, **Tenant-Z** forbidden company. Two branches, two overlapping vehicles, **10 cargo units (8 accepted, 2 handled separately)**. All states follow existing domain source ownership; any unreviewed action is treated as proposed.

### R0_MUST — 22 cases

critical R0 acceptance candidate.

| SIM | Actor → counterpart | Process | Correct result | Variant / fault examples |
|---|---|---|---|---|
| `SIM-01` | PSA → TNO | Tenant onboarding and first owner | Verified organization obtains precisely one active invited owner after acceptance | invalid invite; duplicate request; forged platform role |
| `SIM-03` | TNO → TEN | Tenant staff invitation and delegation | Only delegated role sets assigned within legal entity/branch; owner remains protected | self-escalation; last-owner removal; expired invitation |
| `SIM-04` | TEN → EXC | Invite non-tenant external customer | Verified CustomerAccount grant without provider employee Membership | wrong organization; shared email domain; replayed invite |
| `SIM-06` | EXC → SAL | Customer view-only versus requester/signatory/feedback actor | Each capability individually granted and rechecked for exact customer organization | viewer attempts signature; non-signatory accepts; reviewer posts foreign service |
| `SIM-07` | EXC → SAL | RFQ submit, duplicate, missing cargo | One logical SUBMITTED RFQ, customer sees My RFQs and provider sees authorized inbound | duplicate idempotency altered payload; incomplete weight/route; exhausted deadline |
| `SIM-08` | SAL → SAL | Concurrent provider inbox assignment | One responsible assignee under expectedVersion; wrong branch denied | simultaneous assignments; reassignment after employee leave |
| `SIM-09` | SAL → EXC | RFQ needs-info clarification | No binding Quote until required cargo and operating constraints qualified | late amendment after Quote issued; endless clarification; missing safety fields |
| `SIM-11` | SAL → EXC | Within-limit immutable quote issue | Exact immutable issued version with expiry and customer-facing fields only | incorrect currency/tax snapshot; stale prior version |
| `SIM-12` | APR → SAL | Over-limit approval and segregation of duty | Independent approver approves only matching quote version/terms within authority | self-approval through combined roles; quote modified after signoff |
| `SIM-13` | EXC → SAL | Quote decline/expiry/acceptance races | Read-only actor cannot decline/accept; one valid version transition; no Booking confirmation | race at expiry; superseded quote; wrong legal signatory |
| `SIM-14` | EXC → DSP | Accepted terms but no capacity | Customer sees awaiting resource confirmation; no false confirmed booking | notification arrives early; stale capacity hold; failed outbox |
| `SIM-15` | PRC → CAR | Request carrier offer via scoped partnership | Carrier sees only authorized buy-side details; no forwarder customer sell price or margin | carrier without paid tenant; revoked grant; quote rate leak |
| `SIM-18` | PLN → DSP | Double-booking race for same truck/time window | At most one indivisible capacity hold/confirmation despite concurrent commands | overlapping slot; expiry/confirmation race; stale job |
| `SIM-19` | COM → PLN | Compliance critical UNKNOWN or DENY | No ready/confirmed capacity or illegal route auto-allow; independent evidence needed | dangerous cargo; permit expired; manual bypass attempt |
| `SIM-20` | DSP → CAR | Booking confirm after verified capacity and compliance | Confirmed only when commercial/legal/resource facts all valid and authoritative | carrier withdraw; purchase/sales timing mismatch; lost ack |
| `SIM-24` | DRV → DSP | Offline pickup replay and accurate custody ledger | One custody transfer with observedAt/receivedAt; Trip start not pickup | duplicate offline submit; out-of-order event; server crash |
| `SIM-26` | DSP → EXC | Tracking stale GPS and customer projection | ETA freshness explicit; no raw other-customer GPS, GPS alone not delivery | GPS offline; provider disclosure; stale cached grant |
| `SIM-28` | RCV → DRV | 8/10 partial POD and remaining cargo | Delivered only 8; other 2 have custodian and documented disposition/reattempt | mixed damage/return; late POD; duplicate signature |
| `SIM-30` | DOC → EXC | Document verification and authorized POD publication | Versioned evidence review, permitted customer-only release after server authorization | rejected package; stale signed URL; document not yet complete |
| `SIM-31` | FIN → EXC | Invoice, receivable, payable without status collapse | Issued invoice and independent AR/AP, no delivery=paid or approval=settled shortcut | credit note needed; corrected tax; customer partial payment |
| `SIM-32` | FAP → FIN | Payment approval versus bank settlement | Different approver, bank/ERP verified unique allocations and no false settlement | same person initiates/approves; duplicate payment callback; disputed surcharge |
| `SIM-34` | TEN → EXC | Customer self-revocation vs colleague access | Revoke only selected membership, other authorized CustomerOrg users stay active | warm Redis cache; old JWT; signed URL residual TTL |

### R0_EXCEPTION_RISK — 15 cases

R0 safety/exception handling design, scope review required before implementation.

| SIM | Actor → counterpart | Process | Correct result | Variant / fault examples |
|---|---|---|---|---|
| `SIM-02` | PSA → TNO | Lost tenant owner recovery | Recovery only with independent verification, MFA, two distinct approvals and immutable audit | one approver; wrong tenant; last owner disappeared |
| `SIM-05` | SHP → EXC | Customer company owns tenant and also buys transport | Independent B2B PartnerGrant, never implicit membership in provider Tenant | carrier/customer multiple identities; tenant switching; unauthorized foreign provider |
| `SIM-10` | EXC → SAL | Edit submitted RFQ and re-qualification | Material edit creates explicit revision and invalidates stale commercial assumptions | client changes address after accepted quote; stale quote on screen |
| `SIM-16` | CAR → PRC | Offer refusal/withdrawal before resource commitment | No capacity/booking inferred from carrier SELECTED; replacement sourcing audited | offer expiry vs selection; carrier rejection after selected |
| `SIM-17` | PLN → DSP | Own-fleet reservation without CarrierOffer | Own vehicle follows exclusive resource proof and no fabricated external carrier offer | vehicle assigned to another booking; unavailable driver/trailer |
| `SIM-21` | EXC → DSP | Request-only cancellation before departure | Cancellation request recorded; Booking remains until authorized decision and cost rules | double cancel; invoice already issued; approval unavailable |
| `SIM-22` | EXC → DSP | Cancellation after pickup | Cannot directly terminal-CANCELLED Trip in custody; controlled exception/return and financial impact | in-flight carrier; missing custody receiver; active claim |
| `SIM-23` | DRV → DSP | Pickup cargo mismatch and refusal | Pickup cannot confirm wrong units/weight/damage; operator sees exception | mismatched seal; unauthorized substitute driver; unsafe load |
| `SIM-25` | DRV → DSP | Breakdown or mid-trip driver/trailer replacement | Custody explicitly handed over, original leg/driver evidence immutable | breakdown with cargo held; chain-of-custody gap; insurer notice |
| `SIM-27` | RCV → DSP | Receiver absent or refuses to sign | Failed attempt with reason and continued custody; not delivered | receiver unreachable; expired one-time token; wrong representative |
| `SIM-29` | EXC → RCV | POD dispute and claim evidence correction | Append claim/correction, never silently rewrite signed evidence | photo missing; wrong consignee; damage discovered later |
| `SIM-33` | EXC → SAL | Private feedback eligibility and provider visibility | One service-backed private review, no public star rating or self-review | partial/disputed POD; deleted customer membership; repeated rating |
| `SIM-35` | SUP → TEN | Scoped job replay and identity revocation | Redacted job metadata, authorized replay only with active scope and idempotency | crash between effect and ack; admin revoked while worker runs |
| `SIM-41` | TNO → DSP | Subscription suspended during active shipment | No new paid actions by default but active cargo safety, custody evidence, notifications and access to critical POD cannot disappear; exact continuity/retention policy needs contract signoff | tenant subscription expires during Trip.STARTED; invoice overdue while POD pending; platform billing outage |
| `SIM-42` | SAL → EXC | RFQ captured by provider staff from phone/email without customer portal login | Sales may record request with verifiable origin/attribution and notify customer; cannot forge customer signature or pretend acceptance; quote requires separately authorized customer agreement | phone request from unverified caller; duplicate phone/email and portal RFQ; employee tries to accept quote for customer |

### R1 — 3 cases

subsequent operations capability.

| SIM | Actor → counterpart | Process | Correct result | Variant / fault examples |
|---|---|---|---|---|
| `SIM-36` | WHS → DRV | Warehouse transfer/crossdock custody | Stock ledger and custody transfer reconcile per cargo unit and tenant | cross-dock partial; late scan; lost pallet |
| `SIM-37` | OWN → FIN | Executive KPIs and financial/privacy scoping | Only authorized aggregate performance, confidential cost/driver data hidden | branch denied; report from stale projections; wrong customer |
| `SIM-38` | EXC → TEN | Switch customer provider or organization | Explicit authorized relationship selected; one provider cannot read another's data | shared person across orgs; wrong default provider scope |

### R2 — 2 cases

marketplace or intelligence advanced capability.

| SIM | Actor → counterpart | Process | Correct result | Variant / fault examples |
|---|---|---|---|---|
| `SIM-39` | MKT → CAR | Marketplace tender/listing, partner visibility | Only owner can manage listing; moderation and public reputation independently reviewed | anonymous spam; rate leak; fake partner capacity |
| `SIM-40` | MLS → OWN | Intelligence ML dataset permission and lineage | Source lineage/tenant opt-in and point-in-time separation, no cross-tenant training by default | training uses private customer data; leaked GPS; stale ETA label |


**Case model:** every `SIM-*` in the JSON has `primaryRole`, `counterpartyRole`, owner boundary, existing or discovery `USB-*` links, related candidate test IDs, expected domain invariants, adversarial variations and `NOT_EXECUTED` status. Tests must later create exact Given/When/Then for selected cases instead of assuming every listed fault already has an executable check.

## 4. One end-to-end replay as each actor sees it

**Context:** a normal cargo request by CustomerOrg-X to Tenant-A; Tenant-C provides truck. A sequential illustration of 28 role actions. Events between aggregate owners should travel through exported module APIs and reliable event/outbox infrastructure. This is a **conceptual simulation**, not proof the integration already works.

| # | Role | What user does / sees | Authoritative business owner | Evidence / mandatory denial |
|---:|---|---|---|---|
| 01 | PSA | Проверяет Tenant-A и приглашает владельца | SaaS Control/Tenancy | Провизионная заявка / владелец принимает; Не читать финансы Tenant-A |
| 02 | TNO | Назначает TEN и scope филиала | Tenancy | Актор, делегирование, аудит; Нельзя сделать себя platform admin |
| 03 | TEN | Приглашает EXC сотрудника CustomerOrg-X | Tenancy | CustomerAccount grant (не Membership Tenant-A); CustomerOrg-Y не получает доступ |
| 04 | EXC | Заходит в «Мои заявки», создаёт RFQ | Commercial | RFQ SUBMITTED, собственный RFQ ID; Не создавать Booking автоматически |
| 05 | SAL | Видит заявку Tenant-A во входящем окне | Commercial | Очередь по branch/assignee; Скрыть RFQ чужого Tenant |
| 06 | SAL | Запрашивает отсутствующие характеристики груза | Commercial | NEEDS_INFO и причина; Никаких binding условий без данных |
| 07 | EXC | Уточняет массу/окно/адрес | Commercial | Версия/аудит исправления; Старая цена не переносится автоматически |
| 08 | SAL | Выпускает QuoteVersion в пределах полномочий | Commercial | Immutable ISSUED с expiry; Не раскрыть закупочную ставку |
| 09 | APR | При исключительной цене утверждает другую подпись | Commercial | Approval actor≠requester, exact version; Отклонить самоутверждение |
| 10 | EXC-signatory | Акцептует правомочно точную версию | Commercial | QuoteVersion ACCEPTED + доказательство; Это ещё не Booking.CONFIRMED |
| 11 | PRC | Запрашивает CarrierOffer у Tenant-C | Commercial | Только buy-side условия; Нет customer sell price у Carrier |
| 12 | CAR | Подтверждает своё предложение и ресурс | Commercial/Fleet | OFFERED / подтверждённое capacity; SELECTED не означает reservation |
| 13 | PLN | Проверяет габариты, маршрут и условия | Fleet/Cargo/Compliance | Compatibility/Compliance evidence; Critical UNKNOWN не ALLOW |
| 14 | DSP | Удерживает capacity и подтверждает Booking | Fleet/Booking | HELD→CONFIRMED; Booking CONFIRMED; Параллельный booking другого пользователя DENY |
| 15 | DSP | Назначает Trip и водителя | Execution | Trip ASSIGNED/READY; Водителю доступны лишь его Trip |
| 16 | DRV | Начинает рейс, фиксирует pickup отдельно | Execution | CargoUnit evidence, custody; Trip.STARTED не значит IN_CUSTODY |
| 17 | DRV | Повторяет офлайн-операцию после связи | Execution | Один custody event с observedAt/receivedAt; Двойной pickup DENY/dedup |
| 18 | DSP | Получает задержку/старый GPS | Tracking | Freshness flag + exception; Не показывать stale как live |
| 19 | EXC | Открывает «Мой заказ» и ETA | CustomerPortalApi/Tracking | Только свои milestone/POD разрешения; Скрыть чужие остановки, цены carrier |
| 20 | RCV | Принимает 8 из 10 CargoUnit | Execution | DeliveryAttempt.PARTIAL; Shipment не DELIVERED полностью |
| 21 | DRV | Оформляет возврат/повтор доставки 2 единиц | Execution | Custody and disposition evidence; Не терять две единицы |
| 22 | DOC | Проверяет POD и пакет документов | Documents | Versioned COMPLETE или REJECTED; Upload сам по себе не COMPLETE |
| 23 | FIN | Выставляет документы/учётные факты | Finance | Invoice, AR/AP independently; DELIVERED != PAID |
| 24 | FAP | Утверждает payable (иной инициатор) | Finance | Approval snapshot; Approval не банковская выплата |
| 25 | FIN | Сверяет банковский/ERP факт | Finance | Unique allocation/reference; Повторный callback не платёж дважды |
| 26 | EXC | Подаёт претензию/частный отзыв при допустимых условиях | Commercial | Issue отдельно от Review eligibility; Спорная partial доставка не получает авто-публичный rating |
| 27 | TEN | Отзывает доступ конкретного внешнего контактного лица | Tenancy | Revoke membership, audit; Коллеги CustomerOrg остаются авторизованы |
| 28 | SUP | Повторяет разрешённый failed job с redacted metadata | PlatformJobs | Attempt+idempotency+tenant scope; Нельзя читать или менять чужие данные |

**UI reliability acceptance:** the customer must have readable `My RFQs`, `My Orders`, Quote decisions, Tracking (including stale state), Documents/POD, Issues, Feedback. Provider must have `Incoming RFQs` with ownership/assignment, Commercial approvals, active Booking & Trip windows, exceptions, document and finance queues. Carrier must have permitted offer/assigned Trip view, not full Tenant-A customer finance. Every screen requires correct **empty, loading, unauthorized, expired grant, stale data and recoverable error** states; a blank list must not silently masquerade as "no orders" when a backend call failed.

## 5. Gap register: 33 potential under-specified processes

Severity meaning: **BLOCKER** = legal/business/security contract must be decided *before implementing corresponding R0 operation*; **R0-SAFETY** = fail closed and collect evidence in first pilot, not necessarily full automated UI; **R1/R2** = defer unless a concrete pilot forces it. A gap is a **design finding**, not a confirmed production bug.

| Gap | Severity | Missing outcome / actor issue | Proposed correction / evidence owner | Simulations |
|---|---|---|---|---|
| `GAP-01` | BLOCKER | **EXC quote acceptance signatory proof** — Who can legally bind CustomerOrg by QuoteVersion? Portal viewer/requester does not confer signing authority. | Commercial + Legal: Evidence of delegate authority and terms/version receipt; wrong actor DENY | SIM-06,13 |
| `GAP-02` | BLOCKER | **Customer quote decline right** — v2.1 COM-08 covers SHP own-tenant, not EXC scoped rejection. | Commercial + Security: Design customer:quote:decline and immutable reason/state guard; no read→write | SIM-13 |
| `GAP-03` | BLOCKER | **Provider tenant vs customer-owned tenant** — Same person may be Tenant-B shipper and EXC of Tenant-A; account linking must not grant provider membership. | Tenancy + Security: Explicit relationship and resource scoping; Tenant-A/Customer-Y negative tests | SIM-05,38 |
| `GAP-04` | R0-SAFETY | **Sales-assisted telephone/email RFQ** — No confirmed channel for customer without portal, common in real dispatch. | Commercial: Source/identity attestation, dedup and invitation; never simulate customer acceptance | SIM-42 |
| `GAP-05` | BLOCKER | **Tenant subscription restriction during live cargo** — SaaS suspension might strand a driver or hide mandatory POD. | SaaS Control + Legal + Execution: Approved safe-continuity policy for active Booking, cargo custody, evidence and retention | SIM-41 |
| `GAP-06` | R0-SAFETY | **Customer role delegation and offboarding** — Company contact resigns; other customer contacts must retain access. | Tenancy: Separate customer capabilities; targeted revoke; revoke active sessions/short-lived URLs | SIM-04,06,34 |
| `GAP-07` | R0-SAFETY | **Internal inbox handoff** — Unassigned incoming order or absent manager can remain stuck. | Commercial + Ops: Assigned-owner SLA/escalation; expectedVersion and scoped reassignment | SIM-08,09 |
| `GAP-08` | BLOCKER | **RFQ material amendment after issue/acceptance** — Changing cargo/address/time may invalidate pricing or capacity. | Commercial + Booking: No silent edits; versioned revision and renewed approval/acceptance as needed | SIM-09,10 |
| `GAP-09` | BLOCKER | **Carrier acceptance/withdrawal legal effect** — CarrierOffer.SELECTED can be misinterpreted as binding capacity. | Commercial + Carrier + Legal: Define accepted carrier terms, withdraw authority and effective cutoff | SIM-15,16 |
| `GAP-10` | R0-SAFETY | **Carrier without paid tenant** — R0 may rely on partner who has no KERUENIX Tenant. | Tenancy + Procurement: Choose verified constrained portal/one-time confirmation or manual auditable evidence; no guessed acceptance | SIM-15 |
| `GAP-11` | R0-SAFETY | **Own fleet path** — No CarrierOffer needed, but resource confirmation still mandatory. | Fleet + Booking: Same capacity/compatibility/audit guard with own-fleet actor | SIM-17 |
| `GAP-12` | BLOCKER | **Capacity allocation race** — Vehicle + driver + trailer exclusive intervals need DB enforcement. | Fleet: Testcontainers overlapping holds and expiry/confirmation conflict, not Redis-only lock | SIM-18 |
| `GAP-13` | BLOCKER | **Compliance critical UNKNOWN** — An unverified legal restriction must not become a default allow. | Compliance + Legal: DENY/hold until qualified source and approval; no dispatcher override | SIM-19 |
| `GAP-14` | R0-SAFETY | **Pickup mismatch and refusal** — Driver can arrive but cargo weight/seal differs. | Execution + Cargo: Refusal/incident state and exact cargo-unit evidence without phantom custody | SIM-23,24 |
| `GAP-15` | BLOCKER | **Offline event ordering and authority** — Event may arrive after assignment revoke or after newer custody event. | Execution + Security: Separate historical evidence ingestion from authority to mutate; dedup, quarantine and reconciliation | SIM-24,25,35 |
| `GAP-16` | R0-SAFETY | **Driver / vehicle replacement mid-trip** — Cannot simply overwrite original driver or cargo custodian. | Execution + Recovery: Append handover and new trip/leg references with safe custody continuity | SIM-25 |
| `GAP-17` | R0-SAFETY | **Missing consignee and failed attempt** — No signature does not equal delivered and must allow retry/return. | Execution: FAILED attempt with reason, time, continued custody and reattempt disposition | SIM-27 |
| `GAP-18` | BLOCKER | **Partial POD quantity accounting** — Accepted 8/10 while 2 returned must not double count or vanish. | Execution + Documents: Conservation property tests and append-only proof/correction | SIM-28,29 |
| `GAP-19` | R0-SAFETY | **Signature/evidence authenticity** — Guest receiver can mis-sign or receive leaked link. | Execution + Security + Legal: Narrow token, recipient proof, timestamps and immutable evidence; jurisdiction sign-off | SIM-27,29 |
| `GAP-20` | R0-SAFETY | **Document publishing/revocation** — Reviewed package and object-storage URL grants may diverge. | Documents + Security: Versioned verified release; deny at broker/proxy, acknowledge signed-URL TTL exposure | SIM-30,34 |
| `GAP-21` | BLOCKER | **Booking cancellation financial effect** — Customer request != authorized cancellation; effect changes by pickup state. | Booking + Commercial + Finance: Time/state guard, actor, fees, explicit agreement and compensation | SIM-21,22 |
| `GAP-22` | BLOCKER | **Payable approval versus banking truth** — Manual approve or callback could falsely mark cash received. | Finance: Separate approval, bank/ERP verified transaction and idempotent allocations | SIM-31,32 |
| `GAP-23` | R0-SAFETY | **Surcharge and invoice correction** — Supplier extra charge or tax correction may silently rewrite invoice. | Finance + Legal: Do not mutate issued invoice; hold dispute, credit-note in R1 if needed; R0 safe deny | SIM-31,32 |
| `GAP-24` | R0-SAFETY | **Tracking stale and privacy visibility** — Live label could be shown from stale GPS or expose other customers. | Tracking: Watermark, observedAt/receivedAt, field allowlist and revocation-aware cache | SIM-26 |
| `GAP-25` | R0-SAFETY | **Customer issue versus service review** — Customer must report damage before delivery; review is not claim settlement. | Commercial + Execution: Independent issue intake, evidence, owner, follow-up; private feedback eligibility distinct | SIM-29,33 |
| `GAP-26` | R0-SAFETY | **Authorization after job replay and token revoke** — Delayed service job may re-use revoked user context or leak payload. | Jobs + Tenancy: Service principal, resource-specific reauthorization, redacted support, idempotent replay | SIM-34,35 |
| `GAP-27` | R1 | **Multi-provider customer organization selection** — One user participates with multiple provider Tenants. | Tenancy + Portal: Explicit active relationship switch and no cross-provider cache/query leakage | SIM-05,38 |
| `GAP-28` | R1 | **Warehouse cross-dock transfer** — Goods move between custody locations with split scans. | Warehouse + Execution: Ledger + handover per CargoUnit, late event handling | SIM-36 |
| `GAP-29` | R1 | **Executive reporting privacy and profitability** — Aggregated dashboard may leak customer or buy-rate values. | Finance + Read Models: Scoped aggregates, reconciliation watermark, cost permissions | SIM-37 |
| `GAP-30` | R1 | **Consumer notifications and language/consent** — Customer offline, no SMS, multilingual legal terms and wrong recipient. | Customer Portal + Ops: Best-effort notifications, inbox truth, source language snapshot, consent and fallback | SIM-07,26,27 |
| `GAP-31` | R1 | **Data retention / privacy & audits** — POD/photos/reviews/GPS have different access, retention and deletion restrictions. | Security + Legal + Documents: Per-data-type retention, holds, archive/export; no blanket delete of evidence | SIM-30,40 |
| `GAP-32` | R2 | **Public marketplace ratings fraud** — Private verified review should not automatically become public trust signal. | Marketplace + Legal: Independent moderation, complaint/appeal, counterparty verification | SIM-33,39 |
| `GAP-33` | R2 | **ML data lineage and consent** — Sensitive telemetry and customer data should not be pooled across tenants by default. | Intelligence + Security: Verified lineage/tenant grants, point-in-time holdout, no training on unapproved data | SIM-40 |

**Count by category:** `BLOCKER` 12 · `R0-SAFETY` 14 · `R1` 5 · `R2` 2. Many gaps are already partly addressed in other documentation; the deficit is that the specific **end-to-end business acceptance and authorization decision** remains open.

## 6. Have we covered all variants? Coverage matrix and reduction strategy

**No exhaustive claim.** Potential combinations grow multiplicatively across tenants, roles, legal state, cargo, route, resource, time, network and payment. A combinatorial explosion is neither necessary nor affordable for R0. Instead:

| Variant axis | Values to mix | Highest-risk intersection |
|---|---|---|
| Identity | PSA, TenantMember, EXC without tenant, SHP own tenant, carrier, driver, guest receiver | Manual actor permission switch and grant revocation |
| Ownership | provider Tenant-A, CustomerOrg-X/Y, separate Tenant-B/C/Z, branch 1/2 | Same ID guess and cross-organization list/fields |
| RFQ | complete/incomplete, unique/duplicate/changed idempotency key, voice/manual origin | Quote cannot issue on invalid cargo |
| Commercial | within/exceeding limit, issued/expired/superseded, signed/viewer, KZT/other currency | Atomic Quote accept/expiry and SoD |
| Capacity | own fleet vs third-party, overlapping/not overlapping, driver/trailer present/absent | DB exclusion, no false Booking |
| Execution | online/offline, wrong CargoUnit, interrupted trip, driver reassigned | Custody reconciliation/replicated event |
| Receiver/POD | full/partial/failed/refused, confirmed/guest/invalid recipient, damaged/undamaged | No GPS-based delivered, conservation 10/10 |
| Financial | AR/AP, prepayment/partial/full, surcharge/dispute, bank source missing/duplicate | Approval vs settlement and unique allocations |
| Network | normal/retry/timeout/crash/late message, Redis up/down, RustFS URL expired/live | Idempotency, no unscoped fallback |
| Delivery evidence | signed/pending/expired/invalid POD; wrong partner; old signed URL | Read authorization, immutable version and residue TTL |
| SaaS | active/suspended subscription while trip active | Safe continuity/legal policy without silent cargo loss |
| Review | completed/disputed/partial, eligible/not eligible, duplicate, private/public | Private verified-only R0, public marketplace later |

**Required targeted 3-way intersections** to test before R0:
1. `EXC viewer + Tenant-A/CustomerOrg-Y foreign order + warm cache` → DENY, no cross-customer data.
2. `Quote ISSUED/EXPIRED race + customer signatory + stale earlier version` → exactly one admissible transition.
3. `Capacity HELD expiry + two dispatchers + same vehicle/trailer slot` → at most one active exclusive confirmed reservation.
4. `Offline pickup event + driver reassignment + late replay` → no duplicate custody/no privilege bypass; historical evidence quarantined if required.
5. `8/10 POD + remaining 2 returned + signed evidence correction` → cargo-unit conservation and no false delivered.
6. `Payment approved + bank callback duplicate + credit/surcharge dispute` → no false SETTLED and no duplicate allocation.
7. `Subscription suspended + active Trip + missing POD` → explicit safety-continuity policy, no loss of custody/document access.
8. `CarrierOffer SELECTED + external carrier withdraw + customer already accepted Quote` → valid exception/re-sourcing, no false capacity confirmation.

**Test selection:** 100% of critical authorization barriers and domain invariants must be represented in designed tests, not 100% of hypothetical role/state pairs. Use pairwise selection for low-risk parameter combinations; enumerate all credible BLOCKER branches and hand-picked high-risk triples above. Evidence for coverage requires executable tests on exact SHA and business signed acceptance, not an invented pass percentage.

## 7. What should be built and reviewed next

| Gate | Business output | Implementation boundary |
|---|---|---|
| `SIM-G0` | Review actor identity and source-of-truth map, resolve BLOCKER decisions | No new permissions activated |
| `SIM-G1` | Approve `SIM-01/03/04/06/07/08/09/11/12/13` (onboarding + RFQ + quote) | Tenancy/Commercial TDD + PostgreSQL RLS |
| `SIM-G2` | Approve `SIM-15..20` (Carrier/Fleet/Booking) | Capacity SQL constraints, retry/Outbox, Modulith ownership |
| `SIM-G3` | Approve `SIM-23..32` (custody/POD/Docs/Finance) | Cargo-unit ledger, evidence, verified cash |
| `SIM-G4` | Approve `SIM-21/22/33/34/35/41/42` (cancellation/review/revoke/SaaS/manual RFQ) | Exception contracts, fail-closed rules and customer UX |
| `SIM-G5` | Reassess `SIM-36..40` R1/R2 | No premature Warehouse/Marketplace/ML platform |

**Minimum future TDD artifacts:** `TDD-SIM-NNN-{positive,negative,race,replay,tenant}` with Given/When/Then, expected aggregate version, field-level projected JSON, PG/RLS fixture and recovery/assertion. These IDs are **plans**, not existing test classes. Keep `USB`, `BSC`, `AUTH`, `LFC` references stable and add a permission row only for a business-approved command. Prioritize first concrete path:

```text
CustomerAccount invite → EXC RFQ → Tenant Incoming RFQ → clarified data
  → immutable QuoteVersion → independent approval (if needed) → legal accept
  → CarrierOffer / own-fleet → exclusive capacity hold → Booking confirmed
  → assigned Trip → pickup and custody → verified POD → documents
  → AR/AP and actual bank/ERP evidence → private service feedback
```

**Stop rule:** If a scenario requires inventing legal authority, money threshold, retrospective POD edit, a fake Carrier acceptance or cross-tenant data leak, mark `BLOCKED_FOR_BUSINESS_REVIEW` and preserve the underlying facts; do not satisfy it with a mock-positive test.

## 7A. Blocker disposition after the fourth analysis pass

The 12 `BLOCKER` gaps `GAP-01/02/03/05/08/09/12/13/15/18/21/22` now each have explicit fail-closed **proposed technical rules** and decision evidence in [27 — Business Policy Decisions](27-r0-blocker-policy-decisions.md), [machine JSON](contracts/r0-blocker-decisions.v1.json).

**Status distinction:** `DESIGN_SPECIFIED` for all 12; **zero real business/legal stakeholder approvals recorded**. They therefore remain **BLOCKED_FOR_BUSINESS_SIGNOFF** for irreversible legal/financial/customer commitments. Simulations do not replace a meeting.

[28 — R0 TDD Bank](28-r0-tdd-acceptance-bank.md) supplies 60 blocker-level tests, 14 R0 safety tests (one for each safety gap) and 10 cross-role end-to-end checks. [29 — Stakeholder Workshop Kit](29-r0-business-acceptance-workshop-kit.md) provides five review sessions; neither test implementation nor approval is claimed. R1/R2 gap entries remain deferred.

## 7B. Negative scenario hardening after fifth review

The [30 — Negative & Failure Bank](30-negative-and-failure-scenario-bank.md) adds 48 concrete test designs (12 fault families) to 84 existing proposals, for 132 planned individual cases, plus eight uncounted mixed-failure executions. Each `NEG-R0-*` retains links to `USB-*`, `SIM-*`, `GAP-*` and an existing `AUTH/LFC/TDD` anchor. All tests are still **NOT EXECUTED**. No original blocker severity is declared closed by the existence of test specifications; real company/legal signoff remains required.

The most important new acceptance requirement is **no false business state after a refused or interrupted command**: not merely status 403/409, but no unauthorized DB mutation, no phantom capacity/custody/payment effect, no false Outbox/notification, and no customer UI misrepresentation. See mixed-race `MIX-01..08` in doc 30.

## 8. Outstanding workshop questions

- Which documents prove authority for customer signatory, carrier capacity confirmation and POD recipient in the Kazakhstan R0 corridor?
- Is a carrier without its own Tenant permitted by verified one-time portal, or only through recorded manual acknowledgement?
- When can a Sales employee enter a customer RFQ from telephone without impersonating the client?
- What happens to active transport when SaaS billing or subscription changes while cargo is in transit?
- Can an assigned driver report pickup while offline and after a delayed grant revoke? How to preserve historical facts without stale-privilege writes?
- Who pays cancellation fees, extra mileage or a cargo damage claim, and who independently approves each exceptional cost?
- Does private customer feedback require fully resolved delivery/claim, and what appeal/edit process exists?
- What are acceptable bank/ERP settlement evidence sources and invoice correction requirements in the pilot?

## 9. Status and anti-overengineering decision

All 42 simulations are **desk walkthroughs**; **0 actual user sessions, 0 Testcontainers, 0 CI test executions** were performed by this audit. The existing **17 business modules** remain unchanged. No new microservice, universal BPM, separate Customer Portal database, generic role/approval DSL or ML runtime is recommended.

A realistic platform cannot promise *all* variants have been explored. The correct next milestone is to **approve prioritized business truths**, then execute the agreed negative and recovery journeys on real database/API code and user-facing screens.

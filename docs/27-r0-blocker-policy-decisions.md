# 27 — Twelve R0 Blocker Decisions: Proposed Business Contracts, Owners & Signoff

**Version:** 1.0 · **Date:** 2026-11-07 · **Status:** `DESIGN_SPECIFIED / STAKEHOLDER SIGNOFF PENDING / NOT IMPLEMENTED`.

**Canonical machine record:** [r0-blocker-decisions.v1.json](contracts/r0-blocker-decisions.v1.json). **Prior gap audit:** [26](26-role-process-simulation-and-gap-audit.md). **Binding domain lifecycle:** [10](10-commercial-execution-lifecycle-v1.md). **Security baseline:** [Access Governance v2.1](24-access-control-tdd-matrix-v2.md).

## 1. What is closed today — and what is not

The earlier audit found **12 blocking decision gaps**, not 12 already-implemented production bugs. This version specifies a deterministic **fail-safe technical contract** for all 12, with exact actor/domain owner, evidence and negative variants. That closes **the missing design proposal**, *not* stakeholder legal/business approval. No stakeholder signatures, real client interviews, code commits to application, tests, or CI qualification were performed.

| Decision / gap | Issue | Domain owner | Technical status | Business acceptance |
|---|---|---|---|---|
| `BR-01` / `GAP-01` | Customer legal signatory on Quote | Commercial | DESIGN_SPECIFIED | PENDING_REAL_STAKEHOLDER |
| `BR-02` / `GAP-02` | External customer Quote decline | Commercial | DESIGN_SPECIFIED | PENDING_REAL_STAKEHOLDER |
| `BR-03` / `GAP-03` | Own-tenant customer vs provider EXC identity | Tenancy | DESIGN_SPECIFIED | PENDING_REAL_STAKEHOLDER |
| `BR-04` / `GAP-05` | Subscription suspended with active cargo | SaaS Control | DESIGN_SPECIFIED | PENDING_REAL_STAKEHOLDER |
| `BR-05` / `GAP-08` | Material change to RFQ/Quote after issue or acceptance | Commercial + Booking | DESIGN_SPECIFIED | PENDING_REAL_STAKEHOLDER |
| `BR-06` / `GAP-09` | CarrierOffer selection/withdrawal and binding capacity | Commercial + Fleet | DESIGN_SPECIFIED | PENDING_REAL_STAKEHOLDER |
| `BR-07` / `GAP-12` | Double-booking exclusion and expiry race | Fleet | DESIGN_SPECIFIED | PENDING_REAL_STAKEHOLDER |
| `BR-08` / `GAP-13` | Compliance critical UNKNOWN and legal route safety | Compliance | DESIGN_SPECIFIED | PENDING_REAL_STAKEHOLDER |
| `BR-09` / `GAP-15` | Offline pickup event after reassignment/revoke | Execution | DESIGN_SPECIFIED | PENDING_REAL_STAKEHOLDER |
| `BR-10` / `GAP-18` | Partial POD and conservation | Execution | DESIGN_SPECIFIED | PENDING_REAL_STAKEHOLDER |
| `BR-11` / `GAP-21` | Booking cancellation and financial impact | Booking | DESIGN_SPECIFIED | PENDING_REAL_STAKEHOLDER |
| `BR-12` / `GAP-22` | Payment approval vs bank/ERP settlement | Finance | DESIGN_SPECIFIED | PENDING_REAL_STAKEHOLDER |

**Fail-closed rule:** if a legal signing method, carrier authority, approved amount threshold, compliance decision, cargo evidence or valid signature/verification source is unavailable, the system must not pretend the irreversible state transition succeeded. Draft/pending/hold/reconciliation records remain available; no imaginary acceptance/capacity/POD/paid events.

## 2. Concrete recommendations for the 12 blockers

### BR-01 — Customer legal signatory on Quote (GAP-01)

**Owner of business rule:** Commercial. **Review stakeholders:** Customer legal representative, legal counsel.

**Proposed safe operational contract:** Customer quote acceptance requires verified identity, org representation/delegation evidence, exact immutable QuoteVersion digest, full terms, authority valid at event time; separate signatory grant; if verified signing method unavailable: signing-evidence workflow remains pending while canonical QuoteVersion stays ISSUED, never ACCEPTED and no binding booking.

**Mandatory evidence:** Signed/accepted record: signer identity, tenant/customerOrg, delegation proof ref, signature method, UTC timestamp, termsHash, version, policyVersion.

**Must cover variants:** `Customer without tenant`; `customer tenant`; `delegated signer`; `role change while quote open`; `signer expired`; `acceptance retry.`.

**Signoff still required:** Signing method and Kazakhstan pilot contract wording require written legal signoff; portal click alone not assumed equivalent to statutory EDS.

**Trace:** `USB-EXC-004`, `USB-SHP-002`; `SIM-06`, `SIM-13`; existing planned test IDs `AUTH-EXT-006`, `LFC-003`, `LFC-004`.

**Current decision state:** `DESIGN_SPECIFIED` · business `PENDING_REAL_STAKEHOLDER` · policy `DISABLED_UNTIL_ACCEPTANCE` · executed test `NO`.


### BR-02 — External customer Quote decline (GAP-02)

**Owner of business rule:** Commercial. **Review stakeholders:** Customer representative, provider sales.

**Proposed safe operational contract:** customer:quote:decline requires explicit customer decline permission (not read), current ISSUED version, exact customer-account relationship and reason. Decline is an authorized state-changing command, idempotent and audited; cannot decline ACCEPTED/EXPIRED/SUPERSEDED version.

**Mandatory evidence:** quoteVersion, actor, reasonCode, idempotencyKey, expectedVersion, timestamp, event id.

**Must cover variants:** `viewer only`; `signer without decline grant`; `expiry race`; `duplicate decline`; `different customerOrg.`.

**Signoff still required:** Business must decide whether general customer requester can decline or only signatory; default separate grant.

**Trace:** `USB-EXC-014`; `SIM-13`; existing planned test IDs `AUTH-COM-008`, `AUTH-X-019`.

**Current decision state:** `DESIGN_SPECIFIED` · business `PENDING_REAL_STAKEHOLDER` · policy `DISABLED_UNTIL_ACCEPTANCE` · executed test `NO`.


### BR-03 — Own-tenant customer vs provider EXC identity (GAP-03)

**Owner of business rule:** Tenancy. **Review stakeholders:** Tenant Admin, customer org admin, security.

**Proposed safe operational contract:** Each request resolves verified subject, active relationship and providerTenant/customerOrg/account; no caller-supplied tenant override; own Tenant-B membership never creates membership in provider Tenant-A; RLS and field projections deny cross-customer and cross-provider reads.

**Mandatory evidence:** grantId, providerTenantId, customerOrgId, customerAccountId, scope, expiry, revocation, policy version.

**Must cover variants:** `same user in 2 customer orgs`; `multiple providers`; `branch scoping`; `partner Grant revoked while Redis warm`; `subscription difference.`.

**Signoff still required:** CustomerAccount ownership, verified company contact, invite origin and authority require customer pilot signoff.

**Trace:** `USB-EXC-001`, `USB-EXC-003`, `USB-TEN-005`; `SIM-04`, `SIM-05`, `SIM-38`; existing planned test IDs `AUTH-X-001`, `AUTH-X-002`, `AUTH-X-015`, `AUTH-X-021`, `AUTH-X-023`.

**Current decision state:** `DESIGN_SPECIFIED` · business `PENDING_REAL_STAKEHOLDER` · policy `DISABLED_UNTIL_ACCEPTANCE` · executed test `NO`.


### BR-04 — Subscription suspended with active cargo (GAP-05)

**Owner of business rule:** SaaS Control. **Review stakeholders:** Tenant Owner, operations head, legal.

**Proposed safe operational contract:** SaaS subscription restrictions never delete, hide or silently stop in-flight safety-critical trip/custody/POD/evidence and incident reporting. Proposed SAFE_CONTINUITY mode permits scoped safety/evidence commands on already active work, blocks new discretionary paid bookings; immutable ledger and audit. Never treat billing fault as transport cancellation.

**Mandatory evidence:** subscription state, active booking/trip refs, continuity policy version, authorized actors, audit, exact allowed actions.

**Must cover variants:** `subscription suspended before booking`; `during Trip.STARTED`; `after delivery while POD pending`; `unpaid invoice`; `SaaS service outage.`.

**Signoff still required:** Scope/duration of safe continuity, contractual commitments and retention need legal/operations/SaaS signoff; no default automatic operation without policy.

**Trace:** `USB-TNO-004`; `SIM-41`; existing planned test IDs `LFC-011`, `LFC-034`.

**Current decision state:** `DESIGN_SPECIFIED` · business `PENDING_REAL_STAKEHOLDER` · policy `DISABLED_UNTIL_ACCEPTANCE` · executed test `NO`.


### BR-05 — Material change to RFQ/Quote after issue or acceptance (GAP-08)

**Owner of business rule:** Commercial + Booking. **Review stakeholders:** Customer and Sales, legal, operations.

**Proposed safe operational contract:** Material edit of cargo/address/date/quantity/price creates explicit revision with snapshot and change proposal, never mutates issued/accepted QuoteVersion. Pre-accept: supersede old version and require new approval; post-accept: amendment request, commercial and customer agreement, Booking revalidation/re-reservation if capacity impacted. Until acceptance keep current binding truth and explicit pending change; no phantom cancellation.

**Mandatory evidence:** old/new immutable version refs, change reason, expectedVersion, approval/acceptance hashes, reservation impact.

**Must cover variants:** `small draft correction`; `price increase`; `weight change after booking`; `changed carrier/time window`; `acceptance races revision.`.

**Signoff still required:** Which changes are material, cancellation price and legal amendment process require customer/Sales/legal signoff.

**Trace:** `USB-EXC-011`, `USB-SAL-008`, `USB-SAL-002`; `SIM-09`, `SIM-10`; existing planned test IDs `LFC-004`, `LFC-026`, `AUTH-COM-012`.

**Current decision state:** `DESIGN_SPECIFIED` · business `PENDING_REAL_STAKEHOLDER` · policy `DISABLED_UNTIL_ACCEPTANCE` · executed test `NO`.


### BR-06 — CarrierOffer selection/withdrawal and binding capacity (GAP-09)

**Owner of business rule:** Commercial + Fleet. **Review stakeholders:** Carrier authorized representative, procurement, legal.

**Proposed safe operational contract:** CarrierOffer REQUESTED/OFFERED/SELECTED is sourcing state, never resource availability proof. Carrier may decline/withdraw before specifically defined cutoff; store carrier-authorized acknowledgement with expiry/version. Fleet holds resource and obtains separate owner consent; only CONFIRMED capacity may unblock Booking. Post-confirm withdrawal triggers BookingException/replacement, not silent resource release or false confirmation.

**Mandatory evidence:** carrierOffer version, actor authority, supplier agreement, ack timestamp, expiry, capacity reservation ref, exception event.

**Must cover variants:** `carrier without paid tenant`; `carrier calls phone`; `offer expires during selection`; `withdraw before/after HELD/CONFIRMED`; `own fleet.`.

**Signoff still required:** Carrier commitments, contract signature method, cancellation liabilities and fallback manual evidence require carrier/legal signoff.

**Trace:** `USB-CAR-001`, `USB-CAR-003`, `USB-PRC-003`; `SIM-15`, `SIM-16`, `SIM-17`; existing planned test IDs `LFC-006`, `AUTH-COM-010`, `AUTH-FLT-002`.

**Current decision state:** `DESIGN_SPECIFIED` · business `PENDING_REAL_STAKEHOLDER` · policy `DISABLED_UNTIL_ACCEPTANCE` · executed test `NO`.


### BR-07 — Double-booking exclusion and expiry race (GAP-12)

**Owner of business rule:** Fleet. **Review stakeholders:** Planner, Dispatcher, carrier manager.

**Proposed safe operational contract:** PostgreSQL is authority for exclusive vehicle/driver/trailer per overlapping time interval; unique/exclusion constraints or explicit locked resource-interval model; version checks and transactional hold+outbox. HELD expiry job can RELEASE only same version and expired state; CONFIRMED or CONSUMED never released by stale expiry. No Redis-only booking lock.

**Mandatory evidence:** resource ids, tenant/owner, UTC tstzrange interval, reservation version, holdExpiresAt, commit event.

**Must cover variants:** `two dispatchers race`; `held/confirmed same instant`; `different time zones`; `server crash after hold`; `shared-load not enabled.`.

**Signoff still required:** Shared load and partial vehicle capacity not supported in R0 unless separately qualified; vehicle/driver/trailer resource model to be signed by Fleet.

**Trace:** `USB-DSP-001`, `USB-PLN-001`; `SIM-18`; existing planned test IDs `LFC-007`, `AUTH-FLT-001`, `AUTH-BKG-001`.

**Current decision state:** `DESIGN_SPECIFIED` · business `PENDING_REAL_STAKEHOLDER` · policy `DISABLED_UNTIL_ACCEPTANCE` · executed test `NO`.


### BR-08 — Compliance critical UNKNOWN and legal route safety (GAP-13)

**Owner of business rule:** Compliance. **Review stakeholders:** Compliance specialist, legal, planner.

**Proposed safe operational contract:** Critical missing/unverified permit, cargo restriction, jurisdictional route constraint or UNKNOWN assessment yields HOLD/DENY, never default allow. Only qualified Compliance authority and versioned rule/evidence can resolve; not Dispatcher/ML/ETA. Keep manual review in pilot; no general-purpose rules engine.

**Mandatory evidence:** source rule version, validity/jurisdiction, cargo/route snapshot, reviewer identity/qualification, decision and evidence refs.

**Must cover variants:** `dangerous goods`; `expired permit`; `region unknown`; `conflict among legal sources`; `override request`; `offline driver.`.

**Signoff still required:** Kazakhstan corridor applicability, binding norm version and legally qualified reviewer must be validated against official sources and counsel.

**Trace:** `USB-COM-001`, `USB-COM-002`; `SIM-19`; existing planned test IDs `LFC-009`.

**Current decision state:** `DESIGN_SPECIFIED` · business `PENDING_REAL_STAKEHOLDER` · policy `DISABLED_UNTIL_ACCEPTANCE` · executed test `NO`.


### BR-09 — Offline pickup event after reassignment/revoke (GAP-15)

**Owner of business rule:** Execution. **Review stakeholders:** Driver, Dispatcher, security, operations.

**Proposed safe operational contract:** Separate capture of historical fact from authority to mutate current custody. Offline event with stable event ID, signed device/actor assignment snapshot, observedAt/receivedAt, baseVersion, cargo units and evidence; on late replay verify authoritative assignment history and monotonic custody. Valid historical evidence may be quarantined for reconciliation; revoked/current unauthorized actor cannot create new custody state. Exactly one logical effect via DB dedup.

**Mandatory evidence:** eventId, actor, trip/assignmentVersion, cargoUnitIds, evidence hash, observedAt, receivedAt, signature, decision/reconciliation.

**Must cover variants:** `offline replay after driver reassigned`; `duplicate delayed event`; `wrong device clock`; `no network`; `expired role`; `order inversion.`.

**Signoff still required:** Legal admissibility of offline signature and custody handover proof needs operations/legal signoff.

**Trace:** `USB-DRV-002`, `USB-DSP-006`; `SIM-24`, `SIM-25`, `SIM-35`; existing planned test IDs `LFC-011`, `LFC-029`, `LFC-032`.

**Current decision state:** `DESIGN_SPECIFIED` · business `PENDING_REAL_STAKEHOLDER` · policy `DISABLED_UNTIL_ACCEPTANCE` · executed test `NO`.


### BR-10 — Partial POD and conservation (GAP-18)

**Owner of business rule:** Execution. **Review stakeholders:** Consignee, driver, operations, finance.

**Proposed safe operational contract:** Each identified CargoUnit has nonnegative conserved quantity across current custodian, accepted delivered, returned and incident disposition. DeliveryAttempt 8/10=PARTIAL, Shipment not DELIVERED; residual 2 remain owned by known custodian with reattempt/return case. POD evidence append-only and corrections versioned; duplicate signature/event does not create second delivery.

**Mandatory evidence:** cargoUnit IDs, accepted/refused/damaged counts, custody actor, verified receiver, signed POD, evidence hash, disposition refs.

**Must cover variants:** `full, partial, no-show, reject, damaged, return, mixed units, duplicate callback, delivery correction.`.

**Signoff still required:** Recipient authority and jurisdiction-specific evidence form need consignee/legal review.

**Trace:** `USB-RCV-001`, `USB-RCV-002`; `SIM-27`, `SIM-28`, `SIM-29`; existing planned test IDs `LFC-013`, `LFC-014`, `LFC-035`, `AUTH-EXE-003`.

**Current decision state:** `DESIGN_SPECIFIED` · business `PENDING_REAL_STAKEHOLDER` · policy `DISABLED_UNTIL_ACCEPTANCE` · executed test `NO`.


### BR-11 — Booking cancellation and financial impact (GAP-21)

**Owner of business rule:** Booking. **Review stakeholders:** Customer, operations manager, commercial, finance.

**Proposed safe operational contract:** Customer submits CancellationRequest, does not mutate Booking. Booking owner checks exact aggregate state+version, started Trip, custody and contractual terms. Before execution may CANCEL after policy approval with reservation release, invoice/charges audit; in execution must record exception/return/rescue with custody and payment impact, not direct CANCELLED. Nonapproved fees stay disputed/pending.

**Mandatory evidence:** cancelRequest id, booking version, legal terms snapshot, reason, actor, time, carrier response, approved charges, resource release/compensation event.

**Must cover variants:** `cancel before capacity`; `after Booking confirmed`; `after pickup`; `concurrent Trip.STARTED`; `outstanding invoice`; `seller carrier refuses.`.

**Signoff still required:** Precise time windows, fee thresholds, party liable and cancellation authority require forwarder/customer/carrier/finance/legal agreement.

**Trace:** `USB-EXC-009`, `USB-DSP-003`; `SIM-21`, `SIM-22`; existing planned test IDs `LFC-034`, `AUTH-EXT-013`, `AUTH-BKG-003`.

**Current decision state:** `DESIGN_SPECIFIED` · business `PENDING_REAL_STAKEHOLDER` · policy `DISABLED_UNTIL_ACCEPTANCE` · executed test `NO`.


### BR-12 — Граница продукта: внешняя бухгалтерия, без платежей в KERUENIX (GAP-22)

**Владелец бизнес-решения:** Product Owner с представителем бухгалтерии/коммерции и юристом. **Статус:** PENDING_REAL_STAKEHOLDER; продуктовая директива пользователя **NO PAYMENTS** уже отражена в scope, но не подменяет фактическое согласование договора и внешних обязанностей.

**Предлагаемое правило:** KERUENIX ведёт стоимость перевозки, покупную/продажную цену, версию коммерческих условий, маржу и может ссылаться на документ внешней бухгалтерии. **НЕ** выставляет официальный ЭСФ, не проводит платежи, не интегрируется с банком, не распределяет поступления, не ведёт AR/AP ledger, не хранит статусы `PAID/SETTLED/REFUNDED`, не инициирует возвраты. Факт ЭЦП на Quote/акте подтверждает подписанный документ — не оплату.

**Сценарии:** (1) carrier видит лишь разрешённый cost, не маржу экспедитора; (2) CustomerOrg-Y не читает чужие commercial references; (3) внешний бухгалтер оформляет документ в отдельной системе, KERUENIX хранит только безопасную ссылку; (4) фальшивый bank callback/markPaid/refund не поддерживается; (5) спорная доплата остаётся предложением к новым договорным условиям, не платёжным обязательством платформы.

**Рекомендованные TDD:** `PAY-ABS-01..06` и реальная PostgreSQL+HTTP изоляция pricing данных, отсутствие платёжных CRUD и опасных секретов. Исторические тесты `TDD-R0-E2E-06`, `TDD-SIM-32-G22-01..05`, `NEG-R0-033..036` **архивированы, не переносятся автоматически в R1/R2**.

**Нужное утверждение:** кто ведёт внешнюю бухгалтерию, какие идентификаторы/ссылки можно сохранять, кто вправе видеть buy/sell/margin, договорные документы и место хранения. Истинность `paid` не является предметом KERUENIX.

**State:** BUSINESS_PENDING / DOMAIN_NOT_IMPLEMENTED / NO_PAYMENT_SCOPE_ACTIVE.

## 3. Cross-role business review protocol — cannot be simulated as acceptance

| Review | Real parties required | They need to verify | Signoff artifact |
|---|---|---|---|
| BR-W1 Customer + Forwarder Sales | Customer organization authorized signatory, Sales owner, commercial approver, lawyer | `BR-01, BR-02, BR-03, BR-05`: identity, delegation, legally binding quote, price revisions and authority | Signed minutes/policy version + exemplar terms/acceptance evidence |
| BR-W2 Carrier/Fleet/Dispatcher | Carrier authorized representative, Procurement, Fleet, Dispatcher, transport legal | `BR-06, BR-07, BR-08`: offer/capacity vs contractual commitment, exclusion/time windows and compliance signoff | Supplier acceptance procedure, capacity constraints, exception/rescue agreement |
| BR-W3 Driver + Consignee + Operations | Assigned driver, shipper/custodian representative, consignee, execution owner | `BR-09, BR-10`: offline pickup, handover, partial/failed POD and cargo unit accounting | Approved pickup/POD samples + custody/disposition policy |
| BR-W4 Finance + Customer/Carrier | Finance controller, independent approver, accounting, bank/ERP owner, commercial, legal | `BR-11, BR-12`: cancellation fees, advances, payables and verified cash allocation | Authority thresholds + sample contract tariff + reconciled synthetic ledger |
| BR-W5 SaaS/Platform + Tenancy | Tenant Owner, SaaS product/billing, support/SRE, security, legal | `BR-04`: safe cargo/evidence continuation during subscription suspension, roles, incident recovery | Subscriber suspension matrix + continuity and retention signoff |

No assistant may mark `BUSINESS_APPROVED` or `LEGAL_APPROVED` without an actual named approver and evidence. The user may approve *product defaults*, but legal validity of a signature or local transportation form still needs appropriate review.

### Required interview and approval record (copyable)

```yaml
reviewId: BR-W1
decisionIds: [BR-01, BR-02, BR-03, BR-05]
pilotCorridor: "Kazakhstan: origin/destination to be confirmed"
signerCompanyOrRole: "business stakeholder, not software user name"
approvedPolicyVersion: null
decision: "PENDING | ACCEPTED | REVISED | REJECTED"
exceptionsAndLimits: []
evidenceDocumentRef: null
legalReviewRef: null
datedAtUtc: null
approverAuthorityBasis: null
openQuestions: []
```

Review must cover both parties' view of the same action, not only an administrator's permission. Legal signatory and recipient authority cannot be established by allowing a role template.

## 4. Kazakhstan legal verification gate — research, not legal signoff

For electronic legally meaningful documents, use **current** official Kazakhstani sources and verify their effective editions. The Kazakhstan **Digital Code No.255-VIII (2026)** describes electronic signatures and electronic documents, including checking authority to sign for a legal entity. Source: <https://old.adilet.zan.kz/rus/docs/K2600000255>. Earlier **2003 electronic-document law** is reported repealed and must not be used uncritically: <https://adilet.kz/ru/laws/doc-14027/>.

**Engineering consequence:** an in-app "Accept" button, an OTP, a scanned signature or a signed DeliveryAttempt are **not automatically equivalent to a legally compliant electronic signature**. Define the contractual form, verification method, delegation and timestamp evidence with legal counsel for the selected carrier/route/document. The code should preserve proof references and prevent irreversible acceptance when method is unknown. Do not assert one universal electronic POD format for every shipment type or jurisdiction.

## 5. Explicit irreversible-state safety invariants

1. `QuoteVersion.ACCEPTED` requires a verified signatory and exact effective version, not login alone.
2. `CarrierOffer.SELECTED` is **not** `CapacityReservation.CONFIRMED` nor binding carrier promise.
3. `Booking.CONFIRMED` requires accepted terms, confirmed exclusive capacity and approved compliance/evidence; never infer from UI notifications.
4. `Trip.STARTED` never means `Shipment.IN_CUSTODY`.
5. No GPS reading, warehouse scan or driver's unilateral click can fabricate verified `POD`.
6. `Shipment.DELIVERED` requires verified complete cargo-unit disposition; a 8/10 partial POD is not full delivery.
7. `Payable.APPROVED` is distinct from bank `SETTLED`; duplicate bank callbacks cannot allocate twice.
8. Customer cancellation request cannot directly set `Booking.CANCELLED`, especially after pickup.
9. Tenant subscription suspension must not silently erase safely permitted in-flight custody/POD/evidence.
10. A revoked customer or carrier grant cannot authorize new actions using stale JWT/cache or worker context.

## 6. Anti-overengineering and status

No universal BPM/rules engine, Kafka, separate IAM microservice or newly invented business module is needed. Use explicit module-owned policies, strict transaction boundaries, PostgreSQL constraints, typed state machines and minimum approval records. Optional screen flows for R1 remain deferred.

**Next gate:** review W1–W5 and freeze accepted per-tenant rules, then allow `TDD-SIM-*` implementation. TDD design may be drafted ahead of approval, but **green tests for guessed legal rules are not acceptance**. See [28 — R0 TDD Bank](28-r0-tdd-acceptance-bank.md).

# 29 — R0 Business Acceptance Workshop Kit: 5 Role-based Simulation Sessions

**Version:** 1.0 · **Date:** 2026-11-07 · **Status:** `READY_TO_REVIEW / NOT CONDUCTED / NO SIGNATURES`.

**Objective:** convert the proposed business and security rules of [27 — 12 Blocker Decisions](27-r0-blocker-policy-decisions.md) into verified pilot-specific acceptance with actual customer, forwarder, carrier, driver/receiver, finance, legal and SaaS stakeholders. Review [26 — 42 role desk simulations](26-role-process-simulation-and-gap-audit.md) and [28 — 84 TDD cases](28-r0-tdd-acceptance-bank.md) while validating the actual workflow from each party's view.

**Rule:** a ChatGPT-generated workshop packet is not evidence of a held meeting, identity verification, legal advice or approvals. Until recorded signatures/decisions exist, all BR-01..12 remain `PENDING_REAL_STAKEHOLDER`.

## 1. Workshop completion model

```text
PROPOSED_POLICY
  → ROLE_WALKTHROUGH_REVIEWED
  → ACTOR/COMPANY SIGNOFF
  → SECURITY/LEGAL SIGNOFF (where required)
  → ACCEPTED_FOR_TDD
  → TESTS_IMPLEMENTED / EXACT-SHA CI
  → BUSINESS_QUALIFIED
```

For each action establish: authorized principal and delegation evidence, actual tenant/company and resource owner, legal agreement scope, happy path, negative actor, concurrent timeout/replay, admissible state transition, external data visibility, evidence hash/audit and user-visible status.

## W1 — Грузовладелец / Внешний заказчик / Экспедитор / Юрист

**Decisions:** `BR-01`, `BR-02`, `BR-03`, `BR-05`. **Expected participants:** External Customer Viewer; Customer Authorized Signatory; Tenant Sales; Commercial Approver; Tenant Legal/Compliance.

**Synthetic setup:** CustomerOrg-X granted to Tenant-A; customer without paid tenant and customer with own Tenant-B; two QuoteVersions, one expired.

**Tabletop role simulation, one actor at a time:**
1. Представитель клиента показывает, как подтверждаются права физического пользователя действовать от юридического лица; подтверждает допустимый метод электронного согласия для пилотного договора
2. Viewer читает Quote, но не может акцептовать или отклонить без раздельных полномочий; клиент объясняет требуемые разрешения
3. Клиент уточняет массу/адрес после ISSUED и после ACCEPTED: стороны договариваются о новой версии, оплате последствий и переходном состоянии
4. Sales демонстрирует draft и exceptional price approval; автор собственной скидки не утверждает её
5. Проверить, что клиентская сторона не видит закупочную ставку перевозчика/маржу

**Required policy decisions/evidence:** Signer evidence method, delegated authority, Quote wording, decline authority, material-change list, cross-tenant visibility.

**Fail-safe if no decision:** Without confirmed legal acceptance method leave QuoteVersion ISSUED; never synthesize ACCEPTED.

**Approval record (not signed):**

| Field | Current value |
|---|---|
| Workshop | `W1` |
| Business owner / authorized signer | **PENDING — real person** |
| Customer/carrier counterpart acknowledgment | **PENDING** |
| Legal/compliance review | **PENDING where applicable** |
| Decision | `PENDING` |
| Chosen policy version | `PENDING` |
| Approval evidence artifact link | `PENDING` |
| Date / participants / exceptions | `PENDING` |
| Mark `ACCEPTED_FOR_TDD`? | **NO** |


## W2 — Закупка перевозок / Перевозчик / Планировщик / Compliance

**Decisions:** `BR-06`, `BR-07`, `BR-08`. **Expected participants:** Forwarder Procurement Manager; Carrier Authorized Manager; Fleet Planner; Dispatcher; Compliance Officer; Transport Legal.

**Synthetic setup:** Selected carrier offer and own-fleet alternative; two overlapping vehicle/driver/trailer slots; one critical UNKNOWN permit.

**Tabletop role simulation, one actor at a time:**
1. Перевозчик различает OFFERED, SELECTED, HELD и CONFIRMED, указывает, когда возникает договорное обязательство
2. Независимый carrier manager подтверждает машину и окно без раскрытия клиентской цены
3. Два диспетчера одновременно бронируют один слот: поддерживается только один истинный резерв
4. Отзыв/истечение предложения до и после подтверждения ресурса: определить кто платит и когда возможна замена
5. Compliance демонстрирует квалификацию источника, когда неизвестный норматив блокирует Booking/Trip и кто вправе снять HOLD

**Required policy decisions/evidence:** Carrier contractual cutoff, evidence method, interval exclusivity, own-fleet path, compliance source/version and reviewer.

**Fail-safe if no decision:** UNKNOWN compliance/expired or withdrawn resource never yields Booking.CONFIRMED.

**Approval record (not signed):**

| Field | Current value |
|---|---|
| Workshop | `W2` |
| Business owner / authorized signer | **PENDING — real person** |
| Customer/carrier counterpart acknowledgment | **PENDING** |
| Legal/compliance review | **PENDING where applicable** |
| Decision | `PENDING` |
| Chosen policy version | `PENDING` |
| Approval evidence artifact link | `PENDING` |
| Date / participants / exceptions | `PENDING` |
| Mark `ACCEPTED_FOR_TDD`? | **NO** |


## W3 — Водитель / Грузоотправитель / Получатель / Operations / Documents

**Decisions:** `BR-09`, `BR-10`. **Expected participants:** Driver; Shipper Dock Representative; Consignee; Dispatcher; Document Controller; Transport Legal.

**Synthetic setup:** Shipment with 10 distinct CargoUnits, assigned driver, offline device, alternate driver and receiver token.

**Tabletop role simulation, one actor at a time:**
1. Водитель фиксирует pickup 10 единиц и observedAt офлайн, затем меняется водитель до синхронизации; не допускается фантомная передача
2. Получатель принимает 8, 2 повреждены/не получены: определить реального custodian и дальнейшую судьбу
3. Отсутствующий получатель создаёт failed attempt, а не DELIVERED
4. Подтверждение POD от чужого/просроченного guest identity запрещено
5. Коррекция подписанного акта добавляет новую версию доказательства, не меняет оригинал

**Required policy decisions/evidence:** POD/evidence forms, who signs pickup and receipt, failed attempt and exception documentation, allowed late/offline fact capture.

**Fail-safe if no decision:** Trip.STARTED, geo arrival and 8/10 never prove full delivery.

**Approval record (not signed):**

| Field | Current value |
|---|---|
| Workshop | `W3` |
| Business owner / authorized signer | **PENDING — real person** |
| Customer/carrier counterpart acknowledgment | **PENDING** |
| Legal/compliance review | **PENDING where applicable** |
| Decision | `PENDING` |
| Chosen policy version | `PENDING` |
| Approval evidence artifact link | `PENDING` |
| Date / participants / exceptions | `PENDING` |
| Mark `ACCEPTED_FOR_TDD`? | **NO** |


## W4 — Коммерция / Диспетчер / Финансы / Утверждающий платежи / Бухгалтер

**Decisions:** `BR-11`, `BR-12`. **Expected participants:** Authorized Customer Representative; Forwarder Operations Manager; Carrier Representative; Finance Officer; Independent Finance Approver; Bank/ERP Integration Owner; Transport Legal.

**Synthetic setup:** One Booking in RESOURCE_PENDING, one CONFIRMED and one Trip.STARTED; payable with approved amount, advance and duplicate bank callback.

**Tabletop role simulation, one actor at a time:**
1. Заказчик просит отменить Booking до старта: определить применимые тарифные условия, кто утверждает и когда освобождается ресурс
2. Заказчик просит отменить после pickup: показать safe custody/Return/Recovery, а не прямой CANCELLED
3. FIN создаёт заявку на платёж, отдельный FAP утверждает; сценарий одного сотрудника с обеими ролями отказывает самосогласование
4. Без банковского/ERP подтверждения оплата не считается SETTLED; при повторном callback уникальная allocation
5. Спорная доплата/аванс и корректировка выпущенного Invoice не стирают первоначальное обязательство

**Required policy decisions/evidence:** Cancellation cutoff/penalties, party liable, delegated limits, supported bank/ERP truth, correction and reversal procedure.

**Fail-safe if no decision:** No cancellation charges or settled cash by guesses or UI override.

**Approval record (not signed):**

| Field | Current value |
|---|---|
| Workshop | `W4` |
| Business owner / authorized signer | **PENDING — real person** |
| Customer/carrier counterpart acknowledgment | **PENDING** |
| Legal/compliance review | **PENDING where applicable** |
| Decision | `PENDING` |
| Chosen policy version | `PENDING` |
| Approval evidence artifact link | `PENDING` |
| Date / participants / exceptions | `PENDING` |
| Mark `ACCEPTED_FOR_TDD`? | **NO** |


## W5 — Tenant Owner / SaaS Operator / Support / Security / Legal

**Decisions:** `BR-04`, `BR-03`. **Expected participants:** Tenant Owner; Tenant Admin; Platform Super Admin; SaaS Billing; SRE Support; Security Officer; Legal.

**Synthetic setup:** Tenant-A with live Trip in custody and POD pending; revoked customer member; old JWT/cache/short-lived signed URL; billing suspension.

**Tabletop role simulation, one actor at a time:**
1. При остановке подписки Tenant не может создавать новые discretionary Bookings, но согласованные safety operations продолжаются по определённой политике
2. Определить продолжительность безопасного режима, уведомления и процедуру согласования исключений договора
3. Tenant Admin отключает внешнего сотрудника CustomerOrg-X, не блокируя коллег, и проверяет stale JWT/cache
4. Support перезапускает failed Job без просмотра грузов и финансов, при этом действие остаётся идемпотентным
5. Подтвердить политику хранения/доступа к обязательным документам после окончания подписки и фактическое ограничение presigned URL TTL

**Required policy decisions/evidence:** Continuity scope, subscription contract, access revocation guarantees, evidence retention/legal hold, support break-glass boundaries.

**Fail-safe if no decision:** Subscription/Redis/Job failure must not erase cargo custody or grant global operator data access.

**Approval record (not signed):**

| Field | Current value |
|---|---|
| Workshop | `W5` |
| Business owner / authorized signer | **PENDING — real person** |
| Customer/carrier counterpart acknowledgment | **PENDING** |
| Legal/compliance review | **PENDING where applicable** |
| Decision | `PENDING` |
| Chosen policy version | `PENDING` |
| Approval evidence artifact link | `PENDING` |
| Date / participants / exceptions | `PENDING` |
| Mark `ACCEPTED_FOR_TDD`? | **NO** |


## 6. Approval matrix: who must be present at least once

| Organization | Representative | Must decide | May authorize what |
|---|---|---|---|
| CustomerOrg-X | Customer delegated signatory | Quote acceptance, material amendments, cancellation, POD visibility | **Only their authorized customer organization**, not provider staff |
| Forwarder Tenant-A | Commercial + Ops lead | Quote issue, carrier terms, Booking cancellation, staffing | Within tenant/legal-entity/approval limits |
| Carrier Tenant-C or verified outside partner | Carrier representative | Offer acknowledgement, capacity commitment, driver assignment and replacement | Only carrier-side responsibilities and evidence |
| Receiver | Authorized consignee | Cargo units accepted/refused, receiver proof and partial POD | Exact delivery attempt, no invoice permissions |
| Finance + Bank/ERP | Finance officer + independent approver + source integration owner | Actual invoice/payable/advance/payment evidence, reconciliation | Explicit amount/currency/legal-entity limits, independent SoD |
| Platform | Super Admin + Security/SRE + SaaS billing | Provisioning, scoped grants, support replay, continuity on subscription suspension | Control plane and safety-limited operations, not tenant business-data superuser |
| Legal/Compliance | Pilot corridor-qualified reviewer | Contractual electronic acceptance/POD, compliance rules and enforceable penalties | Rule evidence/version and review; never dispatcher auto-override |

## 7. Handoff reconciliation sheet for one actual transport

| Transition | Giving party | Receiving party | Required acknowledged evidence |
|---|---|---|---|
| RFQ submitted | EXC / customer | Forwarder Sales | `rfqId`, provider/customer relation and cargo snapshot |
| Quote ISSUED | Forwarder Sales/Approver | Customer signatory | `versionId`, price/currency, validity, terms hash |
| Quote ACCEPTED | Authorized customer | Forwarder | Signed/verified acceptance for that version, authority proof |
| Carrier resource confirmed | Carrier or own-fleet authority | Forwarder Booking/Fleet | Identified vehicle/driver/trailer slot and reservation proof |
| Pickup | Shipper loading representative | Driver/custodian | CargoUnit counts, custody and signed evidence |
| Delivery/POD | Driver/custodian | Authorized consignee | Accepted/refused quantities and evidence; no lost balance |
| Invoice/AP/AR | Forwarder Documents/Finance | Customer/Carrier | Versioned package and distinct accounting records |
| Payment receipt | Bank/ERP verified source | Finance | Unique transaction and allocation evidence |
| Review eligibility | Execution delivery source | Customer Portal/Commercial | Verified service completion proof, not a GPS marker |

## 8. Decision gate

**Exit required for technical readiness:** all 12 blocker decisions record real business actor, relevant customer/carrier counterparty and legal review where applicable, an approved policy version, reference to evidence, unambiguous negative/exception rules and TDD test IDs. A missing legal authority keeps the corresponding operation in safe pending/denied state, not mock-approved. The 14 R0 Safety rules must be at least fail-closed. Subsequent R1/R2 work is not in R0 acceptance.

**Next handoff:** produce a named signed acceptance packet in repository or secured Project storage (do not put secrets/identity documents in a public repo), then run tests from [28](28-r0-tdd-acceptance-bank.md) on exact SHA. The current PR remains documentation-only until code exists.

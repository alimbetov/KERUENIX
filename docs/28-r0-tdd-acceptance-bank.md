# 28 — KERUENIX R0 TDD Acceptance Bank: 12 Blockers + 14 Safety Cases + Cross-role E2E

**Date:** 2026-11-07 · **Version:** 1.0 · **Status:** `DESIGNED / REAL STAKEHOLDER ACCEPTANCE PENDING / NOT IMPLEMENTED / NOT EXECUTED`.
**Machine-readable:** [r0-tdd-scenarios.v1.json](contracts/r0-tdd-scenarios.v1.json).
**Business rules:** [27 — Twelve Blocker Decisions](27-r0-blocker-policy-decisions.md).
**Source simulations:** [26 — Role/Process Simulation](26-role-process-simulation-and-gap-audit.md).
**Existing contract anchors:** [10 — Lifecycle](10-commercial-execution-lifecycle-v1.md), [11 — Legacy test plan](11-commercial-execution-acceptance-v1.md), [24 — Access Governance v2.1](24-access-control-tdd-matrix-v2.md), [20 — Engineering TDD Standard](20-mapstruct-tdd-engineering-standard.md).

## 1. Acceptance inventory

| Group | Count | Why |
|---|---:|---|
| `TDD-SIM-*-G*` | **60** | Five positive/negative/race/replay/tenant checks for each of the 12 blocking business decisions |
| `TDD-SIM-*-S*` | **14** | Exactly one explicit fail-closed behavior test for each of 14 safety gaps |
| `TDD-R0-E2E-*` | **10** | Cross-company and cross-module user journeys |
| **Total planned tests** | **84** | Planned acceptance contracts; none implemented or executed |

**Important interpretation:** tests currently assert **design assumptions**. They cannot become authoritative release gates until the real business/legal owners approve the relevant [BR-01..12](27-r0-blocker-policy-decisions.md). Until then, code may fail closed rather than infer customer signatory, valid carriage document, allowable cancellation charges or actual bank receipt.

## 2. Synthetic Testcontainers fixture

Use one reproducible fixture `FIX-R0-TRANSPORT-001`:

| Axis | Test data |
|---|---|
| Tenants | Tenant-A (forwarder, two branches), Tenant-B (shipper with own tenant), Tenant-C (carrier), Tenant-Z (forbidden) |
| External customers | CustomerOrg-X and CustomerOrg-Y with independent customer accounts; distinct VIEWER / REQUESTER / SIGNATORY / FEEDBACK_AUTHOR grants |
| Drivers and receivers | Assigned driver, revoked driver, guest consignee with exact delivery attempt token; second driver for handover |
| Commercial | Two immutable quote versions, one expired, one requiring approval, authorized and unauthorized signatory |
| Fleet | Vehicle + trailer + driver with overlapping time ranges; own fleet vs third-party |
| Cargo | Ten identified CargoUnits, eight accepted and two retained/returned, duplicate pickup and POD |
| Finance | Invoice/AR/AP, approved payable, verified bank/ERP source, advance, partial payment and replayed callback |
| Failure | PostgreSQL transaction conflict, Outbox replay, Redis outage/warm cache, old JWT, RustFS signed URL, SaaS subscription suspended mid-trip |

Do **not** implement RLS isolation using mocked repositories or H2. Tests must run with production-like PostgreSQL/PostGIS permissions, actual migration schema, app DB role without `BYPASSRLS`, tenant context transaction-scoped, and concurrent connections from HikariCP.

## 3. TDD acceptance by blocking business decision

### BR-01 — Customer legal signatory on Quote / GAP-01

**Business rule owner:** Commercial. **Needed review:** Customer legal representative; legal counsel.

| TDD case | Type | Given | When | Then | Test layer |
|---|---|---|---|---|---|
| `TDD-SIM-13-G01-01` | POSITIVE | Verified company signatory; valid delegation and exact issued quote hash | Actor signs using pilot-approved method with accepted terms | Only exact QuoteVersion transitions to ACCEPTED with immutable proof, otherwise remain ISSUED | Commercial policy JUnit + HTTP + PostgreSQL |
| `TDD-SIM-13-G01-02` | NEGATIVE | Portal Viewer with requester capability but without separately verified signer authority | Actor attempts quote accept | DENY; no QuoteVersion state or Outbox acceptance event | HTTP + RLS |
| `TDD-SIM-13-G01-03` | RACE | Quote ISSUED with expiry and parallel supersede command | Authorized signer accepts at boundary | Single authoritative valid transition; expired/superseded version cannot be accepted | PostgreSQL concurrency Testcontainers |
| `TDD-SIM-13-G01-04` | REPLAY | Previously successful signatory acceptance and identical idempotency key | Client retries after timeout | Same logical acceptance and evidence, no duplicate customer commitment/event | HTTP + Outbox/Inbox |
| `TDD-SIM-13-G01-05` | TENANT | Authorized user from CustomerOrg-Y or provider Tenant-B but quote belongs to CustomerOrg-X | Submit accept using guessed quoteId | DENY and no terms/signature visibility | HTTP + PostgreSQL RLS |


### BR-02 — External customer Quote decline / GAP-02

**Business rule owner:** Commercial. **Needed review:** Customer representative; provider sales.

| TDD case | Type | Given | When | Then | Test layer |
|---|---|---|---|---|---|
| `TDD-SIM-13-G02-01` | POSITIVE | Current ISSUED QuoteVersion; customer has explicit decline authority | Customer declines with allowed reason and expectedVersion | QuoteVersion DECLINED with correct actor, audit and no Booking | Commercial JUnit + HTTP |
| `TDD-SIM-13-G02-02` | NEGATIVE | Customer only has quote:read permission | Customer POST decline | DENY without state write or side effects | HTTP + policy unit |
| `TDD-SIM-13-G02-03` | RACE | Authorized decline races customer acceptance and quote expiry | Both commands execute against same version | Exactly one lawful final transition; losers conflict/re-read | PostgreSQL concurrency Testcontainers |
| `TDD-SIM-13-G02-04` | REPLAY | Decline recorded with same request digest | Retry decline command | One logical decline/audit outcome, no duplicate outbound notifications | HTTP + Outbox/Inbox |
| `TDD-SIM-13-G02-05` | TENANT | External customer from another provider relationship | Decline foreign QuoteVersion | DENY with no quote existence disclosure | HTTP + PostgreSQL RLS |


### BR-03 — Own-tenant customer vs provider EXC identity / GAP-03

**Business rule owner:** Tenancy. **Needed review:** Tenant Admin; customer org admin; security.

| TDD case | Type | Given | When | Then | Test layer |
|---|---|---|---|---|---|
| `TDD-SIM-05-G03-01` | POSITIVE | User belongs to Tenant-B and separately to provider Tenant-A's CustomerAccount-X via grant | User opens permitted Tenant-A order from customer workspace | Only provider-scoped customer projection returned; no Tenant-A employee Membership | HTTP + PostgreSQL RLS |
| `TDD-SIM-05-G03-02` | NEGATIVE | Same user switches browser context by caller-supplied tenantId header | Request Tenant-Z data using forged header | DENY, server-derived trusted context unaffected | HTTP + security integration |
| `TDD-SIM-05-G03-03` | RACE | Grant revocation and concurrent My Orders request | Provider disables CustomerAccount membership while read is in flight | New post-revoke authorization denies; in-flight semantics explicitly documented and DB-consistent | PostgreSQL + HTTP concurrency |
| `TDD-SIM-05-G03-04` | REPLAY | Cached customer projection created before revocation | User refreshes listing with active old JWT | No stale customer data leakage after authoritative revoke; 401/403 as appropriate | HTTP + cache integration |
| `TDD-SIM-05-G03-05` | TENANT | Two customers X/Y same provider Tenant-A | Customer X asks list/filter with Y order IDs | Only X's authorized subset; no count/fields from Y | HTTP + PostgreSQL RLS |


### BR-04 — Subscription suspended with active cargo / GAP-05

**Business rule owner:** SaaS Control. **Needed review:** Tenant Owner; operations head; legal.

| TDD case | Type | Given | When | Then | Test layer |
|---|---|---|---|---|---|
| `TDD-SIM-41-G05-01` | POSITIVE | Trip STARTED and active custody; subscription enters SUSPENDED | Authorized assigned driver records necessary POD/evidence under continuity policy | Safety/evidence permitted and auditable, no cargo evidence lost; new discretionary booking blocked | SaaS/Execution module test + PostgreSQL |
| `TDD-SIM-41-G05-02` | NEGATIVE | Tenant suspended and sales attempts new discretionary Booking | Sales submits booking command | DENY under agreed SaaS policy while evidence/recovery operations remain available | HTTP + policy unit |
| `TDD-SIM-41-G05-03` | RACE | Suspension transition races driver pickup/POD write | Both operations commit concurrently | Deterministic scoped continuity guard, no orphan evidence/custody | PostgreSQL concurrency |
| `TDD-SIM-41-G05-04` | REPLAY | SaaS service temporarily unreachable with safe-continuity policy version available | Critical custody event retries | Idempotent evidence accepted only under valid preapproved continuity scope; logs decision | Jobs + Testcontainers |
| `TDD-SIM-41-G05-05` | TENANT | Suspended Tenant-A driver tries read another Tenant-B Trip | Call via continuation privileges | DENY; safe continuity does not grant cross-tenant access | HTTP + RLS |


### BR-05 — Material change to RFQ/Quote after issue or acceptance / GAP-08

**Business rule owner:** Commercial + Booking. **Needed review:** Customer and Sales; legal; operations.

| TDD case | Type | Given | When | Then | Test layer |
|---|---|---|---|---|---|
| `TDD-SIM-10-G08-01` | POSITIVE | Quote ISSUED, customer changes cargo weight | Sales submits versioned amendment, obtains approvals as configured | New QuoteVersion created, original immutable and prior assumptions invalidated explicitly | Commercial JUnit + PostgreSQL |
| `TDD-SIM-10-G08-02` | NEGATIVE | Quote ACCEPTED and stale RFQ edit request | Customer tries direct mutation to old QuoteVersion or active Booking | DENY; persisted change request only, no stealth contract mutation | HTTP + domain policy |
| `TDD-SIM-10-G08-03` | RACE | Customer acceptance races issuance of replacement quote version | Two commands use expectedVersion | Only one coherent signed version remains effective; no mixed price/cargo snapshots | PostgreSQL concurrency |
| `TDD-SIM-10-G08-04` | REPLAY | Identical amend request repeated after response timeout | Client retries with idempotency key | One change proposal and one new version at most, no duplicate approval requests | HTTP + Outbox |
| `TDD-SIM-10-G08-05` | TENANT | Sales from unrelated legal entity attempts amendment | Submit change for foreign customer quote | DENY and no buy/sell details leak | HTTP + RLS |


### BR-06 — CarrierOffer selection/withdrawal and binding capacity / GAP-09

**Business rule owner:** Commercial + Fleet. **Needed review:** Carrier authorized representative; procurement; legal.

| TDD case | Type | Given | When | Then | Test layer |
|---|---|---|---|---|---|
| `TDD-SIM-16-G09-01` | POSITIVE | CarrierOffer OFFERED then SELECTED and supplier confirms valid held vehicle | Fleet confirms exclusive reservation with correct carrier authority | Only CapacityReservation CONFIRMED authorizes Booking predicate; OFFER SELECTED alone does not | Commercial/Fleet/Booking module integration |
| `TDD-SIM-16-G09-02` | NEGATIVE | Carrier withdraws before reservation confirmation | Dispatcher attempts Booking.CONFIRMED based on SELECTED offer | DENY/resource pending and supplier exception; no fake capacity | Booking policy unit + HTTP |
| `TDD-SIM-16-G09-03` | RACE | Offer expiry/withdrawal races Fleet hold confirmation | Concurrent commands reference supplier version | No confirmation based on invalidated offer or stale authority; failure reconciled | PostgreSQL concurrency |
| `TDD-SIM-16-G09-04` | REPLAY | Provider processes carrier acknowledge callback twice | Same callback/outbox id replayed | Single logical carrier ack/reservation effect and versioned audit | Outbox/Inbox + PostgreSQL |
| `TDD-SIM-16-G09-05` | TENANT | Carrier-C receives buy offer with sell quote, margin and other carrier data | Carrier reads view via its grant | Only own offer/public shipment terms returned; provider margin/cross-carrier fields absent | HTTP + RLS + JSON field allowlist |


### BR-07 — Double-booking exclusion and expiry race / GAP-12

**Business rule owner:** Fleet. **Needed review:** Planner; Dispatcher; carrier manager.

| TDD case | Type | Given | When | Then | Test layer |
|---|---|---|---|---|---|
| `TDD-SIM-18-G12-01` | POSITIVE | Vehicle/driver/trailer free for specified UTC interval | Fleet commits HELD and validates confirmation | Single valid reservation and holdExpiry/version recorded atomically | Fleet PostgreSQL Testcontainers |
| `TDD-SIM-18-G12-02` | NEGATIVE | Overlapping active reservation exists for same indivisible resource | Second dispatcher reserves overlapping interval | DB enforces conflict, no second HELD/CONFIRMED | PostgreSQL exclusion/locked-slot test |
| `TDD-SIM-18-G12-03` | RACE | Two dispatchers and hold expiry job compete for same slot | Concurrent HELD/CONFIRM/EXPIRE operations execute | At most one compatible final reservation; stale expiry cannot free confirmed hold | PostgreSQL concurrency + job integration |
| `TDD-SIM-18-G12-04` | REPLAY | Crash after capacity transaction commits before notification | Job retries from durable outbox | One authoritative reservation, eventual notification, no new capacity hold | PostgreSQL Outbox/Inbox |
| `TDD-SIM-18-G12-05` | TENANT | Planner from ungranted Tenant-Z attempts Tenant-A vehicle hold | Send vehicle ID and interval | DENY before write; RLS still protects resource row | HTTP + RLS |


### BR-08 — Compliance critical UNKNOWN and legal route safety / GAP-13

**Business rule owner:** Compliance. **Needed review:** Compliance specialist; legal; planner.

| TDD case | Type | Given | When | Then | Test layer |
|---|---|---|---|---|---|
| `TDD-SIM-19-G13-01` | POSITIVE | Cargo/route compliance assessed with qualified applicable rule source and reviewer | Qualified Compliance actor approves reviewed evidence | Versioned legally applicable permit/assessment permits allowed transition as configured | Compliance policy unit + module test |
| `TDD-SIM-19-G13-02` | NEGATIVE | Critical jurisdiction/cargo permit status is UNKNOWN or DENY | Dispatcher presses override/Start Trip | DENY; pending HOLD with reason; no route/Trip READY/Booking allow | HTTP + policy unit |
| `TDD-SIM-19-G13-03` | RACE | Permit expires between assessment and Trip READY | READY command checks current effective rule snapshot/version | DENY or requalification; no stale compliance approval | PostgreSQL transaction + Clock test |
| `TDD-SIM-19-G13-04` | REPLAY | Late Compliance ALLOW event arrives after later DENY | Consumer retries outdated event | No regression from DENY into ALLOW, emit reconciliation/audit | Outbox/Inbox module test |
| `TDD-SIM-19-G13-05` | TENANT | Reviewer with scope for another legal entity tries to release HOLD | Submit approval for foreign cargo | DENY, full audit of attempted release | HTTP + RLS |


### BR-09 — Offline pickup event after reassignment/revoke / GAP-15

**Business rule owner:** Execution. **Needed review:** Driver; Dispatcher; security; operations.

| TDD case | Type | Given | When | Then | Test layer |
|---|---|---|---|---|---|
| `TDD-SIM-24-G15-01` | POSITIVE | Assigned driver captures pickup evidence offline while valid assignment; server receives later | Upload event with assignment history/version and evidences | One validated historical custody transition after authoritative reconciliation | Execution policy unit + PostgreSQL |
| `TDD-SIM-24-G15-02` | NEGATIVE | Reassigned/revoked driver forges new pickup observedAt after revocation | Upload stale assignment event | DENY for current state mutation; evidence quarantined if needed, not silently dropped or accepted | HTTP + PostgreSQL history |
| `TDD-SIM-24-G15-03` | RACE | Two drivers submit overlapping cargo-unit custody transfers at same instant | Both commands compete on same CargoUnits | One legal custodian per unit, inconsistency quarantined with audit | PostgreSQL concurrency + property test |
| `TDD-SIM-24-G15-04` | REPLAY | Offline event resent five times after server crash | Replay same stable event ID, payload digest | Exactly one logical custody movement; no duplicate handover | PostgreSQL inbox unique/replay test |
| `TDD-SIM-24-G15-05` | TENANT | Carrier driver has grant for Trip-1, attempts Trip-2 under different Tenant | Upload pickup evidence | DENY, no evidence leak or foreign cargo mutation | HTTP + RLS |


### BR-10 — Partial POD and conservation / GAP-18

**Business rule owner:** Execution. **Needed review:** Consignee; driver; operations; finance.

| TDD case | Type | Given | When | Then | Test layer |
|---|---|---|---|---|---|
| `TDD-SIM-28-G18-01` | POSITIVE | 10 CargoUnits in custody, consignee accepts 8 and refuses 2 | Recipient signs partial POD | 8 accepted, 2 retained with named custodian/disposition; Shipment not fully DELIVERED | Execution property test + PostgreSQL |
| `TDD-SIM-28-G18-02` | NEGATIVE | Receiver with invalid link or mismatched units attempts mark all delivered | Submit POD for 10 though only 8 scanned/verified | DENY; no delivery proof for remaining 2 | HTTP + domain policy |
| `TDD-SIM-28-G18-03` | RACE | Driver and receiver concurrently submit overlapping POD/delivery attempts | POD acceptance races reattempt for 2 units | No double-counted accepted/returned quantities; per-unit conservation holds | PostgreSQL concurrency + property tests |
| `TDD-SIM-28-G18-04` | REPLAY | Duplicate signed POD callback or offline photos arrive out of order | Process same evidence key twice | One logical accepted quantity; original signature immutable and correction append-only | Inbox + PostgreSQL |
| `TDD-SIM-28-G18-05` | TENANT | Receiver guest token for one DeliveryAttempt accesses other shipment | Read/submit POD for foreign cargo | DENY with no unrelated identity/cargo disclosure | HTTP + RLS |


### BR-11 — Booking cancellation and financial impact / GAP-21

**Business rule owner:** Booking. **Needed review:** Customer; operations manager; commercial; finance.

| TDD case | Type | Given | When | Then | Test layer |
|---|---|---|---|---|---|
| `TDD-SIM-21-G21-01` | POSITIVE | Booking confirmed, no Trip started, customer submits cancel request | Booking owner evaluates policy, consent/charges and versions | Request separate from state; only authorized approval may CANCEL and release capacity with audit | Booking unit + PostgreSQL |
| `TDD-SIM-21-G21-02` | NEGATIVE | Customer sees cancel button while Trip.STARTED with custody | Customer submits direct cancellation | Booking not directly CANCELLED; exception/recovery and cargo disposition required | HTTP + booking guard |
| `TDD-SIM-21-G21-03` | RACE | Trip.STARTED occurs while cancellation approval commits | Both commands operate same Booking expectedVersion | One coherent outcome; no vehicle released with active custody | PostgreSQL concurrency |
| `TDD-SIM-21-G21-04` | REPLAY | Cancellation request and compensation event retransmitted | Same idempotency key after timeout | One cancel request and at most one authorized compensation/release effect | Outbox/Inbox + PostgreSQL |
| `TDD-SIM-21-G21-05` | TENANT | Customer from different provider relationship requests cancellation | Post cancel for foreign Booking | DENY; booking/tariff hidden | HTTP + RLS |


### BR-12 — Payment approval vs bank/ERP settlement / GAP-22

**Business rule owner:** Finance. **Needed review:** Finance controller; independent approver; accounting.

| TDD case | Type | Given | When | Then | Test layer |
|---|---|---|---|---|---|
| `TDD-SIM-32-G22-01` | POSITIVE | Invoice issued, approved payable, verified bank transaction matches currency and legal entity | Finance reconciles unique payment allocation | Balance settles only to extent of verified allocated cash, independent of approval | Finance JUnit + PostgreSQL |
| `TDD-SIM-32-G22-02` | NEGATIVE | Finance user clicks Paid without bank/ERP evidence | Try mark receivable SETTLED | DENY; no accounting state mutation; audit attempted manual override | HTTP + domain policy |
| `TDD-SIM-32-G22-03` | RACE | Two workers process same bank reference simultaneously | Both try allocate identical cash | One unique allocation, no overpayment or duplicate settlement | PostgreSQL concurrency/unique constraint |
| `TDD-SIM-32-G22-04` | REPLAY | Bank callback delivered again after successful response | Inbox replays payment transaction with same verified source key | No second allocation or income recognition, original proof preserved | Finance Outbox/Inbox + PostgreSQL |
| `TDD-SIM-32-G22-05` | TENANT | Finance user from Tenant-B submits payment source reference belonging Tenant-A | Attempt cross-tenant allocation | DENY, no financial detail leak and per legal entity accounts remain separate | HTTP + RLS |


## 4. R0 Safety — 14 fail-closed test contracts

These cases prevent incorrect/silent effects while exceptional workflow UI is not yet fully automated in R0. Each has a corresponding [GAP record](26-role-process-simulation-and-gap-audit.md). They do **not** demand a universal exception handler or rules engine.

| TDD case | GAP | Given | Then | Test level |
|---|---|---|---|---|
| `TDD-SIM-042-S04-01` | GAP-04 | Sales records verified-attribution phone/email request; customer has not accepted anything | Record assisted RFQ with origin and no customer impersonation; acceptance requires separate signer evidence | Commercial + HTTP |
| `TDD-SIM-034-S06-01` | GAP-06 | External contact revoked but colleagues share CustomerOrg-X | Target only member grant revocation, keep other active users and audit stale tokens | Tenancy + RLS |
| `TDD-SIM-008-S07-01` | GAP-07 | Incoming RFQ has absent assignee and two Sales workers | Reassign under branch and expectedVersion; no lost unassigned jobs, never cross-branch | Commercial + PG concurrency |
| `TDD-SIM-015-S10-01` | GAP-10 | Carrier without paid Tenant sends confirmation through approved constrained channel | Record explicit verified counterparty evidence and grant, no automatic internal carrier membership | Commercial + HTTP |
| `TDD-SIM-017-S11-01` | GAP-11 | Provider uses own truck with no external CarrierOffer | Fleet exclusive hold/confirm succeeds without fictitious third-party offer | Fleet/Booking + PG |
| `TDD-SIM-023-S14-01` | GAP-14 | Driver discovers wrong weight/units or broken seal on pickup | Do not create IN_CUSTODY; create auditable mismatch/incident for owner review | Execution + JUnit |
| `TDD-SIM-025-S16-01` | GAP-16 | Assigned vehicle breaks down with cargo already in custody | Append incident and handover/RecoveryCase; do not overwrite original carrier, keep custodian known | Execution + PG |
| `TDD-SIM-027-S17-01` | GAP-17 | Receiver absent or declines to sign | Failed DeliveryAttempt and continued named custody, not Shipment.DELIVERED | Execution + HTTP |
| `TDD-SIM-029-S19-01` | GAP-19 | Guest POD recipient has expired/guessed delivery link | DENY unless exactly scoped authorized recipient, immutable evidence | Documents + HTTP |
| `TDD-SIM-030-S20-01` | GAP-20 | Verified POD access revoked while old presigned URL exists | Protected API denies immediately; signed URL exposure bounded/documented; never claim hard revoke without proxy | Documents + RustFS/HTTP |
| `TDD-SIM-031-S23-01` | GAP-23 | Carrier claims disputed surcharge after original Invoice issued | Block auto payable and in-place invoice edits, preserve independent dispute | Finance + PG |
| `TDD-SIM-026-S24-01` | GAP-24 | GPS cache is stale and partner grant revoked | Customer sees stale/unavailable time marked; no foreign live coordinates or post-revoke updates | Tracking + HTTP |
| `TDD-SIM-029-S25-01` | GAP-25 | Customer reports cargo issue before completion | Accept scoped issue with evidence, keep review eligibility independent | Commercial/Execution + HTTP |
| `TDD-SIM-035-S26-01` | GAP-26 | Job handler retries after user membership revoke | Re-check service scope and resource grant; deny stale authority, preserve dedup and audit | Jobs + PG/RLS |

## 5. Cross-role real user acceptance — 10 E2E scenarios

These are acceptance plans that require a running backend, migrations, security, test data and a user-facing API/portal. **No real sessions were run.**

| E2E ID | Journey | Expected business result | Required integration | SIM refs |
|---|---|---|---|---|
| `TDD-R0-E2E-01` | CustomerOrg-X invited -> RFQ -> provider inbox -> quote approved -> customer acceptance | Customer sees own business objects; provider sees only allowed queue; no Booked until capacity | HTTP + PG RLS + Modulith | `SIM-04`, `SIM-07`, `SIM-09`, `SIM-13` |
| `TDD-R0-E2E-02` | Forwarder + external carrier -> offer -> capacity hold -> confirmed booking | Customer can see Booking confirmed only after authoritative Fleet and compliance verification | PostgreSQL concurrency + API + Outbox | `SIM-15`, `SIM-16`, `SIM-18`, `SIM-20` |
| `TDD-R0-E2E-03` | Own fleet instead of external carrier | No fake CarrierOffer required, same exclusive reservation invariants | Fleet + Booking integration Testcontainers | `SIM-17`, `SIM-18` |
| `TDD-R0-E2E-04` | Driver online/offline pickup -> partial POD 8/10 -> remaining returned | Cargo conservation and original proof immutable; track customer-safe statuses | Execution + Documents + HTTP | `SIM-24`, `SIM-28`, `SIM-29` |
| `TDD-R0-E2E-05` | Confirmed Booking cancellation before/after Trip.STARTED | Request-only separation and correct compensation/custody branch | Booking + Execution + Finance Testcontainers | `SIM-21`, `SIM-22` |
| `TDD-R0-E2E-06` | Payable approved -> advance + partial bank receipt + duplicate callback | No false Paid, unique allocations and money precision | Finance + verified mock adapter + PostgreSQL | `SIM-31`, `SIM-32` |
| `TDD-R0-E2E-07` | Subscription suspended while active custody and mandatory POD pending | Only approved safety continuity, no new discretionary booking, no cargo evidence stranded | SaaS + Execution + HTTP | `SIM-41` |
| `TDD-R0-E2E-08` | Provider staff phone RFQ and explicit later customer acceptance | Captured request provenance distinct from customer signatory; no forged approval | Commercial + Tenancy + HTTP | `SIM-42` |
| `TDD-R0-E2E-09` | Revoke CustomerAccount grant while read cache and signed link active | Future protected API denies; signed URL TTL semantics explicit | HTTP+Cache+Documents | `SIM-34`, `SIM-35` |
| `TDD-R0-E2E-10` | Carrier withdraws after customer accepted quote before/after hold | Booking never falsely confirmed; exception and replacement sourced safely | Commercial + Fleet + Booking | `SIM-16`, `SIM-20` |

## 6. Java TDD and Testcontainers implementation plan

```text
src/test/java/kz/keruenix/
  tenancy/
    CustomerAccountGrantPolicyTest.java
    TenantRlsIsolationIT.java
    OwnerAndAdminProvisioningIT.java
  commercial/
    QuoteAuthorityAndVersionPolicyTest.java
    RfqIdempotencyIT.java
    CarrierOfferLifecycleIT.java
  fleet/
    ExclusiveCapacityHoldIT.java
    CapacityExpiryRaceIT.java
  booking/
    BookingConfirmationInvariantTest.java
    CancellationRequestedNotCancelledIT.java
  execution/
    CargoUnitConservationPropertyTest.java
    OfflinePickupReplayIT.java
    PartialPodAndCustodyIT.java
  finance/
    PaymentApprovalSeparationTest.java
    VerifiedBankAllocationIdempotencyIT.java
  platform/
    TenantScopedJobReplayIT.java
  acceptance/
    ExternalCustomerToBookingE2EIT.java
    ShipmentToPodAndFinanceE2EIT.java
```

**This is a proposed file layout, not existing files.** Actual package structure should follow module-owned Spring Modulith boundaries and the selected Maven organization.

**Red → Green → Refactor first vertical slice:**
1. Define `TDD-SIM-013-G01-02`: EXC Viewer cannot accept a customer quote; **RED** at policy/HTTP layer.
2. Implement smallest `CommercialAuthorizationPolicy` and account grant checks, make test **GREEN** without bypassing RLS.
3. Define `TDD-SIM-013-G01-03`: concurrent expiry vs acceptance, test real PostgreSQL version race.
4. Repeat for `ExclusiveCapacityHoldIT`, `OfflinePickupReplayIT`, `CargoUnitConservationPropertyTest`, `VerifiedBankAllocationIdempotencyIT`.
5. Refactor mapper DTO ↔ immutable commands with MapStruct; generated DTO mapping must never import client-supplied `tenantId`, `approvalState` or mutable aggregate state.

**Required technical acceptance:** JUnit Jupiter / AssertJ / Spring Modulith `ApplicationModules.verify()` / `@ApplicationModuleTest`, Flyway migration test, Testcontainers PostgreSQL/PostGIS, actual RLS integration, Mockito only for pure upstream boundaries, JaCoCo for visibility, exact SHA CI logs. API and event schema compatibility included.

## 7. CI gates and completion evidence

| Gate | Criteria | Status now |
|---|---|---|
| TDD-READY | Business owner approves all affected `BR-*` decisions and named legal signature/cancellation/payment policies | `PENDING` |
| UNIT | All approved domain policy guards/invariants pass JUnit and property tests | `NOT RUN` |
| DB | Tenant RLS, capacity races, cargo conservation and payment uniqueness pass real PostgreSQL | `NOT RUN` |
| CONTRACT | OpenAPI/event versions and Modulith boundaries verified; no cross-module repository shortcuts | `NOT RUN` |
| E2E | Two tenants + external CustomerOrg + carrier complete RFQ → Quote → Booking → POD → finance | `NOT RUN` |
| FAILURE | Network/replay/Redis outage, subscription safety continuity, revoked grants, signed URL limitations tested | `NOT RUN` |
| RELEASE | Exact Git SHA and full passing CI/report references recorded with stakeholder approval | `NOT RUN` |

Each result must record `testId, requirementId, storyId, decisionId, scenarioId, appSha, migrationVersion, fixtureVersion, dateUtc, environment, evidenceLink, reviewer, actualOutcome`. Paper acceptance does not count as green CI. A normal deny does not guarantee compliance with unspecified Kazakhstani legal signing/document rules.

## 8. Test selection guidance — all variants without combinatorial explosion

Do not promise exhaustive coverage. Mandatory are the 12 blocking decisions (five risk dimensions each), 14 minimum safety denial pathways, 10 cross-role customer/forwarder/carrier journeys. Then use property-based tests for cargo conservation and financial allocations, pairwise combinations for noncritical variants and deliberate 3-way combinations of actor + tenant + stale state for high-risk breaches.

High-risk specifically: quote expiry + signatory revocation + previous version; vehicle interval + hold expiry job + two dispatchers; offline pickup + driver reassignment + out-of-order replay; partial delivery + returned units + duplicate POD; bank reference + two workers + disputed surcharge; suspended subscription + cargo in custody + POD pending.

**Unapproved permission gap:** do not implement EXC `quote:decline`, carrier withdrawal, material post-acceptance amendment, direct currency conversion, compensation posting or compliance override merely because an imagined UI needs it. Design the domain-owned `AUTH` policy and signoff first; current v2.1 contains 67 draft permissions and is not an execution-ready role database.

## 9. Practical status

- **Specified:** 60 blocker tests, 14 safety tests and 10 cross-role cases.
- **Not done:** real end-user interviews/signoff; Spring Boot/Java test implementation; Testcontainers execution; RLS code qualification; integration E2E on exact SHA.
- **Next code prerequisite:** Gradle/Maven project bootstrap (choose project standard: Maven Java21), Spring Modulith Tenancy/Commercial slice and database migrations. The absence of code is not a reason to falsely claim green tests.

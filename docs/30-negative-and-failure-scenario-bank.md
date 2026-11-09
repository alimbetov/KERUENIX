# 30 — Negative & Failure Scenario Bank: R0 Roles, State Transitions and Recovery

**Date:** 2026-11-07 · **Version:** 1.0 · **Status:** `DESIGNED / BUSINESS-LEGAL REVIEW PENDING / NOT IMPLEMENTED / NOT RUN`.

**Canonical contract:** [r0-negative-scenarios.v1.json](contracts/r0-negative-scenarios.v1.json).
**Existing TDD baseline:** [28 — R0 Acceptance Bank](28-r0-tdd-acceptance-bank.md), [JSON](contracts/r0-tdd-scenarios.v1.json).
**Upstream design:** [User Story Book](21-user-story-book.md), [Business Scenarios](25-business-scenario-book.md), [Role Simulation](26-role-process-simulation-and-gap-audit.md), [12 Business Policy Decisions](27-r0-blocker-policy-decisions.md), [Access Governance v2.1](24-access-control-tdd-matrix-v2.md).

## 1. Audit result and why the original tests were insufficient

The previous baseline has **84 draft tests**: 60 decision variants (positive, negative, race, replay, tenant), 14 R0 safety cases, 10 E2E journeys. These cover major guardrails but are not enough to prove **failure containment** across actual customer/cargo/money operations. A denied HTTP request alone does not prove that a database row, Outbox event, notification or stale read projection was not already changed.

This bank adds **48 risk-selected cases**, grouped into 12 security/business fault families. They are **additional scenarios**, not duplicate relabels of the prior 84 and **not running tests**.

| Bank | Existing planned | New planned | Combined planned |
|---|---:|---:|---:|
| Blocker/Safety/Cross-role [28] | 84 | 0 | 84 |
| Negative/failure [30] | 0 | 48 | 48 |
| **All R0 proposed acceptance** | **84** | **48** | **132** |

**Limits:** 132 are proposed **test case specifications**, not 132 test methods or green checks. Some scenarios may be executed efficiently via JUnit parameterized variants or one integrated fixture. No finite count proves exhaustive combinations.

## 2. Negative-test contract: what every meaningful denial must verify

A full negative test should record **at least six observable outcomes**:

1. **Principal/permission/relationship**: correct verified actor and active tenant/customer-account/grant; no fallback from `Customer Viewer` to `Customer Signatory`, or platform operator to Tenant data reader.
2. **Valid aggregate state and expectedVersion**: no illegal transition, stale update, phantom Booking/custody/POD/settlement.
3. **Database**: assert unchanged canonical state, resource quantity, account scope and snapshot (or an explicitly allowed audit/incident/quarantine record) using actual PostgreSQL and RLS.
4. **Side effects**: assert no false Outbox/Inbox/notification, no duplicate financial allocation, release or signed document; retries may deliver an event at least once but must not duplicate its **business effect**.
5. **User-visible truth**: deny/conflict/retry/pending/exception shown correctly; a failed backend read must not render as an empty successful order list.
6. **Audit and privacy**: record permitted security reason, actor, tenant, resource, policy version, correlation ID without secrets or unrelated personal/financial payload.

Where an error can be safely distinguished:
- unauthenticated → candidate `401`;
- authenticated without permission → candidate `403`;
- protected foreign resource → consistent `404` or indistinguishable denial to avoid resource-existence enumeration;
- stale aggregate version/idempotency payload conflict → candidate `409`;
- invalid business state/precondition → a **versioned domain error code** with HTTP mapping to agree (e.g. `409` or `422`).

These codes are design recommendations pending API conventions; do not hardcode speculative HTTP semantics in TDD until the contract is accepted. Authorization is rechecked inside the command/domain boundary, not only at web controller entry. Reject dangerous writes **atomically**.

## 3. Risk matrix — 12 negative/fault families

| IDs | Area | What was missing |
|---|---|---|
| 01–04 | Identity / Platform Super Admin | Подмена приглашения, последний Owner, административный обход, второй аккаунт того же согласующего |
| 05–08 | CustomerAccount / Multi-Tenant | Утечка через count/pagination, отзыв прав между запросами, email-domain autojoin, смешение полей buyer/carrier |
| 09–12 | RFQ / Quote | Подделка акцепта менеджером, чужой termsHash, retry с изменённым payload, гонка отказа и акцепта |
| 13–16 | Carrier / Procurement | Отзыв до HELD, подтверждение после revoke, утечка sell margin, own-fleet без фиктивного carrier |
| 17–20 | Fleet / Booking | Конкурентные слоты между филиалами, просроченный expiry job, частичный hold, Outbox replay |
| 21–24 | Compliance | UNKNOWN как ALLOW, истёкший норматив, обход ручным override, устаревшее ALLOW-событие |
| 25–28 | Custody / Offline | Поддельное observedAt, повтор с иным payload, смена водителя без handover, поздний pickup после POD |
| 29–32 | POD / Documents | Повторное использование guest-link, ложный full POD 8/10, переписывание оригинала, TTL старого URL |
| 33–36 | Finance | Самоутверждение через второй аккаунт, разные callback IDs одной оплаты, FX mismatch, reversal |
| 37–40 | SaaS / Access lifecycle | Suspended tenant и POD, опасный fallback, booking по safety credential, отзыв только в UI |
| 41–44 | Jobs / Projections | Outbox duplicate, revoked context, PII в логах, stale booking projection |
| 45–48 | Cancellation / Claims / Review | Подмена комиссии отмены, гонка отмены и старта, претензия как POD/refund, self-review |

The 12 families are **test taxonomy**, not 12 new modules or 12 new roles.

## 4. Full negative scenario cards — Given / When / Then + four layers of evidence

### IDENTITY — Platform and tenant identity / privilege escalation (4)

#### NEG-R0-001 — Bootstrap invite token swapped across legal entities

**Actor:** Invited owner of Tenant-A. **Priority:** `P0_SECURITY`. **Links:** `GAP-03` · `SIM-01` · `USB-PSA-001` · `AUTH-TEN-002`.

- **Given:** A pending owner invitation is bound to verified A legal entity and recipient
- **When:** Replay the same token on pending Tenant-B or different verified principal
- **Then / authoritative decision:** DENY: no cross-entity initial owner bootstrap
- **DB/canonical invariant:** Tenant-B has no owner membership from token; Tenant-A invitation still scoped
- **Outbox/Inbox/Jobs/Documents:** No OwnerActivated for Tenant-B
- **User-visible outcome:** Invite rejected without tenant-B metadata
- **Execution layer:** HTTP+PostgreSQL RLS. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-002 — Last owner revocation races owner transfer

**Actor:** Tenant Owner. **Priority:** `P0_SECURITY`. **Links:** `GAP-03` · `SIM-03` · `USB-TNO-001` · `AUTH-TEN-006`.

- **Given:** Tenant-A has one active owner and a not-yet-accepted successor
- **When:** Revoke owner concurrently with successor invitation acceptance
- **Then / authoritative decision:** DENY removal unless successor accepted and owner invariant atomically holds
- **DB/canonical invariant:** At least one active verified owner after every commit
- **Outbox/Inbox/Jobs/Documents:** No orphan-Tenant activation or misleading owner-revoked event
- **User-visible outcome:** Owner transfer pending or conflict, never silently ownerless
- **Execution layer:** PostgreSQL concurrency. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-003 — Admin grants itself through inherited template

**Actor:** Tenant Admin. **Priority:** `P0_SECURITY`. **Links:** `GAP-03` · `SIM-03` · `USB-TEN-003` · `AUTH-X-004`.

- **Given:** Admin may grant staff templates but not owners or Finance approval
- **When:** Submit composite role template that includes nondelegable permission
- **Then / authoritative decision:** DENY entire unauthorized grant; no partial privilege elevation
- **DB/canonical invariant:** RoleAssignment unchanged; no hidden approval capability granted
- **Outbox/Inbox/Jobs/Documents:** No RoleGranted event for rejected assignment
- **User-visible outcome:** Clear permission denied without exposing admin configuration secrets
- **Execution layer:** Policy JUnit+HTTP+RLS. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-004 — Second signoff uses same human via another account

**Actor:** Platform Super Admin. **Priority:** `P0_SECURITY`. **Links:** `GAP-01` · `SIM-02` · `USB-PSA-002` · `AUTH-TEN-004`.

- **Given:** High-risk owner recovery requires independent reviewers
- **When:** Initiator approves the request using secondary login identity linked to same principal
- **Then / authoritative decision:** DENY: distinct credential is not distinct approving person
- **DB/canonical invariant:** Recovery remains pending; approval actor identity distinctness preserved
- **Outbox/Inbox/Jobs/Documents:** No OwnerRecovered event
- **User-visible outcome:** Recovery still waiting for independent authorization
- **Execution layer:** Policy JUnit+PostgreSQL. **Status:** `DESIGNED_NOT_EXECUTED`.

### CUSTOMER — External customer account and data isolation (4)

#### NEG-R0-005 — Customer Org Y sees page count of Org X

**Actor:** External Customer Viewer. **Priority:** `P0_SECURITY`. **Links:** `GAP-03` · `SIM-05` · `USB-EXC-003` · `AUTH-X-001`.

- **Given:** Customer-X and Y share provider Tenant-A; X has 11 private orders, Y has 0
- **When:** Request filtered list/sort/pagination with X ID and cursor
- **Then / authoritative decision:** DENY cross-account data including totals/facets, not only item content
- **DB/canonical invariant:** No customer-X IDs or counts returned; query scoped before pagination
- **Outbox/Inbox/Jobs/Documents:** No export or cache entry from X attributed to Y
- **User-visible outcome:** Y sees empty/unauthorized correctly; no count side-channel
- **Execution layer:** HTTP+PostgreSQL RLS. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-006 — Customer relation revoked between list and detail download

**Actor:** External Customer. **Priority:** `P0_SECURITY`. **Links:** `GAP-03` · `SIM-34` · `USB-EXC-008` · `AUTH-X-007`.

- **Given:** EXC receives order list but grant is revoked before detail/POD request
- **When:** Use previously received orderId and old session for detail/download
- **Then / authoritative decision:** DENY every new protected read after committed revoke
- **DB/canonical invariant:** No customer data returned from old cached projection; read-only DB protected
- **Outbox/Inbox/Jobs/Documents:** No document link issuance, no customer-specific notification
- **User-visible outcome:** Access revoked state, not stale order data
- **Execution layer:** HTTP+RLS+cache. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-007 — Shared email domain used to auto-join provider CustomerAccount

**Actor:** Tenant Admin. **Priority:** `P0_SECURITY`. **Links:** `GAP-03` · `SIM-04` · `USB-TEN-005` · `AUTH-X-015`.

- **Given:** CustomerCorp X uses same email domain as unrelated contractor
- **When:** Invite unverified mailbox to X account by domain inference
- **Then / authoritative decision:** DENY without explicit verified identity and organization relationship
- **DB/canonical invariant:** No cross-org membership or provider Tenant employee assignment
- **Outbox/Inbox/Jobs/Documents:** No invitation accepted/role granted event
- **User-visible outcome:** Verification required
- **Execution layer:** HTTP+Tenancy Testcontainers. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-008 — Scoped search and export mixes buyer and carrier fields

**Actor:** EXC who also works for Carrier-C. **Priority:** `P0_SECURITY`. **Links:** `GAP-03` · `SIM-38` · `USB-EXC-003` · `AUTH-X-023`.

- **Given:** Same principal holds multiple explicit customer/provider contexts
- **When:** Switch from carrier view to buyer export using stale active context/cache key
- **Then / authoritative decision:** DENY field/context confusion; context derived from verified grant per request
- **DB/canonical invariant:** Projection excludes margin, supplier buy rates, foreign shipment and ungranted PII
- **Outbox/Inbox/Jobs/Documents:** No unscoped CSV export job created
- **User-visible outcome:** Only authorized customer-safe columns; no hidden cross-role data
- **Execution layer:** HTTP+CSV projection+RLS. **Status:** `DESIGNED_NOT_EXECUTED`.

### QUOTE — RFQ and legally significant Quote authorization (4)

#### NEG-R0-009 — Customer acceptance forged through provider staff request

**Actor:** Sales staff. **Priority:** `P0_LEGAL_COMMERCIAL`. **Links:** `GAP-01` · `SIM-42` · `USB-SAL-009` · `TDD-R0-E2E-08`.

- **Given:** Sales created assisted phone RFQ, customer has no verified acceptance evidence
- **When:** Sales submits Quote accept with customer's name/phone but own provider identity
- **Then / authoritative decision:** DENY legally significant acceptance; leave ISSUED
- **DB/canonical invariant:** No QuoteVersion.ACCEPTED; no signer evidence fabricated
- **Outbox/Inbox/Jobs/Documents:** No Booking request event based on counterfeit acceptance
- **User-visible outcome:** Customer must approve via authorized method
- **Execution layer:** Commercial HTTP+PostgreSQL. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-010 — Quote terms replaced after delegated signing proof

**Actor:** Customer Signatory. **Priority:** `P0_LEGAL_COMMERCIAL`. **Links:** `GAP-01` · `SIM-13` · `USB-EXC-004` · `AUTH-EXT-006`.

- **Given:** Delegation proof is valid for version v3 and its terms digest
- **When:** Send old signature proof with newer quote version v4 / amount changed
- **Then / authoritative decision:** DENY because version and terms hashes mismatch
- **DB/canonical invariant:** v4 remains ISSUED; v3 proof immutable
- **Outbox/Inbox/Jobs/Documents:** No Accepted(v4) event
- **User-visible outcome:** Present new terms and require new signature
- **Execution layer:** Commercial JUnit+HTTP+PG. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-011 — Same idempotency key with changed cargo payload

**Actor:** EXC Requester. **Priority:** `P0_LEGAL_COMMERCIAL`. **Links:** `GAP-08` · `SIM-07` · `USB-EXC-002` · `AUTH-EXT-002`.

- **Given:** A submitted RFQ exists for idempotency key K and content hash H1
- **When:** Retry request K with different weight or destination H2
- **Then / authoritative decision:** CONFLICT; do not treat as successful replay or silent amendment
- **DB/canonical invariant:** One original RFQ; original cargo snapshot unchanged
- **Outbox/Inbox/Jobs/Documents:** No second RFQSubmitted or QuoteRequested event
- **User-visible outcome:** Conflict and explicit amendment action; no false success
- **Execution layer:** HTTP+PostgreSQL unique constraint. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-012 — Quote decline replay after later accept/expiry

**Actor:** Authorized customer decliner. **Priority:** `P0_LEGAL_COMMERCIAL`. **Links:** `GAP-02` · `SIM-13` · `USB-EXC-014` · `AUTH-X-019`.

- **Given:** Quote is declined or expires concurrently with another decision
- **When:** Retry old decline with changed reason / stale expectedVersion
- **Then / authoritative decision:** No state regression or mutation; only identical prior request may return idempotent result
- **DB/canonical invariant:** Quote transition remains authoritative; immutable audit preserved
- **Outbox/Inbox/Jobs/Documents:** No duplicate customer decision event
- **User-visible outcome:** Show actual current quote state and refresh
- **Execution layer:** PG concurrency+HTTP. **Status:** `DESIGNED_NOT_EXECUTED`.

### CARRIER — External carrier commitments and procurement boundaries (4)

#### NEG-R0-013 — Carrier withdraws selected offer while hold is requested

**Actor:** Carrier Manager. **Priority:** `P0_COMMERCIAL`. **Links:** `GAP-09` · `SIM-16` · `USB-CAR-003` · `LFC-006`.

- **Given:** Carrier offer SELECTED but no authoritative capacity CONFIRMED
- **When:** Carrier sends WITHDRAWN concurrently with Fleet HELD request
- **Then / authoritative decision:** Only valid ordered supplier/hold state; unresolved booking cannot confirm
- **DB/canonical invariant:** Either valid confirmed proof before cutoff or exception; no unbacked reservation
- **Outbox/Inbox/Jobs/Documents:** Booking confirmation event absent without valid capacity evidence
- **User-visible outcome:** Customer sees pending/re-sourcing, never false confirmed
- **Execution layer:** PG concurrency+Modulith. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-014 — Carrier loses authorization before asynchronous confirmation

**Actor:** Carrier Manager. **Priority:** `P0_COMMERCIAL`. **Links:** `GAP-09` · `SIM-15` · `USB-CAR-001` · `AUTH-FLT-002`.

- **Given:** Supplier grant active at offer request, revoked before delayed callback
- **When:** Delayed carrier confirmation arrives after revocation
- **Then / authoritative decision:** DENY new binding capacity; retain historical callback evidence separately
- **DB/canonical invariant:** No unauthorized CapacityReservation.CONFIRMED; grant state checked
- **Outbox/Inbox/Jobs/Documents:** Callback quarantined/reconciled, no BookingConfirmed event
- **User-visible outcome:** Carrier lacks permission; forwarder sees exception
- **Execution layer:** Outbox/Inbox+PG. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-015 — Procurement quote response leaks forwarder profit

**Actor:** Carrier Tenant-C. **Priority:** `P0_COMMERCIAL`. **Links:** `GAP-03` · `SIM-15` · `USB-PRC-001` · `AUTH-COM-009`.

- **Given:** Carrier has scoped active partner grant for one request
- **When:** Read carrier offer page or download attachment containing internal sell quote/margin
- **Then / authoritative decision:** DENY hidden field disclosure while preserving allowed carrier terms
- **DB/canonical invariant:** No internal margin in body, export, logs, downloadable artifacts
- **Outbox/Inbox/Jobs/Documents:** No export job or signed URL containing restricted fields
- **User-visible outcome:** Only own buy-side and required cargo/route information
- **Execution layer:** HTTP+JSON allowlist+RLS. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-016 — Own-fleet confirmation wrongly requires external carrier offer

**Actor:** Planner. **Priority:** `P0_COMMERCIAL`. **Links:** `GAP-09` · `SIM-17` · `USB-PLN-003` · `TDD-R0-E2E-03`.

- **Given:** Tenant-A owns vehicle, legal owner capacity authority and valid compliance
- **When:** Create Booking with own vehicle and no CarrierOffer
- **Then / authoritative decision:** Do not reject valid own-fleet path and do not fabricate external Carrier identity
- **DB/canonical invariant:** One own-fleet reservation, no fake CarrierOffer or external PartnerGrant
- **Outbox/Inbox/Jobs/Documents:** No bogus CarrierOfferSelected event
- **User-visible outcome:** Provider sees internally confirmed vehicle after actual capacity proof
- **Execution layer:** Fleet+Booking Testcontainers. **Status:** `DESIGNED_NOT_EXECUTED`.

### CAPACITY — Fleet reservation, Booking and concurrent state (4)

#### NEG-R0-017 — Two overlapping holds commit across different branches

**Actor:** Two Dispatchers. **Priority:** `P0_CORRECTNESS`. **Links:** `GAP-12` · `SIM-18` · `USB-PLN-001` · `LFC-007`.

- **Given:** Same shared vehicle/trailer/driver exists across provider branches
- **When:** Both branches reserve overlapping UTC intervals in parallel
- **Then / authoritative decision:** At most one exclusive active hold/confirmation for physical resource
- **DB/canonical invariant:** DB exclusion or row lock enforces physical uniqueness independent of branch
- **Outbox/Inbox/Jobs/Documents:** Only winning reservation produces hold outbox event
- **User-visible outcome:** Loser receives conflict/reselect vehicle, not confirmed
- **Execution layer:** PostgreSQL real concurrent transactions. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-018 — Stale expiry job releases already confirmed hold

**Actor:** Fleet Job. **Priority:** `P0_CORRECTNESS`. **Links:** `GAP-12` · `SIM-18` · `USB-DSP-001` · `AUTH-FLT-001`.

- **Given:** HELD expiry task queued, dispatch confirms the same hold with newer version
- **When:** Run old expiry task after confirmation commit
- **Then / authoritative decision:** No release of CONFIRMED/CONSUMED capacity by stale job
- **DB/canonical invariant:** CONFIRMED version and booking remain intact
- **Outbox/Inbox/Jobs/Documents:** No ReservationReleased event from old version
- **User-visible outcome:** Booking stays confirmed, not 'resource unavailable'
- **Execution layer:** PostgreSQL+Jobs fencing. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-019 — Partial capacity reservation in multi-resource failure

**Actor:** Planner. **Priority:** `P0_CORRECTNESS`. **Links:** `GAP-12` · `SIM-18` · `USB-DSP-001` · `AUTH-BKG-001`.

- **Given:** Vehicle available but required trailer or driver unavailable
- **When:** Attempt atomic reservation of all mandatory resources
- **Then / authoritative decision:** Fail entire operation or compensate consistently; never confirm partial resource set
- **DB/canonical invariant:** No stranded active HELD for vehicle if transaction fails; exact released state if saga
- **Outbox/Inbox/Jobs/Documents:** No BookingConfirmed; no orphan reservation event
- **User-visible outcome:** Needs alternate driver/trailer; not confirmed
- **Execution layer:** PostgreSQL transaction/constraint. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-020 — Outbox failure after Booking confirmation triggers second booking

**Actor:** Booking Worker. **Priority:** `P0_CORRECTNESS`. **Links:** `GAP-12` · `SIM-20` · `USB-DSP-001` · `TDD-R0-E2E-02`.

- **Given:** Booking and Outbox commit succeeded but publish ack lost
- **When:** Retry command and publish same event twice
- **Then / authoritative decision:** One Booking and one logical business outcome; consumers deduplicate
- **DB/canonical invariant:** Same booking ID/version; no additional exclusive capacity
- **Outbox/Inbox/Jobs/Documents:** Event published at-least-once but consumer effect exactly once logically
- **User-visible outcome:** Client can refresh authoritative booking, not duplicate cards
- **Execution layer:** Modulith+Outbox+PG. **Status:** `DESIGNED_NOT_EXECUTED`.

### COMPLIANCE — Regulatory/legal safety hold (4)

#### NEG-R0-021 — Missing authoritative rule treated as noncritical pass

**Actor:** Dispatcher. **Priority:** `P0_SAFETY`. **Links:** `GAP-13` · `SIM-19` · `USB-COM-001` · `LFC-009`.

- **Given:** Cargo requires regulated permit; rule source unavailable or unknown
- **When:** Press mark-ready/confirm without qualified Compliance evidence
- **Then / authoritative decision:** DENY and retain critical UNKNOWN/HOLD
- **DB/canonical invariant:** No READY or Booking confirmation from UNKNOWN
- **Outbox/Inbox/Jobs/Documents:** No trip-dispatch/customer confirmation event
- **User-visible outcome:** Display compliance review required, not ready
- **Execution layer:** Policy JUnit+HTTP. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-022 — Compliance approval based on expired source

**Actor:** Compliance Reviewer. **Priority:** `P0_SAFETY`. **Links:** `GAP-13` · `SIM-19` · `USB-COM-002` · `LFC-009`.

- **Given:** Compliance approval references rule/permit expired before Trip READY
- **When:** Execute downstream READY or confirm Booking
- **Then / authoritative decision:** DENY until fresh qualified evidence/review
- **DB/canonical invariant:** Approval version no longer validates current cargo/route snapshot
- **Outbox/Inbox/Jobs/Documents:** No ready/departure instruction event
- **User-visible outcome:** Renew/reverify mandatory documents
- **Execution layer:** Clock+PG integration. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-023 — Unknown route segment bypassed by manual dispatcher override

**Actor:** Dispatcher. **Priority:** `P0_SAFETY`. **Links:** `GAP-13` · `SIM-19` · `USB-COM-001` · `AUTH-X-016`.

- **Given:** Route contains segment with unresolved official restriction
- **When:** Actor submits manual override with invented reason
- **Then / authoritative decision:** DENY nonqualified actor; no implicit legal clearance
- **DB/canonical invariant:** Compliance HOLD and route provenance retained
- **Outbox/Inbox/Jobs/Documents:** No override-applied event
- **User-visible outcome:** Operator sees independent review requirement
- **Execution layer:** HTTP+Compliance security policy. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-024 — Later DENY event processed before older ALLOW event

**Actor:** Compliance async consumer. **Priority:** `P0_SAFETY`. **Links:** `GAP-13` · `SIM-19` · `USB-COM-002` · `LFC-009`.

- **Given:** Regulatory source emits versions 6 DENY then delayed version 5 ALLOW
- **When:** Consumer replays old ALLOW after current DENY
- **Then / authoritative decision:** Do not regress to ALLOW on outdated evidence
- **DB/canonical invariant:** Persist current rule version/decision; monotonic version check
- **Outbox/Inbox/Jobs/Documents:** No BookingUnlocked event
- **User-visible outcome:** Hold remains until current approved review
- **Execution layer:** Outbox/Inbox+PG. **Status:** `DESIGNED_NOT_EXECUTED`.

### CUSTODY — Driver, offline events and custody chronology (4)

#### NEG-R0-025 — Forged offline observedAt before revoked assignment

**Actor:** Former Driver. **Priority:** `P0_CUSTODY`. **Links:** `GAP-15` · `SIM-24` · `USB-DRV-002` · `LFC-011`.

- **Given:** Driver assignment revoked, device still has offline queue
- **When:** Forge event timestamp preceding revocation with invalid evidence/assignment snapshot
- **Then / authoritative decision:** DENY current custody mutation; suspicious historical evidence quarantined
- **DB/canonical invariant:** Custody ledger unchanged; invalid event recorded separately for investigation
- **Outbox/Inbox/Jobs/Documents:** No PickupConfirmed for forged event
- **User-visible outcome:** Driver told evidence needs reconciliation, not success
- **Execution layer:** Execution policy+PG. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-026 — Duplicate offline event payload differs on same eventId

**Actor:** Driver App. **Priority:** `P0_CUSTODY`. **Links:** `GAP-15` · `SIM-24` · `USB-DRV-002` · `LFC-029`.

- **Given:** Earlier offline eventId E1 accepted for CargoUnits [A,B]
- **When:** Replay E1 with different cargo unit set or proof hash
- **Then / authoritative decision:** CONFLICT/quarantine, never ignore changed payload as identical retry
- **DB/canonical invariant:** One original custody effect, tamper/replay attempt audit
- **Outbox/Inbox/Jobs/Documents:** No second PickupConfirmed
- **User-visible outcome:** Show conflict, request support/inspection
- **Execution layer:** PostgreSQL Inbox unique+hash. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-027 — Replacement driver receives cargo before previous custodian handover

**Actor:** Dispatcher. **Priority:** `P0_CUSTODY`. **Links:** `GAP-15` · `SIM-25` · `USB-DSP-006` · `LFC-032`.

- **Given:** Trip INTERRUPTED; cargo assigned to previous driver custodian
- **When:** Assign replacement driver and mark custody transferred without signed handover
- **Then / authoritative decision:** DENY custody transfer without handover evidence
- **DB/canonical invariant:** Original custodian retained pending qualified transfer, no phantom transfer
- **Outbox/Inbox/Jobs/Documents:** No successful handover event
- **User-visible outcome:** Trip interruption visible, replacement pending handover
- **Execution layer:** Execution aggregate/property. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-028 — Late offline pickup after POD from newer legitimate attempt

**Actor:** Execution Inbox. **Priority:** `P0_CUSTODY`. **Links:** `GAP-15` · `SIM-24` · `USB-DRV-002` · `LFC-032`.

- **Given:** Customer already has confirmed later custody/POD for same cargo unit
- **When:** Receive earlier offline pickup not previously reconciled
- **Then / authoritative decision:** Do not rewind custody or double deliver; quarantine order conflict
- **DB/canonical invariant:** Current custody and accepted units unchanged
- **Outbox/Inbox/Jobs/Documents:** No stale PickupConfirmed / DeliveryReversed event
- **User-visible outcome:** No status regression in My Orders
- **Execution layer:** PG ordering+Outbox consumer. **Status:** `DESIGNED_NOT_EXECUTED`.

### POD — Consignee, partial delivery and document evidence (4)

#### NEG-R0-029 — Guest receiver link reused for another delivery attempt

**Actor:** Guest Receiver. **Priority:** `P0_CUSTODY`. **Links:** `GAP-18` · `SIM-27` · `USB-RCV-001` · `AUTH-X-012`.

- **Given:** One-time proof link bound to DeliveryAttempt-1 and recipient
- **When:** Reuse link for DeliveryAttempt-2 or after expiration
- **Then / authoritative decision:** DENY outside exact attempt/validity, no equivalent company-wide access
- **DB/canonical invariant:** No signed POD or foreign CargoUnit disclosure
- **Outbox/Inbox/Jobs/Documents:** No DeliveryAccepted event
- **User-visible outcome:** Link invalid/not authorized
- **Execution layer:** HTTP+RLS+one-time token. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-030 — POD 8/10 falsely marks shipment delivered

**Actor:** Receiver. **Priority:** `P0_CUSTODY`. **Links:** `GAP-18` · `SIM-28` · `USB-RCV-002` · `LFC-035`.

- **Given:** Ten identified units in custodian ledger; eight accepted, two refused
- **When:** Submit complete delivery flag with partial accepted counts
- **Then / authoritative decision:** DENY full-delivery transition; preserve 8 accepted + 2 identified residual
- **DB/canonical invariant:** Conservation invariant and Shipment != fully DELIVERED
- **Outbox/Inbox/Jobs/Documents:** No ShipmentDelivered(all) event
- **User-visible outcome:** Client sees partial + outstanding two units
- **Execution layer:** Execution property+PG. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-031 — POD evidence overwritten after damage claim

**Actor:** Document Controller. **Priority:** `P0_CUSTODY`. **Links:** `GAP-18` · `SIM-29` · `USB-EXC-010` · `LFC-014`.

- **Given:** Signed original POD and photo hash already stored; damage reported later
- **When:** Update original signed document bytes/receiver/date instead of append correction
- **Then / authoritative decision:** DENY overwrite; immutable original, separate correction/dispute record
- **DB/canonical invariant:** Original evidence digest/version unchanged
- **Outbox/Inbox/Jobs/Documents:** Only CorrectionAdded event, not retroactive POD rewrite
- **User-visible outcome:** Customer sees original and corrected evidence history
- **Execution layer:** Documents+RustFS+PG. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-032 — Signed URL issued before revoke remains active beyond declared TTL

**Actor:** EXC Customer. **Priority:** `P0_CUSTODY`. **Links:** `GAP-18` · `SIM-30` · `USB-DOC-003` · `TDD-SIM-30-S20-01`.

- **Given:** Customer had temporary signed POD URL before grant revoked
- **When:** Download after revoke through protected API and test direct URL after TTL
- **Then / authoritative decision:** Protected API DENY immediately; object URL unusable after actual TTL, no false hard-revoke claim
- **DB/canonical invariant:** No new signed links after revoke; no unrestricted metadata
- **Outbox/Inbox/Jobs/Documents:** No later delivery of link after revoke
- **User-visible outcome:** Access revoked; already issued link documented bounded exposure
- **Execution layer:** HTTP+RustFS integration. **Status:** `DESIGNED_NOT_EXECUTED`.

### FINANCE — Money, invoices, approval and settlement (4)

#### NEG-R0-033 — Same principal approves payable under alternate account

**Actor:** Finance Officer/FAP. **Priority:** `P0_FINANCIAL`. **Links:** `GAP-22` · `SIM-32` · `USB-FAP-001` · `AUTH-FIN-003`.

- **Given:** Payment prepared by principal P using account A; same person holds account B
- **When:** Approve same payable through account B
- **Then / authoritative decision:** DENY self-approval by stable human identity, not merely username
- **DB/canonical invariant:** Approval remains pending, no accounting settlement
- **Outbox/Inbox/Jobs/Documents:** No PayableApproved event
- **User-visible outcome:** Requires independent approver
- **Execution layer:** Finance+identity policy. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-034 — Duplicate bank settlement with different provider message IDs

**Actor:** Bank Inbox. **Priority:** `P0_FINANCIAL`. **Links:** `GAP-22` · `SIM-32` · `USB-FIN-003` · `AUTH-FIN-004`.

- **Given:** Same source transaction received with two callback/message IDs
- **When:** Allocate both to same invoice using different eventId
- **Then / authoritative decision:** Dedup by authoritative bank transaction identity, not only transport eventId
- **DB/canonical invariant:** One unique allocation and unchanged balance after duplicate
- **Outbox/Inbox/Jobs/Documents:** No second Settled event
- **User-visible outcome:** Paid amount correctly displayed once
- **Execution layer:** PostgreSQL unique financial transaction. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-035 — Bank callback amount/FX mismatches invoice

**Actor:** Finance. **Priority:** `P0_FINANCIAL`. **Links:** `GAP-22` · `SIM-31` · `USB-FIN-003` · `LFC-025`.

- **Given:** Invoice KZT, bank amount/currency/FX or legal account does not match
- **When:** Auto-reconcile unverified converted amount
- **Then / authoritative decision:** Do not settle without approved allocation/FX rules and source truth
- **DB/canonical invariant:** Mismatch held for investigation; no guessed conversion or negative balance
- **Outbox/Inbox/Jobs/Documents:** No PaymentSettled notification
- **User-visible outcome:** Reconciliation pending, not Paid
- **Execution layer:** Finance money precision+PG. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-036 — Refund/reversal ignored after previously settled invoice

**Actor:** Finance Reconciliation. **Priority:** `P0_FINANCIAL`. **Links:** `GAP-22` · `SIM-32` · `USB-FIN-003` · `AUTH-FIN-004`.

- **Given:** Payment was allocated, bank reports authenticated reversal/chargeback
- **When:** Process reversal and re-run reconciliation
- **Then / authoritative decision:** No permanent falsely paid balance; post compensating allocation under approved rule
- **DB/canonical invariant:** Original ledger immutable, reversal separately recorded; balances consistent
- **Outbox/Inbox/Jobs/Documents:** Appropriate adjustment event, not duplicate original payment
- **User-visible outcome:** Customer sees accurate corrected status after verified event
- **Execution layer:** Finance+verified bank adapter+PG. **Status:** `DESIGNED_NOT_EXECUTED`.

### SAAS — Subscription continuity and access lifecycle (4)

#### NEG-R0-037 — Tenant suspension blocks POD for active cargo

**Actor:** SaaS Operator. **Priority:** `P0_CONTINUITY`. **Links:** `GAP-05` · `SIM-41` · `USB-TNO-004` · `TDD-R0-E2E-07`.

- **Given:** Trip STARTED, customer cargo in custody, subscription suspended
- **When:** Assigned driver/recipient records mandatory handover/POD under continuity contract
- **Then / authoritative decision:** Do not strand active safety evidence; allow exactly scoped approved continuity
- **DB/canonical invariant:** Evidence stored and auditable; no new discretionary booking
- **Outbox/Inbox/Jobs/Documents:** No fake Trip cancellation
- **User-visible outcome:** Safety action available subject to approved scoped policy
- **Execution layer:** SaaS+Execution integration. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-038 — SaaS outage opens global unrestricted fallback

**Actor:** SaaS/Jobs. **Priority:** `P0_CONTINUITY`. **Links:** `GAP-05` · `SIM-41` · `USB-TNO-004` · `AUTH-X-014`.

- **Given:** Billing or policy service unreachable; driver task ongoing
- **When:** Call safety API with absent tenant context or forged trip ID
- **Then / authoritative decision:** DENY cross-tenant, do not enable blanket fallback; only previously approved safety scope
- **DB/canonical invariant:** No foreign custody/POD writes
- **Outbox/Inbox/Jobs/Documents:** No cross-tenant JobAccepted
- **User-visible outcome:** Service unavailable or narrow authorized continuation
- **Execution layer:** HTTP+PG RLS. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-039 — Suspended tenant sends fresh booking through safe-continuity token

**Actor:** Tenant Admin. **Priority:** `P0_CONTINUITY`. **Links:** `GAP-05` · `SIM-41` · `USB-TNO-004` · `TDD-SIM-41-G05-02`.

- **Given:** Tenant has active trip continuity grant only and subscription suspended
- **When:** Call create new Booking using continuity credential
- **Then / authoritative decision:** DENY new commercial action; safety grant cannot expand
- **DB/canonical invariant:** No new Booking/reservation
- **Outbox/Inbox/Jobs/Documents:** No BookingRequested event
- **User-visible outcome:** New order action disabled, active cargo remains visible
- **Execution layer:** HTTP+policy unit. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-040 — External membership revoke takes effect only in UI

**Actor:** External Customer. **Priority:** `P0_CONTINUITY`. **Links:** `GAP-03` · `SIM-34` · `USB-EXC-008` · `AUTH-X-021`.

- **Given:** Grant revoked in DB but old JWT, WS subscription and cached response remain
- **When:** Call HTTP, stream and async export after commit
- **Then / authoritative decision:** DENY all newly authorized data operations; close/re-authorize stream and export
- **DB/canonical invariant:** No new read/export granted by stale token
- **Outbox/Inbox/Jobs/Documents:** No protected stream event or export delivery
- **User-visible outcome:** UI shows revoked status; not stale data
- **Execution layer:** HTTP+stream+cache+Jobs. **Status:** `DESIGNED_NOT_EXECUTED`.

### ASYNC — Outbox, Jobs, recovery and field projection (4)

#### NEG-R0-041 — Outbox dispatch duplicates business side effect

**Actor:** Platform Job. **Priority:** `P0_RELIABILITY`. **Links:** `GAP-15` · `SIM-35` · `USB-SUP-001` · `AUTH-X-010`.

- **Given:** DB transaction committed and Outbox message delivered, acknowledgement lost
- **When:** Retry same message concurrently on two workers
- **Then / authoritative decision:** At-least-once transport, exactly one logical domain effect via inbox uniqueness
- **DB/canonical invariant:** No duplicate Booking, invoice, custody or review row
- **Outbox/Inbox/Jobs/Documents:** Duplicate delivery acknowledged/dedup; not repeated notification side effect
- **User-visible outcome:** Only one completed operation is visible; no duplicate notifications or ledger entries
- **Execution layer:** Modulith + PostgreSQL Outbox/Inbox concurrency. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-042 — Job retries after original actor privilege is revoked

**Actor:** Support. **Priority:** `P0_RELIABILITY`. **Links:** `GAP-03` · `SIM-35` · `USB-SUP-001` · `AUTH-X-010`.

- **Given:** Manual delegated job queued under active role, role revoked before execution
- **When:** Use saved JWT/role snapshot to execute privileged operation
- **Then / authoritative decision:** DENY unauthorized new action; service principal only within explicit scoped job contract
- **DB/canonical invariant:** Business aggregate unchanged, audit of revoked job attempt
- **Outbox/Inbox/Jobs/Documents:** No domain success event
- **User-visible outcome:** Job marked denied/escalated; no silent success
- **Execution layer:** Jobs+RLS+policy unit. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-043 — Support logs reveal cargo PII in failed job exception

**Actor:** Platform Support. **Priority:** `P0_RELIABILITY`. **Links:** `GAP-03` · `SIM-35` · `USB-SUP-001` · `AUTH-X-027`.

- **Given:** Failed job payload contains customer contact, driver location and finance data
- **When:** Inspect job metadata/log trace under support operator
- **Then / authoritative decision:** Redact protected fields, deny raw payload access
- **DB/canonical invariant:** No unredacted payload in query/export/log for support audience
- **Outbox/Inbox/Jobs/Documents:** No raw replay/log artifact attached to support output
- **User-visible outcome:** Only redacted reason code and correlation ID
- **Execution layer:** Jobs+logging+security integration. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-044 — Stale read model projects successful booking after compensation

**Actor:** Projection Consumer. **Priority:** `P0_RELIABILITY`. **Links:** `GAP-12` · `SIM-20` · `USB-DSP-001` · `AUTH-X-016`.

- **Given:** Booking confirmation failed/rolled back but old event arrives late
- **When:** Update customer My Orders from stale/replayed event
- **Then / authoritative decision:** Do not show authoritative CONFIRMED unless current valid Booking version; order events with version watermark
- **DB/canonical invariant:** Canonical Booking remains pending/exception and projection eventual state converges
- **Outbox/Inbox/Jobs/Documents:** No customer booking success notification from invalid stale event
- **User-visible outcome:** Pending/exception with freshness, not false confirmed
- **Execution layer:** Outbox+read model+HTTP. **Status:** `DESIGNED_NOT_EXECUTED`.

### DISPUTES — Cancellation, claims and verified feedback (4)

#### NEG-R0-045 — Customer cancellation request used as immediate cancel command

**Actor:** EXC. **Priority:** `P0_BUSINESS`. **Links:** `GAP-21` · `SIM-21` · `USB-EXC-009` · `AUTH-X-020`.

- **Given:** Booking.CONFIRMED and driver/cargo assignment still active
- **When:** Customer posts cancellation request with cancel=true and fee=0 overposted
- **Then / authoritative decision:** Only request recorded; server derives terms/fees, Booking unchanged
- **DB/canonical invariant:** No released capacity, no mutating fee from user-controlled field
- **Outbox/Inbox/Jobs/Documents:** No BookingCancelled event from customer command
- **User-visible outcome:** Requested; awaiting decision
- **Execution layer:** Booking HTTP+PG. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-046 — Cancellation wins while Trip.STARTED update commits

**Actor:** Dispatcher. **Priority:** `P0_BUSINESS`. **Links:** `GAP-21` · `SIM-22` · `USB-DSP-003` · `LFC-034`.

- **Given:** Authorized cancellation and Trip.STARTED race on same Booking
- **When:** Commit actions concurrently with stale versions
- **Then / authoritative decision:** One coherent contract/custody branch; cannot free vehicle with active cargo
- **DB/canonical invariant:** Either valid pre-start cancellation or execution exception; never both
- **Outbox/Inbox/Jobs/Documents:** No contradictory Cancelled and InExecution customer events
- **User-visible outcome:** Single consistent status; exceptions displayed
- **Execution layer:** Booking/Execution PG concurrency. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-047 — Complaint incorrectly changes POD or grants refund

**Actor:** EXC. **Priority:** `P0_BUSINESS`. **Links:** `GAP-18` · `SIM-29` · `USB-EXC-010` · `AUTH-X-026`.

- **Given:** Service partial POD or undelivered with customer damage report
- **When:** Submit customer complaint with requested amount and altered POD fields
- **Then / authoritative decision:** Create scoped claim record only; no automatic evidence mutation/refund
- **DB/canonical invariant:** POD immutable; money unchanged; claim linked to service
- **Outbox/Inbox/Jobs/Documents:** ClaimOpened only, not Delivered/RefundGranted
- **User-visible outcome:** Complaint accepted for review independently of feedback
- **Execution layer:** Commercial+Execution+Finance integration. **Status:** `DESIGNED_NOT_EXECUTED`.

#### NEG-R0-048 — Provider staff submits rating for own company

**Actor:** Tenant Sales. **Priority:** `P0_BUSINESS`. **Links:** `GAP-03` · `SIM-33` · `USB-EXC-006` · `AUTH-X-008`.

- **Given:** Provider employee has Sales permission and can see customer records
- **When:** Submit private review as customer using forged customerAccountId
- **Then / authoritative decision:** DENY; only verified customer feedback capability on eligible completed service
- **DB/canonical invariant:** No review or public rating created
- **Outbox/Inbox/Jobs/Documents:** No ReputationChanged event
- **User-visible outcome:** Review submission denied; existing original untouched
- **Execution layer:** Commercial+HTTP+RLS. **Status:** `DESIGNED_NOT_EXECUTED`.


## 5. High-risk combination tests that cannot be replaced by isolated mocks

These selected intersections should be executed as integrated stress/failure cases, reusing individual negative cases above:

| Combination | Composition | Required oracle |
|---|---|---|
| MIX-01 | `NEG-R0-005` + `NEG-R0-006` + `NEG-R0-040` | Cross-customer RLS + revoked grant + warm cache / stream -> never expose foreign data |
| MIX-02 | `NEG-R0-010` + `NEG-R0-012` + `NEG-R0-009` | Exact terms/signature + expiry/decline race + assisted RFQ -> no forged acceptance |
| MIX-03 | `NEG-R0-013` + `NEG-R0-018` + `NEG-R0-019` | Carrier withdrawal + stale hold expiry + partially acquired fleet -> no false Booking |
| MIX-04 | `NEG-R0-025` + `NEG-R0-027` + `NEG-R0-028` | Offline forged timestamp + reassignment + out-of-order custody -> one defensible custodian per CargoUnit |
| MIX-05 | `NEG-R0-030` + `NEG-R0-031` + `NEG-R0-032` | Partial POD 8/10 + immutable signed proof + stale link -> no full delivery or unauthorized evidence |
| MIX-06 | `NEG-R0-034` + `NEG-R0-035` + `NEG-R0-036` | Two bank message IDs + wrong currency + reversal -> no duplicate income or false SETTLED |
| MIX-07 | `NEG-R0-037` + `NEG-R0-038` + `NEG-R0-043` | SaaS suspension + no global fallback + redacted support -> continuity without escalation |
| MIX-08 | `NEG-R0-041` + `NEG-R0-042` + `NEG-R0-044` | Outbox duplicate + revoked user job + old customer projection -> one effect and no false UI state |

**Priority:** run isolated P0 invariants first, then mix tests under fault injection and genuine concurrent connections. Do not add a distributed fault-testing platform or chaos cluster to accomplish R0.

## 6. Coverage criteria and recommended test structure

**Cross-layer test selection:**

| Test level | Mandatory proofs | Recommended JUnit/Java test type |
|---|---|---|
| Pure policy / aggregate | SoD, legal identity delegation, state guards, amount/cargo-unit conservation | JUnit 5 + AssertJ + property invariants |
| Spring Security / HTTP | No direct privilege escalation, no unauthorized field/view/export/cursor exposure | `MockMvc` / Servlet HTTP integration with real service auth |
| PostgreSQL/PostGIS | RLS tenant isolation, exclusive resource range race, financial uniqueness, out-of-order version checks | Testcontainers PostgreSQL/PostGIS, migration/app role without `BYPASSRLS` |
| Modulith / Outbox-Inbox | No double logical effect, event ordering and compensation after crash | `@ApplicationModuleTest`, real DB Outbox/Inbox + controlled failures |
| Documents/RustFS | Invalid links, signed URL TTL, immutable hashes/versions | API + access broker + storage integration |
| UI acceptance | Distinct unauthorized, pending, conflict, stale vs empty business list | HTTP snapshot + later actual browser/UI E2E |

**Test-fixture contract:** reuse `FIX-R0-TRANSPORT-001` (Provider Tenant-A with two branches, Customer-X/Y, Tenant-B shipper, Tenant-C carrier, forbidden Tenant-Z, 10 CargoUnits, 8 delivered and 2 outstanding, double vehicle time slot, quote expiry, bank callback replay, revoked access/old signed URL).

**Mutation validation:** For each critical guard, deliberately remove/invert the check in a controlled test environment and require the corresponding test to fail (e.g. tenant filter, quote terms hash, overlap constraint, event ID/payload hash, custody balance, bank allocation uniqueness). Do not measure reliability solely by test count or line coverage.

**Isolation and concurrency:** run real separate JDBC connections and competing transactions; verify after commit as authoritative result, not only via mock callbacks. Network/Outbox/JWT/Redis effects must be tested at trust boundaries. For cargo and finance, assert `sum(quantity)` / `sum(allocatedAmount)` invariants after *every* attempted transition.

## 7. TDD prioritization and release gates

| Gate | Selected cases | Must demonstrate |
|---|---|---|
| NEG-G0 — identity + customer | 001–012 | No privilege elevation, forged signing, RFQ replay or customer data enumeration |
| NEG-G1 — procurement + capacity | 013–020 | No false carrier/own-fleet commitments, double hold or duplicate Booking |
| NEG-G2 — legal safety + custody | 021–028 | UNKNOWN fails closed, no stale compliance ALLOW, one lawful custodian after offline/reassignment |
| NEG-G3 — POD + finance | 029–036 | 8/10 partial truth, evidence immutability, verified bank reconciliation and reversal |
| NEG-G4 — continuity + jobs | 037–044 | Safe active transport on SaaS failure, no global fallback, idempotent Outbox or data leak |
| NEG-G5 — exceptions + feedback | 045–048 | Cancellation request is not cancellation, claim is not refund, no provider self-review |

**Definition of Ready:** relevant `BR-xx` and real actor/legal approval, true owner-module state machine, permission linked to v2.1 or marked `PENDING_POLICY`, database/Outbox negative oracle, realistic fixture and exact error semantics. See [29 — Stakeholder Review Kit](29-r0-business-acceptance-workshop-kit.md). A proposed case may still be authored as TDD design before approval, but not used to justify irreversible acceptance.

**Definition of Done (later):** running Java tests on exact SHA; real Testcontainers+RLS/concurrency; no unexpected domain writes/events for rejected actions; verified customer-side UI truth; no severity-P0 open security/cargo/finance regression; CI report and business/legal evidence where required.

## 8. Open review questions for this bank

- Does the Kazakhstan pilot require an EDS for specific B2B commitments or is another contractually valid method accepted after qualified legal review? Never assume portal click alone.
- Should Quote decline be allowed to a `CUSTOMER_REQUESTER`, to signatory only, or as separately delegated capability?
- How is carrier and vehicle confirmation evidenced when carrier has no paid Tenant or data signal is offline?
- For cargo mismatch/guest receiver, who is qualified to quarantine evidence and approve custody reconciliation?
- What can execute during SaaS subscription suspension: which in-flight POD, recovery, incident and evidence accesses, for how long?
- What qualifies as verified bank settlement/reversal/credit adjustment, and which ledger or ERP is source of truth?
- Which customer details can appear in support logs and signed URL generation, including after a grant revoke?

**No code or test execution is claimed.** The original 84 cases remain unchanged as historical test design; the 48 new cases and 8 MIX intersection specifications are supplementary, not additional implementation/release achievements.

## 9. Uniform HTTP error contract as an additional acceptance dimension

The 48 `NEG-R0-*` cases must assert a stable [RFC 9457 Problem Details standard](31-unified-error-handling-standard.md), [21-code catalog](contracts/api-error-catalog.v1.json) and a server-generated `requestId` whenever the failure crosses the REST boundary. In a foreign CustomerAccount or Tenant access denial, a protected resource must be indistinguishable from missing even by **machine code** (same public `KX-GEN-404-001`), with internal audit kept separate. No raw SQL, exception, rejected validation input, JWT, driver GPS or customer finance details enter the public problem response. HTTP-denial tests remain insufficient without verifying canonical DB, Outbox/Inbox and user-visible state. Error-only backend handler scaffold is committed but not CI-qualified; business acceptance tests are still planned.

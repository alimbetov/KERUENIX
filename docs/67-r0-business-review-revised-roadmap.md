# 67 — Business review and revised R0 commercial roadmap

**Review date:** 2026-11-13. **Status:** BUSINESS REVIEW PROPOSAL; NO FORMAL BUSINESS/S2 APPROVAL. **Source:** [docs/66](66-r0-rfq-execution-pod-vertical-slice-s0.md), [docs/62](62-r0-pragmatic-architecture-adoption.md), [PR #3](https://github.com/alimbetov/KERUENIX/pull/3) and [Issue #10](https://github.com/alimbetov/KERUENIX/issues/10).

## Executive business verdict

The original RFQ→Offer→Agreement→Execution→Tracking→POD sequence is the correct **core transaction**, but incomplete as an independently sellable logistics workflow. It under-specifies what is offered and contractually accepted, which company has custody and liability, how exceptions and disputes are handled, and how the customer proves the delivered outcome. It also risks premature breadth (two carriers, geo automation, sophisticated optimization, multiple modes) before proving a complete transaction.

**Revised north-star:** one legitimate **customer–carrier** movement with end-to-end traceability, defensible commercial terms, handling of one realistic exception and evidence-backed delivery. Multi-carrier optimization, payments and automatic vehicle tracking are **not** pilot prerequisites.

## P0 user, buyer and value hypotheses — NOT validated demand

| Role / company | Primary job to be done | Value to validate with users |
|---|---|---|
| Customer logistics coordinator (shipper) | Ask for transport, compare/accept explicit terms, monitor status, prove receipt | Fewer calls and lost documents; one linked RFQ/booking/POD timeline |
| Carrier dispatcher / small transport company | Receive qualified request, price and commit capacity, assign vehicle/driver, complete shipment | Fewer status calls; less duplicate data entry; transparent handover |
| Driver / operator | Confirm pickup and delivery without complex software | Mobile-responsive minimal confirmation, role-limited access |
| Recipient / authorized receiver | Confirm quantity/condition, capture discrepancies | Credible timestamped receipt/evidence, not a silent status flip |
| Platform operations | Onboard participants, resolve exceptions and audit changes | Traceable support; restricted admin tools with dual control where required |

**Buyer and monetization assumptions requiring validation:** likely paying company = shipper or carrier on a subscription or per completed shipment. Do not invent a price or margin. Discover who controls budget, current alternatives, volume per month, status/POD processing time and willingness to pay through pilot interviews; record actual baseline and outcome data.

## Pilot scope: one movement, one customer, one carrier

**IN**: company onboarding/verified relationship, scoped actors, RFQ Draft + Submit under approved policy, one explicit carrier quote and acceptance, one pickup, one delivery leg, manually entered milestone/status, pickup handover record, recipient-approved POD with discrepancy state, immutable audit and accessible linked commercial summary. Two CustomerAccounts under same provider tenant must be isolated. One vehicle/driver may be associated when available; no hard dependency on a GPS vendor.

**NOT IN R0 pilot**: multi-carrier bidding marketplace, algorithmic matching, dynamic pricing, route optimization, live telematics/GPS, multi-modal legs, freight brokerage marketplace settlement, payment execution, invoices/tax fiscalization, automatic claims adjudication, complex split consignments, customs integration, mobile native app, Redis/Kafka/new job platform. These remain later capabilities subject to measured user demand and regulatory/legal review.

**One exception must work:** carrier cancellation or failed pickup **before** loading, and recipient-reported shortage/damage **at** delivery. Do not forcefully mark Delivered or silently rewrite accepted commercial terms. Design rollback/compensation and support action first.

## Business process, decision ownership and outcomes

| Stage | Owner/action | Inputs and business invariant | Observable customer outcome |
|---|---|---|---|
| B0 Relationship & authority | Platform admin + parties verify organizations and relationship | Tenant/account boundaries, employee roles, service region, approved counterparty visibility | Only entitled shipper/carrier can interact |
| B1 RFQ Draft | Customer coordinator creates and edits non-binding request | Pickup/dropoff address, cargo description, declared units/weight/volume, desired window, handling requirements, contact; completeness validation | Persistent editable Draft, saved/reopened with audit |
| B2 RFQ Submitted | Customer coordinator explicitly submits after DEC-R0-03 | Authorized submit, route/cargo valid, versioned snapshot; contact disclosures limited to actual invited carrier | Carrier sees a *request*, not an accepted contract |
| B3 Quote | Carrier dispatcher responds, customer can decline or request revision | Single quote version, currency, total amount, inclusion/exclusion, taxes as applicable, validity, vehicle/service constraints | Compare agreed offer to request, transparent cost |
| B4 Acceptance & Booking | Authorized customer accepts a specific still-valid quote | Explicit acceptance and timestamp, quote terms/version immutable, accepted actor, company, capacity and cancellation terms; no automatic booking from RFQ submit | One confirmed booking and traceable commercial contract reference |
| B5 Execution & Pickup | Carrier dispatcher assigns resource; driver records pickup | Vehicle/driver if applicable, pickup arrival vs actual loading time, actor/quantity/condition handover, custody initiates only at confirmed pickup | Traceable physical possession, not just status text |
| B6 In-transit & exception | Carrier dispatcher or driver posts verified milestone, ETA changes and incidents | Append-only events with occurredAt/recordedAt, source, corrected records via new events, reason for disruption | Customer can see last valid event and exception responsibility |
| B7 Delivery & POD | Receiver/authorized agent confirms physical delivery | Local delivery timestamp, delivered qty, condition, attachment reference/digest, recipient identity, consent/acknowledgment and discrepancies | Verifiable POD, status **DELIVERED_WITH_EXCEPTION** if unresolved shortage/damage |
| B8 Close / post-delivery | Customer and carrier review POD, operations resolves issues | Distinguish actual receipt, dispute/claim status, final commercial amount vs agreed estimate; prohibit automated payment/invoice | Shipment visibly complete or exception-pending; exportable event/terms summary |

**Important:** 'POD submitted', 'POD accepted', 'Delivered' and 'Business closed' are not synonyms. Define semantics before S1. A recipient exception can be a genuine delivery event but must **not** imply dispute/claims acceptance or automatic financial settlement.

## P0 state vocabulary (proposed)

- RFQ: `DRAFT → SUBMITTED → QUOTED → BOOKED`; `CANCELLED` from allowed pre-booking states; `EXPIRED` based on reviewed terms. A declined/expired quote does not erase RFQ history.
- Quote: `OFFERED → ACCEPTED | DECLINED | EXPIRED | SUPERSEDED`; immutable version on acceptance. One accepted quote per single-load pilot booking.
- Booking: `CONFIRMED → CANCEL_REQUESTED → CANCELLED` (only with approved policy), or `CONFIRMED → EXECUTION_CREATED`. **Do not** treat cancellation after pickup as simple deletion; incident/return protocol required.
- Execution: `PLANNED → ASSIGNED → AT_PICKUP → PICKED_UP → IN_TRANSIT → AT_DELIVERY → DELIVERY_RECORDED`; `EXCEPTION_OPEN` as orthogonal overlay instead of destructive one-way status, with a separate closure decision.
- POD: `DRAFT_EVIDENCE → SUBMITTED → ACKNOWLEDGED` or `DISCREPANCY_RECORDED`, with `REJECTED`/correction via additional evidence where policy allows. Need authoritative recipient model to define ACKNOWLEDGED.
- Exception: `REPORTED → ASSIGNED → RESOLVED | DISPUTED`, with due dates and append-only notes/evidence. No automatic liability assignment.

These are **business design candidates**, not production enum approvals or legal conclusions. Do not implement all state variants blindly; S0 should reduce them to minimum evidenced events and transitions.

## Revised phased roadmap (business outcome first)

| Gate | Small deliverable | Done only when | Commercial evidence |
|---|---|---|---|
| G0 — customer discovery & decisions | 3–5 shipper interviews + 3–5 carrier interviews as *planning target*; verify payer, document baseline, counterparty relationships, authority and exception policy | Sponsor/domain/security/QA record approved decisions; no made-up interviews | Defined pilot sponsor, success metric, existing workflow |
| G1 — secure RFQ Draft | Real PostgreSQL grant + RFQ create/edit/reopen, idempotency, no cross-account read, audit | Real API + persistent data + exact-SHA GREEN after S2 | Customer can enter a real draft without staff assistance |
| G2 — explicit offer & booking | Submit, one quoted offer, revision/expiry, acceptance, cancellation-before-pickup policy | Customer+carrier see same immutable accepted terms, one booking under concurrency | Both companies agree on what/where/when/how much |
| G3 — physical execution | Resource/driver association, pickup custody, manual status/ETA, disruption events | Driver/dispatcher can record handover and update event while account-level reads stay secure | Traceable pickup and latest trustworthy milestone |
| G4 — POD with discrepancy | Authorized receipt, quantities/condition, attachment, duplicate protection and exception | Receiver can submit evidence; customer sees delivered vs discrepancy separately | Downloadable/verifiable evidence; no silent closing |
| G5 — production pilot qualification | One complete pilot transaction with negative auth, concurrency, restart/retry, recoverability, incident and support process | 2 company actors, no account leaks, document+timeline+quote+POD integrity, operator runbook and independent S2/S4 decisions | Real user's sign-off and observed process/time saved |

**Sequence rule per gate:** S0 scenario → S1 negative/positive behavior RED → independent S2 test review → S3 minimal GREEN → S4 operational/business acceptance. G0 decisions and existing Foundation S2 (#9) are prerequisites for relevant security/integrity work. No work may treat `COMMENTED` as human APPROVED.

## Business acceptance scenarios to ADD to existing registry after reconciliation (not yet counted in 132)

| ID | Business oracle | Failure condition |
|---|---|---|
| BIZ-VS-01 | Shipper requests a quote for one cargo and can reopen/edit before submit | Draft accidentally creates confirmed booking |
| BIZ-VS-02 | Quote explicitly shows currency, total, service inclusions, validity and version | Hidden surcharge/changed terms silently accepted |
| BIZ-VS-03 | Acceptance by authorized role creates exactly one booking with frozen quote version | Expired/revised quote accepted or double booking under concurrent accept |
| BIZ-VS-04 | Carrier cancels **before pickup** and customer sees reason/time; booking state and reassignment documented | Execution remains in-progress without accountable cancellation |
| BIZ-VS-05 | Pickup handover captures qty/condition and actor; custody starts at actual pickup | Driver status alone fabricates transfer of possession |
| BIZ-VS-06 | Driver posts late ETA/incident; original event remains in audit | Correction overwrites evidence or leaks other customers' location |
| BIZ-VS-07 | Recipient signs POD with shortage/damage; customer sees delivery with open exception | Damage becomes clean `DELIVERED`, claim wrongly settled |
| BIZ-VS-08 | Attempt to submit POD twice or attach another shipment's document | Duplicate delivery, cross-account file read or forged receipt |
| BIZ-VS-09 | Carrier and shipper independently view identical quote, pickup and delivery evidence | Different commercial snapshots across parties |
| BIZ-VS-10 | Same-tenant Account X must not list/count/export Account Y shipments, quotes or POD | Hidden cross-account existence/meta leak |
| BIZ-VS-11 | DB grant outage/revocation between requests blocks protected operation | Stale JWT allows changed quote or POD acceptance |
| BIZ-VS-12 | One journey ends with an auditable commercial summary; money movement is absent | Accidental automatic invoice/payment/settlement |

**Mapping requirement:** before declaring scenario design complete, map BIZ-VS-01…12 to existing 132/26 PR ledger; mark duplicate/extend/new and assign owners and expected oracle. They are **candidate gaps**, not an assertion that all 12 are missing.

## Pilot success criteria and go/no-go

**Hard acceptance:** zero confirmed cross-account disclosure in the scenario suite; no unauthorized or duplicate agreement; no unsupported Delivered/POD; complete immutable evidence link; recoverable interrupted flow; no misleading payment claims. These are release blockers regardless of business metrics.

**Measure (targets to be set after interview baseline, not fabricated now):** elapsed time from initial RFQ to quote acceptance; dispatcher touches/calls per load; POD availability delay after receipt; percentage of shipments with complete evidence; percentage of discrepancies recorded accurately; support interventions per load; adoption by both companies; repeat usage; users willing to pay.

**Pilot go/no-go decision:** validate real demand and payer, demonstrate one full shipment and one exception with two companies, independent technical approvals and agreed operational responsibilities. If value is not demonstrated, optimize the specific user workflow before adding complex routing/AI/marketplace features.

## Critical new business decision ledger — must be owned

| Decision | Owner for sign-off | Question |
|---|---|---|
| BR-VS-01 | Product sponsor + commercial owner | Who is paying customer, subscription vs per shipment, pilot company/region and first cargo type? |
| BR-VS-02 | Legal/business + shipper/carrier representatives | What constitutes submission, quote acceptance, legally binding booking, cancellation penalties and disclosure permissions? |
| BR-VS-03 | Logistics/operations | Who has custody at each handover; driver identity, recipient verification, damage/shortage rules? |
| BR-VS-04 | Commercial/finance | Quote structure, taxes/currency, additional charges/price changes, settlement *outside* R0 |
| BR-VS-05 | Logistics/operations + service | Exception severity, ownership, resolution SLA, dispute/claim path and partial/failed delivery |
| BR-VS-06 | Security/privacy + domain | Contact/geo/document visibility, retention, recipient identity/consent |
| BR-VS-07 | Product sponsor + operations | Single load/leg/vehicle pilot restrictions, manual vs automated milestones, metric targets |

**Dependencies retained:** BR-03, DEC-R0-02, DEC-R0-03, DEC-CA-01/03/04, DEC-VS-01…04 and independent Outbox S2 [#9](https://github.com/alimbetov/KERUENIX/issues/9).

## Overall conclusion

**Business design CONDITIONAL GO for S0 refinement / pilot discovery. NO-GO for binding booking, real custody, authenticated POD, payments and S3 implementation until decisions and independent S2.** The earlier [docs/66](66-r0-rfq-execution-pod-vertical-slice-s0.md) remains a technical source for 14 scenario oracles; this business review **refines its rollout priorities and adds exception/commercial coverage**, not a replacement of approved decisions.

# 21 — KERUENIX User Story Book: Role-Based Scenario Bank

**Version:** 0.1 — ITERATION 1 / ROLE INVENTORY + R0 STORY SEEDS. **Date:** 2026-11-07. **Status:** PROPOSED / business workshop required. **No implemented features or executed TDD tests are implied.**

**Purpose:** Maintain a single versioned, traceable bank of actor-centered scenarios; build it incrementally in several iterations, *then* derive acceptance tests, TDD unit tests and integration/E2E cases. Do not confuse role catalog with a list of software privileges or tenant membership.

**Based on:** [operational journeys](../idea/04-operational-workflows.md), [dispatcher day](../idea/17-forwarder-dispatcher-day-simulation.md), [commercial lifecycle](10-commercial-execution-lifecycle-v1.md), [existing lifecycle test plan](11-commercial-execution-acceptance-v1.md), [requirements matrix](04-requirements-traceability.md), [engineering TDD standard](20-mapstruct-tdd-engineering-standard.md).

## 1. User Story Book editorial rules

- **One story ID, one business outcome:** `USB-<role>-NNN`, stable IDs never reused. Role describes primary actor, but collaborators and tenant owner must also be named.
- A story has: `ID, title, primary actor, tenant/legal-entity context, trigger, desired outcome, prerequisites, main steps, alternatives/negative cases, data/evidence, state changes, permitted visibility, business invariants, linked requirement/lifecycle/test IDs, priority, status, owner/open decision`.
- **Status** transitions: `DISCOVERED → DRAFT → BUSINESS_REVIEWED → ACCEPTED_FOR_TDD → TESTS_DESIGNED → IMPLEMENTED → QUALIFIED`. No skip to QUALIFIED from document approval.
- One source of truth: story owns human intent/observable outcome; lifecycle contract owns allowed transitions; requirement matrix owns obligation; test specifications own executable cases. Use cross-references instead of copying state machine tables.
- Three scenario layers: **happy path**, **negative/exception**, **security/concurrency/recovery**. Create test cases only after business guard/actor/financial and legal rules are reviewed; a discovery scenario may have *test ideas* without becoming a test contract.
- Story status and implementation status are independent. Version all changes; retain superseded rationale and map each story to the business owner.
- Role ≠ global RBAC grant. Enforce tenant, membership, legal entity, assignment, partner grant, resource scope and separation of duties for each command and response field. No implicit driver rights to contract or invoice.
- For pilot evidence use synthetic data; real prices, regulatory permissions, insurer requirements and legal acceptance require external owner sign-off.

## 2. Persona and role catalog — first pass

Roles are **personas**, not a fixed one-role-per-user permission scheme. A person can have several job functions within a company, subject to SoD restrictions. `TENANT-A` expeditor, `TENANT-B` shipper, `TENANT-C` carrier are independent organizations; pilot may begin with trusted carriers/own fleet and two fully isolated tenant accounts.

| Role code | Actor / organization | Primary goal | Relevant contexts | Priority |
|---|---|---|---|---|
| SHP | Грузовладелец / customer logistics employee | Request, approve terms, track, accept evidence | Commercial, Tracking, Documents | R0 |
| SAL | Экспедитор / коммерческий менеджер | Qualify RFQ, quote, customer commitments | Commercial | R0 |
| PLN | Логист / транспортный планировщик | Determine eligible carrier/vehicle and route | Fleet, Booking, Compliance | R0 |
| DSP | Диспетчер | Assign trip, monitor execution and exceptions | Booking, Execution, Tracking | R0 |
| CAR | Менеджер внешнего перевозчика | Offer capacity, confirm obligations and fleet | Commercial, Fleet, Booking | R0 (trusted partner) |
| DRV | Водитель | Accept assignment, record pickup/delivery evidence | Execution, Documents | R0 |
| RCV | Получатель груза | Verify quantities/condition and acknowledge POD | Execution, Documents | R0 |
| FIN | Финансовый контролёр / бухгалтер | Review receivables/payables and payment evidence | Finance, Commercial | R0 finance-lite |
| TEN | Tenant administrator | Manage membership, permission and scoped sharing | Tenancy | R0 |
| SUP | Platform support / SRE | Observe, recover jobs and diagnose without excess data access | Platform Jobs, Observability | R0 support |
| WHS | Оператор склада / хаба | Receive, move, handover and control stock | Warehouse, Execution | R1 |
| COM | Compliance / quality specialist | Resolve regulatory holds and cargo suitability | Compliance, Cargo | R0 limited; expansion R1 |
| OWN | Руководитель компании / operations owner | See KPI, exception cost and profitability | Reporting, Finance | R1 |
| MKT | Freight exchange participant / moderator | Post permitted listings, verify partner and disputes | Marketplace | R2 |
| MLS | ML model operator / data steward | Approve datasets/models and interpret quality | Intelligence | R1 design / R2 operation |

**Identity and authorization note:** `SHP/RCV/DRV` may interact through a portal/link or authenticated account depending on pilot decision; every grant must have a bounded resource scope, expiry and audit. Platform support is not a superuser of tenant cargo/payment data.

## 3. Multi-pass development program

| Pass | Focus | Deliverable | Stop condition |
|---|---|---|---|
| 1 (this revision) | Role catalog + 12 R0 story seeds | Actor map, core journeys, questions and initial TDD trace | Reviewed for missing roles/process ownership |
| 2 | SHP/SAL/PLN/CAR: RFQ, quote, vehicle hold/Booking | Full main/alternate/negative paths, state guards and documents | Commercial/legal actor responsibilities agreed |
| 3 | DSP/DRV/RCV: Trip, pickup, cargo custody, POD, tracking | Evidence rules, offline replay, partial/failed delivery | Logistics/operations signatures and derived status reviewed |
| 4 | FIN/TEN/SUP: reconciliation, permissions, recovery | Finance-lite, tenant isolation, ops exceptions | Security + finance business review |
| 5 | WHS/COM/OWN/MKT/MLS and cross-border extensions | Prioritized R1/R2 story catalog | Strictly no R0 scope inflation |
| 6 | Story → Acceptance → TDD transformation | Given/When/Then, test IDs, unit/module/integration/E2E, dataset fixtures | `ACCEPTED_FOR_TDD` stories can become executable test specifications |

Subsequent passes may revisit earlier stories when discoveries change assumptions. Do not treat a pass as delivered software.

## 4. First-pass scenario inventory (12 story seeds)

All entries: `status=DRAFT`, `evidence=NOT EXECUTED`. Synthetic tenant IDs and shipment facts only. These entries are **story sketches**; full acceptance criteria and tests are developed later.

| Story ID | Actor | User story / result | Primary business rules and risk | Existing references |
|---|---|---|---|---|
| USB-SHP-001 | SHP | As shipper I submit RFQ for specified origin/destination, cargo units, conditions and time window to receive a qualified offer | Missing mandatory cargo/safety fields cannot yield binding quote; tenant owner and share grant | KX-COM-001, LFC-002 |
| USB-SAL-001 | SAL | As expeditor I request missing RFQ data and issue an immutable versioned quote to avoid unapproved commitment | Quote version, expiry, price approval, legal binding rules pending | KX-COM-002, LFC-003/004 |
| USB-SHP-002 | SHP | As authorized customer I accept exactly one current quote version | Accepted quotation does **not** prove reserved truck; stale/replayed version denied | KX-LFC-002/004, LFC-004/005 |
| USB-CAR-001 | CAR | As carrier manager I respond with a capacity offer and confirm/decline assigned work | `SELECTED` != physical reservation; partner only sees permitted job and buy-side terms | KX-LFC-003, LFC-006/017 |
| USB-PLN-001 | PLN | As planner I shortlist physically eligible vehicle combinations and route | Capacity/height/door/cargo compatibility and approved constraints; no unverified legal allow | KX-VEH-001, KX-CAR-001/003 |
| USB-DSP-001 | DSP | As dispatcher I request an atomic capacity hold, then confirm booking only with valid quote and confirmed resource | Competing holds, stale state and timeout cannot double-book or falsely confirm | KX-OPS-002, LFC-005/007 |
| USB-DRV-001 | DRV | As assigned driver I report pickup and custody evidence for actual cargo units | Trip started/GPS != pickup; duplicate offline evidence dedup | KX-LFC-005, LFC-011 |
| USB-DSP-002 | DSP | As dispatcher I view shipment milestones and stale-aware GPS/ETA to handle delays | No false live position; GPS geofence != delivery; privacy-filtered customer data | KX-OPS-004, LFC-012 |
| USB-RCV-001 | RCV | As consignee I record full/partial/refused delivery with verifiable POD | 8/10 units != delivered all; signed evidence/authorized receiver required per policy | KX-OPS-005, LFC-013/014 |
| USB-FIN-001 | FIN | As financial controller I reconcile sell/buy amounts and evidence separately from actual cash receipt | Delivered != Paid; no duplicate payment allocation or invoice status from unverified callback | KX-FIN-001/002, LFC-021..026 |
| USB-TEN-001 | TEN | As tenant admin I grant/revoke scoped access for a carrier or customer on a shipment | Role != ownership; revoke must stop new access to GPS, quote, documents, cache | KX-TEN-001/002, LFC-008/017 |
| USB-SUP-001 | SUP | As support operator I inspect job failures and initiate authorized safe replay without disclosing unrelated tenant data | Least privilege, audited replay, no duplicate side effects, RLS and source-owner checks | JOB-004..008, KX-ARC-OPS-001 |

## 5. Detailed seed example — USB-DSP-001 (ready for business elaboration, NOT ready for TDD)

**Primary:** TENANT-A Dispatcher. **Collaborators:** Commercial (valid customer quote), Fleet (owner of CapacityReservation), Booking (orchestrator), optional TENANT-C carrier. **Trigger:** authorized actor requests assignment of an eligible vehicle for a customer-accepted quote.

**Preconditions:** quote version accepted and unexpired under business rules; carrier authority and cargo/vehicle compatibility checked; prospective capacity interval defined; existing resource holds available as authoritative DB state. **Main flow:**
1. Dispatcher selects approved quote and eligible vehicle/time window.
2. Booking validates authenticated tenant scope, customer agreement and expectedVersion.
3. Booking calls exported Fleet API; Fleet serializes capacity hold against competing requests and returns typed result.
4. Booking only marks confirmed when contractual and reservation prerequisites satisfy its own state machine; transaction/outbox or durable process coordination guarantees convergence.
5. Customer and carrier receive scoped notifications asynchronously; notification failure cannot undo committed business truth.

**Alternative cases:** quote expires during command; carrier withdraws; competing dispatcher reserves same truck; worker retries expired hold; Redis outage; unauthorized partner; Booking process crashes after Fleet hold and before confirmation. None may silently produce `CONFIRMED` without authoritative proof.

**Immutable evidence:** quote ID/version, tenant owner, reservation ID/version, chosen vehicle/time range, command idempotency key, authorization decision, outbox event ID and timestamps.

**Candidate TDD targets (NOT TESTS YET):** `USB-DSP-001-AC-01` valid booking; `-AC-02` conflicting hold; `-AC-03` expired quote; `-AC-04` replay; `-AC-05` tenant spoofing; `-AC-06` restart after hold; `-AC-07` stale expiry job; `-AC-08` notification failure. Once approved, assign test IDs `TDD-USB-DSP-001-*` and map to unit, integration and E2E suites.

**Open for business review:** binding quote before carrier confirmation; owner of definitive booking state; precise obligations for TENANT-C; cancellation charges; hold time and tenant-visible state names. Until answered, the story remains `DRAFT`.

## 6. Scenario-to-TDD traceability standard

```text
ROLE + TENANT + CAPABILITY
 -> USER STORY (USB-...)
 -> BUSINESS ACCEPTANCE CRITERIA (USB-...-AC-nn)
 -> DOMAIN POLICY/STATE TRANSITION (module-owned)
 -> TEST DESIGN (TDD-USB-...-nn)
 -> UNIT / PROPERTY / MODULE / POSTGRES-RLS / E2E
 -> EXACT SHA + CI + BUSINESS SIGN-OFF
```

Coverage target is **risk/invariant completeness**, not story count or an arbitrary coverage %. A single story can require several test levels. Reuse existing `LFC-*`, `JOB-*`, `ENG-*`, `KX-*` instead of defining competing versions of the same rule. MapStruct maps snapshots/DTOs but must not bypass actor permissions or aggregate constructors.

## 7. Iteration-1 acceptance and open questions

Iteration 1 is accepted for **documentation review**, not business sign-off, when:
- roles include the actor, tenant scope and primary goal, without granting rights by job title alone;
- story IDs are unique, refer to existing requirement/test identifiers and cover first end-to-end freight lifecycle;
- no story falsely equates accepted quote/selected carrier/vehicle GPS/POD/payment;
- R0/R1/R2 boundaries remain explicit; next pass targets commercial/booking detail.

**Questions for role interviews:** who legally commits expeditor and carrier, who may approve price deviations, who signs pickup/POD and when, how independent carrier gets a grant, when customer sees GPS, who verifies bank/ERP payment reference, what support may view without impersonation.

**Next planned pass:** `PASS-2 — Commercial & Booking` expands `USB-SHP-001/002`, `USB-SAL-001`, `USB-CAR-001`, `USB-PLN-001`, `USB-DSP-001` with fully typed main/alternative/negative steps and business-owned acceptance. Do not fabricate approval or production test results.

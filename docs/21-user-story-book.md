# 21 — KERUENIX User Story Book: Role-Based Scenario Bank

**Version:** 0.4 — ITERATION 1 REWORK / ACCESS POLICY V2.1 SECOND REVIEW. **Date:** 2026-11-07. **Status:** PROPOSED / business workshop required. **No implemented features or executed TDD tests are implied.**

**Purpose:** Maintain a single versioned, traceable bank of actor-centered scenarios; build it incrementally in several iterations, *then* derive acceptance tests, TDD unit tests and integration/E2E cases. Do not confuse role catalog with a list of software privileges or tenant membership.

**Canonical authorization matrix (v2.1):** [24 — Access Governance & TDD](24-access-control-tdd-matrix-v2.md) and [machine contract](contracts/access-policy-matrix.v2.json). **External customer journey:** [23 — External Customer Portal](23-external-customer-portal.md). The [v1 matrix](22-role-permission-scope-approval-matrix.md) is retained as historical draft.

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
| PSA | Platform Super Administrator / KERUENIX operator | Provision tenant and first TENANT_OWNER; optional approved initial TENANT_ADMIN; recover ownership safely | Platform Control Plane, Tenancy | R0 |
| TNO | Tenant Owner / authorized legal-entity representative | Accept control of company, appoint admins, transfer owner with verification | Tenancy | R0 |
| EXC | Внешний клиент компании-Tenant / customer portal | Create requests, view My Orders, monitor shipment, leave verified feedback without internal employee rights | Commercial, Tracking, Documents | R0 |
| SHP | Грузовладелец / customer logistics employee | Request, approve terms, track, accept evidence | Commercial, Tracking, Documents | R0 |
| APR | Commercial Approver / лицо с лимитом утверждения | Approve exceptional client terms, independently of proposer | Commercial | R0 scoped permission template |
| PRC | Carrier Procurement Manager / закупщик перевозок | Request/select offers within authorized supplier policy | Commercial, Fleet | R0 scoped permission template |
| SAL | Экспедитор / коммерческий менеджер | Qualify RFQ, quote, customer commitments | Commercial | R0 |
| PLN | Логист / транспортный планировщик | Determine eligible carrier/vehicle and route | Fleet, Booking, Compliance | R0 |
| DSP | Диспетчер | Assign trip, monitor execution and exceptions | Booking, Execution, Tracking | R0 |
| CAR | Менеджер внешнего перевозчика | Offer capacity, confirm obligations and fleet | Commercial, Fleet, Booking | R0 (trusted partner) |
| DRV | Водитель | Accept assignment, record pickup/delivery evidence | Execution, Documents | R0 |
| RCV | Получатель груза | Verify quantities/condition and acknowledge POD | Execution, Documents | R0 |
| FAP | Finance Approver / финансовый утверждающий | Independently approve payments by financial authority and limits | Finance | R0 scoped permission template |
| DOC | Document Controller / контролёр документов | Verify evidence/package version; release permitted customer files | Documents | R0 scoped permission template |
| FIN | Финансовый контролёр / бухгалтер | Review receivables/payables and payment evidence | Finance, Commercial | R0 finance-lite |
| TEN | Tenant administrator | Manage membership, permission and scoped sharing | Tenancy | R0 |
| SUP | Platform support / SRE | Observe, recover jobs and diagnose without excess data access | Platform Jobs, Observability | R0 support |
| WHS | Оператор склада / хаба | Receive, move, handover and control stock | Warehouse, Execution | R1 |
| COM | Compliance / quality specialist | Resolve regulatory holds and cargo suitability | Compliance, Cargo | R0 limited; expansion R1 |
| OWN | Руководитель компании / operations owner | See KPI, exception cost and profitability | Reporting, Finance | R1 |
| MKT | Freight exchange participant / moderator | Post permitted listings, verify partner and disputes | Marketplace | R2 |
| MLS | ML model operator / data steward | Approve datasets/models and interpret quality | Intelligence | R1 design / R2 operation |

**Identity and authorization note:** `EXC` is a verified external customer relationship, not a staff membership of its provider Tenant; `SHP` remains an own-tenant shipper/signatory persona. `SHP/RCV/DRV` may interact through a portal/link or authenticated account depending on pilot decision; every grant must have a bounded resource scope, expiry and audit. Platform support is not a superuser of tenant cargo/payment data.

## 3. Multi-pass development program

| Pass | Focus | Deliverable | Stop condition |
|---|---|---|---|
| 1 (this revision) | Role catalog + 37 R0 story seeds | Actor map, core journeys, questions and initial TDD trace | Reviewed for missing roles/process ownership |
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

## 4A. Platform onboarding and ownership scenarios (iteration 1 extension)

All scenarios below are `DRAFT`, not business accepted; no TDD tests executed. Platform roles are separate from tenant-operational personas.

| Story ID | Actor | User outcome | Critical guard | Requirement |
|---|---|---|---|---|
| USB-PSA-001 | PSA | As a platform super admin I verify and create a new tenant, invite and initialize its first TENANT_OWNER | Verified organization, verified intended recipient, idempotent provisioning, audit and invitation acceptance; never uncontrolled self-enrollment | KX-TEN-003 |
| USB-PSA-002 | PSA | As platform super admin I provision an initial TENANT_ADMIN where an explicitly approved onboarding request requires it, or recover owner access under dual approval | No ordinary cross-tenant access or unapproved permanent impersonation; MFA, independent approval for recovery, scoped event audit | KX-TEN-003 |
| USB-TNO-001 | TNO | As a verified company owner I appoint or revoke TENANT_ADMIN, transfer ownership safely and prevent the last active owner from disappearing | Authority and permitted delegation, no self-escalation, no platform grants, explicit replacement-owner acceptance | KX-TEN-004 |

### USB-PSA-001 — first tenant owner bootstrap (draft elaboration)

**Actors:** `PLATFORM_SUPER_ADMIN` in platform control plane, invited `TENANT_OWNER` in new tenant. **Preconditions:** platform operator strong authentication, verified corporate identity and owner designation. **Main flow:** operator records/validates onboarding request → platform creates pending tenant with idempotency key → creates expiring owner invitation bound to intended verified identity → intended owner accepts and completes required authentication → platform enables tenant owner membership → emits audit/outbox event and notifies designated representatives. **Denials:** anonymous onboarding cannot grant PSA; failed identity verification cannot activate owner; replay cannot create duplicate tenant/membership; tenant admin cannot create a PSA; super-admin has no default read access to company invoices, cargo or GPS. **Open:** business verification SLA, legal identity evidence and dual-approval policy.

**Candidate acceptance (not test code):** `USB-PSA-001-AC-01` verified first owner; `-AC-02` duplicate onboarding request; `-AC-03` wrong invitee/expired invite; `-AC-04` lost platform access during onboarding; `-AC-05` tenant-data isolation for super-admin. TDD later after actor and approval process sign-off.

## 4B. Access governance and Commercial scenarios — iteration 1 extension

These **seven additional DRAFT story seeds** extend the first pass; acceptance rules are in [22 — Role, Permission, Scope, Approval](22-role-permission-scope-approval-matrix.md). They do not constitute signed-off business policy or executable tests.

| Story ID | Actor | User outcome | Critical decision / referenced approval |
|---|---|---|---|
| USB-TNO-002 | TNO | Transfer company ownership to verified successor without orphaning tenant | Owner authority; successor acceptance; no last-owner removal |
| USB-TEN-002 | TEN | Invite an employee within delegated company/branch scope | Verified invitee and expiring one-time invitation |
| USB-TEN-003 | TEN | Assign only permissible roles and bounded permissions | No self-escalation, owner creation, platform role grant |
| USB-TEN-004 | TEN | Revoke terminated employee membership safely | Existing sessions/Jobs no longer grant future protected access |
| USB-SAL-002 | SAL | Issue approved immutable QuoteVersion or publish amended version | Limits and policy; changed terms require new version |
| USB-APR-001 | APR | Review/approve exceptional price or terms independently of author | Approval bound to quote version, amount, legal entity, person and expiry |
| USB-PRC-001 | PRC | Request, compare and select carrier offers without binding vehicle availability | Partner scope, buy/sell confidentiality; SELECTED not CONFIRMED |

`APR` and `PRC` are permission/role templates that may be assigned to existing staff within scoped tenant policy, not mandatory separate employees. For R0, one person may combine SAL/PRC, but cannot approve their own exception above policy limits.

**Reference:** [machine-readable role permissions](contracts/role-permission-scope-approval.v1.json) defines 24 draft policies and planned acceptance IDs `AUTH-TEN-*` / `AUTH-COM-*`. Story acceptance is approved in business review before becoming TDD test code.

## 4C. External Customer, provider Inbox and sensitive approvals — v2 extension

These **15 additional DRAFT stories** supply missing external-client/product and access-governance roles; not tested or legally accepted. Details: [23 — Customer Portal](23-external-customer-portal.md), [24 — Access Governance v2](24-access-control-tdd-matrix-v2.md).

| Story ID | Actor | Business outcome | Critical rule |
|---|---|---|---|
| USB-TEN-005 | TEN | Invite a verified external customer to a provider-scoped CustomerAccount | No provider employee membership, no email-domain autojoin |
| USB-EXC-001 | EXC | Activate portal through verified provider/customer relationship | No internal provider Tenant membership |
| USB-EXC-002 | EXC | Submit idempotent RFQ to selected provider | Own customer account, correct cargo/route fields; never directly Booking |
| USB-EXC-003 | EXC | Browse and open own requests/orders | CustomerOrg + providerTenant + exact resource; no foreign records |
| USB-EXC-004 | EXC | Read quote and, if authorized signatory, accept exact unexpired version | Reading and legal acceptance are different permissions |
| USB-EXC-005 | EXC | Monitor delivery milestones/ETA and view permitted POD documents | No foreign GPS, provider margin, unapproved evidence |
| USB-EXC-006 | EXC | Submit private review for eligible completed service | One logical review, real completion evidence, no self-review |
| USB-EXC-007 | EXC | Withdraw own RFQ while pre-binding | No silent cancellation of accepted quote/confirmed Booking |
| USB-EXC-008 | EXC | Revoke own provider relationship safely | Revoke future access without granting admin controls |
| USB-EXC-009 | EXC | Request contractual cancellation of confirmed order | Booking owner decides under cancellation policy |
| USB-SAL-003 | SAL | Work provider Tenant inbound customer RFQ queue | Assignee/branch and customer data scope |
| USB-SAL-004 | SAL | Respond to private verified customer review after authorized release (R1) | No editing original text/score; R1 |
| USB-SAL-005 | SAL | Read verified customer feedback scoped to provider company | No foreign provider/customer reviews or edit of original content |
| USB-DOC-001 | DOC | Verify document package before business use/release | Exact package, evidence and immutable version |
| USB-FAP-001 | FAP | Approve valid payable by policy and amount | Initiator cannot self-approve same payment |

**Interpretation:** `FIN` can prepare accounting evidence; `FAP` is a separate **approval capability** (may belong to another appointed person, not automatically a separate headcount). `SHP` and `EXC` must never be used interchangeably in security decisions. A person with several roles still cannot approve their own exception.

**Traceability:** all existing `USB-*` identifiers are preserved; v2 maps `67` draft policy rows and `27` cross-cutting adversarial cases. See [policy JSON](contracts/access-policy-matrix.v2.json). Approval and acceptance requirements must be reviewed before turning into executable `TDD-USB-*` tests.

## 4D. Second-pass access review — three missing business stories (DRAFT)

These stories address gaps discovered in [24 — Access Governance v2.1](24-access-control-tdd-matrix-v2.md) and map to planned `AUTH-*` acceptance checks. No TDD test or legal approval is claimed.

| Story ID | Primary actor | Business result | Hard guard / affected permissions |
|---|---|---|---|
| USB-EXC-010 | EXC | Report damaged, delayed, disputed or missing shipment service and follow status **before or after** completion | `customer:issue:report/read`; exact order/grant, evidence, no direct POD or payment mutation |
| USB-DSP-003 | DSP | Review a customer's request to cancel a confirmed Booking using contract/financial policy | `booking:cancel_request:review`; authorized Booking owner, state/version, charge assessment, independent approval if terms require |
| USB-TNO-003 | TNO | Suspend provider's customer-organization relationship with reason and notification | `tenant:customerrelationship:suspend` (R1); business authority, audit, scope not data erasure |

**Rights clarification:** a verified external customer account may have distinct capability grants `CUSTOMER_VIEWER`, `CUSTOMER_REQUESTER`, `CUSTOMER_SIGNATORY`, and `CUSTOMER_FEEDBACK_AUTHOR`. These are not four new mandatory role templates. A customer who can create RFQ cannot automatically accept a legally significant QuoteVersion or publish a review. Closing an external user's session is not deleting the customer organization or its coworkers.

**Coverage:** 40 unique story seeds, 67 draft policy rows, 27 cross-cutting negative tests. No executed code or tests; business approval is still required.

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

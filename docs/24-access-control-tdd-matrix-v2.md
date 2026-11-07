# 24 — KERUENIX Access Governance v2.1: Roles, Scopes, Approvals & TDD

**Version:** 2.1.0 · **Date:** 2026-11-07 · **Status:** DESIGN REVIEW / NOT IMPLEMENTED. **Machine contract:** [access-policy-matrix.v2.json](contracts/access-policy-matrix.v2.json). **Supersedes:** [v1 matrix](22-role-permission-scope-approval-matrix.md) and [v1 JSON](contracts/role-permission-scope-approval.v1.json) for future design decisions; v1 remains available for historical traceability. No existing implemented code was migrated.

## 1. Executive re-audit

v1 was directionally correct but **incomplete**. Important gaps and corrective decisions:

| Gap identified | Impact | v2 resolution |
|---|---|---|
| `SHP` versus external customer lacked precise identity boundaries | Provider employee membership accidentally granted to external customer | Distinguish own-tenant shipper/signatory from `EXTERNAL_CUSTOMER` tied to explicit `CustomerAccount` and provider relationship |
| Customer ordering and provider incoming queue were missing | Only internal freight workflows, no B2B self-service | Separate `My Requests/My Orders` and tenant `Incoming RFQs`; each has scoped read projection |
| Role templates mixed with authorizations and ownership | Tenant leakage and privilege escalation | Explicit `SubjectType`, `Permission`, resource scope, delegation ceiling, policy and deny-by-default |
| Human approval treated similarly to ordinary scoped read | Excess approval friction or accidental unconditional allow | Split **guard-only**, **conditional human approval**, **mandatory independent approval**, **customer attestation** |
| No dedicated payment approver and document verifier policies | Financial SoD/POD attestation gap | `FAP` Finance Approver, `DOC` Document Controller profiles; separate Finance/Execution/Documents checks |
| Missing Booking/Fleet/Driver/Recipient operational permission rows | Break between commercial quote and actual delivery | Add capacity, booking, assignment, pickup/POD and evidence scopes |
| Review and reputation not separated | Fraud, unauthorized public reputation publication | Private verified-service feedback in Commercial for R0; public ranking later with moderation policy |
| No full adversarial replay/tenant matrix | Mock-positive tests could pass with leaks | Planned `AUTH-X-001..016` plus each per-permission acceptance |
| Approval limits and legal identity not specified | False legal guarantees | Explicit business/legal sign-off items; no invented amount thresholds |
| Platform support and background jobs authority poorly defined | Cross-tenant privilege retained after job creation | Service-principal scope, revalidation, redaction and replay permissions |

**Strategic posture:** Do not turn this into a separate IAM microservice, enterprise policy DSL, or 30 new deployed services. One Spring Modulith backend, 17 existing business modules; Tenancy owns security/identity policies, domain owners enforce their own aggregate guards. R0 adopts only necessary role templates. Review across all 17 modules is iterative; v2 covers the critical operational vertical, not every future logistics function.

## 2. Authorization decision model

```text
Identity: PERSON / PLATFORM OPERATOR / EXTERNAL CUSTOMER / SERVICE PRINCIPAL
  -> verified authentication (MFA where privileged)
  -> active provider or own tenant context (never raw caller header)
  -> explicit permission via active role assignment / customer capability grant
  -> resource: tenantId + legalEntityId + branchId + owner/assignment
  -> CustomerAccount OR PartnerGrant OR guest receiver token, if applicable
  -> field allowlist + expiry/revocation + resource/version state
  -> conditional human approval or SoD (only when action requires it)
  -> domain owner enforcement in transactional command
  -> ALLOW or DENY (default)
```

**Guard vs approval:** `AP-SCOPED-READ` and similar `GUARD_ONLY` rules are deterministic authorization checks. They must **not** trigger human approval. `AP-COM-EXCEPTION` and `AP-FINANCE` require an independent authorized human decision. `AP-COM-CUSTOMER-ACCEPT` requires evidence of authority of the **customer** to accept a specific quote version. `AP-COM-ISSUE` is conditional: Sales can issue only within configured terms/limits; beyond that an exceptional approval is mandatory.

Policies are additive **preconditions**, not a flat role permission lookup. A template may grant a capability, but effective access is still denied unless subject, tenant/customer account, exact resource and legal/operational conditions pass.

## 3. Principal taxonomy and ownership

| Principal | Example | Membership and trust boundary | Default exposure |
|---|---|---|---|
| `PLATFORM_OPERATOR` | PSA/SUP | Separate platform control plane; privileged onboarding vs redacted support operations | Platform metadata only |
| `TENANT_MEMBER` | TEN, SAL, APR, PRC, FIN, FAP, DOC, DSP, PLN | Verified active membership of owner tenant and legal-entity/branch/delegation | Authorized tenant resources only |
| `EXTERNAL_CUSTOMER_ACCOUNT_MEMBER` | EXC, buyer of transport service | Verified `customerOrgId + customerAccountId + providerTenantId + scoped grant`; **not provider employee membership** | Only own customer-safe requests/orders/tracking/reviews |
| `PARTNER_TENANT_MEMBER` | Carrier working through its company tenant | Carrier's own membership + provider's active resource PartnerGrant | Assigned shipment/offer/operational details, not provider sell price/margin |
| `TENANT_OR_ASSIGNED_EXTERNAL_WORKER` | Driver | Own verified identity, assigned trip/unit and time scope | Own work and safety instructions only |
| `AUTHORIZED_CONSIGNEE_OR_TIME_LIMITED_GUEST` | Receiver/POD signer | Verified recipient or narrow one-time delivery-attempt token | Specific delivery attempt, no general order browse |
| `SERVICE_PRINCIPAL` | Outbox/Job handlers | Explicit job type + tenant resource context, independent service identity | Only handler allowlist, audited and bounded |

**External customer model:** a buyer may purchase services from Tenant-A without registering their own KERUENIX tenant. Their `CustomerAccount` is provider-linked. A buyer that also operates Tenant-B uses its own Tenant-B membership plus explicit B2B grant toward Tenant-A; it **does not** acquire Tenant-A employee membership. A person authorized for multiple customer organizations must select an actively granted organization context per request.

Data ownership: `Tenancy` secures identity and grants; `Commercial` owns customer relationship records, RFQ/QuoteVersion and private `ServiceReview`; `Booking` owns booking state; `Fleet` owns resource reservation; `Execution` owns custody/delivery truth; `Tracking` owns customer-safe derived projections; `Documents` owns evidence access; `Finance` owns invoices and payment approvals. Consumer-facing order cabinet is a composed view/API, **not** an additional database source of truth.

## 4. Canonical Role → Permission → Resource Scope → Policy → TDD matrix

**67 policies — draft, all entries machine-readable.** This is a policy candidate, not an automatic role grant. In particular `CustomerPortalApi` and `PlatformJobs` are technical surfaces, **not** new business modules. All listed permissions require active assignment, relationship and resource guard. Writes remain owned by their domain.

### Tenancy + platform identity — 16 policies

| Policy | Role template | Permission | Scope key | Guard / approval | Planned acceptance |
|---|---|---|---|---|---|
| `TEN-01` | Platform Super Admin | `platform:tenant:create` | `PLATFORM_ONBOARDING_CASE` | `AP-PLAT-ONBOARD` | `AUTH-TEN-001` |
| `TEN-02` | Platform Super Admin | `platform:owner:bootstrap` | `PENDING_TENANT_AND_VERIFIED_INVITEE` | `AP-PLAT-ONBOARD` | `AUTH-TEN-002` |
| `TEN-03` | Platform Super Admin | `platform:admin:bootstrap` | `PENDING_TENANT_AND_VERIFIED_INVITEE` | `AP-PLAT-ONBOARD` | `AUTH-TEN-003` |
| `TEN-04` | Platform Super Admin | `platform:owner:recover` | `VERIFIED_INCIDENT_AND_TARGET_TENANT` | `AP-PLAT-RECOVERY` | `AUTH-TEN-004` |
| `TEN-05` | Tenant Owner | `tenant:admin:appoint` | `OWN_ACTIVE_TENANT_LEGAL_ENTITY` | `AP-TEN-DELEGATION` | `AUTH-TEN-005` |
| `TEN-06` | Tenant Owner | `tenant:owner:transfer` | `OWN_ACTIVE_TENANT_LEGAL_ENTITY` | `AP-TEN-DELEGATION` | `AUTH-TEN-006` |
| `TEN-07` | Tenant Admin | `tenant:member:invite` | `DELEGATED_TENANT_LEGAL_ENTITY_BRANCH` | `AP-TEN-DELEGATION` | `AUTH-TEN-007` |
| `TEN-08` | Tenant Admin | `tenant:role:assign` | `DELEGATED_ROLE_SET_AND_MEMBER_SCOPE` | `AP-TEN-DELEGATION` | `AUTH-TEN-008` |
| `TEN-09` | Tenant Admin | `tenant:member:revoke` | `DELEGATED_MEMBER_SCOPE` | `AP-TEN-DELEGATION` | `AUTH-TEN-009` |
| `TEN-10` | Tenant Owner | `tenant:partnergrant:manage` | `AUTHORIZED_SHIPMENT_AND_PARTNER_SCOPE` | `AP-TEN-DELEGATION` | `AUTH-TEN-010` |
| `TEN-11` | Tenant Admin | `tenant:partnergrant:revoke` | `DELEGATED_SHIPMENT_PARTNER_SCOPE` | `AP-TEN-DELEGATION` | `AUTH-TEN-011` |
| `EXT-01` | External Customer | `customer:portal:activate` | `PROVIDER_TENANT_CUSTOMER_RELATIONSHIP_AND_VERIFIED_INVITEE` | `AP-CUSTOMER-RELATION` | `AUTH-EXT-001` |
| `EXT-12` | External Customer | `customer:access:revoke_self` | `EXACT_OWN_CUSTOMER_ACCOUNT_MEMBERSHIP_ONLY` | `AP-CUSTOMER-SELF-REVOKE` | `AUTH-EXT-012` |
| `TEN-12` | Tenant Admin | `tenant:customeraccount:invite` | `AUTHORIZED_PROVIDER_TENANT_CUSTOMER_ORGANIZATION_AND_VERIFIED_INVITEE` | `AP-CUSTOMER-RELATION` | `AUTH-TEN-012` |
| `TEN-13` | Tenant Admin | `tenant:customeraccount:member:revoke` | `PROVIDER_TENANT_CUSTOMER_ACCOUNT_EXACT_MEMBER_SCOPE` | `AP-CUSTOMER-RELATION` | `AUTH-TEN-013` |
| `TEN-14` | Tenant Owner | `tenant:customerrelationship:suspend` | `PROVIDER_TENANT_VERIFIED_CUSTOMER_ORGANIZATION` | `AP-CUSTOMER-RELATION-SUSPEND` | `AUTH-TEN-014` |

### Commercial, RFQ and feedback — 29 policies

| Policy | Role template | Permission | Scope key | Guard / approval | Planned acceptance |
|---|---|---|---|---|---|
| `COM-01` | Shipper signatory | `rfq:create` | `OWN_SHIPPER_TENANT_OR_EXPLICIT_SUBMISSION_GRANT` | `AP-RFQ` | `AUTH-COM-001` |
| `COM-02` | Shipper signatory | `rfq:amend_draft` | `OWN_RFQ_ALLOWED_EDITABLE_STATE` | `AP-RFQ` | `AUTH-COM-002` |
| `COM-03` | Sales/Expeditor | `rfq:qualify` | `ASSIGNED_CUSTOMER_RFQ_IN_FORWARDER_TENANT` | `AP-RFQ` | `AUTH-COM-003` |
| `COM-04` | Sales/Expeditor | `quote:draft` | `ASSIGNED_CUSTOMER_IN_FORWARDER_TENANT` | `AP-COM-DRAFT` | `AUTH-COM-004` |
| `COM-05` | Sales/Expeditor | `quote:issue` | `ASSIGNED_QUOTE_VERSION_AND_LEGAL_ENTITY` | `AP-COM-ISSUE` | `AUTH-COM-005` |
| `COM-06` | Commercial Approver | `quote:approve_exception` | `AUTHORIZED_FORWARDER_LEGAL_ENTITY_AND_LIMIT` | `AP-COM-EXCEPTION` | `AUTH-COM-006` |
| `COM-07` | Shipper signatory | `quote:accept` | `EXACT_QUOTE_VERSION_FOR_AUTHORIZED_SHIPPER` | `AP-COM-CUSTOMER-ACCEPT` | `AUTH-COM-007` |
| `COM-08` | Shipper signatory | `quote:decline` | `EXACT_QUOTE_VERSION_FOR_AUTHORIZED_SHIPPER` | `AP-QUOTE-DECLINE` | `AUTH-COM-008` |
| `COM-09` | Carrier Procurement | `carrier_offer:request` | `AUTHORIZED_FORWARDER_RFQ_AND_VERIFIED_PARTNER` | `AP-COM-PROCUREMENT` | `AUTH-COM-009` |
| `COM-10` | Carrier Manager | `carrier_offer:submit` | `OWN_CARRIER_TENANT_AND_EXPLICIT_REQUEST_GRANT` | `AP-COM-PROCUREMENT` | `AUTH-COM-010` |
| `COM-11` | Carrier Procurement | `carrier_offer:select` | `AUTHORIZED_FORWARDER_PROCUREMENT_SCOPE` | `AP-COM-PROCUREMENT` | `AUTH-COM-011` |
| `COM-12` | Sales/Expeditor | `quote:revise` | `OWN_ISSUED_QUOTE_CONTEXT` | `AP-COM-ISSUE` | `AUTH-COM-012` |
| `COM-13` | Finance Officer | `commercial:margin:read` | `OWN_FORWARDER_LEGAL_ENTITY_FINANCIAL_SCOPE` | `AP-COM-MARGIN` | `AUTH-COM-013` |
| `EXT-02` | External Customer | `customer:rfq:create` | `CUSTOMER_RELATIONSHIP_TO_EXACT_PROVIDER_TENANT` | `AP-RFQ` | `AUTH-EXT-002` |
| `EXT-05` | External Customer | `customer:quote:read` | `CUSTOMER_AUTHORIZED_QUOTE_VERSION` | `AP-SCOPED-READ` | `AUTH-EXT-005` |
| `EXT-06` | External Customer | `customer:quote:accept` | `EXACT_UNEXPIRED_QUOTE_VERSION_AND_CUSTOMER_SIGNATORY_SCOPE` | `AP-COM-CUSTOMER-ACCEPT` | `AUTH-EXT-006` |
| `EXT-09` | External Customer | `customer:review:submit` | `COMPLETED_ELIGIBLE_SERVICE_FOR_CUSTOMER_ORDER` | `AP-CUSTOMER-REVIEW` | `AUTH-EXT-009` |
| `EXT-10` | External Customer | `customer:rfq:withdraw` | `OWN_CUSTOMER_RFQ_IN_ALLOWED_PRECOMMIT_STATE` | `AP-RFQ` | `AUTH-EXT-010` |
| `COM-14` | Sales/Expeditor | `rfq:inbox:read` | `PROVIDER_TENANT_ALLOWED_BRANCH_TEAM_INBOX_INCLUDING_UNASSIGNED_RFQ` | `AP-SCOPED-READ` | `AUTH-COM-014` |
| `COM-15` | Sales/Expeditor | `review:respond` | `PROVIDER_TENANT_VERIFIED_COMPLETED_SERVICE_REVIEW` | `AP-CUSTOMER-REVIEW` | `AUTH-COM-015` |
| `EXT-11` | External Customer | `customer:review:read` | `VERIFIED_CUSTOMER_ACCOUNT_EXACT_SERVICE` | `AP-SCOPED-READ` | `AUTH-EXT-011` |
| `COM-16` | Commercial Approver | `quote:approval:withdraw` | `AUTHORED_APPROVAL_FOR_SAME_VERSION` | `AP-COM-EXCEPTION` | `AUTH-COM-016` |
| `COM-17` | Sales/Expeditor | `review:provider:read` | `AUTHORIZED_PROVIDER_TENANT_CUSTOMER_SERVICE_REVIEW` | `AP-SCOPED-READ` | `AUTH-COM-017` |
| `EXT-14` | External Customer | `customer:rfq:list` | `AUTHORIZED_PROVIDER_AND_EXACT_CUSTOMER_ACCOUNT_RFQ_SET` | `AP-SCOPED-READ` | `AUTH-EXT-014` |
| `EXT-15` | External Customer | `customer:rfq:read` | `AUTHORIZED_EXACT_RFQ_AND_CUSTOMER_ACCOUNT` | `AP-SCOPED-READ` | `AUTH-EXT-015` |
| `COM-18` | Sales/Expeditor | `rfq:inbox:assign` | `PROVIDER_TENANT_ALLOWED_BRANCH_TEAM_RFQ` | `AP-RFQ-ASSIGN` | `AUTH-COM-018` |
| `COM-19` | Sales/Expeditor | `rfq:request_clarification` | `AUTHORIZED_ASSIGNED_RFQ_PROVIDER` | `AP-RFQ` | `AUTH-COM-019` |
| `EXT-16` | External Customer | `customer:issue:report` | `OWN_ACTIVE_CUSTOMER_ORDER_AND_SERVICE_REF` | `AP-CUSTOMER-ISSUE` | `AUTH-EXT-016` |
| `EXT-17` | External Customer | `customer:issue:read` | `EXACT_OWN_CUSTOMER_ISSUE_REF` | `AP-SCOPED-READ` | `AUTH-EXT-017` |

### Customer Portal API composition (technical facade) — 2 policies

| Policy | Role template | Permission | Scope key | Guard / approval | Planned acceptance |
|---|---|---|---|---|---|
| `EXT-03` | External Customer | `customer:orders:list` | `CUSTOMER_ACCOUNT_PROVIDER_TENANT_ALLOWED_ORDER_SET` | `AP-SCOPED-READ` | `AUTH-EXT-003` |
| `EXT-04` | External Customer | `customer:orders:read` | `EXACT_CUSTOMER_ORDER_ID_AND_PROVIDER_TENANT` | `AP-SCOPED-READ` | `AUTH-EXT-004` |

### Fleet and capacity — 2 policies

| Policy | Role template | Permission | Scope key | Guard / approval | Planned acceptance |
|---|---|---|---|---|---|
| `FLT-01` | Planner | `fleet:capacity:hold` | `ASSIGNED_VEHICLE_AND_TENANT_LEGAL_ENTITY_WINDOW` | `AP-FLEET-RESERVATION` | `AUTH-FLT-001` |
| `FLT-02` | Carrier Manager | `fleet:capacity:confirm` | `OWN_CARRIER_RESOURCE_AND_ACTIVE_PARTNER_AGREEMENT` | `AP-FLEET-RESERVATION` | `AUTH-FLT-002` |

### Booking and cancellation — 4 policies

| Policy | Role template | Permission | Scope key | Guard / approval | Planned acceptance |
|---|---|---|---|---|---|
| `EXT-13` | External Customer | `customer:order:cancel_request` | `OWN_CONFIRMED_BOOKING_CUSTOMER_PROJECTION` | `AP-BOOKING-CANCEL-REQUEST` | `AUTH-EXT-013` |
| `BKG-01` | Dispatcher | `booking:confirm` | `ASSIGNED_BOOKING_OWN_PROVIDER_TENANT` | `AP-BOOKING` | `AUTH-BKG-001` |
| `BKG-02` | Dispatcher | `booking:cancel` | `ASSIGNED_BOOKING_OWN_PROVIDER_TENANT` | `AP-BOOKING` | `AUTH-BKG-002` |
| `BKG-03` | Dispatcher | `booking:cancel_request:review` | `OWN_PROVIDER_TENANT_BOOKING_AND_AUTHORIZED_ASSIGNEE` | `AP-BOOKING-CANCEL-REQUEST` | `AUTH-BKG-003` |

### Execution and POD — 3 policies

| Policy | Role template | Permission | Scope key | Guard / approval | Planned acceptance |
|---|---|---|---|---|---|
| `EXE-01` | Dispatcher | `trip:assign` | `ASSIGNED_PROVIDER_TRIP_AND_DRIVER` | `AP-TRIP` | `AUTH-EXE-001` |
| `EXE-02` | Driver | `pickup:confirm` | `EXACT_ASSIGNED_TRIP_CARGO_UNITS` | `AP-CUSTODY` | `AUTH-EXE-002` |
| `EXE-03` | Consignee | `pod:submit` | `EXACT_DELIVERY_ATTEMPT_AND_AUTHORIZED_RECEIVER` | `AP-POD` | `AUTH-EXE-003` |

### Tracking — 2 policies

| Policy | Role template | Permission | Scope key | Guard / approval | Planned acceptance |
|---|---|---|---|---|---|
| `EXT-07` | External Customer | `customer:tracking:read` | `AUTHORIZED_SHIPMENT_CUSTOMER_PROJECTION_AND_ACTIVE_GRANT` | `AP-SCOPED-READ` | `AUTH-EXT-007` |
| `TRK-01` | Dispatcher | `tracking:provider:read` | `ASSIGNED_PROVIDER_SHIPMENT` | `AP-SCOPED-READ` | `AUTH-TRK-001` |

### Documents — 3 policies

| Policy | Role template | Permission | Scope key | Guard / approval | Planned acceptance |
|---|---|---|---|---|---|
| `EXT-08` | External Customer | `customer:pod:read` | `AUTHORIZED_ORDER_DELIVERY_EVIDENCE_AND_DOCUMENT_SCOPE` | `AP-DOCUMENT` | `AUTH-EXT-008` |
| `DOC-01` | Document Controller | `document:verify` | `OWN_PROVIDER_DOCUMENT_PACKAGE_AND_VERSION` | `AP-DOCUMENT` | `AUTH-DOC-001` |
| `DOC-02` | External Customer | `customer:document:list` | `CUSTOMER_ACCOUNT_AND_AUTHORIZED_ORDER_PACKAGE` | `AP-DOCUMENT` | `AUTH-DOC-002` |

### Finance-lite — 4 policies

| Policy | Role template | Permission | Scope key | Guard / approval | Planned acceptance |
|---|---|---|---|---|---|
| `FIN-01` | Finance Officer | `invoice:prepare` | `OWN_PROVIDER_LEGAL_ENTITY_AND_AUTHORIZED_ORDER` | `AP-FINANCE-PREP` | `AUTH-FIN-001` |
| `FIN-02` | Finance Officer | `payment:prepare` | `OWN_PROVIDER_PAYABLE_AND_APPROVED_EVIDENCE` | `AP-FINANCE-PREP` | `AUTH-FIN-002` |
| `FIN-03` | Finance Approver | `payment:approve` | `OWN_PROVIDER_LEGAL_ENTITY_AMOUNT_LIMIT_AND_PAYABLE` | `AP-FINANCE` | `AUTH-FIN-003` |
| `FIN-04` | Finance Officer | `finance:payment:reconcile` | `OWN_PROVIDER_LEGAL_ENTITY_AND_VERIFIED_BANK_ERP_PAYMENT` | `AP-FINANCE-RECONCILE` | `AUTH-FIN-004` |

### Platform Jobs (technical capability) — 2 policies

| Policy | Role template | Permission | Scope key | Guard / approval | Planned acceptance |
|---|---|---|---|---|---|
| `SUP-01` | Platform Support | `platform:job:inspect` | `PLATFORM_JOB_METADATA_WITH_REDACTED_FIELDS` | `AP-PLATFORM-OBS` | `AUTH-SUP-001` |
| `SUP-02` | Platform Support | `platform:job:retry` | `FAILED_JOB_AND_APPROVED_REPLAY_REQUEST` | `AP-PLATFORM-JOB` | `AUTH-SUP-002` |

## 5. Reusable approval and guard catalog — 31 rules

| Policy | Type | Responsibility | Required testable check |
|---|---|---|---|
| `AP-PLAT-ONBOARD` | GUARD_ONLY | Platform/Tenancy | Verified business onboarding request, MFA; first owner invitation and recipient acceptance |
| `AP-PLAT-RECOVERY` | HUMAN_APPROVAL_REQUIRED | Platform/Tenancy | Independently verified company evidence, two distinct approvers and audited recovery |
| `AP-TEN-DELEGATION` | GUARD_ONLY | Tenancy | Owner/delegated admin within grantable scope; verified invitation and accepted membership |
| `AP-COM-ISSUE` | CONDITIONAL_HUMAN_APPROVAL | Commercial | Valid exact quote version, allowed amount/terms; exceptional cases require prior approval |
| `AP-COM-EXCEPTION` | HUMAN_APPROVAL_REQUIRED | Commercial | Independent authorized approver, limit/currency/legal entity, matching quote version |
| `AP-COM-CUSTOMER-ACCEPT` | CUSTOMER_ATTESTATION_REQUIRED | Commercial | Verified customer signatory, accepted exact current version, explicit terms evidence |
| `AP-COM-PROCUREMENT` | GUARD_ONLY | Commercial | Carrier offer verified, partner permission and allowed procurement scope |
| `AP-BOOKING` | GUARD_ONLY | Booking | Accepted customer terms + confirmed exclusive reservation + approved cargo/compliance state |
| `AP-POD` | GUARD_ONLY | Execution | Authorized receiver, cargo-unit evidence and signed/verified delivery outcome |
| `AP-FINANCE` | HUMAN_APPROVAL_REQUIRED | Finance | Independent payment approver, authority amount, legal entity, verified obligation/payment reference |
| `AP-CUSTOMER-REVIEW` | GUARD_ONLY | Commercial | Execution source verified completion, customer relationship, one eligible review per service |
| `AP-JOB-REPLAY` | GUARD_ONLY | Platform Jobs | Authorized replay request, redacted diagnostics, attempt audit and dedup |
| `AP-SCOPED-READ` | GUARD_ONLY | Owning business module | Active identity and exact resource scope, allowlisted fields, relevant grant |
| `AP-CUSTOMER-RELATION` | GUARD_ONLY | Tenancy + Commercial | Verified customer organization and provider relationship, account membership/invitation |
| `AP-RFQ` | GUARD_ONLY | Commercial | Authorized submitter, correct customer/provider scope and RFQ lifecycle state |
| `AP-COM-DRAFT` | GUARD_ONLY | Commercial | Assigned Sales/Expeditor, legal entity, quote in draft state and policy |
| `AP-FLEET-RESERVATION` | GUARD_ONLY | Fleet | Vehicle/time ownership, authoritative capacity state and carrier consent |
| `AP-CUSTODY` | GUARD_ONLY | Execution | Driver assignment and actual cargo unit handover evidence |
| `AP-TRIP` | GUARD_ONLY | Execution | Authorized dispatcher, assigned booking/driver and valid resource state |
| `AP-DOCUMENT` | GUARD_ONLY | Documents | Exact package/document, tenant/customer grants, evidence verification, time-limited access |
| `AP-FINANCE-PREP` | GUARD_ONLY | Finance | Own legal entity, verified obligation/accounting reference and correct state |
| `AP-PLATFORM-OBS` | GUARD_ONLY | Platform SRE | Read-only redacted job metadata, incident/operational purpose and audit |
| `AP-COM-MARGIN` | GUARD_ONLY | Commercial + Finance | Explicit margin-read financial permission and own legal entity |
| `AP-QUOTE-DECLINE` | GUARD_ONLY | Commercial | Customer authorization on exact current QuoteVersion and declinable state; idempotent command and reason audit |
| `AP-RFQ-ASSIGN` | GUARD_ONLY | Commercial | Provider team/branch scope for unassigned RFQ, atomic assignee change with expectedVersion, audit |
| `AP-BOOKING-CANCEL-REQUEST` | GUARD_ONLY | Booking | Customer Account scope, exact booking and open cancellation-request eligibility; persisted request with reason; no automatic cancel |
| `AP-CUSTOMER-ISSUE` | GUARD_ONLY | Commercial intake -> owning Execution/Booking issue handling | Requester has exact customer order/Booking, issue type and evidence; clear escalation owner; not a review or POD rewrite |
| `AP-FINANCE-RECONCILE` | GUARD_ONLY | Finance | Approved Finance permission, source-verified bank/ERP transaction reference, unique allocation, amounts/currency and immutable audit |
| `AP-CUSTOMER-SELF-REVOKE` | GUARD_ONLY | Tenancy | Verified EXC user and exact own provider CustomerAccount membership; revoke own sessions/tokens |
| `AP-CUSTOMER-RELATION-SUSPEND` | CONDITIONAL_HUMAN_APPROVAL | Tenancy + Commercial | Authorized provider manager/Owner, verified business basis, notice and safe retention |
| `AP-PLATFORM-JOB` | GUARD_ONLY | Platform Jobs (technical) | Scoped platform operator job metadata or specifically approved replay, tenant and job-type allowlists, audit |

**Approval is not authorization:** a guard-only check never opens a human approval step. An independent approver is required only for actions like financial payment approval, commercial exception, or verified recovery. Ordinary reads and RFQ updates are explicitly authorized state-checked operations.

## 6. Two user workspaces and review lifecycle

**External customer / EXC:** invitation/identity → choose authorized provider/customer organization → RFQ → My Requests/My Orders → customer QuoteVersion view (signatory accepts) → awaiting provider resource confirmation → Booking → delivery status and freshness-aware ETA → authorized POD/document downloads → private review of verified completed service. `QuoteVersion.ACCEPTED != Booking.CONFIRMED`. No raw GPS, internal rates, other customer shipments, self-assignable roles or open tenant dashboards.

**Provider Sales / Tenant-A:** inbound RFQs scoped by owning tenant and assignee/branch → validate and qualify → quote preparation, approval/issue → customer response → Procurement/Booking flow → provider shipment monitoring → review visibility/response (response R1). Inbound queue is a view of provider Commercial RFQs, not an independently writable order state.

**Reviews (R0 minimal):** authenticated EXC with an active CustomerAccount, eligible service verified from Execution/POD, one logical review per provider+customer account+eligible booking; rating/text private by default; source event ID, reviewer and moderation audit recorded; dedup enforced at DB. For partial/refused/disputed delivery, review eligibility **remains pending** until a verified resolution rule is approved; this does not erase customer complaint rights. General complaints/claims are a separate business workflow. No public star ranking or automated reputational penalties in R0.

**Revocation:** deny future protected reads immediately at server authorization boundary after confirmed revoke. Be honest about previously issued presigned RustFS URLs: they may survive until TTL unless access is proxied and continuously checked. Cache keys and all derived projections include enough customer/provider/permission scope; revoke blocks stale cached authorizations, not merely invalidates a user’s displayed UI.

## 7. Planned TDD adversarial suite — 27 high-risk tests

All cases are **planned**; no executable tests or CI passed. 

| Test ID | Adversarial condition | Expected outcome | Required test layer |
|---|---|---|---|
| `AUTH-X-001` | external-customer cross-account listing/order UUID enumeration | DENY without record-count or field leak | HTTP+PostgreSQL-RLS |
| `AUTH-X-002` | customer EXC tries provider internal tenant role API | DENY; no provider membership | HTTP+RLS |
| `AUTH-X-003` | provider Super Admin requests customer margin or POD without grant | DENY; platform data plane separation | HTTP+RLS |
| `AUTH-X-004` | TenantAdmin assigns itself PlatformSuperAdmin or FinanceApprover | DENY; delegation ceiling enforced | JUnit+HTTP+PostgreSQL |
| `AUTH-X-005` | same user has Sales and CommercialApprover template and attempts self approval | DENY for same quote exception | JUnit+PostgreSQL concurrency |
| `AUTH-X-006` | two customer actors race QuoteVersion expiry and accept | only valid authoritative version transition occurs once | JUnit+PostgreSQL concurrency |
| `AUTH-X-007` | PartnerGrant revoked while tracking cache still warm | new reads denied, no cached restricted DTO leak | HTTP+Redis failure matrix |
| `AUTH-X-008` | two verified customers from different org submit ratings on foreign Booking | DENY for foreign; one eligible logical review by authorized owner | PostgreSQL unique+HTTP |
| `AUTH-X-009` | customer reads POD via stale signed URL after revoke | documented TTL exposure or access broker enforcement, no false immediate revoke claim | HTTP+RustFS acceptance |
| `AUTH-X-010` | support job replay executes after authorizing user membership revoked | revalidated authority, policy and idempotency; no stale privilege | Jobs+Testcontainers |
| `AUTH-X-011` | provider employee issues Quote with MapStruct-supplied tenantId or approval flag | server derives tenant, ignores/denies overposted sensitive fields | HTTP+Mapper Unit |
| `AUTH-X-012` | receiver follows leaked POD link for another delivery | DENY due exact delivery attempt or token authorization | HTTP+RLS |
| `AUTH-X-013` | one user is Tenant Owner and FinanceApprover and requests self financial approval | no bypass of payment-level SoD | JUnit+PostgreSQL |
| `AUTH-X-014` | internal event handler acts under absent tenant context | fail closed, no cross-tenant writes | Job+Modulith+RLS |
| `AUTH-X-015` | provider grants EXC to wrong customer org across shared email domain | scope verified by explicit invited identity and org mapping; no domain-based autojoin | HTTP+PostgreSQL |
| `AUTH-X-016` | quote acceptance / booking / review confuse lifecycle projections | no accepted quote implies booking; GPS not POD; delivery not payment | Module integration+E2E |
| `AUTH-X-017` | provider admin invites external buyer by shared email domain without verifying customer organization | deny unverified relationship, no provider employee membership or cross-customer access | HTTP+PostgreSQL |
| `AUTH-X-018` | Sales staff in provider Tenant-A tries to inspect private reviews belonging to provider Tenant-B | deny across provider tenant and customer service scope | HTTP+RLS |
| `AUTH-X-019` | Quote viewer invokes decline command via read-only permission | DENY; read does not authorize state mutation | HTTP+JUnit+PostgreSQL |
| `AUTH-X-020` | External customer requests cancellation of confirmed Booking | request stored, Booking remains unchanged until owner policy decision and contract effects | Module+PostgreSQL |
| `AUTH-X-021` | EXC revokes own access while coworkers share customer organization | only actor membership/sessions disabled; others retain correct scope | HTTP+RLS |
| `AUTH-X-022` | Unassigned incoming RFQ is assigned concurrently by two branch Sales actors | one committed assignee/version, other conflict; wrong-branch DENY | PostgreSQL concurrency+HTTP |
| `AUTH-X-023` | Customer reads provider-composed My Orders from multiple source modules | no direct cross-module DB writes; exact CustomerAccount-scoped list and field allowlist | Modulith+HTTP+PostgreSQL RLS |
| `AUTH-X-024` | Finance approver approves outgoing payable without bank settlement evidence | approval recorded but Paid/Settled unchanged until independently reconciled verified cash fact | Finance unit+PostgreSQL |
| `AUTH-X-025` | Customer read-only capability tries to create RFQ, sign quote and post review | each action requires separate explicit CustomerAccount capability | HTTP+security |
| `AUTH-X-026` | External client submits damage issue before service completed | valid issue accepted/triaged if order scoped; standard review eligibility remains independent | HTTP+Commercial integration |
| `AUTH-X-027` | Job monitoring role sees tenant finance payload via diagnostics | redacted operational metadata only; no Tenancy SQL side door | Jobs+RLS+HTTP |

**Integration requirement:** each of the 67 entries also has a distinct `AUTH-...` acceptance ID. Security verification uses HTTP+Spring Security plus actual PostgreSQL RLS/Testcontainers for isolation; booking and quota race tests must exercise real transactions. Red–Green–Refactor applies to domain policy, not to a fake SQL mock.

## 8. Rollout with minimum overengineering

| Stage | Scope | Gate |
|---|---|---|
| A0 | Security/legal review of principal types, customer signing, approval limits, scoped read projections, retention | No ambiguous tenant or resource owner |
| A1 | Tenant onboarding, Membership, external CustomerAccount grant, immutable role templates, guarded APIs | Two-tenant and two-customer isolation green |
| A2 | External RFQ + provider inbound queue; Quote issue/approval/customer accept; Booking/Fleet resource guards | No self approval; no false booking; test fixtures pass |
| A3 | Driver/POD/evidence, customer tracking, Finance-lite, minimal private verified review | Full vertical E2E, no GPS=POD or delivered=paid |
| A4 | Ops recovery, revocation, cache/worker replay and exact-SHA CI/performance | Negative matrix and failure injection passed |

**Out of R0:** general custom-role builder, drag-and-drop workflow/RBAC editor, external self-signup with open public ordering, marketplace-wide public reviews, delegated subcontractor hierarchy editor, embedded enterprise BPM, standalone IAM microservice and realtime permissions graph service. All may be reconsidered on measurable demand.

## 9. Business decisions requiring explicit sign-off

- Who may legally accept QuoteVersion for customer organization (EXC role alone is insufficient) and what evidence/form of electronic agreement is required in pilot jurisdiction?
- May customer have several providers/branches and who approves access/withdrawal? Can customer order as an individual, or only on behalf of organization?
- Finance approval thresholds in KZT/other currencies and independent approver availability; define emergency procedure before deploying.
- Which data/fields are visible to provider's CustomerOrg-X vs Y, receiver, external carrier, and which signed URLs must support hard revocation?
- Does the contract permit a customer rating after partial delivery or dispute? R0 defaults to no standard service rating until resolution; claims remain possible.
- Who can request vs approve cancellation after binding quote/Booking? How are charges/compensation represented?
- Which role is authorized to release compliance holds and verify regulated documents? Expand later in domain-specific pass, not silently by Dispatcher.
- How is customer account identity verified without an independent paid Tenant, and who handles account suspension and data deletion?
- What exact performance/load metrics are required for high-volume external order listing, tracking and authorization checks?

**Architectural verdict:** v2 is a design draft ready for cross-functional review, not legal acceptance, executable TDD or production-grade authorization. Earlier v1 content remains historical; do not use it to generate new role code without v2 review.

## 10. Coverage boundary — remaining nine business modules

This v2 is the **R0 vertical-slice authorization baseline**, not permission sign-off for all 17 business modules. The following need separate actor/scenario passes when enabled:

| Business module | Roles/access question | Recommended phase |
|---|---|---|
| Cargo | Cargo profile owner, customer-provided attributes, evidence correction | R0 safety rules with module-specific guards; full policy matrix later |
| Compliance | Expert assessment, HOLD denial, independent release, proof of qualification | R0 hard-deny defaults, R1 full access catalog |
| Optimization | Planner/dispatcher job request, solver result approvals and quotas | R1 |
| Intelligence | Data steward, feature/model approval, training scopes and export restrictions | R1/R2 |
| Recovery | Subcontract rescue authorization, custody and cost change approvals | R1 |
| Warehouse | Warehouse operator, inventory ledger adjustments, owner/custodian scope | R1 |
| Marketplace | Listing author, moderator, counterparty trust, complaints and reputation | R2 |
| Regulatory | Official rule-set editor, independent approver and version provenance | R1/R2 |
| SaaS Control | Subscription administrator, plans, billing records and provisioning quotas | R1 |

The existence of a role name does not grant access to these modules. Apply `deny-by-default` until the relevant business module defines its own policies. Integrate with [User Story Book](21-user-story-book.md) passes and exact-`SHA` tests instead of implementing hypothetical UI and policy engines prematurely.

**Contract qualification before implementation:** validate JSON schema/version, uniqueness of policy IDs and acceptance IDs, reference to a known role, referenced approval/guard definition, and linkage to a real `USB-*` story. These are documentation checks today; they are not CI checks until implementation.

## 11. Second-pass hard audit — v2.1 corrective decisions

The second review found **business correctness and authorization gaps**; every change below is now reflected in [JSON v2.1](contracts/access-policy-matrix.v2.json).

1. **State-changing Quote decline:** `COM-08` cannot use `AP-SCOPED-READ`; must use `AP-QUOTE-DECLINE` and authorization against the exact version and valid state. A reader of a quote is not automatically entitled to decline it.
2. **External customer workspace is not provider staff membership:** `customer:rfq:list/read` and `customer:orders:list/read` independently verify `providerTenantId + customerAccountId + customerOrgId + exact resource`. Different users in the same customer company may hold Viewer, Requester, Signatory, Feedback Author capabilities. `EXC` is a persona, not four automatically bundled permissions.
3. **Read composition without breaking Modulith boundaries:** `EXT-03/04` are exposed by `CustomerPortalApi`, a transport/application facade that composes **exported** Commercial, Booking, Execution, Tracking and Documents APIs; it cannot import internal modules or directly write their tables. It is **not** an 18th business module.
4. **Inbound RFQ operability:** Sales receives an explicitly scoped branch/team queue, `rfq:inbox:assign` with expectedVersion, and `rfq:request_clarification` to move `SUBMITTED → NEEDS_INFO` under Commercial owner rules. Concurrent assignments are not lost updates.
5. **Cancellation request is not cancellation:** `EXT-13` is now owned by Booking; EXC may submit a request, but an authorized Booking actor decides the outcome and contractual cost. Customer request never directly changes `Booking.CONFIRMED` to `CANCELLED`.
6. **Self-disconnection versus organization suspension:** `EXT-12 customer:access:revoke_self` revokes only the actor's CustomerAccount membership and sessions. `TEN-13` revokes a specific invited member; `TEN-14` organization-wide suspension is an explicitly audited R1 policy requiring business review. Colleagues must not be locked out by one user's action.
7. **Approval ≠ Payment:** `FIN-03` approves a payable, but approval alone is not a bank transfer or `SETTLED` status. `FIN-04` reconciles a unique verified bank/ERP payment reference with amount/currency/allocations.
8. **Issue/claim intake ≠ review:** `EXT-16/17` permits a customer to raise and follow a delivery issue even before delivery is complete; eligibility for a standard verified-service rating remains separate. Issue receipt does not change POD or imply a refund.
9. **Platform Jobs own operations:** `SUP-01/02` inspect/retry Jobs under a technical `PlatformJobs` API with scoped service authorization, not Tenancy's business tables. Neither support nor Super Admin gets global tenant payload visibility.
10. **Role template ≠ automatically granted rights:** R0 may show a role preset, but explicit assignments, customer grants, state/version checks, field projections and transaction-specific SoD are still required.

**Unresolved for sign-off:** the actual legal signer for an external company, commercial limit thresholds, contract cancellation penalties, dispute case ownership, consent/retention for review and bank-reconciliation evidence adapter. These require owner/business/security approval; no false universal policy defaults.

**TDD priorities for next implementation slice:**
- `AUTH-X-019,025` — no read→write privilege inference or automatic EXC grants;
- `AUTH-X-020,022` — cancellation request and concurrent assignment correctness;
- `AUTH-X-021,023` — external membership isolation and composed My Orders;
- `AUTH-X-024` — approval separate from verified settlement;
- `AUTH-X-026,027` — issues before POD, no support payload leak.

**Scope policy:** 17 business modules unchanged. V2.1 adds security contracts and scenarios, not new services, cross-module direct repositories, IAM DSL, distributed workflows or a general rules engine. Historical v1 remains readable; only v2.1 is the current design candidate.

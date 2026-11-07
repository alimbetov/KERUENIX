# 23 — External Customer Portal, Tenant Order Inbox, Delivery Monitoring & Reviews

**Version:** 0.1 / User Story Book iteration 1 extension · **Date:** 2026-11-07 · **Status:** DESIGN / business and security review required. **Implementation/tests:** NOT STARTED.

**Authoritative security policy:** [Access Governance v2](24-access-control-tdd-matrix-v2.md), [JSON v2](contracts/access-policy-matrix.v2.json). The earlier v1.1 policy references below are historical. **Decision:** introduce `EXTERNAL_CUSTOMER` (code `EXC`), an external buyer of logistic services with a **customer order cabinet** and a provider-Tenant-facing **inbound order inbox**. This is a **role/experience and read-model capability**, not an 18th business module or a second platform. It belongs to existing Tenancy, Commercial, Booking, Execution, Tracking and Documents boundaries. Reviews are private B2B service feedback in R0; public reputation is a separately governed later feature.

**Relationships:** [User Story Book](21-user-story-book.md), [Role/Permission Matrix](22-role-permission-scope-approval-matrix.md), [machine matrix](contracts/role-permission-scope-approval.v1.json), [Lifecycle](10-commercial-execution-lifecycle-v1.md), [MVP qualification](05-mvp-qualification.md).

## 1. Business gap and personas

Previous `SHP` describes **shipper logistics employee / legally authorized customer signatory**, often in a distinct `TENANT-B`; this does **not** guarantee the existence of an actual portal for an external customer buying services from `TENANT-A`.

Introduce `EXC = EXTERNAL_CUSTOMER_PORTAL`:
- can be an individual employee of a company **without a purchased KERUENIX tenant**, granted access to a provider-specific customer account after verification/invitation;
- can also belong to a company that operates its **own tenant**; in that case the same customer-facing capabilities are supplied by narrow B2B `PartnerGrant` and never by inheriting roles in the forwarder's tenant;
- may work with several providers, but each provider relationship, quote, RFQ, order and tracking projection is independently authorized. No automatic cross-provider visibility;
- **cannot** view provider's internal fleet availability, procurement buy rates, margin, unrelated customer accounts, job queue, driver personal details or raw GPS history.

**R0 scope decision:** authenticated, invited/verified external portal identities and customer relationships. Do not make a public anonymous RFQ equivalent to an accepted quote or binding Booking. Anonymous lead intake, self-signup risk controls and public review/search are later options.

## 2. Two business workspaces

### External Customer — My Orders / «Мои заказы»

```text
Клиентский кабинет [поставщик услуг Tenant-A]
  Обзор: мои активные / ожидающие решения / завершённые
  Новая заявка (RFQ)
  Мои заявки: черновик | отправлено | уточнение | предложение
  Мои заказы: ожидает подтверждения ресурсов | подтверждён | в работе
               частичная доставка | доставлено | исключение | закрыто
  Заказ №...: условия и QuoteVersion, согласование, статусы, ETA freshness,
              доступные документы/POD, сообщения по исключениям
  Мои отзывы: оценка исполненной услуги, история / ответ поставщика
  Профиль: мои уведомления и доступные организации/поставщики
```

The user-friendly labels are **customer read-projection labels**, NOT new authoritative aggregate states. They are derived from RFQ, QuoteVersion, Booking, Shipment, DeliveryAttempt and Documents with watermarks; `QuoteVersion.ACCEPTED != Booking.CONFIRMED`, `Trip.STARTED != Pickup`, `GPS != POD`, `Shipment.DELIVERED != Finance.PAID`.

### Provider Tenant — Incoming Orders / «Заявки клиентов»

```text
Tenant-A Operations / Sales
  Входящие RFQ: новые | требуют уточнения | в работе | ожидание клиента
  Customer/organization, cargo profile, route, date/time window, priority
  Assignee and SLA (as configured), quote version, customer acceptance
  Transfer to Booking only when explicit quote/resource guards succeed
  Customer orders: Booking and Shipment operational milestones (scoped view)
  Customer feedback: completed-service reviews, reply/moderation workflow
```

An external `New RFQ` is not inserted directly into a provider's confirmed `Booking` table and does not pre-allocate equipment. An inbound queue belongs to the provider tenant, not a second business source of truth. Its items are provider-owned Commercial RFQ records and/or derived queue projections with explicit assignment.

## 3. Scenario bank extension

| Story ID | Role | User outcome | Priority |
|---|---|---|---|
| USB-EXC-001 | EXC | Activate customer portal via verified invitation/customer relationship without becoming provider Tenant staff | R0 |
| USB-EXC-002 | EXC | Submit RFQ to selected provider tenant with cargo/route/window details and get tracking reference | R0 |
| USB-EXC-003 | EXC | Browse/filter **My RFQs / My Orders** and open details, no access to other customer accounts | R0 |
| USB-EXC-004 | EXC | Read a customer QuoteVersion and accept it only with separate signatory authority | R0 |
| USB-EXC-005 | EXC | See authorized delivery milestones, ETA freshness, and signed/verified POD evidence | R0 |
| USB-EXC-006 | EXC | Leave one attributable, auditable post-service review of a verified fulfilled order | R0 minimal |
| USB-EXC-007 | EXC | Withdraw/amend an RFQ before binding agreement under version/state rules | R0 |
| USB-SAL-003 | SAL | Handle incoming customer RFQs in the provider tenant with assignment and conversion to verified quote | R0 |
| USB-SAL-004 | SAL | Respond to a customer's eligible review without editing their original feedback | R1 |

**Ownership:** `Commercial` owns inbound RFQs/customer quotes and a minimal private `ServiceReview` aggregate; `Tracking` owns authorized shipment projection; `Documents` owns evidence access; `Execution` owns verified completion facts; `Booking` owns confirmed service agreement. No global `OrderStatus` table and no duplicate shipment truth.

## 4. Standard R0 workflow — customer request to delivery feedback

1. `Tenant-A` admin/Sales establishes allowed customer relationship with `CustomerOrg-X`; invite EXC user bound to verified identity, provider, organization and scope. The EXC accepts; no provider internal membership is granted.
2. EXC creates RFQ: origin, destination, cargo units, weight/volume, handling conditions, pickup/delivery windows and contact data; client receives `rfqId` and status `SUBMITTED`. Retries use `idempotencyKey`.
3. Tenant-A Sales sees request in **Incoming RFQ**, qualifies it, asks for missing data and drafts an immutable QuoteVersion. Only authorized Sales/Approver can issue within approved limits.
4. EXC can read customer-facing quote and, if legally authorized to sign for its company, accepts **that exact unexpired version**. Another EXC without signatory scope can view but cannot accept.
5. Booking/Fleet separately confirm resource and agreement. EXC sees `Awaiting resource confirmation` until Booking actually becomes `CONFIRMED`.
6. Execution generates pickup/custody/POD events; Tracking projects permitted milestone/ETA with `observedAt/receivedAt/watermark`; customer cannot see internal driver/other customers or procurement data.
7. Authorized EXC downloads customer-releasable document/POD only after server-side rights check; grants can expire or be revoked.
8. After verified full service completion (or explicit business-accepted exception rules), Commercial receives trusted completion evidence/event and creates a **ReviewEligibility** record. EXC may leave one review for that eligible completed service; customer sees own review, Tenant-A sees review and may respond in R1. Reviews do not alter POD or financial truth.

**Review in R0:** private to actual customer and provider; optional rating (e.g. 1–5) and text, with verified `orderId/bookingId`, `reviewerCustomerAccountId`, `providerTenantId`, completion proof reference, timestamps, audit. One logical review per eligible service (unique DB constraint and idempotency); correction/version policy must be agreed, moderation/reporting and public ratings belong to later iteration. No reviews of unrelated orders, no self-reviews by provider staff, and no public exposure by default.

## 5. Authorization and isolation contract

```text
principal identity
 -> CustomerAccount / verified customerOrg + providerTenant relationship
 -> EXC permission
 -> exact RFQ/Order/Quote/Shipment/Document/Review ownership
 -> active resource grant + field-filtered projection
 -> ALLOW or DENY (default)
```

- Customer access is a **relationship grant**, **not** `Tenant-A` employee Membership. If EXC is itself a member of another tenant, use an independently validated B2B grant.
- Authenticated user may work for multiple customer organizations or providers; each workspace action selects a verified relationship, not a spoofable `tenantId` HTTP header.
- RLS must not be bypassed by changing connection context from user input. Backend exposes customer-safe views/projections with verified provider-owned scope; pooled JDBC context uses `SET LOCAL` per authorized transaction. Ensure no leaking cache keys/read models across `customerAccountId + providerTenantId`.
- Quote detail excludes carrier buy rate, margin, other shipper and contract data. Tracking excludes historical raw vehicle positions unless explicit contracted policy. Documents are checked at request/download time, with signed URL TTL limitations noted.
- If relationship or grant is revoked, all subsequent protected API/worker/cache reads fail closed, with short-token strategy; already downloaded evidence cannot be retroactively erased.
- `customer:quote:accept` is a **distinct permission from** `customer:quote:read` and must verify company signatory authority and evidence of acceptance.

## 6. Role-to-permission and acceptance extension

The historical machine contract [v1.1](contracts/role-permission-scope-approval.v1.json) preserved 24 original policies and added 12 lines. The **current design authority** is [v2](contracts/access-policy-matrix.v2.json), which further adds booking, evidence, finance, customer revocation, and negative-access policies:

| Policy | Permission | Scope / critical gate | Acceptance |
|---|---|---|---|
| EXT-01 | `customer:portal:activate` | Verified provider/customer relationship; no provider staff role | AUTH-EXT-001 |
| EXT-02 | `customer:rfq:create` | Exact provider tenant and customer account | AUTH-EXT-002 |
| EXT-03 | `customer:orders:list` | Own/customer-org authorized orders only | AUTH-EXT-003 |
| EXT-04 | `customer:orders:read` | Exact own order, filtered fields | AUTH-EXT-004 |
| EXT-05 | `customer:quote:read` | Customer-safe version | AUTH-EXT-005 |
| EXT-06 | `customer:quote:accept` | Verified signatory, exact version, expiry | AUTH-EXT-006 |
| EXT-07 | `customer:tracking:read` | Permission-filtered shipment milestones and ETA | AUTH-EXT-007 |
| EXT-08 | `customer:pod:read` | Exact authorized POD/document and download rights | AUTH-EXT-008 |
| EXT-09 | `customer:review:submit` | Evidence-verified completed service, one review | AUTH-EXT-009 |
| EXT-10 | `customer:rfq:withdraw` | Own request before binding effect | AUTH-EXT-010 |
| COM-14 | `rfq:inbox:read` | Tenant Sales queue/assignment | AUTH-COM-014 |
| COM-15 | `review:respond` | Reply, never edit original (R1) | AUTH-COM-015 |

## 7. Proposed TDD acceptance suite — to implement after business review

| Test ID | Given / When | Then |
|---|---|---|
| AUTH-EXT-001 | EXC activates via valid vs expired/wrong-company invite | Correct customer relationship only; no Tenant-A membership/permissions |
| AUTH-EXT-002 | EXC submits complete/incomplete RFQ twice with idempotency key | Exactly one SUBMITTED RFQ or validation response; never Booking.CONFIRMED |
| AUTH-EXT-003 | EXC lists orders with same provider and two customer accounts | Only authorized customer/organization orders returned, no count leakage |
| AUTH-EXT-004 | EXC guesses another customer order UUID | DENY; no price/margin/data exposure |
| AUTH-EXT-005 | Customer reads quote with internal buy and sell rates in provider source | Only authorized customer-facing quote fields returned |
| AUTH-EXT-006 | Read-only EXC tries to accept; authorized EXC races expiry | Read-only denied; version/expiry/identity atomic guard; no implicit Booking |
| AUTH-EXT-007 | User tracks own/foreign shipments with stale GPS | Own freshness-aware milestones only, no unrelated raw GPS |
| AUTH-EXT-008 | EXC downloads unrelated or revoked POD link | Denied at protected access boundary; TTL semantics qualified |
| AUTH-EXT-009 | Unfulfilled/foreign/self order reviewed; duplicate review submitted concurrently | Deny or dedup; only verified service one logical review |
| AUTH-EXT-010 | EXC withdraws RFQ before/after customer accepted quote | Allowed in permitted draft stage; denial or amendment workflow afterward |
| AUTH-COM-014 | Provider Sales lists inbound orders for authorized and foreign tenant/branch | Only authorized tenant queue and customer fields |
| AUTH-COM-015 | Provider reply submitted twice or tries to rewrite customer review | Idempotent append-only reply, no mutation of original review |

**Unit:** authorization policy, review eligibility, version guard, projection field allowlist. **PostgreSQL/Testcontainers:** RLS, scope leakage, unique review/idempotency constraints, two-customer concurrency. **HTTP/Modulith:** end-to-end permission-protected RFQ/quote/booking lifecycle, event-triggered customer status, expiry/revocation, scoped review. **UI acceptance:** verify the customer **My Orders** and provider **Incoming Orders** show matching lifecycle facts without promising illegal progress. No tests have been executed.

## 8. Release scope and decisions requiring owner review

**R0:** invited authenticated customer portal; new RFQ; My Requests/My Orders; customer QuoteVersion acceptance for authorized representative; read-only tracking/ETA/POD; minimal private verified-service review. Provider: incoming RFQ queue, assignment, response and handoff to existing Booking. Implement via same backend and existing role/security mechanisms; no new business module or marketplace ratings service.

**R1:** provider reply/moderation workflow, comprehensive review analytics, advanced notifications, multi-provider organization switching, broader client organization delegation.

**R2:** public marketplace reputation, open self-signup/anonymous lead conversion, fraud scoring, appeal/reporting policy after legal/product review.

**Open decisions:** which customer person can sign quote; invoice visibility and financial status in My Orders; customer relationship onboarding without own tenant; handling disputed/partially completed service reviews; privacy/retention/moderation of opinion; customer notifications channel and consent. These require pilot stakeholders, not invented rules.

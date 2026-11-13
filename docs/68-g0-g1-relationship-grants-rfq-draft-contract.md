# 68 — G0 → G1: business relationship, authority and RFQ Draft S0 decision packet

**Date:** 2026-11-13. **Status: PROPOSED — business, Security, DB and independent S2 approvals NOT granted.** Applies to [R0 business review](67-r0-business-review-revised-roadmap.md) and [vertical slice](66-r0-rfq-execution-pod-vertical-slice-s0.md). This packet defines a small explicit decision surface rather than authorizing production work.

## 1. Pilot operating model (recommended, not approved)

Select one verified **shipper organization** and one verified **carrier organization**, both as explicit legal/business parties, for a **single domestic road shipment and single load/leg**. The current tenancy design also has a **provider tenant** and multiple customer accounts under that tenant. These are not synonyms. The customer may be operationally represented by a provider `CustomerAccount`; a carrier is a separately authorized counterparty, never implicitly a second customer account.

**Important unresolved BR-03 / DEC-R0-02:** determine whether the provider tenant is a carrier/forwarder organization serving shipper CustomerAccounts (B2B logistics-office SaaS), or the neutral platform with independent shipper and carrier tenant organizations (marketplace). **Do not implement both models at once.** The recommended R0 pilot is **provider/carrier workspace + managed shipper CustomerAccounts**, with explicit counterparty relationship to a verified carrier where required. This minimizes cross-tenant marketplace ACL and enables a real transport workflow. Product/domain must explicitly accept this before schemas.

| Party / resource | Proposed legal/operational role | Ownership and visibility invariant |
|---|---|---|
| `Tenant` | Isolation boundary for provider organization/workspace | All tenant-owned rows are tenant-scoped by RLS |
| `Organization` | Verified legal/business party: shipper or carrier | Legal entity and member records distinct from customer account |
| `CustomerAccount` | Shipper commercial relationship inside provider tenant | Owner account scope mandatory for RFQ, list/count/download/export |
| `CounterpartyRelationship` | Explicit provider/carrier or shipper/carrier permitted relationship | Relationship has verified status, effective/expiry dates and limited data disclosure |
| `ActorMembership` | Individual employee of organization with effective permission | JWT subject identifies actor, never proves company membership or RFQ rights alone |
| `OperationGrant` | Narrow actor×tenant×account×operation permission in primary PostgreSQL | Fail closed on missing, revoked or unavailable grant |
| `RFQ` | Non-binding versioned business intent, owned by one CustomerAccount | Cross-account read/write prohibited even for the same tenant without distinct grant |

A single actor may belong to multiple organizations only through separately verified, auditable memberships. Never infer relationship from a shared email domain, phone number, JWT `tenant_id`, client JSON selectors or matching carrier name.

## 2. P0 operation authority matrix (proposal for decision)

| Actor | RFQ Draft create/edit/read | RFQ Submit | Quote create/accept | Execution / POD | Account grant administration |
|---|---|---|---|---|---|
| Shipper coordinator with explicit account grant | Allowed under scope | **Blocked G1** | Blocked G1 | Blocked G1 | No |
| Shipper viewer with `RFQ_READ` only | Read only | No | No | No | No |
| Carrier dispatcher | No customer draft visibility until relationship + invitation | No | Blocked G1 | Blocked G1 | No |
| Driver | No | No | No | Blocked G1 | No |
| Recipient | No | No | No | Blocked G1 | No |
| Provider admin | No blanket customer access; explicit scoped operation grant required | Blocked G1 | Blocked G1 | Blocked G1 | Separately authorized, audited |
| Platform operator | No implicit RFQ content access | No | No | No | Emergency access only after separately approved break-glass policy |

Proposed initial operation identifiers: `RFQ_DRAFT_CREATE`, `RFQ_DRAFT_READ`, `RFQ_DRAFT_UPDATE` and `ACCOUNT_GRANT_ADMIN` (admin scope is separate and requires its own decision). No wildcard, no general `ADMIN` bypass, and no unrestricted SYSTEM_SCOPED principal in G1.

## 3. RFQ Draft business contract (minimum first GREEN)

**Command:** authenticated customer coordinator creates an RFQ DRAFT. Mandatory for initial save: server-selected verified CustomerAccount; cargo line description + quantity + unit; origin and destination as at least human-readable locations; an intended pickup window or explicit `UNSCHEDULED` flag (choose at review). Optional: weight, volume, handling instructions, contact reference; null and units validated. All fields/PII must have review-approved bounds before API freeze.

**Proposal HTTP routes** (not currently implemented or approved):
- `POST /api/v1/rfqs/drafts` -> `201 Created` + `Location` and versioned `{rfqId, status:DRAFT, version, customerAccountId, ...}`; server-derived tenant/account.
- `GET /api/v1/rfqs/{rfqId}` -> `200` for current grant and owning account only; cross-account concealment/error policy to be approved (`404` vs `403` with no existence leak).
- `PATCH /api/v1/rfqs/{rfqId}` with `If-Match` or explicit version -> optimistic locking (`409` or `412`, chosen consistently).
- No `Submit`, `Quote`, `Book` or externally visible carrier invitation in G1.

**Persisted aggregate**: `rfq_id` UUID, `tenant_id`, `customer_account_id`, `created_by_actor`, `status=DRAFT`, `version`, `cargo_snapshot` (typed/versioned; do not use uncontrolled JSON for every indexed field), `origin/destination`, `window`, `created_at/updated_at`, and `request_fingerprint` in an independently scoped idempotency record. Every write also stores structured audit and a non-binding domain event in the same DB transaction. Do not accept request body tenant/account as authorization.

**Idempotency key**: mandatory request header for POST, bound to `tenant+account+actor+operation`, with deterministic normalized payload fingerprint and stable recorded response. Identical replay -> same rfq ID and contract-defined status/body. Same key with different normalized request -> `409`. Postgres unique constraint per scope and concurrency test; expiry policy requires sponsor/DB agreement. No global key uniqueness that leaks other customer activity.

**Security model**: verify signed JWT and primary PostgreSQL operation grant in a trusted application boundary; execute under transaction-local tenant RLS and account predicate on every read/write. Revocation before next command denies. If grant store is unreachable -> fail closed. Do not use present test-only `QualificationGrantRegistry` as production authority. External side effects prohibited for Draft. The Outbox platform is delivery plumbing, not the source of grants.

## 4. S1 → S2 → S3 acceptance contract

| ID | Actual behavior tested against real REST/JDBC/PostgreSQL | Oracle |
|---|---|---|
| G1-01 | Authorized actor creates draft | `201`, persisted owner+version+DRAFT, audit + non-binding outbox atomic |
| G1-02 | Replay same request+key, including concurrent calls | Same persistent RFQ and response contract; no duplicate business effects |
| G1-03 | Same key with changed cargo | `409`, original unchanged |
| G1-04 | Same-tenant Account Y actor reads/updates X's RFQ | Denied, cannot infer list/count/existence; no state change |
| G1-05 | Signed JWT with forged tenant/body/account selector | No privilege expansion; denial |
| G1-06 | Grant revoked after first authorized create/read | Next operation denied with same unexpired JWT |
| G1-07 | Primary grant store fails | Request fails closed with no draft, audit+outbox mutation |
| G1-08 | Concurrent PATCH with same expected version | At most one successful update; other conflict |
| G1-09 | Transaction fails after aggregate write before audit/outbox | All three rollback; no partial intent |
| G1-10 | User tries Submit, Quote, Booking through G1 | No binding transition/event or carrier disclosure |
| G1-11 | Same Hikari physical connection reused across tenants | No leaked transaction-local tenant; account checks still independent |
| G1-12 | Save/reopen after process restart, read pagination and export denial | Full persisted draft; no cross-account leakage and no unrestricted export |

**S1 real RED requirement:** at least one targeted missing-business-behavior test must assert specific authenticated handler and DB effect. A missing Java class or an unconditional `denyAll` is **not** a qualified behavioral RED. Existing `RfqDraftRedContractTest` is only the preliminary handler-missing contract with synthetic grant fixtures. After the real relationship/grant API is approved, replace synthetic grant fixtures with production grant rows and a genuine scoped RFQ service boundary. Record exact SHA and expected assertion signatures.

**S2:** independent business/domain signoff for RFQ fields, Security + DB approval for grant and schema, and QA review of 12 oracles. Reviewer's GitHub identity and verdict recorded; author comments do not count. Only then separate Draft PR for smallest S3 GREEN; no main merge before S4.

## 5. G0 release blockers — decision questions for named owners

| Record | Required signed decision | Owner |
|---|---|---|
| G0-BR-01 | Provider-tenant service model vs neutral cross-tenant marketplace; pilot first cargo geography/mode | Product / Domain |
| G0-BR-02 | Organization vs CustomerAccount ownership and carrier counterparty relationship, visibility prior to invitation | Product / CustomerAccount / Security |
| G0-BR-03 | Who can initiate, update, see customer RFQs, grant/revoke, and emergency access | Security / DB / Domain |
| G0-BR-04 | RFQ Draft minimum fields, units, handling requirements, nullable pickup window, contact/PII | Logistics operations |
| G0-BR-05 | Idempotency replay response/status, key retention, version/ETag and conflict/error contract | API / QA / DB |
| G0-BR-06 | Legal meaning and boundary of future Submit, quote acceptance, cancellation, custody and POD | Business / Legal / Operations |
| G0-BR-07 | Pilot payer, two actual organizations, baseline volumes and measurable time/value outcome | Sponsor / Commercial |

**G0-BR-01/02/03 overlap BR-03/DEC-R0-02 and DEC-CA-01. Resolve existing BR/DEC at the source of truth rather than treating this file as competing approval.** Existing [Issue #4](https://github.com/alimbetov/KERUENIX/issues/4), [#6](https://github.com/alimbetov/KERUENIX/issues/6), [#7](https://github.com/alimbetov/KERUENIX/issues/7) and independent [#9](https://github.com/alimbetov/KERUENIX/issues/9) remain open.

## 6. Gate G0 → G1

**G0 CONDITIONAL:** product sponsor has selected lean R0 direction, but payer, legal identity relationships, minimum RFQ fields and independent Security/DB approvals remain open. **G1 S0 contract may be prepared, but production grant schema, authenticated RFQ endpoints and S3 GREEN MUST NOT begin before approved decisions and independent S2**. Keep PR #3 Draft; no production domain implementation and no main merge.

First user-demonstrable G1 milestone: a verified shipper coordinator can create, reopen and edit a draft in real PostgreSQL; a second account in the same tenant cannot see or change it; idempotent replay creates no duplicate.

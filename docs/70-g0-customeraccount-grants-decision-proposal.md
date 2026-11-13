# 70 — G0 decision proposal: CustomerAccount ownership and RFQ Draft operation grants

**Decision state: PROPOSED / NOT SIGNED.** Date: 2026-11-13. This ADR consolidates [#11](https://github.com/alimbetov/KERUENIX/issues/11), [#4](https://github.com/alimbetov/KERUENIX/issues/4), [docs/68](68-g0-g1-relationship-grants-rfq-draft-contract.md) and [docs/69](69-g1-rfq-s1-executable-oracles-and-gates.md) without asserting business/legal/independent QA approval. Until sign-off, no production grant or RFQ domain implementation is authorized.

## A. Scope and selected design recommendation

For the **first pilot only**, propose the **provider workspace** model instead of a neutral cross-tenant shipper/carrier marketplace:

- `Tenant` identifies an operational provider workspace and is the PostgreSQL RLS isolation boundary.
- `Organization` identifies a verified real-world party, independent of tenant; shipper and carrier can be organizations and may have their own staff.
- `CustomerAccount` identifies one shipper's commercial relationship **within exactly one provider tenant**, with immutable owner organization reference; two shipper accounts may coexist in a single provider tenant.
- `Membership` binds a subject to a verified organization, not by JWT inference.
- `CustomerAccountGrant` permits one subject to perform one specific operation for one live customer account within a tenant; the grant does **not** follow from general organization membership.
- `CarrierRelationship` is explicitly invited/verified and may later reveal a submitted RFQ, but **never** by virtue of another account under the same tenant. It is not required for non-binding private Draft and is a future G2 decision.

**Alternative requiring explicit sponsor rejection/selection:** a neutral marketplace with independently isolated shipper/carrier tenants. That option needs additional cross-tenant sharing, invitation, commercial and responsibility rules and must not be implicitly mixed into G1. The chosen business model, scope of organization linkage, and role delegation remain open BR-03/DEC-R0-02.

## B. Minimal logical schema — NOT a migration

| Record | Candidate key / mandatory attributes | Invariant |
|---|---|---|
| `organization` | `organization_id`, legal identity verification state | Legal party distinct from tenant/customer account |
| `customer_account` | `tenant_id`, `customer_account_id`, `shipper_organization_id`, status, `revision` | Owner cannot change by editing RFQ; one account belongs to one tenant |
| `actor_membership` | `subject_id`, `organization_id`, status, effective/expiry, revision | JWT subject alone never confirms active membership |
| `account_operation_grant` | `tenant_id`, `account_id`, `subject_id`, `operation`, status, effective/expiry, `grant_revision` | Unique account/subject/operation scope; no wildcards or implicit admin privilege |
| `rfq_draft` | `tenant_id`, `rfq_id`, `customer_account_id`, `created_by`, status, version, typed cargo/location snapshot | Owner immutable; operation checks AND tenant RLS/account predicates |
| `rfq_idempotency` | tenant, account, subject, operation, idempotency key, canonical request hash, response reference | Equal scoped key+body replays; changed payload conflicts |

**Candidate indexes/constraints for DB review:** FK account→tenant, grant→account and membership, `UNIQUE(tenant_id,customer_account_id,subject_id,operation)` for active grant identity with revisions tracked separately; `UNIQUE(tenant_id,customer_account_id,subject_id,operation,idempotency_key)`; RLS `FORCE ROW LEVEL SECURITY` on protected account/grant/draft records; application role not owner, no BYPASSRLS. All naming and history/identity decisions require DB/Security review before any Liquibase migration.

## C. Precisely bounded operation semantics

| Operation | Authorized behavior | Prohibited behavior |
|---|---|---|
| `RFQ_DRAFT_CREATE` | Create one private, non-binding draft in verified actor's permitted account; store audit and non-binding event atomically | Submit, carrier invitation, quote, booking, payment, cross-account creation |
| `RFQ_DRAFT_READ` | Read one owned draft, and scoped list/count only if specifically approved as part of READ | Cross-account read/existence/cursor/export, reading carrier documents |
| `RFQ_DRAFT_UPDATE` | Update owned draft while status DRAFT and expected version matches | Transfer owner, bypass version, modify submitted quote/booking |
| `ACCOUNT_GRANT_ADMIN` | Grant/revoke only under separately authorized account-admin delegation with atomic audit | Wildcard access, platform-admin customer content read without explicit grant |

**Decision required:** whether LIST/COUNT is included in READ or needs explicit operations; bulk export **excluded** from G1. Grant administration is not implied by possession of any Draft operation.

## D. Authorization algorithm and concurrency safety

1. Authenticate issuer/audience/expiry/signature of JWT. Extract subject identity only; untrusted tenant/account selectors may direct lookup but never establish rights.
2. Resolve immutable resource owner account for GET/PATCH using trusted DB state. For POST, resolve requested account through trusted membership/relationship data.
3. In a transaction against **primary PostgreSQL**, enforce current `GRANTED` operation with effective dates, live actor membership, live account and matching tenant/account; read current revision; fail closed on missing/unknown/unavailable authority.
4. Access protected draft rows in the same appropriately scoped DB transaction with transaction-local tenant context and explicit `customer_account_id` predicate, enforce optimistic version and idempotency.
5. Update RFQ, audit and Outbox atomically. For G1, never publish externally and never create binding effects. Do not reuse a stale prior-request authorization decision.
6. Revocation is atomic with revision increment, audit and Outbox notification. After commit, new operations must see revoked grants. **Concurrent revoke vs already-running write is a design decision**: DB/Security must approve lock/isolation strategy or revision fencing so an operation committing after revocation cannot bypass policy. Do not claim this race solved merely by an early grant check.
7. Return safe 403/404 semantics on unauthorized resource, avoiding account existence leakage. Temporary primary auth-store unavailability yields a controlled failure with **no write**, never allow-by-default. Prefer consistent Problem Details contract once approved.

**Security hard stop:** PostgreSQL RLS gives only tenant isolation, not CustomerAccount isolation. Every read/write/list/count requires a second account boundary. `platform.outbox_event` is not an authority source. No general impersonation or system principal in G1.

## E. Candidate HTTP and replay contract (needs API/QA sign-off)

- `POST /api/v1/rfqs/drafts` with `Idempotency-Key`, returns `201` and immutable `rfqId` plus `version=1`, `status=DRAFT`. Header never replaces account grant.
- `GET /api/v1/rfqs/{rfqId}` under READ grant and verified owner.
- `PATCH /api/v1/rfqs/{rfqId}` with version/If-Match; stale version fails; choose 409 or 412 before S1 acceptance.
- Same key+identical canonical request -> same persisted ID and fixed approved replay response; same key+changed payload -> 409, no write. Expiry/retention, canonical JSON and key collision scopes must be approved.
- Proposed minimum fields: cargo description, positive quantity+unit, origin/destination, pickup window or explicit unscheduled; field-length/privacy and units are unresolved logistics decisions.
- `POST .../submit` is **not enabled**; quote acceptance and booking remain separate G2 contracts.

## F. Required explicit approvals — do not infer from author comments

| Gate | Decision owner(s) | Must record |
|---|---|---|
| G0-BR-01 / BR-03 / DEC-R0-02 | Product sponsor, CustomerAccount domain | Select provider workspace vs neutral marketplace and party/account relationship semantics |
| DEC-CA-01 [#4](https://github.com/alimbetov/KERUENIX/issues/4) | Security + DB + CustomerAccount domain | Grant source, effective/expiry/revocation, in-flight concurrency/fencing, RLS+account policy |
| G0-BR-04 | Logistics domain | Cargo/location/time fields and units for first Draft |
| G0-BR-05 | API/QA/DB | Idempotency, replay, retention, version conflicts and non-disclosure error codes |
| Independent S2 | Separate QA/Security reviewer(s), not the implementation author | Approved exact SHA/test methods, exact RED assertions, result of negative/security cases |

## G. S1 qualification matrix

[docs/69](69-g1-rfq-s1-executable-oracles-and-gates.md) defines G1-01…12. **Not yet executable as qualified production behavior:** missing approved real DB grants and domain command boundary. Test-first execution begins with approved DB grant/ownership boundary and actual PostgreSQL security-negative cases (X/Y, revoke, outage), then authenticated positive RFQ Draft cases. The existing `RfqDraftRedContractTest` and `scripts/ci_assert_rfq_draft_red.sh` are correctly classified `CONTRACT_UNWIRED`, not S2-ready behavioral RED.

## H. Release decision

**Recommended business option: CONDITIONAL GO for provider-workspace S0**, pending sponsor/domain approval. **Formal decision: OPEN / NO-GO for schema implementation and S3** until owners and independent reviewers record approval in [#11](https://github.com/alimbetov/KERUENIX/issues/11), [#4](https://github.com/alimbetov/KERUENIX/issues/4) and appropriate S2 artifact. Keep [PR #3](https://github.com/alimbetov/KERUENIX/pull/3) Draft and `main` unchanged.

# 45 — PR-01 TDD review checkpoint: JWT scope, revoke, Outbox crash/replay

**2026-11-08 · Status: CODE_VERIFIED_PARTIAL / PR-01 NOT_QUALIFIED.**

Canonical sources: [R0 TDD Cases FOUND-01…12](36-r0-tdd-start-pack.md), [Layered ТЗ](43-layer-by-layer-development-tz.md), [PR acceptance manifest](contracts/pr-acceptance-manifest.v1.json), [earlier FOUND-02 TDD](44-pr01-tdd-found02-tenant-isolation.md).

## 1. Major node A — FOUND-03/08/11: verified JWT HTTP → authorized tenant/customer → real PostgreSQL

**RED:** [commit 061d6b0](https://github.com/alimbetov/KERUENIX/commit/061d6b072a1aa43cfc5d7b245becb650acaf5611) / [CI 42471758251](https://github.com/alimbetov/KERUENIX/actions/runs/42471758251).
After fixing initial AssertJ type ambiguity, compilation succeeded; the correctly signed authorized user got **403 instead of 202** because the grant resolver was deny-only. Negative forged, expired, wrong issuer/audience, cross-account, header/body-injection tests were independently runnable.

**GREEN:** [commit 6ce06b7](https://github.com/alimbetov/KERUENIX/commit/6ce06b73c520741e57d8d16e65c5390665e0328d) / [CI 42471862485](https://github.com/alimbetov/KERUENIX/actions/runs/42471862485).
Test-only Spring Security resource-server chain checks real ephemeral RS256, JWT issuer/audience/expiry and delegates *resource grant* to an independent server-side source. `TenantScopeAuthorization` denies if the token isn't a verified `JwtAuthenticationToken`, if account rights are absent or if untrusted body/header tenant selectors conflict. The passing allowed HTTP request writes an audited fact through a PostgreSQL RLS transaction and cannot write to another tenant.

**Scope limit:** test-only controller/grants in `src/test/java`; **no public route opened in production**, no real auth server, Membership or CustomerAccount schema. Production `SecurityConfig` remains `denyAll`.

## 2. Major node B — FOUND-05: crash after consumer commit before producer ACK

**RED:** [commit fc82c00](https://github.com/alimbetov/KERUENIX/commit/fc82c00f7b66b43579a705a0afa68e043798bccb) / [CI 42472121451](https://github.com/alimbetov/KERUENIX/actions/runs/42472121451). No sender invocation was observed: assertion `Expecting code to raise a throwable` failed because `PlatformOutboxDelivery` was intentionally fail-closed.

**GREEN:** [commit 040b655](https://github.com/alimbetov/KERUENIX/commit/040b6557497cd7d6b84f646432746e89133d6182) / [CI 42472240149](https://github.com/alimbetov/KERUENIX/actions/runs/42472240149).
Transaction-safe durable `claim→read→send→ack` over real PostgreSQL, with delivery outside DB transaction and fenced ACK. Test consumer commits `Inbox + Audit` in one transaction, fails publisher after consumer commit before ACK, forces expired lease takeover, delivers again and asserts **2 sends / 1 logical consumer effect**. The original event reaches PUBLISHED only after the successful second send. A cross-tenant dispatcher sees no event.

**REFACTOR:** [commit 2d9de65](https://github.com/alimbetov/KERUENIX/commit/2d9de65c680bae7dfc3a5cfd5ddf1b45a74ac9ee), explicit regression test prohibits invocation inside an existing business transaction. The job+broker service adapter, tenant-scoped scheduler, metrics, quarantine/DLQ and real external transport are NOT done.

## 3. Major node C — FOUND-08: revoked customer grant under the same JWT

**RED:** [commit 76a7e9b](https://github.com/alimbetov/KERUENIX/commit/76a7e9b787d13e7a07524d0cd245a299468f95d2) / [CI 42472373404](https://github.com/alimbetov/KERUENIX/actions/runs/42472373404). After a grant is revoked, same signed/unexpired JWT still returned **202 instead of 403**.

**GREEN:** [commit 642cb8c](https://github.com/alimbetov/KERUENIX/commit/642cb8c0c55af93634c1f0f874a74ef4fee2f7b3) / [CI 42472481080](https://github.com/alimbetov/KERUENIX/actions/runs/42472481080).
Test-only mutable grant source rechecks the right on each request, denies revoked Customer-X without changing Customer-Y independently valid access. No permanent grant data store or distributed cache invalidation is claimed. Full security/tenancy PR-02/03 qualification remains pending.

## 4. Final execution evidence at last CODE SHA

- **Exact code SHA:** [2d9de65c680bae7dfc3a5cfd5ddf1b45a74ac9ee](https://github.com/alimbetov/KERUENIX/commit/2d9de65c680bae7dfc3a5cfd5ddf1b45a74ac9ee)
- [PostgreSQL / Liquibase CI 42472548203](https://github.com/alimbetov/KERUENIX/actions/runs/42472548203) — SUCCESS, real PostGIS, RLS, Outbox and HTTP JWT test suite.
- [Backend Error Contract CI 42472548163](https://github.com/alimbetov/KERUENIX/actions/runs/42472548163) — SUCCESS.
- [TDD Roadmap Contract CI 42472548420](https://github.com/alimbetov/KERUENIX/actions/runs/42472548420) — SUCCESS.

This file is a **review checkpoint**, not an authorized stakeholder/legal signoff.
It does not assert that all FOUND cases, the full SQL/HTTP threat model, Testcontainers-managed PG, production login or carrier flows are qualified.

## 5. Review checklist and next TDD series

1. Review whether test-only grant adapter will be replaced with a persistent authoritative `Membership/PartnerGrant/CustomerAccount` repository once PR-02 starts. No premature broad `permitAll`.
2. Verify the production issuer/JWKS discovery, audience and key rotation policy; the ephemeral test RSA key is not a deployed IdP.
3. Decide the Outbox transport provider and operational failure policy (delay/backoff, poison, DLQ, metrics, graceful worker shutdown) before production activation.
4. Continue FOUND-09 invalid-module fixture, FOUND-10 restore on snapshot, FOUND-12 geographic tenant-boundary negative case and full FOUND-04 aggregate rollback.
5. Rerun all mandatory tests on the next exact SHA. Keep BR/DEC and PR-01 `NOT_QUALIFIED` until all relevant evidence and human review are in place.

**Product safety boundary: no Payments, AR/AP or bank integration in R0.**

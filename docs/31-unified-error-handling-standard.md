# 31 — Unified API Error Contract & Central Handler (Spring MVC / Security / Jobs)

**Version:** 1.0 (proposed) · **Date:** 2026-11-07 · **Target:** Java 21, Spring Boot 4.1.2 (Spring MVC) · **Status:** DESIGN + IMPLEMENTED ERROR-ONLY BOOTSTRAP. Verified GitHub Actions run #22 passed **15 JUnit tests** and the **21-code Java/JSON parity gate** on commit `ac459923`; subsequent changes require requalification. Domain/RLS/E2E qualification remains outstanding.
**Machine catalog:** [api-error-catalog.v1.json](contracts/api-error-catalog.v1.json). **Baseline:** [28 — TDD Acceptance](28-r0-tdd-acceptance-bank.md), [30 — Negative Scenarios](30-negative-and-failure-scenario-bank.md), [20 — Engineering Standard](20-mapstruct-tdd-engineering-standard.md).

## 1. Decision

Adopt **RFC 9457 Problem Details**, `Content-Type: application/problem+json`, for REST errors. **Do not invent** a second envelope of `success/message/data` or `status:error`. Use `ProblemDetail` standard members `type`, `title`, `status`, `detail`, `instance`; append stable `code`, `requestId`, `timestamp`, `retryable`, optional `violations`. `code` is a documented, permanent application error identity; HTTP status describes the transport class; `detail` is safe and user-directed, never parsed by clients; `requestId` is a server-generated opaque incident correlation marker. The response HTTP status MUST match the `status` member. `type` is `urn:keruenix:problem:<CODE>`; `instance` is `urn:keruenix:incident:<requestId>` (not an unredacted URI path).

RFC primary fields belong at top-level, no nested `error` wrapper. Do not return `entityId`, tenant ID, SQL constraint, stack trace, login, password, OTP, JWT, payment data, driver GPS or the rejected request value.

### Example: exclusive fleet conflict

```http
HTTP/1.1 409 Conflict
Content-Type: application/problem+json
Cache-Control: no-store
X-Request-ID: 019d1e8f-6202-4bd6-8864-d0f5933ef971
```

```json
{
  "type": "urn:keruenix:problem:KX-FLT-409-001",
  "title": "Capacity conflict",
  "status": 409,
  "detail": "The selected resource is unavailable for the requested interval.",
  "instance": "urn:keruenix:incident:019d1e8f-6202-4bd6-8864-d0f5933ef971",
  "code": "KX-FLT-409-001",
  "requestId": "019d1e8f-6202-4bd6-8864-d0f5933ef971",
  "retryable": false,
  "timestamp": "2026-11-07T16:00:00Z"
}
```

Example UUID and timestamp are illustrative. Server generates a different request ID for every HTTP request; a separate idempotency key identifies logical command retries. This code is *not* retryable by blindly repeating a conflicting reservation; the client must revalidate state and select a resource.

## 2. Stable code catalog — v1

| Enum | API code | HTTP | Meaning and safe recovery | Retryable |
|---|---|---:|---|---|
| `BAD_REQUEST` | `KX-GEN-400-001` | 400 | Malformed JSON, unsupported request syntax | No |
| `VALIDATION_FAILED` | `KX-GEN-400-002` | 400 | Invalid input with optional `violations` field names/codes only | No |
| `FRAMEWORK_HTTP_ERROR` | `KX-GEN-000-001` | actual 4xx | Safe generic fallback for uncommon framework 4xx (406, 413 etc.), preserves actual HTTP status | No |
| `AUTHENTICATION_REQUIRED` | `KX-AUTH-401-001` | 401 | Missing/invalid authentication; bearer challenge if configured | No |
| `PERMISSION_DENIED` | `KX-AUTH-403-001` | 403 | Authenticated but lacking permission | No |
| `RESOURCE_NOT_FOUND` | `KX-GEN-404-001` | 404 | Both absent and foreign/private resource: same public status, code and detail | No |
| `METHOD_NOT_ALLOWED` | `KX-GEN-405-001` | 405 | Incorrect HTTP method; preserve `Allow` header | No |
| `UNSUPPORTED_MEDIA_TYPE` | `KX-GEN-415-001` | 415 | Incorrect request media type | No |
| `STALE_VERSION` | `KX-GEN-409-001` | 409 | expectedVersion / optimistic concurrency mismatch | No |
| `IDEMPOTENCY_CONFLICT` | `KX-GEN-409-002` | 409 | Same idempotency key, changed payload digest | No |
| `INVALID_TRANSITION` | `KX-DOM-409-001` | 409 | Rejected aggregate state transition | No |
| `QUOTE_EXPIRED` | `KX-COM-409-001` | 409 | No acceptance on expired/superseded QuoteVersion | No |
| `SIGNATORY_REQUIRED` | `KX-COM-403-001` | 403 | Customer signatory authority missing (avoid leaking quote existence) | No |
| `CAPACITY_CONFLICT` | `KX-FLT-409-001` | 409 | Fleet exclusive interval conflict | No |
| `CUSTODY_EVIDENCE_REQUIRED` | `KX-EXE-422-001` | 422 | Pickup/custody proof incomplete | No |
| `PARTIAL_DELIVERY_CONFLICT` | `KX-EXE-409-001` | 409 | CargoUnit quantities/disposition inconsistent | No |
| `SETTLEMENT_EVIDENCE_REQUIRED` | `KX-FIN-422-001` | 422 | Bank/ERP settlement source not verified | No |
| `SUBSCRIPTION_RESTRICTED` | `KX-SAA-403-001` | 403 | A discretionary action blocked by SaaS policy; in-flight safety is separate | No |
| `RATE_LIMITED` | `KX-GEN-429-001` | 429 | Client should obey `Retry-After` when provided | Yes |
| `UPSTREAM_UNAVAILABLE` | `KX-GEN-503-001` | 503 | Temporary external adapter unavailability; retry only if idempotent | Yes |
| `INTERNAL_ERROR` | `KX-GEN-500-001` | 500 | Generic message, private incident logs by requestId | No |

Codes are **append-only identifiers** once clients depend on them; never reuse or change a code's semantic meaning. A domain-owning module registers new codes via review in this catalog, not arbitrary exception strings. `ErrorCode` enum is shared **platform API**, not a source of domain lifecycle logic. No module imports a different module's internal exception class.

## 3. Mapping policy and trust boundaries

| Trigger | HTTP / code | Explicit rule |
|---|---|---|
| JSON unreadable / invalid type | 400 `BAD_REQUEST` | No JSON parser stack or rejected data |
| Bean Validation | 400 `VALIDATION_FAILED` | `violations: [{field, rule}]`, no rejectedValue |
| No authentication / expired token | 401 `AUTHENTICATION_REQUIRED` | Spring Security `AuthenticationEntryPoint`; send `WWW-Authenticate` for Bearer resource-server when JWT is configured |
| Authenticated, insufficient capability | 403 `PERMISSION_DENIED` | Security `AccessDeniedHandler` + method/security advice |
| Resource from foreign Tenant/CustomerAccount | 404 `RESOURCE_NOT_FOUND` | Check exact grant first; same public code/title/detail as nonexistent private resource (avoid existence side channels) |
| Missing resource | 404 `RESOURCE_NOT_FOUND` | No foreign ID in detail/log |
| Stale aggregate `expectedVersion` | 409 `STALE_VERSION` | Domain-owned exception or known optimistic locking failure |
| Same idempotency key, different payload | 409 `IDEMPOTENCY_CONFLICT` | Stable dedup digest, no second command effect |
| Unsupported method/content type | 405/415 | Preserve framework headers; no generic 500 |
| Illegal Quote/Booking/Execution transition | 409 domain code | No authorized state mutation, no success Outbox |
| Missing custody/payment proof | 422 domain code | Only when authorized owner knows resource exists; do not leak through 422 to unauthorized caller |
| Known rate limiter | 429 `RATE_LIMITED` | Emit `Retry-After` only with measured policy; no fake retry duration |
| Known transient adapter outage | 503 `UPSTREAM_UNAVAILABLE` | Retryable after idempotency and bounded backoff; never assume external write was undone |
| Unknown programming/SQL infrastructure failure | 500 `INTERNAL_ERROR` | Log safe requestId/type; no SQL text to client |

**Never** globally map `DataIntegrityViolationException` / PostgreSQL `23505` or `23P01` to `409`: the same SQLSTATE can originate from unrelated constraints and may reveal data/tenant existence. Instead classify a **known named domain constraint** in the owning repository adapter into a typed `DomainProblemException`. Unrecognized DB exceptions remain 500 and trigger secure investigation. A raw PostgreSQL permission/RLS error is not automatically an HTTP 403; first check a trusted owner-grant policy.

Do not send `500` for a normal business denial; do not send `200` with `success=false`; do not accidentally `403` a private foreign object when a consistent `404` obscures its existence. Avoid `409` and `422` on private resources before auth checks.

## 4. Implementation architecture — one contract, two HTTP integration points

```text
Spring Security FilterChain (runs before controller)
  AuthenticationEntryPoint (401) / AccessDeniedHandler (403)
      └── ApiProblemFactory ── ProblemDetail RFC 9457

Spring MVC REST / validation / domain
  @RestControllerAdvice extends ResponseEntityExceptionHandler
      ├── typed DomainProblemException 4xx
      ├── BeanValidation errors 400 with field+rule allowlist
      ├── optimistic lock 409
      ├── HTTP framework errors keep original 4xx/headers
      └── unknown exception 500 (safe generic)
      └── same ApiProblemFactory

OncePerRequestFilter -> server UUID requestId + X-Request-ID + MDC
```

**Important:** `@ControllerAdvice` cannot intercept every authentication failure from a Security filter before MVC. Do **not** duplicate JSON bodies: use one problem factory for both filter and MVC errors. A `ProblemDetail` schema is an **HTTP presentation contract**, not a persistence model or Outbox event schema. For async workers keep `ErrorCode` and `failureCategory` without blindly encoding a whole HTTP problem body.

The code bootstrap targets [Spring Boot 4.1.2](https://spring.io/blog/2026/10/23/spring-boot-4-1-2-available-now/) with `spring-boot-starter-webmvc` and Servlet Spring Security; **not** Spring WebFlux. It is deliberately fail-closed (no working authentication, no public business endpoints) until Tenancy/JWT integration is implemented. A separate [catalog parity script](../backend/scripts/check_error_catalog.py) is part of the [Maven CI workflow](../.github/workflows/backend-error-contract.yml). Domain modules will throw typed failures only after authorization and aggregate guard checks.

### Source organization

```text
backend/
  pom.xml                  # Java21 / Spring Boot4.1.2 bootstrap; subject to full platform BOM
  src/main/java/kz/keruenix/
    KeruenixApplication.java
    platform/errors/
      ErrorCode.java
      DomainProblemException.java
      RequestIdFilter.java
      ApiProblemFactory.java
      ApiExceptionHandler.java
      SecurityProblemHandler.java
    platform/security/
      SecurityConfig.java
  src/test/java/.../platform/errors/
      ErrorContractTest.java
```

Platform errors package is **infrastructure**, not an eighteenth business module. In the eventual Spring Modulith architecture, expose a narrow public errors API while controllers, Security adapters and formatter belong to the platform web adapter. No business aggregate may depend on a servlet or Spring HTTP type.

## 5. Structured error logging, tracing, privacy and alerts

- Server **always generates** `requestId` (UUID) and `X-Request-ID`. Never use arbitrary client-provided IDs as trusted correlation fields. W3C trace IDs may be linked through observability without replacing requestId.
- **4xx known business denials**: structured counters by `code, httpStatus, ownerModule`, no stack by default; authorization violations optionally generate security audit without request body or sensitive values.
- **5xx**: `ERROR` metric and safe log `requestId, exception class, code, source module`; restricted observability pipeline may retain a protected stack trace according to policy, never client response or support dashboard.
- Do not add high-cardinality `requestId`, customer ID, raw URL or tenant ID to Prometheus metric tags. Logs and incident details use restricted retention and redaction.
- `Cache-Control: no-store` on all error responses. No caching of private existence hints; retry backoff obeys policy and idempotency.
- Validate `Accept-Language` support in a future localized error-message catalog; clients branch only on `code`. Show safe translated message in RU/KK/EN and a copyable requestId, never a Java exception.
- If response is already committed/streaming started, cannot replace payload safely: log incident and close stream / send protocol-specific terminal error; do not claim every WebSocket/SSE failure is an HTTP Problem Detail.

## 6. Jobs, Outbox/Inbox and external adapters

Define internal `FailureClassification`: `PERMANENT`, `TRANSIENT`, `CONFLICT_RECONCILE`, `QUARANTINE`. Reuse stable `ErrorCode` but do **not** send HTTP status codes through event payloads as domain truth. Retriable = bounded retry with jitter, idempotency key, deadline and fencing; `409` capacity conflict is not retryable as-is. Uncertain remote payment/carrier commit is `CONFLICT_RECONCILE`, never automatically replay a money transfer. Permanent authorization/validation rejection has **no** retry. Quarantined late custody proof must be preserved for authorized reconciliation but cannot silently rewrite current shipment state. Document worker attempt error code and safe correlation ID, not raw customer payload.

## 7. Negative TDD acceptance for the handler

| Test | Given / When | Then |
|---|---|---|
| `ERR-001` | `DomainProblemException(CAPACITY_CONFLICT)` | HTTP 409 and `KX-FLT-409-001`, no internal details |
| `ERR-002` | `MethodArgumentNotValidException` | 400, field/rule only, no rejected value |
| `ERR-003` | JSON parse exception | 400, no parser stack |
| `ERR-004` | Missing auth in Security chain | 401 with RFC 9457 JSON, correct headers |
| `ERR-005` | Authenticated no permission | 403 with same contract |
| `ERR-006` | Foreign protected resource vs missing private resource | indistinguishable 404 public error detail; avoid count/field/timing side channels |
| `ERR-007` | expectedVersion / optimistic lock conflict | 409 and stable version code |
| `ERR-008` | Unclassified exception incl. raw SQL failure | 500 generic, no SQL/stack/PII |
| `ERR-009` | Unsupported method or media type | 405/415 preserve framework headers |
| `ERR-010` | Multi-level retry/fault race | denied command has no false DB/Outbox state; actual RLS/PG |
| `ERR-011` | RequestId filter + security error | same server-generated ID in header/body/MDC; injection ignored |
| `ERR-012` | Response already committed | no double response or accidental sensitive fallback |

The initial bootstrap includes standalone MVC contract tests, live Spring Security filter integration tests and servlet-fallback tests. **Real JWT/Tenancy, RLS/Outbox and transactional `ERR-010` business tests remain pending**; some `ERR-*` rows are only partially qualified by these error-only tests. Reference [30](30-negative-and-failure-scenario-bank.md) for 48 high-risk business-negative cases and 8 MIX scenarios. Do not conflate `ERR` unit tests and business acceptance.

## 8. Change management / Definition of Done

1. Freeze **code/status/retryability** and public detail in [catalog v1](contracts/api-error-catalog.v1.json). Add codes append-only; no frontend parsing of free text.
2. Integrate global servlet handler and Security `401/403`; no duplicate default `BasicErrorController` JSON envelope for API. Document `/error` behavior for container/filters as a separate integration gate.
3. Run `mvn -f backend/pom.xml test`; verify via real network-enabled CI and lock exact SHA. Initial JUnit contract tests were verified against one concrete SHA; every later change requires a new verified CI run.
4. Roll out per-module typed exceptions only after domain authorization policies, not as a shortcut for RLS or business aggregate consistency.
5. Monitor P0 error rate, `5xx`, `429/503`, denied cross-tenant accesses, idempotency conflicts and late Outbox retry; do not tag high-cardinality tenant/resource IDs.
6. Version public code catalog and OpenAPI `application/problem+json` examples. Every new negative `NEG-R0-*` should map to the correct code and assert lack of forbidden persistence, events and UI state.

**Explicit limits:** This specification and associated backend bootstrap do **not** prove running authentication, active RLS, real financial/carrier business logic or green Maven CI. Do not merge into production until standalone Spring Boot4 tests, Security integration, tenant boundary checks, Spring Modulith verification and pilot policies pass.

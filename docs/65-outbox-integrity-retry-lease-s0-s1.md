# 65 — Outbox A-03 / A-04 / A-05: S0 decisions and S1 evidence gates

**Status:** PROPOSED technical policy, S1 test-first; **NOT** independent S2 acceptance. Scope: existing PostgreSQL Outbox/Inbox in R0 modular monolith. No Redis, Kafka, new job engine, producer-authorization bypass or CustomerAccount production feature.

## A-03 — payload digest / canonicalization decision

**Preferred R0 policy:** payload is a JSON object. Define **one canonical byte sequence** for hashing, independent of Java object serializer key order and whitespace. Pragmatic candidate: canonical bytes are UTF-8 of PostgreSQL `jsonb::text` as read from the authoritative persisted row; calculate SHA-256 on those bytes at the trusted enqueue boundary or via a single PostgreSQL-side digest function (pgcrypto where available). Include event `payload_schema_version`, `event_type`, `tenant_id`, `event_id` and `aggregate_ref` in a versioned envelope hash *if* the goal is whole-event integrity rather than only JSON body integrity. **Do not silently change the meaning** of the existing `payload_sha256` column: its present name implies payload-only digest. For R0, keep it strictly payload-only; other immutable metadata must be independently integrity-protected or a separate envelope digest introduced under a new migration/DEC.

- Decide whether canonical bytes are obtained from DB `jsonb::text`, or from RFC 8785 JCS (different numeric/unicode semantics). Prefer DB `jsonb::text` only while PostgreSQL is the sole writer/source and declare that this format is a *PostgreSQL-specific versioned contract*. JSONB normalization loses original JSON order/format, which is expected.
- On insert, derive digest from **persisted canonical bytes** rather than trusting a caller's digest. On reading for dispatch, independently verify digest before reaching Sender and fail closed with a diagnosable, durable handling policy.
- Avoid reporting a digest as authentication: SHA-256 detects accidental/cross-layer mismatch only if trusted writer/verifier is enforced; a malicious DB writer can change both JSON and digest.
- Golden vectors must include unordered keys, embedded UTF-8, numeric representations, nulls, arrays, large numbers, same digest on replay, and mismatch after mutation.

**S1 evidence:** `OutboxPayloadDigestIntegrityRedTest` against actual PG outbox + sender must remain targeted RED until reviewed implementation. Note legacy test fixtures currently insert arbitrary 64-char hashes; adjust them to correct canonical digest only in S3 after S2 approval.

## A-04 — retry and terminal failure policy

**R0 provisional default:** 3 total delivery attempts (including first claim), then terminal `DEAD_LETTER` for a poison or permanent failure; transient dependency errors use bounded exponential backoff with jitter and operator visibility. Confirm number of retries, age limits, recoverability and error taxonomy with Operations/Security. **Do not apply this threshold to an in-flight lease without fencing and explicit failure classification**; reclaim after crash does not imply an actually failed external delivery.

- `scheduleRetry` currently returns to `PENDING` with no max. It must not cause indefinite replay of a known poison event. Terminalization must clear owner/lease, record typed reason and audit.
- A `DEAD_LETTER` must not be automatically sent again. Manual replay is a new authorized and audited operation, idempotently preserving event identity/digest or explicitly creating a new event.
- Tests: third consecutive retry terminalizes, fourth claim empty; another tenant unaffected; invalid failure/lease owner cannot terminalize; transient errors do not immediately dead-letter; operator replay requires policy.
- `OutboxPoisonEventRedTest` is the *proposed 3-attempt oracle*. A test-only environment flag isolates its expected failure from standard regressions.

## A-05 — external effects across lease expiration

**R0 policy:** Outbox gives at-least-once delivery only. Claim tokens fence Postgres ACK and retry, **not** remote external side effects. Consumers MUST use durable `(tenant_id, consumer_name, event_id)` Inbox dedup within the same transaction as their logical effect; external providers must support idempotency key or a reconciliation/compensation mechanism. Never claim exactly-once external I/O merely because database ACK is fenced.

- Test with real PostgreSQL: old worker reaches Sender and blocks; force lease expiry in CI; newer worker redelivers and commits Inbox, old worker resumes but loses ACK; assert two send attempts, one logical Inbox/Audit effect, event PUBLISHED.
- A producer must never invoke an unverified account export via generic transport; independent Account caller/grant testing is still blocked by BR-03/DEC-R0-02 and DEC-CA-01/03/04.

## Review and release gate

| Area | Evidence | S2 |
|---|---|---|
| A-03 | Real PostgreSQL wrong-hash targeted RED | Awaiting canonical hash definition/QA/DB review |
| A-04 | Real PostgreSQL third-failure targeted RED | Awaiting policy owner and retry classification |
| A-05 | Real PostgreSQL concurrent slow-send Inbox regression | Awaiting independent Security/QA review |
| A-01 | DB-backed CustomerAccount grants | BLOCKED, not implemented |
| R0 protected cache / generic new worker | Explicitly DEFERRED | Not a required release feature |

**Required:** independent reviewer name, decision date, exact SHA/log IDs, recorded alternatives and acceptance in GitHub. PR #3 stays Draft; production code unchanged under S1.

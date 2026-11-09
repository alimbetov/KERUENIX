# 52 — S0 Commercial: RFQ, Quote, Signature, CarrierOffer test-design checkpoint

**2026-11-08 · Status: `PROPOSED_NOT_REVIEWED`.** Project remains in Scenario Design. No new domain code or legal approval.

**Machine source:** [57 Commercial case contracts](contracts/r0-s0-commercial-case-contracts.v1.json); [132 scenario allocation](contracts/r0-scenario-allocation.v1.json); [18 SIG drafts](contracts/r0-s0-extension-gwt.v1.json); [Decision Ledger](contracts/r0-decision-readiness.v1.json); [mandatory five-step TDD](46-r0-scenario-first-tdd-standard.md).

## 1. Inventory and owners

- **30** canonical primary cases: PR-04 (2), PR-05 (1), PR-06 (6), PR-07 (12), PR-11 (9).
- **9** cross-PR impacted cases whose canonical writer/test owner stays elsewhere (PR-19, Tenancy, Fleet, Execution). They are dependencies, **not duplicated owner assignments**.
- **18** signature cases `SIG-01…18` from earlier candidate inventory; their GWT is proposed, but relevant Kazakhstan signature/certificate/authority/legal profiles remain pending.
- **57** contracts in total. Every contract links original canonical GWT or signature candidate, proposed persistent/Outbox/HTTP+UI oracle, BR/DEC blockers and test-class candidate. **No automated business tests claimed.**

## 2. Main test invariants

| Area | Target cases | Required proof before implementation |
|---|---|---|
| **PR-04 RFQ draft** | `TDD-SIM-42-S04-01`, `NEG-R0-011` | Assisted origin recorded without customer impersonation. Same idempotency key + different cargo payload returns CONFLICT; original cargo snapshot unchanged. No QuoteAccepted from provider-assisted record |
| **PR-05 submit/branch assignment** | `TDD-SIM-08-S07-01` | Actor permission and `expectedVersion`, branch scope, safe reassignment and no lost unassigned job. DEC-R0-03 remains pending; submit not unlocked by test fixtures |
| **PR-06 QuoteVersion** | `TDD-SIM-10-G08-01…05`, `NEG-R0-010` | QuoteVersion hash/terms/cargo/price immutable. Amendment creates a new version; wrong signature hash and stale version cannot mutate published terms; provider buy rate/margin never leaks |
| **PR-06S EDS** | `SIG-01…18` | Exact signed bytes/hash, verified signer and delegated authority, trust-chain and revocation, expiry, time policy, replay and failure of NCA/NCALayer. No click/URL or photo treated as legally binding evidence |
| **PR-07 customer accept/decline** | `TDD-SIM-13-G01-01…05`, `TDD-SIM-13-G02-01…05`, `NEG-R0-009/012` | Separate accept/decline permissions; only current ISSUED version; no replay double commitment; expiry/supersede/concurrency vs acceptance. BR-01/02/05 are PENDING |
| **PR-11 carrier offer** | `TDD-SIM-16-G09-01…05`, `TDD-SIM-15-S10-01`, `NEG-R0-013…015` | OfferSelected, CarrierCommitted, CapacityHeld and BookingConfirmed are distinct independent proofs; carrier withdrawal/stale authority invalidates binding actions; supplier cannot see other carrier's terms |
| **Cross-role** | E2E-01/02/08/10 + tenancy/finance/POD impacts | Real CustomerAccount scope, no fake signer, no Booking without capacity, no forged POD as Quote approval |

## 3. Primary risk questions requiring Test Review

1. **Approval:** who can submit RFQ, issue QuoteVersion, accept and decline? `BR-01`, `BR-02`, `BR-05`, `DEC-R0-03` not signed off. Only DENY/HOLD is safe for binding positive transitions pending review.
2. **Signature:** a real EDS verification must use exact immutable terms bytes and signer legal representation, including revocation and time validity. Test-only RSA/JWT identity is not equivalent to a signing certificate or legal authority.
3. **Price & scope:** customer-visible QuoteVersion must omit provider costs, margins, private supplier buy rates and other CustomerAccount fields; authorization must apply before pagination/cache/export.
4. **Carrier:** selected offer is not confirmed capacity and not contractual commitment. Concurrency between withdraw, hold, cancel and booking requires version-fenced transitions, replay and compensation tests.
5. **Events:** write state + Audit + Outbox atomically; no `QuoteAccepted` or `BookingConfirmed` event from failed/unauthorized command. Consumer retry must not duplicate commitment.
6. **Single canonical writer:** Account relationship depends on Commercial's proposed `CustomerAccount` ownership under `DEC-R0-02` and `BR-03` — see [51](51-s0-platform-tenancy-test-design-review.md).
7. **Cross-owner impacts:** the additional nine cross-PR cases must not be re-owned by Commercial. Existing core case IDs remain immutable, and impacted owners must review interface expectations.

## 4. Test-First preparatory targets (planned, not implemented)

Suggested S1 suites: `RfqDraftCommandContractTest`, `RfqSubmitPermissionTest`, `QuoteVersionImmutabilityTest`, `QuoteAcceptanceRaceTest`, `QuoteDeclineAuthorityTest`, `SignatureValidationContractTest`, `CarrierOfferCommitmentTest`, and `CommercialCrossRoleE2EContractTest`. Each suite needs positive, denied, replay, race, scope and crash/rollback cases with real PostgreSQL/Outbox where relevant. A failure caused solely by missing dependency/compilation is not a meaningful TDD RED.

## 5. Gate to S1

Review the 57 proposed cases against canonical GWT/BR/DEC, approve exact HTTP codes and DB/Outbox/Inbox invariants, allocate an authorized technical reviewer per module, and separate conditional signature/contract acceptance from immediately executable fail-closed negative tests. Do not auto-update readiness based on green documentation CI.

**No Payments. No AR/AP. No bank callback or settlement state.** `main` untouched.

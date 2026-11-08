# 42 — Exact-SHA PR Acceptance Manifest and Engineering Qualification

**Date:** 2026-11-08 · **Status:** 26 PR slices registered; none declared fully qualified.

Canonical machine registry: [PR Acceptance Manifest](contracts/pr-acceptance-manifest.v1.json).
Upstream source of implementation order: [TDD Roadmap v1.7](contracts/tdd-development-roadmap.v1.json).
Business truth: [Decision Evidence Ledger](contracts/r0-decision-readiness.v1.json).

## 1. Non-negotiable qualification semantics

A PR can have documented technical progress without being `QUALIFIED`.
`verification.level=DOC_CONTRACT_CHECKS_GREEN` records structural CI evidence
for PR-00, not actual stakeholder approval. `PLATFORM_PARTIAL_INTEGRATION_GREEN`
records the working PR-01 Boot 4.1.2 → Liquibase → PostgreSQL JDBC integration.
It does **not** certify FOUND-01..12 in full, authenticated HTTP-to-DB ownership,
outbox dispatch, e-signature or live carrier obligations.

`CODE_VERIFIED_DENY_ONLY` must have executable fail-closed code tests and
must not authorize the pending business transition. `QUALIFIED` requires
per-case executable evidence, reviewer authority, signed applicable decisions,
security tests, UI E2E where required and an exact-SHA CI record.
A valid JSON link is not independent proof that a real authorized signer approved.

## 2. Validation and anti-regression controls

Every one of the 26 R0 PR slices mirrors the same roadmap ID, phase, canonical
writer, parent dependencies, activation BR set, DEC due-at-PR set,
critical test IDs, activation gate mode and required UI scope. CI fails
if one item is removed, a declared dependency becomes weaker, required
negative cases are dropped, or a partial proof is promoted to qualification.

Local checks:

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/validate_tdd_roadmap.py
python3 scripts/validate_decision_readiness.py
python3 scripts/validate_pr_acceptance.py
```

The registry intentionally leaves all PRs `NOT_QUALIFIED` pending further code
and business evidence. PR-00/01 can carry prior SHA-specific green links
without claiming that they passed again on a subsequent SHA. Source approvals
remain `PENDING` and W1–W5 are not recorded as conducted.

## 3. Next implementation gates

- PR-01: finish real JWT/token authentication → verified Tenant/CustomerAccount,
  Spring Modulith module verification, runtime Outbox dispatcher with fencing,
  nonprivileged migrations and recovery tests; run full FOUND-01..12.
- PR-02: implement Tenant, LegalEntity, Membership, PartnerGrant and verified
  invitation; test denial of own-role escalation, stale grant and 2-customer
  within same provider. No implicit user membership by email/header.
- PR-06S: prototype NCALayer signing and server verification against the
  actual authorized legal representative and immutable signed document.
  Legal must approve jurisdiction-specific documents and evidence forms first.
- PR-19: only after the upstream real components are qualified, exercise the
  8/10 partial-delivery branch (cannot be marked completed or reviewed) and
  independent 10/10 branch.

The current NO PAYMENTS product boundary remains unchanged.

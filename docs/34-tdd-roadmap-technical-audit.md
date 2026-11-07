# 34 — KERUENIX TDD Roadmap v1 Technical Audit and Improvement Register

**Дата:** 2026-11-07 · **Audit version:** 1.1 · **Status:** TECHNICAL REVIEW COMPLETE / DESIGN IMPROVED / BUSINESS SIGNOFF AND DOMAIN TEST EXECUTION PENDING.

**Audited source:** [33 — TDD Development Roadmap v1.1](33-tdd-development-roadmap-v1.md), originally v1.0.0.
**Revised machine data:** [tdd-development-roadmap.v1.json](contracts/tdd-development-roadmap.v1.json), schema `1.1.0`.
**Reference contracts:** [module boundaries](contracts/module-boundaries.v1.json), [Scenario Backend](32-scenario-driven-backend-design-v1.md), [R0 84-case TDD](28-r0-tdd-acceptance-bank.md), [48 negative tests](30-negative-and-failure-scenario-bank.md), [12 BR decisions](27-r0-blocker-policy-decisions.md), [Error handling](31-unified-error-handling-standard.md), [MVP](05-mvp-qualification.md).

## 1. Audit verdict

**v1 correctly chose** a Spring Modulith modular monolith, one authoritative PostgreSQL data platform, fail-closed Tenancy/RLS, explicit source ownership, TDD with real transactions, UI+API convergence and measured R0 release qualification. These principles remain.

**v1 was not yet an executable implementation schedule:** a late Jobs stage conflicted with earlier event use, stage owners were ambiguous, RD-05 scope was too broad for one merge, legal approvals and permissions were treated as dependencies without a per-command mechanism, and the JSON roadmap had no required CI consistency check. **v1.1 improves sequencing and testability; it does not certify code readiness.**

The PR contains a minimal backend HTTP error-handler bootstrap. GitHub Actions `Backend Error Contract` had a successful run on an earlier HEAD (SHA `964eaec3...` observed before roadmap revisions), **not proof of any real PostgreSQL RLS, Spring Modulith domain modules, Fleet/Booking tests or complete release**. This review did not execute the business application.

## 2. Detailed findings, severity and disposition

| ID | Severity | Finding | Correction in v1.1 | Scope | Required evidence |
|---|---|---|---|---|---|
| `AUD-RD-01` | P0 | **Неправильный порядок Outbox/Jobs**: RD-03+ публикуют события, но RD-10 лишь позже делает jobs | Включить атомарный Outbox/Inbox и самый простой durable dispatcher в RD-01, RD-10 — только resilience hardening | RD-01, RD-10 | Flyway + Testcontainers: commit/rollback, replay, two workers |
| `AUD-RD-02` | P0 | **Слишком крупный RD-05**: Cargo, Compliance, Fleet объединены в один внедренческий этап | Отдельные PR-08 Cargo, PR-09 Compliance, PR-10 Fleet с независимыми контрактами | RD-05 | Unit/Module/PG race and compliance UNKNOWN for each PR |
| `AUD-RD-03` | P0 | **Нечёткая грань владельца модуля**: Участники этапа ошибочно воспринимаются как разрешённые прямые зависимости | Указать primaryWriteOwner, allowed integration via exported APIs/events; module-boundaries validation | RD-02..RD-10 | ApplicationModules.verify and no foreign repository/table writes |
| `AUD-RD-04` | P0 | **Подмена отсутствующей политики права на submit**: SDB RFQ submit ещё PENDING, но RD-03 обещает POST /submit | До принятия scope и права оставить действие DENY/PENDING; отдельный TDD контракт | RD-03 | 401/403/404, no RFQ transition or Outbox on forbidden write |
| `AUD-RD-05` | P0 | **Юридические и финансовые state transitions без signoff**: BR-01..12 пока неподтверждены реальными сторонами | Fail-closed; подписать применимые BR до разрешения конкретного irreversible command, а инфраструктуру можно делать параллельно | RD-04..RD-10 | Exact quote signatures, carrier terms, POD signer, verified payment evidence |
| `AUD-RD-06` | P0 | **Зависимость POD от будущего Documents**: Execution RD-07 опирается на доказательства, но документы начинаются RD-08 | В RD-07 предусмотреть evidence-ref/public contract без изменения собственника Documents; RD-08 публикует пакет | RD-07, RD-08 | Custody 8/10 and immutable evidence reference, validated document proof |
| `AUD-RD-07` | P0 | **Размытый владелец финансовых записей**: RD-09 перечисляет Booking/Documents как будто Finance может читать/писать их JPA | Finance единственный владелец Invoice/AR/AP/Allocation; чужое только через versioned API/event/snapshot | RD-09 | Modulith verify, SoD, bank allocation uniqueness, no direct foreign SQL |
| `AUD-RD-08` | P1 | **Soft Delete мешает R0**: Tracking/Documents смешаны с обсуждением delete/restore и retention | Проверять политики удаления условно; единственный возможный early draft delete по отдельному approval, документы/Booking/POD/финансы запрещены | RD-03, RD-08 | No cross-tenant delete, tombstone replay and legal-hold only when feature enabled |
| `AUD-RD-09` | P0 | **UI не равен backend**: Roadmap описывает экраны, но может допустить backend-only qualification как полноценный MVP | Развести API_QUALIFIED и USER_JOURNEY_QUALIFIED, браузерный и offline-flow E2E обязателен к R0 release | RD-02..RD-12 | Customer/prov/carrier/driver/receiver/finance UI state/error test |
| `AUD-RD-10` | P0 | **Количество test specs выдаётся за покрытие**: 132 кандидата и SDB 20 не составляют независимый исполняемый набор | Ввести per-PR applicability с accepted, failClosed, deferred, blocked; no test-count quota | RD-00, RD-11 | Manifest case/BR/source-to-owner mapping, no orphan IDs, no silent skipped |
| `AUD-RD-11` | P1 | **Неавтоматизированная проверка roadmap**: JSON может ссылаться на неизвестные BR, modules, stages и измениться незаметно | Скрипт validate_tdd_roadmap.py и отдельный CI на docs/roadmap contracts | RD-00, RD-01 | Uniqueness, DAG, 17-module catalog, valid BSC/BR/phase refs, 84+48 baseline counts |
| `AUD-RD-12` | P0 | **Переоценка статуса из старого CI**: Зелёные тесты RFC9457 не подтверждают новую RLS/Booking реализацию | Статус только при точном SHA/бизнес-согласовании/реальных DB+E2E тестах, restore и artifact digest | RD-01..RD-12 | Evidence manifest, no missing P0, signed BR, actual startup and restore |

**Disposition:** all 12 now have a **written plan correction** in [33](33-tdd-development-roadmap-v1.md). For each one, implementation, business approvals and Testcontainers evidence remain **PENDING**. This is not a claim that 12 production defects have been fixed.

## 3. Exact implementation boundary: platform reliability before first business write

Required first foundation PR `PR-01`:
1. Select compatible Java 21 / Boot / Modulith / Flyway / PostGIS / MapStruct / Testcontainers versions after a real build PoC, no invented compatibility from a dependency list.
2. Define transaction-scoped trusted Tenant / CustomerAccount context. Test that missing context denies access and pooled connections cannot leak previous Tenant.
3. In one DB transaction, write authorized aggregate state, audit record and outbox message; prove crash-before-commit leaves none and crash-after-commit leaves durable message for retry.
4. Consumer uses inbox unique identity and monotonic version; at-least-once deliveries do not create duplicate business results. No claim of exactly-once external transport.
5. A constrained job dispatcher exists before RFQ/Quote events. RD-10 later adds fencing, backpressure, DLQ/reconciliation and SaaS safe-continuity fault drills.

**Minimum gate:** CI compile + Module verification + real DB migration/RLS/outbox integration, not mock-only HTTP. No business REST endpoint is opened by merely completing this platform work.

## 4. Minimal vertical user outcomes (not module CRUD)

| Outcome | Small owner PRs | Why this order | R0 no-go |
|---|---|---|---|
| Verified CustomerAccount grant and denial | PR-02, PR-03 | Identity must exist before resource-scoped reads | Tenant-A/Customer-Y data leak |
| Customer RFQ → provider incoming/clarify | PR-04, PR-05 | First actual business write proves RLS, idempotency, pagination and Outbox | Unauthorized submit, cross-customer total |
| Signed immutable customer QuoteVersion | PR-06, PR-07 | Separate pure issue/approve from binding acceptance | Missing BR-01 proof, stale expiry acceptance |
| Cargo/Compliance/Fleet resource readiness | PR-08, PR-09, PR-10 | Separate owners, real route/weight evidence and exclusive slot | UNKNOWN=>ALLOW or double hold |
| Partner carrier or own-fleet → Booking | PR-11, PR-12 | Partner consent not identical to exclusive resource | OFFER SELECTED mistaken for CONFIRMED |
| Actual custody + partial POD | PR-13, PR-14 | Source-of-truth evidence and quantity conservation before document projection | Trip started=>pickup, 8/10=>DELIVERED |
| Timeline + verified document package | PR-15, PR-16 | Tracking is read projection, Documents retains original evidence | Exposed GPS/doc link, rewritten signed POD |
| Finance verified settlement | PR-17 | Source evidence and ledger after relevant delivery/package contracts | Approval=>PAID, duplicate callback allocation |
| Fault recovery + E2E + pilot | PR-18, PR-19, PR-20 | Real restart and actual UI + signed release evidence | Unexecuted tests or no restore drill |

**UI is a deliverable:** client and provider RFQ screens should appear with PR-04/05, not be retrofitted after entire backend. Initial frontend tech choice needs a short technical PoC; no separate complicated frontend architecture is prescribed before acceptance.

## 5. Test coverage model and TDD lifecycle

- Current documented case specifications: **60 blocker + 14 R0 safety + 10 E2E + 48 additional negative = 132**. Eight MIX test combinations are not included; SDB has 20 anchors, not necessarily new distinct test methods.
- A PR's **testApplicabilityManifest** must map test source IDs to `APPLICABLE_APPROVED`, `APPLICABLE_FAIL_CLOSED`, `BLOCKED_PENDING_BR`, `DEFERRED_R1_R2` or `NOT_APPLICABLE_WITH_REASON`. No arbitrary success percentage; no hiding a P0 skipped test.
- RED means failing test recorded for the approved contract; GREEN means an actually passing test; QUALIFIED means exact SHA CI + authorized business truth + required RLS/PG, event side effects, API and UI checks.
- A new BSC or USB is not automatically an authorization grant. Unknown permission stays DENY even if it prevents the UX from succeeding.
- Architecture contracts should validate all referenced story, BSC, BR, module, phase and test IDs. Use [roadmap validator](../scripts/validate_tdd_roadmap.py) on every docs contract change.

## 6. No-go, operational evidence and realistic planning

**Per PR:** compile, JUnit pure policy, Modulith dependency check, known SQL constraints with real PG test, tenancy negative, SQL migrations and safe exception/error codes, mandatory exact-SHA CI. Significant user journeys require UI contract/cross-role test as that slice becomes customer-visible.

**R0 release:** green approved critical tests (no unsigned legal commitments), roles and two+ tenant/customer-account isolation, supplier/capacity concurrency, signed/verified pickup/POD, finance settlement truth, user-visible status consistency, startup/config secrets, image/SBOM/secret scan, backup/restore plus rollback/forward recovery, actual business workshop and acceptance evidence.

**Scope control:** 17 business modules remain in the catalog; only a minimum subset is needed for one R0 transport. No generic BPM engine, all-module controllers, universal soft delete, permanent per-module worker/service, unsanctioned regulatory automation or blanket Kubernetes requirement.

**Planning:** Phase IDs `RD-00..RD-12` and PR IDs `PR-00..PR-20` are logical ordering/gates, **not days or weeks**. Estimate effort from the first 2–3 fully qualified vertical PRs and actual stakeholder availability. Distinguish *work that can start now* (docs validator, platform compatibility, fail-closed auth foundation) from *irreversible business commands blocked pending signoff*.

## 7. Reviewer conclusion

**Decision: APPROVE v1.1 AS A BETTER PROPOSED DEVELOPMENT PLAN, NOT AS BUSINESS-APPROVED IMPLEMENTATION.**

The immediate technical next step is `PR-00 + PR-01`, alongside real stakeholder decisions via [29 — Workshop Kit](29-r0-business-acceptance-workshop-kit.md). Do not start generic 17-module CRUD generation. First proof of real value is one correctly authorized `CustomerAccount → RFQ → Provider Inbox` flow with verified PostgreSQL RLS and negative tests, followed by actual `Quote → Capacity → Booking`.

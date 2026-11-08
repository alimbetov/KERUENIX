# 40 — KERUENIX ТЗ v1.7: Contract Consistency & Business Readiness

**Дата:** 2026-11-08 · **Версия:** 1.7.0 · **Статус:** `DESIGN_CONSISTENCY_UPDATED / BUSINESS_AND_LEGAL_APPROVAL_PENDING / JAVA_BUSINESS_NOT_IMPLEMENTED`.

## 1. Нормативная сфера продукта

KERUENIX управляет RFQ, версиями Quote, обязательствами перевозчика, Booking, Execution/Custody, документами/POD/Tracking и коммерческой стоимостью (sell/buy/cost/margin). Платёжные шлюзы, банковские операции, AR/AP, `InvoiceIssued`, `PaymentAllocation`, `PAID/SETTLED/REFUNDED`, возвраты и выпуск официальной ЭСФ **исключены из продукта**, а не просто перенесены за пределы R0. Возврат этих функций требует отдельного продуктового change request.

Модуль `finance` остаётся в каталоге 17 модулей исключительно ради commercial costing и необязательной opaque-ссылки `ExternalAccountingDocRef`. Внешняя бухгалтерия — источник истины об официальных документах, расчётах и оплате. Подписанный документ не означает оплату.

**Precedence:** продуктовая граница NO PAYMENTS и [scope contract](contracts/r0-scope-eds-signing.v1.json) → доказательно утверждённые BR/Legal/ADR → [machine module boundaries](contracts/module-boundaries.v1.json) и [Roadmap](contracts/tdd-development-roadmap.v1.json) → [Developer Handbook](35-r0-developer-handbook.md) → исторические нарративы. Ни один старый финансовый пример из v1.0–1.6 не может генерировать новые API, миграции, роли или позитивные payment release gates.

## 2. Закрытие P0/P1 документации

| ID | Severity | Contract correction | Test/gate |
|---|---|---|---|
| REV2-01 | P0 | `finance.owns` = CostEstimate, CommercialCostReport, MarginReadModel, ExternalAccountingDocRef; API только cost/report/ref | No invoice, payment, receivable, payable in any `owns/publicContracts` |
| REV2-02 | P0 | Invoice ownership is `EXTERNAL_ACCOUNTING_ONLY`; cancellation is contractual commercial change, not refund ledger | Validator and mutation test |
| REV2-03 | P1 | `RD-09` Markdown and machine dependency only `RD-04` | Phase table parity mutation test |
| REV2-04 | P1 | Product Charter, Architecture, Lifecycle, Blueprint, GIS and traceability aligned with NO PAYMENTS | Document review |
| REV2-05 | P1 | Eleven retired payment test IDs synchronized in signed scope, roadmap and test banks | Exact retired-set parity, separate six PAY-ABS negative cases |
| REV2-06 | P0 | Machine module ownership/public events are checked for forbidden payment entities | Mutation test for PaymentAllocation and InvoiceIssued |
| REV2-07 | P1 | Commercial CustomerAccount/ServiceReview are `proposedOwnershipPendingADR`, not approved automatically | Owner ADR remains pending |
| REV2-09 | P0 | Archived INVOICE/RECEIVABLE/PAYABLE lifecycle machines are non-executable; GIS finance owns no ledger | Validator rejects reactivated state machines and write-model payment records |
| REV2-08 | P0 | `DEC-R0-07` business-scope acknowledgement is a valid PENDING state, not an approval | Approval evidence/authority/version/date required |

The active lifecycle machine contract now contains nine transport/document machines; the three old finance machines are retained solely as historical records with `doNotImplement=true`.

## 3. Business readiness — truthful decision ledger

**BR-01…BR-12:** `PENDING_REAL_STAKEHOLDER`. **DEC-R0-01…08:** statuses as recorded in [delivery contract](contracts/r0-delivery-contract.v1.json); no automatic promotion to APPROVED. Technical design and product NO PAYMENTS decision do not replace legal/business validation.

| Workshop | Participants | Decisions to approve | Fail-safe until approval |
|---|---|---|---|
| W1 | Customer/forwarder/legal | ContractParty and agency capacity, RFQ submit, Quote accept/decline, amendments — BR-01/02/03/05 | No binding Quote ACCEPTED |
| W2 | Carrier/fleet/compliance/legal | Carrier authority, capacity exclusivity, route legality — BR-06/07/08 | No false CarrierCommitment/Booking.CONFIRMED |
| W3 | Driver/consignee/operations/legal | Offline custody, TTN/POD legal form, partial 8/10 — BR-09/10 | HOLD unresolved evidence; no full DELIVERED |
| W4 | Product/accounting/commercial/legal | Cancellation liabilities, external accounting boundary — BR-11/12 | No financial postings or automatic termination |
| W5 | Tenant owner/security/SaaS/legal | Safe-continuity while subscription suspended — BR-04 | No silent cargo abandonment |

For an actual `APPROVED` decision require immutable `approvalEvidenceRef`, `approverAuthorityRef`, `approvedVersion`, `approvedAtUtc`, applicable legal profile and documented subject scope. Missing verification means PENDING/HOLD, never fabricated agreement.

## 4. ЭЦП и юридическое согласование

`platform.signing` — технический сервис. Browser NCALayer/NCA signing, immutable original/hash, verified certificate chain/revocation/time, legal-entity signatory authority, signer exact-document preview and consent, portable original and domain CAS are **design requirements**, not delivered capabilities. `SIG-01..18` remain planned test specifications. For each Quote, CarrierCommitment, TTN, POD or amendment, Legal must approve whether ЭЦП is mandatory, which parties sign, what document format is required, and the permitted fallback. eGov QR cannot be enabled without verified integration access and contract.

## 5. Definition of Ready and no-go

**Documentation READY:** Python validator unit and mutation suite passes; Markdown/JSON dependencies align; exact SHA `TDD Roadmap Contract` in GitHub Actions passes. **Business READY:** applicable BR/DEC approved by real stakeholders with full evidence. **Implementation READY:** PR-00/01 implements real Java/PG/PostGIS/RLS, Outbox/Inbox, transaction/replay and Testcontainers acceptance; CI docs alone is not application qualification.

**No-go:** signed Quote/Carrier/POD activation, full delivery for 8/10 units, accepting payment statuses or a production/pilot R0 release on documentation test results.

[Prior review 39](39-r0-technical-business-review.md) · [Scope & ЭЦП 38](38-r0-eds-signing-no-payments.md) · [Workshops 29](29-r0-business-acceptance-workshop-kit.md) · [Roadmap 33](33-tdd-development-roadmap-v1.md).

# 33 — KERUENIX TDD Development Roadmap v1.6

**Дата:** 2026-11-07 · **Версия:** 1.6.0 · **Статус:** PROPOSED DELIVERY ROADMAP / BUSINESS SIGNOFF PENDING / ROADMAP NOT EXECUTED.

**Цель:** поэтапно реализовать KERUENIX как один надёжный Spring Modulith modular monolith в Java 21, от имеющегося error bootstrap до полной, безопасной и воспроизводимой автомобильной перевозки между независимыми компаниями. Технические решения и бизнес-требования должны квалифицироваться через TDD, реальные PostgreSQL/PostGIS транзакции, RLS, API и cross-role E2E. Не заявлять готовность по наличию документации, mock-тестов или единичного happy path.

**Current product boundary:** [38 — NCA EDS signing without payment functions](38-r0-eds-signing-no-payments.md) / [machine contract](contracts/r0-scope-eds-signing.v1.json). **Implementation handbook:** [35 — R0 Developer Handbook](35-r0-developer-handbook.md) and [R0 Delivery Contract](contracts/r0-delivery-contract.v1.json). **Audit:** [34 — TDD Roadmap Technical Audit](34-tdd-roadmap-technical-audit.md) — 27 design audit findings documented (implementation pending), not business signoff. **Machine roadmap:** [tdd-development-roadmap.v1.json](contracts/tdd-development-roadmap.v1.json). Эта JSON-модель содержит единые ID этапов, связи, owners, scope, связанные BSC/BR и gates. Это план, не GitHub Actions/issue tracker и не CI evidence.

**Опорные спецификации:**
- [32 — Scenario-Driven Backend Design](32-scenario-driven-backend-design-v1.md) + [query/soft delete contract](contracts/backend-query-soft-delete.v1.json): DDD, command/query repositories, DTO/MapStruct, controllers, pagination, filters, Soft Delete.
- [14 — Modular Delivery Blueprint](14-modular-delivery-blueprint.md), [13 — Architecture](13-modular-architecture-options-v1.md), [module boundaries](contracts/module-boundaries.v1.json).
- [20 — MapStruct/TDD](20-mapstruct-tdd-engineering-standard.md), [28 — 84 proposed TDD](28-r0-tdd-acceptance-bank.md), [30 — 48 negative cases](30-negative-and-failure-scenario-bank.md).
- [21 — 80 User Stories](21-user-story-book.md), [25 — BSC-001..011](25-business-scenario-book.md), [26 — Role Simulations](26-role-process-simulation-and-gap-audit.md), [27 — BR-01..12](27-r0-blocker-policy-decisions.md), [29 — Signoff Workshop](29-r0-business-acceptance-workshop-kit.md).
- [24 — Authorization](24-access-control-tdd-matrix-v2.md), [31 — RFC 9457 errors](31-unified-error-handling-standard.md), [15 — PostGIS/Partitioning](15-data-platform-partitioning-postgis.md), [18 — Jobs/State Machines](18-platform-jobs-state-machines-workflows.md), [19 — Reliability](19-architecture-hardening-priorities.md), [05 — MVP Gates](05-mvp-qualification.md).

## Current approved product direction — normative precedence

As of 2026-11-08, **no payment mechanisms are in the KERUENIX product**. Current R0 scope: verified transport, NCA EDS where legal profile requires, commercial price/cost/margin and optional *external-accounting document reference*. [38](38-r0-eds-signing-no-payments.md), [machine scope](contracts/r0-scope-eds-signing.v1.json) and [39 — R0 Technical/Business Re-review](39-r0-technical-business-review.md) supersede any historical `PR-17S`, `PaymentAllocation`, `PAID`, AR/AP or bank-callback requirement elsewhere in this long-running design record. Those historical text passages are preserved for audit traceability and **MUST NOT** generate code, API, privileges, database migrations or release gates. `PR-11` binding carrier contract requires qualified PR-06S signature verification where the agreed legal profile requires EDS. Customer Quote/POD signer rights must be verified server-side; web signing does not authorize the domain state transition by itself.

## 1. Baseline: what is real today

| Component | Checked state | Must not be claimed |
|---|---|---|
| Backend | Java 21 / Spring Boot 4.1.2 minimal error/bootstrap under backend/ | Not a complete logistics backend, JWT/tenancy/SQL not implemented |
| RFC 9457 | 15 error contract tests previously green at commit `ac459923` per backend README | Not proof the **current** HEAD or end-to-end service is qualified |
| Business modules | 17 planned logical modules, structural/architecture contracts | No implemented DDD aggregate/API/migration or accepted business correctness |
| User stories | 80 candidates + BSC-001..011 | Real customer/forwarder/carrier/legal review not completed |
| TDD banks | 84 R0 candidates + 48 negative/failure candidates = 132 existing planned tests | Not 132 executed tests, no fixed 132-test release quota |
| Scenario backend | docs/32 plus 20 SDB trace/testing anchors | SDB are not automatically 20 disjoint new tests; overlap with AUTH/NEG/TDD-SIM |
| BR-01..12 | Fail-closed technical proposals | No real stakeholder signature; cannot turn proposals into unconditional production permission |
| Soft Delete | Opt-in design only | No generic soft-delete for Booking, POD, payments, custody, documents |

**No business module is implemented or qualified at the current design baseline; this plan does not change that status.**

**Status methodology:** DESIGN/PLANNED, RED, GREEN, IMPLEMENTED and QUALIFIED mean different things. The phase tables below use PLANNED until exact-SHA evidence exists; future tracking updates must cite actual CI logs, business approvals and migration version, not memory or estimated completion.

## 2. Delivery strategy and dependency map

**Architecture:** single modular business runtime; Spring MVC with JDBC/typed SQL baseline for R0 pending dependency PoC; PostgreSQL + PostGIS, Flyway, Spring Security, explicit transaction-scoped RLS, bounded jobs, MapStruct only at mapping boundaries. SQL names and business flags must be authorized on the server; all write models have exactly one owner. CQRS-light separates query and command handlers, not databases.

**Execution logic (dependencies, not calendar duration):**

~~~text
RD-00 Business decisions & traceability ─────────────┐
RD-01 Build/CI/PG/PostGIS + durable Outbox/Inbox foundation ────────────────┼─→ RD-02 Tenancy / auth
                                                    │       ├→ RD-03 RFQ / Inbox → RD-04 Quote
                                                    │       └→ RD-05 Fleet / Cargo / Compliance
                                                    │                         └─────────┬──────┘
                                                    │                                   ↓
                                                    │                             RD-06 Booking
                                                    │                                   ↓
                                                    │                             RD-07 Execution
                                                    │                                   ↓
                                                    │                       RD-08 Tracking/Documents
                                                    │                                   ↓
                                                    │                            RD-09 Finance-lite
                                                    └────────→ RD-10 Jobs hardening / safety
                                                                 ↓
                                                        RD-11 Full E2E / restore
                                                                 ↓
                                                        RD-12 Pilot / R0 release
                                                                 ↓
                                                    RX-01/02/03 targeted expansion
~~~

**Dependency note:** RD-01 can proceed while business workshops prepare BR signoffs; **transactional Outbox/Inbox, idempotency and scoped service delivery belong in RD-01**, because RD-03+ already emit business events. RD-10 audits restart/fencing/backpressure and SaaS continuity, it does not introduce first Outbox. The `modules` array is **participant inventory**, not permission to import foreign repositories; use only dependencies permitted in [module-boundaries.v1.json](contracts/module-boundaries.v1.json).

**Dependency note:** RD-01 can proceed while business workshops prepare BR signoffs; RD-04/06/07/09 require signoff of the **specific** affected legal/payment/custody rule before turning a transition into a production-accepted action. A module may deliver safe read-only, mock fixture, or DENY/NEEDS_REVIEW placeholders while unaccepted policy remains blocked. No fake approvals.

**R0 phase plan (13 gates):**

| ID | Vertical slice | Depends on | Domain focus |
|---|---|---|---|
| `RD-00` | Discovery → Testable Contracts | Параллельный старт | tenancy, commercial, fleet, booking, execution, documents, finance |
| `RD-01` | Build + Platform Foundation (Outbox/Inbox baseline) | Параллельный старт | platform infrastructure (not business tenancy) |
| `RD-02` | Tenancy + Identity + Customer Scope | `RD-01` | tenancy grants + commercial CustomerAccount (separate writers) |
| `RD-03` | Commercial RFQ + Customer Inbox | `RD-02` | commercial, tenancy |
| `RD-04` | Commercial Quote + Approvals | `RD-03` | commercial, tenancy |
| `RD-05` | Fleet + Cargo + Compliance + PostGIS (**3 owner PRs**) | `RD-02` | cargo, compliance, fleet (independent owners) |
| `RD-06` | Booking Process + External Carrier | `RD-04`, `RD-05` | booking, fleet, commercial |
| `RD-07` | Execution + Custody + Partial POD | `RD-06` | execution, cargo, compliance |
| `RD-08` | Tracking + Documents + Query/Soft Delete Qualification | `RD-07` | tracking, documents, fleet, execution |
| `RD-09` | Commercial Cost & External Accounting Handoff (**1 PR, NO PAYMENTS**) | `RD-06`, `RD-07`, `RD-08` | finance only writes ledger; other modules via exported facts |
| `RD-10` | **Jobs Resilience Hardening** + Subscription Safety | `RD-02`, `RD-06`, `RD-07`, `RD-09` | platform jobs + scoped tenancy/execution/finance; not first Outbox deployment |
| `RD-11` | R0 Full E2E + Recovery + Performance | `RD-03`, `RD-04`, `RD-05`, `RD-06`, `RD-07`, `RD-08`, `RD-09`, `RD-10` | tenancy, commercial, fleet, cargo, compliance, booking, execution, tracking, documents, finance |
| `RD-12` | Pilot Acceptance + Release Qualification | `RD-11`, `RD-00` | tenancy, commercial, fleet, booking, execution, tracking, documents, finance |

**Release after R0:** `RX-01` Recovery/Warehouse/SaaS Control; `RX-02` Optimization/Intelligence; `RX-03` Marketplace/Regulatory. These are future bounded modules, **not** prerequisites for the first full freight journey. RD-10 covers only the minimum fail-safe subscription continuity contract if BR-04 approves it, not full SaaS Control billing.

## 3. Universal TDD implementation protocol

**One vertical slice = one delivered business outcome, not a batch of entities:**

1. Select stable story `USB-*` / `BSC-*`, requirement ID and related `BR-*`; check actual status of real approval.
2. Write structured Given / When / Then for happy path, forbidden operation, stale version, replay/idempotency, concurrency, tenant boundary, external outage and recovery. Record expected **DB state, outbox, customer/provider UI projection, sanitized API error**.
3. Define aggregate owner, state machine guard, role/scope/SoD, transaction boundary, domain event, failure and compensating action. No implicit generic role permissions.
4. **RED:** committed failing unit tests before business code; when SQL constraints/RLS are material, real PostgreSQL Testcontainers tests also start failing against missing capability. An unapproved BR may get a fail-closed test now, never a pretend positive legal test.
5. **GREEN:** minimum code to satisfy **accepted** AC — aggregate/value objects, domain policy, owner repositories, SQL/Flyway/RLS, application command or query handler, explicit DTO/MapStruct, controller and event/outbox. Business policy never lives only in controller annotation or mapper.
6. **REFACTOR:** remove duplication, keep published contracts stable, check indexes and resource bounds; run regression, security and failure tests again.
7. **QUALIFY:** exact SHA CI, contract and architecture verification, reproducible database fixture, negative tests, cross-role demo and business signoff where applicable.

**Test levels:**

| Level | Test goal | Tool/evidence |
|---|---|---|
| L1 Domain Unit | transition, Value Objects, money/cargo invariants, policy pure functions | JUnit 5, optional property tests |
| L2 Modulith/Mapper | dependency direction, no internal imports, DTO allowlist/MapStruct | `ApplicationModules.verify()`, module tests, strict compiler |
| L3 HTTP/Security | JWT, permission, customer/proxy, RFC 9457, DTO field leaks | Spring MVC/Security tests |
| L4 PostgreSQL/PostGIS | RLS, partial/unique/exclusion constraints, Flyway, pool A→B | Testcontainers real PostgreSQL+PostGIS |
| L5 Concurrency/Replay | two transactions, expiration races, duplicate webhook, expectedVersion, outbox | concurrent real SQL + forced restart |
| L6 Contract/Events | OpenAPI/event version + backward compatibility | schema tests, type snapshots |
| L7 Multi-role E2E | entire journey across tenant/customer/provider/carrier/driver/receiver | HTTP + DB + document storage adapter |
| L8 Reliability & Query | backup/restore, partition/retention, SQL EXPLAIN, p95/p99 measured, fault injection | controlled environment/artifacts |

**Risk-based acceptance:** 100% line coverage is not the gate. A missing critical negative test for payment, RLS, Booking, POD or custody is **blocking**, even if JaCoCo looks green. An accepted P0 test that fails blocks merge; non-applicable tests require explicit owner-approved rationale and evidence.

## 4. Execution passports: R0 stages

### RD-00 — Discovery → Testable Contracts

**Зависимости:** нет; разрешено начать сейчас. **Ответственные модули:** `tenancy`, `commercial`, `fleet`, `booking`, `execution`, `documents`, `finance`. **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** Актуализировать traceability, ownership Order/CustomerAccount/Invoice; разграничить signed и proposed BR; согласовать с реальными ролями W1..W5. Описать Gherkin Given/When/Then для приоритетных сценариев, включая негативные, конкуренцию и отключение внешних интеграций.

**Изменения в коде/артефактах:**
- docs/contracts/ ownership registry (proposed)
- ADR для агрегатов и transactional boundaries
- AC cards/BR signoff ledger with reviewer + date + evidence

**Обязательная TDD-проверка:**
- documentation JSON validation, uniqueness and cross-reference
- negative-case coverage mapping (not executable business acceptance)

**Gate выхода:** Для каждого функционального среза — подтверждённые actor/resource scope, бизнес-владелец, AC, отказ и legal/finance signoff, где необходим; не подписанный BR не превращается в продуктовый allow.

**Затем:** RD-01 возможен параллельно; бизнес-срезы используют только подписанные правила.

### RD-01 — Build + Platform Foundation

**Зависимости:** нет; разрешено начать сейчас. **Технический владелец:** `platform` (не бизнес-модуль). **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** Проверить существующий Spring Boot 4.1.2/Java 21 error bootstrap. PoC совместимости Spring Modulith/MapStruct/Flyway/Testcontainers; добавить PostgreSQL/PostGIS test infra, Testcontainers, profiles, Secret/Connection/Application config, миграции, fail-closed security. **RD-01 сразу реализует минимальный транзакционный Outbox + Inbox dedup + durable dispatcher, а не только интерфейсы: иначе RD-03/04 не смогут гарантировать события и повторы.** Docker Compose/local smoke.

**Изменения в коде/артефактах:**
- backend Maven BOM lock and reproducible build
- Modulith verify() and @ApplicationModuleTest harness
- Flyway + real PG/PostGIS + RLS template
- atomic aggregate + audit + Outbox / Inbox replay, durable dispatch (минимально, без универсального workflow engine)
- CI exact SHA; issue/artifact refs; readme

**Обязательная TDD-проверка:**
- ERR-* existing contract regression on current SHA
- ApplicationModules.verify no cycles/internal imports
- DB migration, startup and rollback/no phantom outbox
- RLS fail-closed + two tenant pool reuse
- invalid JWT/401/403 shared ProblemDetail

**Gate выхода:** mvn verify и startup на конкретном SHA; реальные PG/PostGIS+RLS интеграции, не H2 вместо PG; транзакционная атомарность audit/Outbox, повторное событие не даёт второй бизнес-эффект; не открывать бизнес API без auth.

**Затем:** RD-02.

### RD-02 — Tenancy + Identity + Customer Scope

**Зависимости:** `RD-01`. **Ответственные модули:** `tenancy`, `commercial`. **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** Tenant/LegalEntity, Member/RoleAssignment, PartnerGrant, invitation, verified identity, customer vs tenant employee, revoke/suspension, SoD. **Commercial PR-03C** owns canonical CustomerAccount business relationship and emits a neutral versioned account event; **Tenancy PR-03** owns only grants/membership/revocation referencing that account ID. Tenancy cannot import Commercial internals or query Commercial tables; prerequisite ADR owner signoff remains required. Разделить identity/authorization grant (Tenancy) и commercial relationship facts (Commercial).

**Изменения в коде/артефактах:**
- domain aggregates and repository ports
- verified principal context + transaction-scoped RLS
- JWT/OIDC adapter + scoped application commands
- customer-safe API DTO + MapStruct + migrations

**Обязательная TDD-проверка:**
- AUTH-X-* cross tenant, customer-org, delegated role escalation
- deny foreign entity counts and UUID enumeration
- revoke while cache warm; worker privilege revalidation
- two JDBC connections and pooled tenant switch
- same person with multiple roles, no self-approval

**Gate выхода:** Два Tenant + минимум два CustomerOrg в одном provider не видят чужих записей; сквозной authorization HTTP→DB подтверждён.

**Затем:** RD-03, RD-05.

### RD-03 — Commercial RFQ + Customer Inbox

**Зависимости:** `RD-02`. **Ответственные модули:** `commercial`, `tenancy`. **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** Создать Draft RFQ, submit/clarification/qualification **только после явного утверждения прав customer:rfq:submit (сейчас PENDING в SDB) и соответствующих guards**; Customer My Requests и Provider Incoming RFQs. CQRS-light query ports, URL/API contracts, typed filter/sort allowlists, offset pagination, SQL indexes, tenant/customer scoping. Opt-in draft soft delete только при отдельной принятой политике; иначе скрыть недоступное действие.

**Изменения в коде/артефактах:**
- RFQ aggregate and transitions
- command + query repositories, Flyway and RLS
- Create/Submit/List/Detail DTO and MapStruct
- safe SQL indexed searches + page metadata
- audit/outbox and idempotency

**Обязательная TDD-проверка:**
- BSC-002, AUTH-EXT-*/AUTH-COM-* applicable
- SDB-001..005, SDB-007..009, SDB-013..015, SDB-017
- same-createdAt deterministic ordering, size cap, invalid sort
- cross-account filtering before COUNT/OFFSET; SQL EXPLAIN
- double submit changed payload conflict; draft deletion/quote issuance race if enabled

**Gate выхода:** External customer sees only own RFQs; provider only allowed Inbox; pagination/count and DTO no leak; one logical create/submit effect.

**Затем:** RD-04.

### RD-04 — Commercial Quote + Approvals

**Зависимости:** `RD-03`. **Ответственные модули:** `commercial`, `tenancy`. **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** Immutable QuoteVersion/terms hash, issue/expire/supersede, price approval and SoD; **PR-06S** platform-level NCA EDS signing verification (NCALayer user-side first, eGov QR only after provider qualification) is prerequisite for legally binding Quote.Accepted and source-specific signed document/POD. Never treat an unsigned or merely browser-validated document as legally signed; never treat acceptance as confirmed Booking.

**Изменения в коде/артефактах:**
- QuoteVersion aggregate and guarded state machine
- CommercialApi customer/procurement snapshots
- approval proof/evidence and typed domain events
- outbox consumer/notification jobs; audit

**Обязательная TDD-проверка:**
- BR-01/02/05 TDD-SIM variants after signoff
- AUTH-EXT-006, AUTH-X-005/006 as applicable
- race accept/expiry/supersede, stale expectedVersion
- approve own exception denied; no hidden buy rate in response

**Gate выхода:** Only a server-verified NCA EDS evidence+legal-entity authorization for exact immutable QuoteVersion can permit binding acceptance under approved legal profile. Expired certificate, wrong signer/term hash, revoked authority and duplicate signing fail closed; never mutate issued terms or imply Booking.CONFIRMED.

**Затем:** RD-06 (with RD-05).

### RD-05 — Fleet + Cargo + Compliance + PostGIS

**Зависимости:** `RD-02`. **Ответственные модули:** `fleet`, `cargo`, `compliance`. **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** Четыре проверяемых owner-среза: PR-08 CargoProfile, PR-09 ComplianceAssessment, **PR-10V Fleet Registry**, PR-10 Fleet Capacity Hold/Confirm. PR-10V может выполняться параллельно Cargo/Compliance, но не подтверждает доступный Capacity. VehicleCombination/driver/capacity windows; CargoProfile weights, volume, dimensions and controlled eligibility; ComplianceAssessment with UNKNOWN fail-closed. PostGIS verified coordinates and proximity search; Fleet owns transactional CapacityHold, no read-model guard.

**Изменения в коде/артефактах:**
- FleetCapacityApi hold/confirm/release
- vehicle/cargo master repositories + geo query port
- PostgreSQL exclusive booking interval guard/constraint
- Compliance module decision snapshots + provenance
- GIS migrations/indexes, geospatial smoke

**Обязательная TDD-проверка:**
- BR-07, BR-08; DATA-*, GEO-* applicable
- two competing reservations on separate transactions
- expiry vs confirmation race; old GPS cannot authoritatively reserve
- missing safety rule returns hold/needs review; no automatic allow
- postgis ST_DWithin meters + cross-tenant nearest exclusion

**Gate выхода:** No double hold in DB, no unsafe UNKNOWN release, correct coordinate/units and geo tenant isolation; real concurrency test green.

**Затем:** RD-06.

### RD-06 — Booking Process + External Carrier

**Зависимости:** `RD-04`, `RD-05`. **Ответственные модули:** `booking`, `fleet`, `commercial`. **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** Booking.ResourcePending→Confirmed only after quote and confirmed capacity; **PR-12C отдельно обрабатывает запросы отмены и гонку с Trip.STARTED по BR-11; никакие штрафы или освобождение груза не выводятся из кнопки клиента.** CarrierOffer selected is not exclusive reserve. Own-fleet vs partner carrier, hold TTL, durable orchestration/recovery and cancellation before/after start with compensation.

**Изменения в коде/артефактах:**
- Booking aggregate, BookingProcessManager persisted steps
- Fleet API integration; typed events/outbox/inbox
- carrier adapter mock with status reconciliation
- booking read model and scoped endpoint

**Обязательная TDD-проверка:**
- TDD-R0-E2E-02/03/10 candidates
- WF-001/002, SM-001..005, JOB-001..005 as applicable
- crash after Fleet hold before Booking commit
- carrier withdraw while confirmation races, lease fencing
- retry duplicate command and process restart no double booking

**Gate выхода:** Confirmed Booking always has valid evidence of Quote + exclusive CapacityReservation + compliance; crash/retry converges and cleans hold.

**Затем:** RD-07.

### RD-07 — Execution + Custody + Partial POD

**Зависимости:** `RD-06`. **Ответственные модули:** `execution`, `cargo`, `compliance`. **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** Shipment/Trip/TransportLeg/CargoUnit, pickup/custody handover evidence, offline driver replay after revoke/reassignment, partial delivery/rejection/return with conservation; customer claims as safe exception stub without false Delivered. **Для подписанного POD в этом срезе нужен публичный контракт доказательства с Documents; хранение/публикация полноценного DocumentPackage — отдельный RD-08, оригинал POD не переписывается.**

**Изменения в коде/артефактах:**
- Execution state machines and custody ledger
- offline command intake with verifier and quarantine
- per-unit DeliveryAttempt/POD receipt
- append-only evidence/audit/Outbox

**Обязательная TDD-проверка:**
- TDD-R0-E2E-04, BR-09/10 variants
- online/offline pickup duplicate/out-of-order
- custody conservation 8/10; cannot close 10/10
- driver reassignment/revoke before offline replay, evidence quarantine
- GPS and Trip.STARTED never become pickup/POD evidence

**Gate выхода:** No custody loss or forged POD; verified cargo-unit reconciliation and negative/replay invariants pass.

**Затем:** RD-08.

### RD-08 — Tracking + Documents + Query/Soft Delete Qualification

**Зависимости:** `RD-07`. **Ответственные модули:** `tracking`, `documents`, `fleet`, `execution`. **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** Три независимых owner-среза PR-15 Tracking, PR-16 Documents и **PR-16R Commercial private feedback только после проверенной завершённой услуги (отдельный fulfilled-service тест; 8/10 частичный POD не соответствует eligibility)**: Event-derived customer timeline, permission-filtered milestone, ETA freshness/watermarks; verified document packages and downloads; cursor/keyset for immutable chronological streams. **Soft Delete не является автоматически активируемой функцией:** только явно разрешённые draft-объекты и отдельный бизнес/retention gate; Bookings, POD, finance и custody не удаляются.

**Изменения в коде/артефактах:**
- TrackingQueryApi filtered projection and rebuild
- DocumentPackageVersion and proof access adapter
- cursor signer/validator keyed to scope revision + filter
- retention/tombstone propagation + audit

**Обязательная TDD-проверка:**
- SDB-006, 009..016, 018..019 as applicable
- DATA-08..10, GEO-05..08 conditional GPS slice
- foreign tracking/cursor, stale signed URL after revoke
- read model lag, backfill, out-of-order, delete tombstone replay
- verified document access, legal hold blocks purge

**Gate выхода:** No raw GPS/foreign documents, truthful freshness, no erased legal evidence, cursor cannot cross authorizations.

**Затем:** RD-09.

### RD-09 — Commercial Cost & External Accounting Handoff (No Payments)

**Зависимости:** `RD-04` (договорная стоимость), другие данные о перевозке — по versioned exported facts. **Владелец записи:** `finance` только как bounded-context расчётов коммерческой стоимости; `commercial` публикует утверждённый Quote. **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** `PR-17` считает закупочную/продажную цену, согласованные затраты, валюту и маржу, показывает данные только уполномоченным сотрудникам. Возможна **необязательная ссылка на документ, оформленный во внешней бухгалтерии**. KERUENIX **НЕ** выставляет официальную ЭСФ, не осуществляет платёж, не импортирует банковские операции, не хранит PaymentAllocation/AR/AP ledger, не присваивает PAID/SETTLED/REFUNDED.

**Изменения в коде/артефактах:**
- Версионированная коммерческая цена/контрактный snapshot, Money+Currency/value rounding.
- Account/Tenant-scoped расчёт затрат и маржинальности с разграничением видимости закупочной цены.
- Только метаданные/ссылка на внешний бухгалтерский документ; не источник налоговой/банковской истины.
- Отсутствуют payment gateway, bank/ERP callback, payout, refund и внутренний ledger.

**Обязательные TDD:**
- Цена/валюта/маржа согласуются с immutable Quote и правами стороны; перевозчик не видит margin экспедитора.
- Cross-Tenant/CustomerAccount list/count/export не раскрывают документы и цены других сторон.
- Попытка `/payments`, `/refunds`, `/reconcile`, `markPaid` fail-closed: нет endpoint, таблицы, Outbox PaymentSettled и статуса PAID.
- `TDD-R0-E2E-06`, `TDD-SIM-32-G22-01/03/04/05`, `NEG-R0-033..036` остаются в историческом банке, но **OUT_OF_SCOPE_R0**, не являются обязательными положительными банковскими тестами пилота.

**Gate выхода:** корректные коммерческие суммы и доступ, внешний бухгалтерский документ не притворяется оплатой; платёжных операций нет. **Подписание ЭЦП договора не создаёт статус платежа.**

**Затем:** RD-11; RD-10 не зависит от платежей.

### RD-10 — Jobs + Resilience + Subscription Safety

**Зависимости:** `RD-02`, `RD-06`, `RD-07`. **Ответственные модули:** `tenancy`, `booking`, `execution`. **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** **Операционное усиление уже существующих RD-01 Outbox/Inbox/durable dispatcher:** retry classification/dead letter, fencing, observability, error catalog consistency. Бизнес-срезы не ждут RD-10 для первого надёжного event consumer. Subscription suspension during live cargo follows BR-04 with explicit safety continuity; do not build full SaaS Control billing in R0.

**Изменения в коде/артефактах:**
- PostgreSQL-backed durable jobs and reclaim supervisor
- policy-scoped service principals, retry/replay approvals
- health metrics, structured logs/correlation
- outage modes and safety continuity adapter

**Обязательная TDD-проверка:**
- JOB-001..008 / WF-* and NEG-R0-ASYN* applicable
- worker dies after effect before ack; duplicate callback
- expired lease stale attempt cannot commit
- revocation, fallback, cache/Redis outage fail safe
- R0-E2E-07 subscription suspended but POD/custody guarded

**Gate выхода:** No lost committed event or job, no duplicate logical effect, no cross-tenant worker privilege, operable degraded state.

**Затем:** RD-11.

### RD-11 — R0 Full E2E + Recovery + Performance

**Зависимости:** `RD-03`, `RD-04`, `RD-05`, `RD-06`, `RD-07`, `RD-08`, `RD-09`, `RD-10`. **Ответственные модули:** `tenancy`, `commercial`, `fleet`, `cargo`, `compliance`, `booking`, `execution`, `tracking`, `documents`, `finance`. **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** Reproduce full route two tenants + two customer accounts + external carrier + driver + receiver with NCA EDS-signed binding documents where legally required. **No payment or banking subsystem and no internal PAID/SETTLED state.** Include all accepted applicable 84 TDD and 48 negative scenarios by traceability, not merely test count. Fault injection, CI exact SHA, migrations, backup/restore, partition test conditional GPS and load benchmark.

**Изменения в коде/артефактах:**
- single documented R0 E2E fixture
- smoke runner and CI jobs with reports
- load/perf script with p95/p99 and EXPLAIN
- backup/restore and data integrity/tenant isolation checklist

**Обязательная TDD-проверка:**
- TDD-R0-E2E-01..05 and 07..10 when accepted; former E2E-06 payment case OUT_OF_SCOPE_R0
- SDB-001..020 applicability and exclusions recorded
- AUTH/NEG-R0*/JOB/SM/WF, DB and Outbox assertions
- two independent DB sessions plus network failure matrix
- restore persisted facts and document checksums

**Gate выхода:** Every accepted P0 applicable contract green on exact SHA, zero known P0 leak/dup booking/custody/finance bug, documented SLO from measured benchmark; no mock-only release claim. Для полной квалификации R0 обязательны реальная браузерная/офлайн-проверка пользовательских ролей и их error/stale states; API-only работа не считается USER_JOURNEY_QUALIFIED.

**Затем:** RD-12.

### RD-12 — Pilot Acceptance + Release Qualification

**Зависимости:** `RD-11`, `RD-00`. **Ответственные модули:** `tenancy`, `commercial`, `fleet`, `booking`, `execution`, `tracking`, `documents`, `finance`. **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** Business/legal/finance signoff for applicable BR and corresponding user journeys; selected KZ road corridor/ordinary cargo, supported deployment profiles. Release image SBOM, secret scan, rollback/runbook, tenant/customer onboarding, incident process, measurable pilot KPIs.

**Изменения в коде/артефактах:**
- versioned release manifest and exact SHA test attestation
- deployment profiles + backup/restore/incident runbook
- pilot handoff and business acceptance report

**Обязательная TDD-проверка:**
- repeat E2E on release artifact and production-like database
- restore drill + data/PII retention review
- sanitized audit and monitoring alert exercise
- manual user walkthrough for customer/forwarder/carrier/receiver/commercial price reporter/EDS signatory

**Gate выхода:** Signed business/legal/finance acceptance where required, exact release SHA artifacts/CI green, operational recovery proved; otherwise NO RELEASE.

**Затем:** Enable RX work by measured demand.


## 5. Future stages and module coverage

### RX-01 — R1 Operations Extensions

**Зависимости:** `RD-12`. **Ответственные модули:** `recovery`, `warehouse`, `saas-control`. **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** Rescue/cross-dock/warehouse ledger, subscriptions and billing; each as small TDD vertical with domain ownership and multi-tenant security, never automatic full stack at once.

**Изменения в коде/артефактах:**
- R1 module-owned APIs/migrations
- owner-specific query filters and retention

**Обязательная TDD-проверка:**
- custody transfer, warehouse conservation, billing control, cancellation compensation

**Gate выхода:** New module tests + regression R0 all green, measured business value.

**Затем:** RX-02 / RX-03 conditional.

### RX-02 — R1/R2 Optimization + Intelligence

**Зависимости:** `RD-12`. **Ответственные модули:** `optimization`, `intelligence`. **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** Optimization jobs and ML history separated: approved data lineage, point-in-time features, model version, source provenance; workers optional after workload evidence.

**Изменения в коде/артефактах:**
- optimization solver adapter
- intelligence dataset and model registry
- optional isolated CPU training workers

**Обязательная TDD-проверка:**
- reproducible datasets, no cross tenant training leak
- solver outputs never bypass mandatory compliance and booking guards

**Gate выхода:** Use-case benefit/quality/latency and tenant security verified; fallback deterministic.

**Затем:** Optional activation.

### RX-03 — R2+ Market / Regulations

**Зависимости:** `RD-12`. **Ответственные модули:** `marketplace`, `regulatory`. **Статус:** PLANNED / NOT QUALIFIED.

**Scope и результат:** Private load board then optional public freight marketplace, country-specific authoritative rules and typed standards only with licensing/expert signoff; no unverified eCMR/customs guarantees.

**Изменения в коде/артефактах:**
- verified listing and trust contracts
- versioned regulatory rules and provenance

**Обязательная TDD-проверка:**
- fraud/disclosure negative cases, no booking ownership leakage
- rule version rollback, unknown jurisdiction fail closed

**Gate выхода:** Separate business/legal/regulatory acceptance and R0 regression.

**Затем:** Feature release only.


**Every one of the 17 modules has at least one planned phase owner; a module's presence in a later phase is not an instruction to implement its full future backlog now.** Retain clean module contracts for future extraction to workers/services only when needed.

## 6. API, filtering, pagination, DTO & mapping gates

For **every query endpoint** agree typed allowlisted `filter`, `sort`, pagination mode and permissions **before repository SQL**:
- Offset for RFQ, Booking/provider board/reference lists: page 0-based, default size 20, max 100 subject to benchmarks; fixed tie-break `id`, forbidden deep offset may require cursor; `totalElements` optional and secured.
- Cursor/keyset for GPS, Tracking timeline, audit and high-volume immutable event lists: signed/opaque, versioned, time-limited, filter/sort/scope-bound, no cross-account replay; `limit+1` and stable tuple; no false snapshot claim.
- `createdFrom` inclusive, `createdTo` exclusive; user-specified query text/radii bounded, SQL parameters bound; column and sort expressions only from server-side allowlist.
- Apply resource scope before filtering, counting, ordering and pagination; test lists, aggregate counts and existence inference with multiple CustomerAccounts. Never trust caller's `tenantId`.
- `RfqListItemResponse` and customer detail vs provider detail are distinct field allowlists. MapStruct cannot map user-supplied `tenantId`, `deletedBy`, `approvedBy`, state or internal margin onto writable aggregates.
- EXPLAIN ANALYZE with realistic two-tenant fixture; no guessed SLO or index blindly copied from an example.
- Query read models can be lagging and carry watermark/source timestamp; **Booking, money, custody and Stock write guards must read authoritative state**.

**Soft Delete gates:** active default lists/count exclude deleted eligible drafts; only owner policy can authorize delete/restore; restore must recheck unique keys and stale dependencies; deletion event/outbox/audit commit together, derived projection tombstone and rebuild cannot resurrect; signed documents/Booking/finance/custody never soft-delete. No global JPA `@Where` assumption or generic cascade; per-owner design and legal hold/retention determine erasure. See [32 §10](32-scenario-driven-backend-design-v1.md) and SDB-009..016.

## 6A. Пользовательские интерфейсы и TDD сквозного поведения

**Область:** на R0 требуются минимум Customer Portal, Provider Inbox/Operations и scoped Carrier/Driver/Receiver interactions. Frontend-фреймворк в текущем ТЗ не зафиксирован: выбрать по отдельному короткому PoC без разработки второй бизнес-системы. Backend остаётся единственным источником прав и доменных переходов. UI не должен формировать `tenantId`, `approvedBy`, `deletedAt`, `paid` как управляемые поля authoritative агрегатов.

| Milestone | Frontend/API acceptance |
|---|---|
| `RD-02` | Вход/выбор подтверждённого Tenant или CustomerAccount; запрет доступа к чужому кабинету и безопасная обработка истёкших приглашений. |
| `RD-03` | Customer My Requests: создание/отправка RFQ, фильтры, сортировка, пагинация, empty/error states; Provider Incoming RFQs: только разрешённый inbox. |
| `RD-04` | Разные экраны просмотра и правомерного акцепта QuoteVersion; состояние awaiting resource confirmation не отображается как confirmed booking. |
| `RD-05` | Операционный shortlist автомобилей с freshness/eligibility; UNKNOWN compliance — заблокированная кнопка с объяснением, не фиктивная автоматическая проверка. |
| `RD-06` | Provider/Carrier Booking workflow: hold, pending, confirmation, rejection/cancel request; при конфликте UI показывает актуальную версию после повторного чтения. |
| `RD-07` | Driver offline pickup/POD draft queue + receiver evidence; после устаревшей роли/assignment показать requires reconciliation, не silently delivered. |
| `RD-08` | Customer Tracking + POD/documents, явная свежесть ETA, строгий customer-visible field allowlist, истекшая ссылка не открывает чужой документ. |
| `RD-09` | Finance office AR/AP + evidence status; approval и posting отделены, paid не доступен как произвольный ручной переключатель. |
| `RD-10` | Состояния долгой операции, retry/failed, graceful degradation и безопасная операционная непрерывность при недоступности внешних сервисов. |
| `RD-11` | Сквозная browser/UI и при необходимости offline device simulation: customer→provider→carrier→driver→receiver→finance, все негативные видимые состояния. |
| `RD-12` | User acceptance workshop, accessibility/responsive baseline и документирование наблюдаемых ограничений перед публикацией. |

**Тестовая стратегия:** проверять пользовательские сценарии сначала через API/HTTP с реальной БД; как только появляются интерфейсы — UI component/contract tests и browser E2E (например, Playwright после выбора frontend stack) для важных переходов и ошибочных состояний. Не дублировать весь backend unit suite UI-тестами. У каждого экрана есть ссылки на Story/BSC/BR, permission, API endpoint, read model freshness, loading/empty/denied/error cases. Offline driver flow требует реального устойчивого локального буфера/доказательств при появлении приложения; один браузерный mock не доказывает безопасность offline replay.

**Gate:** пользовательский сценарий считается завершённым только когда API, права, данные и пользовательский экран показывают одно и то же фактическое состояние, включая ошибки, а не только красивый happy-path screen. Пока UI-код не создан, этап маркируется BACKEND/API QUALIFIED, но не USER-JOURNEY QUALIFIED.

## 7. Data modeling, migrations, transactions and module boundaries

**Migrations:** Flyway, named schema/table ownership, PostgreSQL RLS policies, not superuser runtime app; transaction `SET LOCAL` or equivalent from verified context, no pool leakage. Expand/contract migrations and executable migration smoke on an existing DB snapshot; if rollback is impossible, document forward-recovery and backup restore procedure.

**Concurrency:** aggregate expectedVersion plus named unique/exclusion constraints; one Fleet authority for temporal capacity. Database constraint violation translated to a specific domain code **only for known owner-named constraints**; no blanket SQLSTATE 23505/23P01→409.

**Events:** local state change + audit + outbox in one committed transaction; inbox dedup per tenant/producer/event; handlers at least once, no arbitrary external exactly-once promise. External carrier/bank uncertainty routes to reconciliation rather than blind money retries. Job workers have attempts, leases/fencing and explicit scoped service identity. Redis optional only, not authoritative.

**GIS:** own Fleet geo position and separate Tracking customer projection; query in meters with PostGIS geography/appropriate GiST and tenant filtering; if live GPS ingestion is enabled, add RANGE(observed_at) partitions, future premake and global ingest dedup registry. No GIS-derived POD or legal road-routing approval.

## 8. Engineering PR plan and branching discipline

Use one independently testable vertical increment per PR (or smaller when needed), retaining a single business runtime. No unsupported claim that a document branch is already a compiled implementation branch.

**Suggested sequence:** `feat/r0-foundation` → `feat/r0-tenancy` → `feat/r0-rfq` → `feat/r0-quote`; independent `feat/r0-fleet-cargo-compliance`; then `feat/r0-booking`, `feat/r0-execution`, `feat/r0-tracking-documents`, `feat/r0-finance`, `feat/r0-ops-hardening`, `feat/r0-e2e-qualification`. These are proposed branch names; **none is automatically created** by this roadmap.

**PR template:**

~~~yaml
storyIds: [USB-...]
scenarioIds: [BSC-...]
businessRuleIds: [BR-...]
businessSignoff: PENDING | APPROVED
aggregateOwner: ...
permissions: [ ... ]
databaseMigrations: [ ... ]
apiDtoAndMapper: [ ... ]
queriesAndIndexes: [ ... ]
softDeleteAndRetentionPolicy: NOT_APPLICABLE | ...
tddRedEvidence: ...
tddGreenEvidence: ...
unitTests: ...
postgresRlsConcurrency: ...
negativeAndRecovery: ...
exactSha: ...
ciRunUrl: ...
releaseRisk: ...
~~~

No PR containing a new legally binding command or financial effect can merge based solely on future test IDs or unreviewed policy drafts. Read-only/denied stubs are clearly labeled and tested.

## 9. CI workflow and quality gates

**Every PR (minimum, when applicable):**
- `contracts`: JSON schema/IDs/links; no orphan story→BR→test→owner mapping; OpenAPI/error-code compatibility.
- `compile-and-unit`: Maven, pinned compatible BOM, MapStruct annotation processor, JUnit tests and JaCoCo diagnostics.
- `modulith`: `ApplicationModules.verify()`, named public interfaces only; no foreign SQL writes.
- `pg-integration`: PostgreSQL+PostGIS Testcontainers, Flyway, tenant A/B isolation, CustomerOrg-X/Y counts, pool reuse, transaction/outbox/soft delete.
- `security-and-api`: JWT/permissions/SoD, ProblemDetail RFC9457 parity (Security filter vs MVC), request field overposting, field leakage.
- `critical-races`: only impacted/accepted race suites (hold/expiry, quote acceptance, POD/offline, bank duplicate).
- `supply-chain`: secrets scanning, dependency/license/SBOM checks; exact baseline before R0 release.

**Release qualification (RD-11/12):** all applicable accepted P0 checks, ten cross-role E2E candidates when signed, recovery/restart/backup drill, spatial/partition tests if GPS enabled, document store integrity, load benchmarks, observed p95/p99, incident playbook and real stakeholder signoffs. Long-running load/chaos may be a separately required release workflow, but results must be attached to the **same release candidate SHA** or a documented unchanged artifact digest. Do not mark green if a required job was skipped.

**Machine readable evidence record**:

~~~json
{
  "phaseId": "RD-05",
  "gitSha": "<exact-real-sha>",
  "ciRunUrl": "<actual-ci-url>",
  "businessDecisionVersions": ["BR-07:APPROVED", "BR-08:APPROVED"],
  "postgresVersion": "<actual-version>",
  "migrationVersion": "<actual-flyway-version>",
  "tests": {"passed": "<actual>", "failed": "<actual>", "skipped": "<actual>"},
  "negativeAndRaceProofs": ["<actual-artifact-url>"],
  "qualification": "QUALIFIED"
}
~~~

**The above is a schema example, not a result.** All placeholders must be replaced by actual run evidence before status changes.

## 10. Synthetic test environment and fault injection

Minimum DB fixture:

~~~text
Provider Tenant-A (forwarder)
  ├── CustomerOrg-X / ExternalCustomer-X1, X2
  ├── CustomerOrg-Y / ExternalCustomer-Y1
  ├── Sales, CommercialApprover, Procurement, Planner, Dispatcher
  ├── FinanceInitiator + independent FinanceApprover
  └── own vehicle(s) and customer-safe read-model projection
Tenant-B (own subscribing shipper)
Tenant-C (independent external carrier/driver; scoped PartnerGrant)
Tenant-Z (foreign/forbidden, no access)
Receiver-R (one delivery attempt only)
  ├── RFQ/Quote accepted and expired variants
  ├── Capacity windows with overlap + expiry race
  ├── Shipment with 10 CargoUnits; partial POD 8/10, return 2/10
  ├── Documents signed/unsigned and revoked signed URL
  └── Finance partial allocation + duplicate bank reference
~~~

**Repeat across:** same request, changed idempotency payload, competing workers/transactions, unauthorized tenant/customer, revoke mid-operation, clock boundary, offline delivery replay, external timeout after side effect, Redis outage, restored DB and event projection rebuild.

Negative tests assert: safe HTTP Problem code, **no forbidden DB mutation**, no aggregate version slip, no fake outbox/notification, no customer/carrier data leak and accurate UI state. HTTP status only is insufficient.

## 11. Definition of Ready, Done, and no-go rules

| Gate | Entry/exit criterion | No-go when |
|---|---|---|
| DoR BUSINESS | agreed actor, legal entity, tenant/customer scope, actual accepted AC/BR (or explicit fail-closed scope) | signature/amount/charge/custody rule ambiguous but code assumes allow |
| DoR TECH | aggregate owner, command/query interfaces, SQL/RLS/index, DTO/maps, API/error/retention, test fixture | direct cross-module internals or generic CRUD would bypass invariants |
| DoD CODE | production code + migrations/constraints + docs + repeatable unit/security/DB tests | green mocks but not real PG when DB rule matters |
| DoD E2E | real multi-role flow + accepted negative cases + crash/replay and observations | fake paid, fake POD, cross-tenant record count leak, double booking |
| DoD RELEASE | exact SHA and release artifact, accepted business and legal evidence, restore and deployment procedure, critical CI green | any P0 violation or missing applicable signoff |

**Hard no-go:** unverified customer signatory may not accept a binding quote; carrier OFFER selection is not reserved vehicle; UNKNOWN compliance cannot become legal approval; stale GPS is not a delivery receipt; unsigned/offline custody must not silently overwrite newer authorized facts; payment approver cannot self approve; "paid" cannot be toggled without verified bank/ERP evidence; generic soft delete cannot hide invoice, booking, cargo custody or POD; no cross-tenant data or logs leak.

## 12. Planning & reporting cadence without invented deadlines

Track each stage with owner (role, not guessed person), status, dependency, AC approved/unapproved, PR URL, exact SHA, test results, blocker and next unblock action. Use **weekly gate review** when active implementation begins: update only with evidence. Do not represent P0..P5 or RD-00..12 numbers as day/week estimates. Establish durations after RD-01 baseline throughput and stakeholder workshop availability.

An example progress record:

~~~text
Phase RD-03
Status: DESIGNED (not GREEN)
Requirements: USB-EXC-002, BSC-002
Prerequisites: RD-02 QUALIFIED; customer relationship and RFQ rule approved
Evidence: none (planned)
Blocking: CustomerAccount scopes/submit permission not signed
Next action: finalize owner and consent/identity AC, then failing tests
~~~

**Workstream anti-overengineering:** no separate service per module, no universal search DSL, no premature event sourcing, no Java reflection generic mapper, no Kubernetes/Kafka as R0 gates, no measured performance claim before benchmark, no ML provider before reliable historical facts.

## 13. Decisions to close before the first business PR

1. Confirm business owner of Order, CustomerAccount, Invoice in module-boundaries contract.
2. Record business signatures for applicable BR-01..12 via docs/29 before allowing legal/custody/finance transitions.
3. Confirm R0 trusted customer relationship and exact permission for RFQ submit; `customer:rfq:list` and `customer:rfq:read` are distinct from `customer:orders:*`.
4. Confirm user-facing semantics of "discard draft" and opt-in soft delete vs Archive/Cancel/Erase.
5. Select production runtime library versions only after RD-01 exact SHA compatibility CI.
6. Define baseline pilot volume, query SLO targets and PostgreSQL index measurements; no guessed p95/ETA guarantee.
7. Determine authoritative payment evidence source, tenant provisioning and emergency continuity policy.

## 14. First concrete implementation package

**Recommended immediate PR:** RD-01 `feat/r0-foundation`. Start from existing error-handler bootstrap and keep Security `anyRequest().denyAll()` until tested identity authentication is ready.

Minimum contents: pinned supported Java/Boot/Modulith/MapStruct/Flyway/Testcontainers stack, `mvn verify` CI, `ApplicationModules.verify()`, PostgreSQL/PostGIS + Flyway smoke, two-tenant RLS tests using real transactions and connection pooling, runtime configuration samples without secrets, error-handler regression, and a README exact-SHA verification. Do not write a broad RFQ/Booking CRUD scaffold in that PR.

**Then:** RD-02 Tenancy, RD-03 customer/provider RFQ with query+soft-delete rules, RD-04 and RD-05 after signoffs, converging at RD-06 Booking. The first material release proof is **one real fully scoped business vertical slice**, not the number of created packages.


## 15. Technical re-audit v1.3 — corrected planning and anti-risk decisions

This audit is attached as [34 — Roadmap Technical Audit](34-tdd-roadmap-technical-audit.md). **Audit register has 27 findings; 14–27 are further corrections to the initial thirteen.** **Changes to this roadmap are proposals, not implementation, not business/finance/legal signoff, and not passing Testcontainers.** The existing verified handler-only CI cannot qualify any RD-01..RD-12 business milestone.

| Finding | Severity | Original risk | v1.1 remedy |
|---|---|---|---|
| AUD-RD-01 | P0 | RD-10 creates reliability too late; Commercial and Booking already need events | RD-01 includes thin transactional Outbox/Inbox, retry+dedup; RD-10 hardens operational jobs |
| AUD-RD-02 | P0 | RD-05 Cargo, Compliance, Fleet bundled into one large merge | Three independently qualified owner PRs PR-08/09/10 |
| AUD-RD-03 | P0 | Stage "modules" could be mistaken for allowed direct dependencies | Explicit primary write owner per PR; only exported APIs/events per module-boundaries contract |
| AUD-RD-04 | P0 | RFQ submit command has PENDING permission in SDB contract | Public write remains disabled until owner-auth policy and negative acceptance are approved |
| AUD-RD-05 | P0 | Binding Quote/POD/money could pass unit mocks despite unsigned BR | BR-specific decision signoff + exact-version RLS/PG/contract test required before state ALLOW |
| AUD-RD-06 | P0 | RD-07 needs POD evidence before Documents RD-08 | Execution stores verified evidence reference/receipt contract in RD-07; later Documents publishes package without changing original proof |
| AUD-RD-07 | P0 | Finance stage listed Booking/Documents without authorized dependency | Finance alone writes financial ledger; consume documented Booking/Documents snapshots through allowed APIs/events |
| AUD-RD-08 | P1 | Query+soft delete conflated with Shipping/Tracking delivery | Typed queries mandatory, draft soft delete strictly opt-in, no delete for legal evidence |
| AUD-RD-09 | P0 | UI end-to-end not an explicit stage qualification category | API_QUALIFIED ≠ USER_JOURNEY_QUALIFIED; role-based browser/offline tests part of RD-11 |
| AUD-RD-10 | P0 | Counts (84 + 48) might become meaningless test quota | Applicability register by story/owner/BR; 132 planned case specs, eight MIX not counted, no blind gate from unsigned legal flow |
| AUD-RD-11 | P1 | No executable roadmap JSON/ID consistency gate | New stdlib roadmap validator & CI workflow; cross-check modules, phases, story/test catalogs |
| AUD-RD-12 | P0 | Status might be promoted from previously green handler SHA | Per-phase evidence manifest: exact SHA, artifact digest, RLS/restore/UI/legal evidence; stage remains planned until that evidence exists |
| AUD-RD-13 | P0 | 21 PR cuts had no explicit per-PR prerequisites | Each PR has `dependsOnPrs` and an acyclic DAG; prerequisite code-qualified before merge |
| AUD-RD-14..21 | Mixed P0/P1 | RFQ submit split, ownership/ADR, evidence provenance, user-facing PR coverage, real test anchors, customer account isolation, verified settlement, validator self-tests | Recorded in technical audit §2 and machine roadmap §audit; no implementation claimed |
| AUD-RD-22 | P0 | CI schema mismatch: JSON v1.2/21 findings vs validator v1.1/13, actual failed run | Schema and all views synchronized; validator checks machine+Markdown and future approved evidence states |
| AUD-RD-23 | P0 | Commercial CustomerAccount canonical writer had no PR before Tenancy grants | Add PR-03C commercial CustomerAccount registry and published account-id event; PR-03 tenancy grants consume exported-neutral event, no Tenancy->Commercial import |
| AUD-RD-24 | P0 | RD-00 documents ALL BR-01..12 but generic qualifier demanded all signed for RD-00 before PR-02 | RD-00 records BR review state/evidence without declaring approval; per irreversible PR activationGate governs signoff |
| AUD-RD-25 | P0 | Execution proofs depended on future Documents and risked cyclic module dependency | Platform EvidenceBlobGateway verifies staged bytes and checksums, Execution owns custody receipt, Documents later owns package via Execution exported event |
| AUD-RD-26 | P0 | Finance PR-17 mixes bookkeeping with external payment verification and paid status | Split PR-17 invoice/AR/AP from PR-17S verified settlement/reversal, both with distinct TDD and mock≠PAID |
| AUD-RD-27 | P1 | Roadmap validator did not verify criticalCaseIds, activation/UI field correctness or PR Markdown dependency parity | Strengthen CI contract validator with per-PR case existence, dependency parity, required fields and deterministic negative mutation tests |

**R0 contract truth:** `CustomerPortalApi` and `PlatformJobs` are technical integration surfaces, not 18th/19th business modules. The 17-domain catalog stays fixed. RD-01 Platform baseline is infrastructure, not a Tenancy feature.

## 16. Executable delivery increments — 26 small PR cuts

A phase is an **epic with exit criteria**, not a requirement to implement all participating modules in one PR. Each row below is one recommended **independently testable small PR or smaller**. Early PRs may be separate focused branches but must build/test on the target baseline; dependents cannot merge on red integration.

| PR | Phase | Canonical write owner | Requires code-qualified PRs | Runnable outcome / first critical gate |
|---|---|---|---|---|
| `PR-00` | `RD-00` | `architecture` | Parallel foundation start | traceability validator, signoff ledger and phase-by-phase test selection. **Gate:** catalog IDs and BR status truthful |
| `PR-01` | `RD-01` | `platform` | Parallel foundation start | Spring Modulith+Flyway+PostgreSQL/PostGIS with real RLS, typed errors and basic Outbox/Inbox. **Gate:** verify() + migration + auth fail-closed + 2-tenant RLS + outbox atomic |
| `PR-02` | `RD-02` | `tenancy` | `PR-00`, `PR-01` | tenant/legal entity and verified identity/invitation/grants and exported AccountRelationship grant interface. **Gate:** real JWT or verified auth adapter + multi-grant denial + SoD |
| `PR-03C` | `RD-02` | `commercial` | `PR-02` | canonical CustomerAccount business relationship, provider legal entity binding and versioned AccountRegistered integration event. **Gate:** customer-org/provider uniqueness, no cross-tenant inference; public event to Tenancy projection with no reverse dependency; ADR approved |
| `PR-03` | `RD-02` | `tenancy` | `PR-03C` | Tenancy CustomerAccount member grants/revoke referencing commercial account ID via neutral verified event, never a second CustomerAccount table. **Gate:** Customer-X/Y negative list/detail, warm cache, RLS context reset |
| `PR-04` | `RD-03` | `commercial` | `PR-03` | RFQ DRAFT creation + Customer My RFQs list/detail/filter; submit remains fail-closed until separate permission accepted. **Gate:** scoped DRAFT create+list; no write on unauthorized submit; pagination, outbox atomic and key conflict |
| `PR-05` | `RD-03` | `commercial` | `PR-04` | scoped RFQ submit (after explicit permission decision) + provider Inbox assignment/clarification. **Gate:** submit permission approved+negative; exact CustomerAccount, stable Inbox, branch CAS assignment, no false legally accepted Quote |
| `PR-06` | `RD-04` | `commercial` | `PR-05` | immutable QuoteVersion issue/supersede, independent price approval. **Gate:** version race + SoD; no binding acceptance without BR-01 |
| `PR-06S` | `RD-04` | `platform` | `PR-01`, `PR-02` | NCA EDS online signing platform port: NCALayer web adapter and server verification of immutable legal documents; optional eGov QR via qualified provider; publicly verifiable portable original, exact-document user preview and legal entity authority service. **Gate:** SIG-01..18, signer authority, certificate chain/revocation/time, exact document bytes, no private keys, replay/expired/wrong-tenant denial, external provider timeout safe pending |
| `PR-07` | `RD-04` | `commercial` | `PR-06`, `PR-06S` | authorized customer Quote accept/decline with evidence. **Gate:** BR-01/02/05 acceptance, exact signer, termsHash and expiry |
| `PR-08` | `RD-05` | `cargo` | `PR-02` | CargoProfile/identified units and physical compatibility inputs. **Gate:** mass/quantity/identity/value invariants |
| `PR-09` | `RD-05` | `compliance` | `PR-08` | versioned compliance decision and critical UNKNOWN safety gate. **Gate:** qualified source / correct HOLD, BR-08 signoff where binding |
| `PR-10V` | `RD-05` | `fleet` | `PR-02` | own-fleet vehicle/driver/trailer registry, verified legal owner and active/expired resource state; NO capacity commitment. **Gate:** fleet identity+ownership, duplicate/expired/archived resource denial, two branches share physical asset, scoped Fleet UI; no BookingConfirmed |
| `PR-10` | `RD-05` | `fleet` | `PR-10V`, `PR-08`, `PR-09` | atomic exclusive capacity hold+confirmation using already verified fleet resource registry, scoped cargo eligibility and Compliance. **Gate:** PostgreSQL exclusion/locked-slot race, hold expiry fencing BR-07 (registry PR-10V is separate and has no resource commitment) |
| `PR-11` | `RD-06` | `commercial` | `PR-03`, `PR-06`, `PR-06S` | carrier sourced offer+withdrawal/ack and own-fleet alternative. **Gate:** partner grants, no margin disclosure, no false capacity, BR-06; binding carrier agreement uses signed legal-entity authority and immutable terms where legally required |
| `PR-12` | `RD-06` | `booking` | `PR-07`, `PR-10`, `PR-11` | Booking pending→confirmed via accepted quote and confirmed exclusive capacity; customer-facing Order remains a read-only projection until DEC-R0-01 ADR. **Gate:** process crash/replay, stale quote/carrier, no phantom Booking |
| `PR-12C` | `RD-06` | `booking` | `PR-12` | customer cancellation REQUEST, provider review, pre-start guarded decision, post-start interruption/recovery request with no phantom release/fee. **Gate:** BR-11 actor+cutoff+terms required; request != cancellation; Trip.STARTED race, cargo custody preserved, finance impact only approved |
| `PR-13` | `RD-07` | `execution` | `PR-12`, `PR-06S` | Trip+pickup offline custody and signed evidence references; implement verified original evidence receipts (not bare URL) before document packaging. **Gate:** historical authority, late replay, one custodian, BR-09; hash/size/signer/object existence/orphan replay tests |
| `PR-14` | `RD-07` | `execution` | `PR-13` | delivery attempts, partial/refused POD and compensating disposition. **Gate:** 8/10 conservation, receiver evidence and proof immutability, BR-10 |
| `PR-15` | `RD-08` | `tracking` | `PR-13` | customer-scoped timeline and ETA freshness. **Gate:** stale cache, wrong-customer cursor, no GPS-derived POD |
| `PR-16` | `RD-08` | `documents` | `PR-14` | verified POD/document package and bounded download. **Gate:** verified version, revoked grant, legal hold, no generic soft delete |
| `PR-16R` | `RD-08` | `commercial` | `PR-14`, `PR-16` | private one-per-eligible-service customer review after verified completion, no self-review or public reputation. **Gate:** EXT-09 customer:review:submit, NEG-R0-048; grant recheck, unique provider+customer+service+reviewer scope, no partial/disputed auto-eligible; 8/10 partial is not automatically completed or eligible, separate verified 10/10 fixture |
| `PR-17` | `RD-09` | `finance` | `PR-07` | commercial sell/buy rates, versioned cost estimate and margin reports with read-only references to externally issued accounting documents; no internal invoicing or payment. **Gate:** Money rounding, private customer/tenant scoped pricing, role separation on margin and verified external document reference; no payments endpoints, PAID status, PaymentAllocation or bank integration |
| `PR-18` | `RD-10` | `platform` | `PR-13` | advanced job fencing, timeout, crash and safe SaaS continuity. **Gate:** replay/failover + BR-04 in-flight evidence after suspension |
| `PR-19` | `RD-11` | `cross-functional` | `PR-12`, `PR-12C`, `PR-14`, `PR-15`, `PR-16`, `PR-16R`, `PR-18`, `PR-17` | full external-customer→forwarder→carrier→driver→receiver journey, EDS binding evidence and commercial cost report; no payments. **Gate:** accepted P0 negative, RLS, outage recovery, UI states and artifact evidence; verified EDS authority/immutability and no payment route/status; two distinct fixture branches: 8/10 POD remains partial and review denied, separately verified completion permits one private review; carrier signed commitment under relevant legal rule |
| `PR-20` | `RD-12` | `release` | `PR-00`, `PR-19` | pilot signoff, container, SBOM, restore drill and release artifact. **Gate:** same SHA/digest, no open P0, signed applicable BR |

**PR DAG rule:** Every `dependsOnPrs` edge denotes a prerequisite **qualified implementation artifact**, not merely a completed document; CI validates no orphan dependency or cycle. Technical parallelism is allowed only where dependencies and security contracts permit.

**Parallelism:** PR-13 Execution не зависит от BR-11/PR-12C отмены; PR-17 Finance может разрабатывать договорный ADVANCE до POD, сохраняя POST_SERVICE fail-closed без evidence.

**Critical path:** `PR-00/01` parallel → `PR-02/03C/03` → `PR-04/05` → `PR-06/07` and `PR-08/09/10` parallel → `PR-11/12` → `PR-13/14` → `PR-15/16/17/17S` as business dependencies permit → `PR-18` hardening → `PR-19` actual E2E → `PR-20` pilot. A dependency is a tested API/data/contract prerequisite, not a calendar estimate.

**Correct implementation order of business writes:** `RFQ state + audit + Outbox` must be in one transaction from RD-03; the general infrastructure comes first in RD-01. Capacity reservation must use real PG exclusivity, not Redis lock. Driver pickup/receiver POD must not rely on Tracking/GPS as source of truth. Money allocation cannot derive paid status from an internal approval.

## 17. Mandatory ownership and dependency checks

**Machine contract:** [module-boundaries.v1.json](contracts/module-boundaries.v1.json) is the allowed dependency graph. `moduleOwner` in a story or PR means authority over its own aggregates and schema — it does **not** mean it can write referenced aggregates.

| Write domain | Canonical owner | Allowed integration in its phase | Forbidden shortcut |
|---|---|---|---|
| Tenant/Member/CustomerAccount | Tenancy | verified security context; customer account grants | caller-provided tenantId or employee role by email domain |
| RFQ/QuoteVersion/CarrierOffer | Commercial | Tenancy public auth, Commercial exported commands/events | Fleet/Booking directly editing Quote |
| Cargo profiles and quantities | Cargo (master) / Execution (custody fact) | published cargo snapshot/identity, handover event | one entity shared/written by multiple modules |
| Compliance decision | Compliance | valid provenance source/version and qualified reviewer | Dispatcher override of UNKNOWN |
| Vehicle/CapacityReservation | Fleet | exported reservation API and typed event | Booking editing Fleet table, Redis-only exclusivity |
| Booking | Booking | exported Commercial/Fleet/Cargo/Compliance guards | CarrierOffer SELECTED accepted as capacity proof |
| Trip/DeliveryAttempt/Custody | Execution | Booking confirmed snapshot; Documents evidence reference | Tracking GPS auto marking POD |
| Customer projection/ETA | Tracking | published Execution milestones | Tracking changing delivery truth |
| Signed proofs/DocumentPackage | Documents | Execution provenance, authorized object adapter | changing signed POD bytes in place |
| Invoice/AR/AP/Allocation | Finance | verified commercial/execution snapshots and reference IDs | direct Booking/Documents repository reads, approval used as bank settlement |
| Jobs / policy errors | Platform (technical) | service principal, scope per owner, durable Outbox/Inbox | general global support superuser |

**Verification:** `ApplicationModules.verify()`, package visibility/export tests, module-owned Flyway migrations, database write-path tests and no foreign repository injection. A read model can join safely only through an explicitly approved owner-published projection or scope-safe SQL owner boundary; business commands always use source-of-truth guards.

## 18. Test applicability, signoff and evidence protocol

**Original bank:** 60 blocker + 14 R0 safety + 10 cross-role E2E = 84. [Additional negative bank](contracts/r0-negative-scenarios.v1.json) 48 = **132 proposed individual case specifications**; [SDB](contracts/backend-query-soft-delete.v1.json) has **20 traceable acceptance anchors** (they may overlap); eight `MIX-*` scenarios are *not* part of the 132. Documentation coverage ≠ executable test count.

**For each implementation PR write an applicability record**:

~~~yaml
phaseId: RD-05
prId: PR-10
sourceOfTruthOwner: fleet
storyIds: []
bscIds: [BSC-004]
brDecisions:
  - id: BR-07
    state: PENDING_REAL_STAKEHOLDER
testSelection:
  accepted: []            # only actual accepted relevant requirements
  failClosed: []          # safe DENY tests allowed before legal approval
  deferredWithReason: []  # R1/R2 or non-applicable, with owner signoff
  blockedPendingBr: [TDD-SIM-18-G12-01]
redEvidenceSha: null
greenEvidenceSha: null
exactCiRunUrl: null
migrationVersion: null
releaseArtifactDigest: null
uiJourneyStatus: NOT_STARTED
~~~

**No promotion rule:** `GREEN` is an actual local test outcome; `QUALIFIED` is exact-SHA, actual CI, contract parity, DB/HTTP/negative behavior and required business approval. If no UI exists, an endpoint may be `API_QUALIFIED` but **not** `USER_JOURNEY_QUALIFIED`; this distinction is compulsory for RD-11/12.

**State and evidence distinctions:** platform code bootstrapped and an earlier handler-only workflow may be green; none of the 17 business module implementations, multi-tenant DB RLS acceptance, carrier/Quote legal effects or end-to-end user journeys have been shown qualified here. No unsupported SLA, coverage percentage or deadline.

## 19. Critical R0 no-go checks before implementation and release

- **RD-01 foundation:** JDK21/Boot BOM/Modulith/Flyway/Testcontainers compatibility must run in CI, empty and upgrade migrations must pass, DB runtime principal has no `BYPASSRLS`, pooled tenant context must be reset, Outbox/Inbox uniqueness and crash-after-commit proven.
- **RD-02 access:** CustomerOrg-X/Y and Tenant-A/B/Z must have isolated list/detail/count/exports; JWT authority server-derived; support and super admin cannot inspect arbitrary customer financial records.
- **RD-03/04 commercial:** RFQ submitted only with explicit signed-off grant; exact immutable QuoteVersion and signer + termsHash; no staff impersonation, no expired acceptance, no false Booking.
- **RD-05/06 physical commitment:** regulatory UNKNOWN = HOLD, real PostgreSQL single exclusive slot across branches and drivers/trailers; carrier selected != confirmed; Booking must re-read authoritative resource.
- **RD-07/08 execution/documents:** offline event history and authorization verifiable, at most one custodian per CargoUnit, eight-of-ten POD remains partial; signed document original immutable; URL revocation and cursor fail closed.
- **RD-09 finance:** independent approver, precise currencies, bank reference idempotency and reversal evidence; approval never turns into SETTLED.
- **RD-10 failure:** a stopped job can restart without double effects, revoked grants rechecked; SaaS subscription suspension cannot silently interrupt documented safe active-cargo functions.
- **RD-11/12 release:** real cross-role screens + API, backup/restore, data retention, security scanning and signed applicable business/legal/finance policy; zero open P0 leakage, double booking, false delivery or settlement, no skipped mandatory checks.

**Scope:** no general BPM engine, Kafka/Kubernetes cluster, universal JPA soft delete, 17 microservices, public marketplace, ML runtime or unverified regulated-cargo automation required for initial R0. Audit improvements add clear gates and small slices, not artificial new platform features.

## 20. Second-pass technical audit v1.2 — AUD-RD-14..21

Design-only corrections: not implemented behavior, real stakeholder approval, or new passing Java/PostgreSQL tests. Previous findings AUD-RD-01..13 remain in [34 — Audit](34-tdd-roadmap-technical-audit.md).

| ID | Severity | New risk in v1.1 | Mandatory correction |
|---|---|---|---|
| AUD-RD-14 | P0 | RFQ create and submit combined despite PENDING submit permission | PR-04 draft-safe only; PR-05 submit disabled until approved; denial must have no RFQ/Outbox mutation |
| AUD-RD-15 | P0 | CustomerAccount writer conflicts with Tenancy grants | Proposed Commercial relationship owner, Tenancy identity/grant owner; approve ADR before migration |
| AUD-RD-16 | P0 | Execution records custody before verified original proof/storage adapter | Evidence bytes/hash/size/authority, immutable receipt, object existence and orphan/replay handling in PR-13/14 |
| AUD-RD-17 | P0 | UI described but no exact per-PR acceptance obligation | Required screens/error/offline checks in machine PR-level uiAcceptance |
| AUD-RD-18 | P0 | Validator checks 132 test count but not PR-specific test risks | PR criticalCaseIds must resolve to canonical test bank, with applicability manifest |
| AUD-RD-19 | P0 | Tenant RLS alone not enough for multiple CustomerAccounts in same provider | Verified CustomerAccount scopes in SQL/COUNT/export/cursor/docs + revoke tests |
| AUD-RD-20 | P0 | Mock/sandbox settlement can produce false production PAID | Verified bank/ERP/manual independently approved evidence required |
| AUD-RD-21 | P1 | Docs PR table can drift from JSON undetected, validator untested | Compare Markdown PR owner/phase/prerequisite DAG and run mutation unit tests in CI |

## 21. RFQ activation, identity, and tenant isolation

**PR-04**: create *DRAFT only*, under actual granted customer:rfq:create (EXT-02) with verified provider/CustomerAccount scope. List/detail must use distinct customer:rfq:list (EXT-14) and customer:rfq:read (EXT-15), not customer:orders:*. DRAFT editor, My Requests pagination and deny/error/empty states are required. An attempted submit is denied by RFC9457; no RFQ status change, approval or submitted Outbox.

**PR-05**: submit plus Provider Inbox only after Commercial owner and Security approve a new submit permission or a documented expansion of existing create permission. Existing permission catalog does **not** automatically permit submit. Denied operation has no success event. The PR may be designed or fail-closed pending approval, but cannot be activated. RD-03 QUALIFIED requires a tested authorized end-to-end submit; PR-04 alone can only be CODE_VERIFIED_DENY_ONLY.

**CustomerAccount owner**: proposed authoritative business relationship in Commercial; Tenancy owns validated identities/LegalEntity/PartnerGrant and revocation. This roadmap does not change the unresolved canonical module ownership ADR. Order aggregate vs composed view and Finance Invoice ownership likewise require alignment before creating tables. Exports, counts and read projections must enforce account grant in addition to Tenant RLS. Same-provider CustomerOrg-X/Y isolation is proven with direct PostgreSQL scoped queries and HTTP, including guessed IDs, COUNT, cursor and doc download, and pool reuse after revoke.

## 22. Custody originals, settlement evidence, and role UI

**Before Documents PR-16**, Execution PR-13/14 must have an exported proof storage adapter contract, not arbitrary URI-as-evidence. Flow: authenticate signer and assigned sender -> stage original bytes in protected temporary object area -> verify SHA-256, size, claimed time, object availability, content safety -> persist immutable evidence receipt + guarded custody state/audit/outbox in one PostgreSQL transaction -> allow Documents later to package the verified proof without rewriting. Database commit cannot atomically commit an external blob: orphan cleanup/reconciliation and duplicate/late-event quarantine mandatory. Tests: changed hash/same eventId, object missing after staged upload, revoked driver, forged capturedAt, double POD and per-unit conservation.

**PR-17 = только Costing / Margin / External Accounting Document Reference.** Оплата, банк, ЭСФ, AR/AP, возврат, PaymentAllocation, PAID/SETTLED не реализуются KERUENIX и не являются условием релиза. Исторические банковские тесты классифицируются OUT_OF_SCOPE_R0. **PR-06S = NCA EDS подпись**: защищённый original, точный version/hash, криптография+полномочия, отказ при просроченном сертификате; backend не получает private key.

**Frontend per PR**: machine uiAcceptance lists role screens, denial, loading/empty/version-conflict states and a UI test requirement. A linked frontend PR may implement the feature separately, but it must have an exact code SHA/artifact and pass before the business PR claims USER_JOURNEY_VERIFIED. Particularly driver offline evidence must have decided local-first/PWA/native durable queue and device authorization policy before PR-13. A backend-only green HTTP test cannot substitute for multi-actor UI or offline replay acceptance.

**Tests per PR**: criticalCaseIds are minimum anchors from the existing 132 proposed cases, not a release pass-count target. Each business PR also needs a full applicability manifest (story, BR, case ID, APPROVED/FAIL_CLOSED/BLOCKED/DEFERRED, owner, real test class, DB/RLS/UI result, exact SHA and any approved omission). Passing fail-closed tests does not grant unsigned irreversible behavior.

## 23. Revised implementation order

Start PR-00 and PR-01 in parallel (traceability/validator plus Boot, Modulith, Flyway, real Postgres/PostGIS/RLS/Outbox). Then PR-02/03 Tenancy and CustomerAccount ownership ADR, PR-04 **Draft**, PR-05 **approved submit**/Inbox, PR-06/07 Quote, PR-08/09/10 Cargo/Compliance/Fleet, PR-11/12 Carrier/Booking, PR-13/14 verified custody/POD, PR-15/16 Tracking/Documents, PR-17 commercial cost/margin report, PR-18 recovery, PR-19 real multi-role API/UI E2E, PR-20 signed pilot.

All 17 existing business modules remain in the architecture map. This version is a **proposal and CI-verifiable documentary plan**, not a completed business backend.

## 24. Second audit v1.3 — critical design corrections

**Verified observed defect in prior HEAD:** Roadmap contract was `schemaVersion=1.2.0` with 21 audit findings while `validate_tdd_roadmap.py` enforced `1.1.0` and 13 findings. GitHub Actions run [42403111243](https://github.com/alimbetov/KERUENIX/actions/runs/42403111243) **FAILED** on these two comparisons. This is a *real documentation CI defect*, not an application defect. The v1.3 machine and Markdown contracts, validator, and synthetic negative validator self-tests are required for correction. Do not claim newest SHA qualified until new CI finishes.

### 24.1 Owner-safe customer onboarding, not duplicate CustomerAccount

`PR-02` is Tenancy identity and verified provider membership. `PR-03C` creates canonical `CustomerAccount` and business provider/customer relationship in **Commercial** after real provider authority/business rule verification, then emits a versioned, tenant-scoped account-registered **integration envelope**. `PR-03` is **Tenancy** external grant (subject → provider/customer account) based on the verified account reference; no direct Tenancy → Commercial class import or repository read is allowed. Commercial may depend on Tenancy exported authorization services, per module boundaries. Integration event schema/producer/consumer and at-least-once/duplicate/revoke tests must be approved before any grant is activated. CustomerOrg-X and Y share provider Tenant-A but must never see each other's RFQs, detail, totals, exports or evidence. PostgreSQL tenant RLS alone is insufficient; scoped predicate/permission contract is mandatory.

**ADR gate:** `CustomerAccount` canonical ownership is still a **proposed** architecture decision, not automatically approved by this edit. `Order` source-of-truth remains `PENDING_ADR` and must be resolved before Booking PR-12 migration. The PR DAG provides technical ordering, not acceptance of these ADRs.

### 24.2 Evidence provenance without Execution ↔ Documents cycle

`PR-13` calls an infrastructure-level `EvidenceBlobGateway` through an exported/own port (not a new business module), stages/uploads original proof bytes, checks object presence, MIME/scan policy, SHA-256, byte size and actor authority. Execution commits verified `ProofReceipt` + custody transition + Outbox atomically *after* externally stored evidence is validated; orphan blobs and uncertain cleanup have explicit reconciliation. `PR-16` Documents consumes Execution's published proof receipt or exported API and assembles versioned immutable `DocumentPackage`. **No Execution→Documents direct module import**, which would contradict the allowed `documents → execution` dependency. An arbitrary signed URL is not legal/operational proof of POD.

### 24.3 Invoice ≠ settled payment — split the finance slice

`PR-17` delivers accurate Finance-owned Invoice, AR/AP, payable approvals, outstanding/partial amounts and immutable originals; `PR-17S` delivers verified bank/ERP transaction ingestion, unique allocation, replay/reversal handling and guarded `SETTLED`. PR-17 may be qualified with no live bank integration **only as an invoicing slice**, while PR-17S and R0 finance E2E may not be qualified by mock/sandbox callback claiming real production payment. Actual payment source, currency/legal-entity matching and independent approver remain business/legal/operational gates.

### 24.4 Workflow/approval status are not global blockers

`RD-00` owns the list of all 12 `BR` decisions and reviews their actual statuses, **not the requirement to get all 12 signatures before PR-01**. It can qualify truthful documentation even while BRs remain `PENDING_REAL_STAKEHOLDER`. For each irreversible command, `activationGate.br` and owner-approved specific policy determine readiness; unknown client RFQ submit permission remains DENY without altering the approved CREATE_DRAFT capability.

### 24.5 Gate design: no silent pass and no status fabrication

The v1.3 validator must check **all 23 PRs**, PR DAG and Markdown parity, `criticalCaseIds` against actual 132 IDs, actor/client scope and `uiAcceptance` fields, `activationGate` known BR, consistent primary owner, and status evidence. Implement positive and deliberate negative/mutation tests for the validator. A case count alone is not meaningful coverage. A declared `ciRunUrl` string is not proof the job passed: that needs GitHub-required check status and artifact/SHA verification outside static JSON validation.

Do not invent green Java or PostgreSQL coverage from successful validation of these documents. The true next R0 implementation gate remains **`PR-00 + PR-01`** on a qualified build, with stakeholder workshops progressing independently.

## 25. Usability pass v1.4 — one implementation entry point and explicit R0 gaps

This pass does **not** replace 27 prior audit findings or falsely claim implementation. It converts earlier documented gaps into independently testable PRs and a concise, navigable handoff:

- [35 — R0 Developer Handbook](35-r0-developer-handbook.md): what to build, canonical owners, scoped APIs, business truth, negative UI states, minimum real Postgres tests and per-PR handoff.
- [R0 delivery truth JSON](contracts/r0-delivery-contract.v1.json): **8 decisions DEC-R0-01..08**, each explicitly pending approval with an owner, safe default and before-PR gate. Order is **proposed read-only composition**, not an already approved mutable aggregate.
- `PR-10V`: register Fleet asset identity/active state before holding resources; **no capacity committed**. Allows some parallel work relative to Cargo/Compliance.
- `PR-12C`: customer cancellation REQUEST, provider-authorized pre-start decision and in-flight execution exception. Need BR-11; never cancel started cargo or assess automatic penalties on request alone.
- `PR-16R`: Commercial-owned **private verified-service review** after proof-backed service completion, not a public marketplace rating. Use a neutral delivered/eligibility event and account-grant recheck, not a direct Commercial→Execution internal repository dependency.
- `PR-17`: commercial sell/buy/margin report and external document reference **without payment/ESF functions**. Removed bank PR-17S. Added `PR-06S` for trusted NCA EDS signing of legally binding documents.
- `PR-19` is gated on `PR-12C` and `PR-16R` because both are in the stated R0 customer day-in-life journey.

**E2E review split:** partial 8/10 remains outstanding and must **not** be declared full-service feedback eligible; a separate confirmed completion fixture proves one private eligible review.\n\n**Maintained count:** `RD-00..12` 13 R0 stages + 3 RX candidates, **26 PR cuts** and **132 previously defined risk-based acceptance specifications** (plus eight MIX compositions not counted). Any new local unit/browser checks for new PRs must appear in their applicability manifest; no invented global "135 passing tests" claim.

**Priority:** Execute `PR-00` (record truthful ADR/BR statuses) + `PR-01` (Java/PG/Modulith/RLS/Outbox foundation) with code, then `PR-02/03C/03/04/05` as applicable. Don't treat documentation CI as successful application-domain TDD.

## 26. v1.5 historical product boundary (superseded by v1.6 above) — supersedes historical settlement text

The authoritative v1.5 [scope and EDS contract](contracts/r0-scope-eds-signing.v1.json) and [38 — online EDS, no payments](38-r0-eds-signing-no-payments.md) supersede all earlier v1.0–v1.4 planning proposals for **PaymentAllocation, bank settlement, refunds, online payments, AR/AP ledger, PAID/SETTLED and official ESF**. Those old sections above are **historical audit rationale**, not valid R0 work requirements. In particular `PR-17S` is **removed**, `PR-06S` introduced and PR-07/PR-13 gated on server-verified legal signatures. Neither partial financial nor bank mocked E2E is an R0 release criterion.

No private NCA keys are stored in KERUENIX. NCALayer is initial web design, eGov QR requires contract/API provider qualification; BR-01/05/06/09/10 and specific legal-document profile control the actual mandatory signing steps. Former payment test IDs remain traceable as OUT_OF_SCOPE_R0; no false all-132-executable promise.

## 27. v1.6 technical/business second review gate

[39 — Technical and Business Re-review](39-r0-technical-business-review.md) details remaining 2026 user scope conflicts and source ownership. **RD-09** depends on **RD-04**, *not* on full custody/Documents, because commercial cost reports can operate before the POD. **PR-11** carrier legal undertaking depends on `PR-06S` signing evidence in addition to Commercial business approval. For legally binding owner actions, `SIG-01..18` are design-only checks; Articles 50,61,62 demand exact-document signer preview/explicit confirmation, verifiable legal entity authority, public verification mechanism and portable original with validated long-term proof. `FIN-02..04` payment permissions are retired; `FIN-01` is scoped `commercial:cost:read` only. Historical positive bank cases are **RETIRED_OUT_OF_PRODUCT_SCOPE**; six PAY-ABS absence cases are the applicable negative gates. The first release is transport+document+commercial-price **without payment or accounting execution**.

# 35 — KERUENIX R0 Developer Handbook: однозначное ТЗ для первой перевозки

**Версия:** 1.1.0 · **Дата:** 2026-11-08 · **Статус:** `DRAFT / DESIGN READY FOR ENGINEERING REVIEW / BR+ADR SIGNOFF PENDING / DOMAIN CODE NOT IMPLEMENTED`.

**Актуальная продуктовая граница:** [38 — онлайн ЭЦП без платежей](38-r0-eds-signing-no-payments.md) / [machine](contracts/r0-scope-eds-signing.v1.json). **С чего начать разработчику:** этот документ → [36 — PR-00/01 стартовое ТЗ](36-r0-tdd-start-pack.md) → [33 — TDD Roadmap](33-tdd-development-roadmap-v1.md) → [R0 delivery contract](contracts/r0-delivery-contract.v1.json) → [32 — Scenario-driven Backend](32-scenario-driven-backend-design-v1.md) → [24 — Access Governance](24-access-control-tdd-matrix-v2.md) → [28+30 — Acceptance](28-r0-tdd-acceptance-bank.md) + [негативные](30-negative-and-failure-scenario-bank.md).

**Разделение документов:** данный документ объясняет **что строить, в каком порядке и как принять**. [33](33-tdd-development-roadmap-v1.md) управляет PR-этапами и зависимостями. [JSON](contracts/r0-delivery-contract.v1.json) фиксирует открытые решения без подмены их согласованием. [34](34-tdd-roadmap-technical-audit.md) — журнал найденных проблем, не источник разрешений на юридически значимые действия. Если источник противоречит принятому BR/ADR, остановить затронутую команду и согласовать изменение; CI на документах не подписывает договор.

## 1. Цель и строгие границы R0

Одна **реальная перевозка**: внешний заказчик создаёт заявку → поставщик/экспедитор обрабатывает её → уполномоченный представитель клиента принимает неизменяемые условия → свой или внешний перевозчик подтверждает ресурс → Booking → водитель принимает груз с доказательством → получатель принимает 8/10 грузовых единиц, остаток сохраняет custodian → подтверждённый POD → документы → коммерческая цена/себестоимость и ссылка на внешнюю бухгалтерию (БЕЗ платежей) → частный отзыв **только по отдельно подтверждённой завершённой услуге**. Частичный POD 8/10 сам по себе не разрешает отзыв о завершённой услуге. Каждый актёр видит только принадлежащие ему сведения.

**R0 обязательно:** внешний CustomerAccount без автоматического членства в Tenant, входящая очередь провайдера, role/scope authorization, безопасные фильтры/пагинация, актуальный tracking, immutable proof с проверенной ЭЦП где требуется юридически значимое подписание, коммерческая стоимость и внешняя бухгалтерия БЕЗ платёжных операций, негативные и race-тесты, пользовательская приёмка интерфейса и восстановление.

**R0 запрещено:** выдать выбранный CarrierOffer за CONFIRMED Capacity; считать Quote.ACCEPTED фактом Booking.CONFIRMED; считать GPS доказательством передачи; считать 8/10 полной доставкой; добавлять PaymentAllocation/PAID или банковские API; стирать юридически значимое доказательство; ослаблять tenant/customer predicate ради UI. Публичный рейтинг, marketplace, универсальный BPM, Kafka и 17 микросервисов не требуются.

## 2. Где находится правда о данных

| Ресурс | Авторитетный владелец записи | Данные для других модулей | Что запрещено |
|---|---|---|---|
| Tenant, LegalEntity, Membership, RoleAssignment, PartnerGrant | **tenancy** | проверенный principal/tenant/account-grant API и scoped security context | создать сотрудника Tenant автоматически по email клиента |
| CustomerAccount + бизнес-отношение CustomerOrg↔Provider | **commercial** — предлагаемый ADR | нейтральный versioned AccountRegistered event, tenant-scoped accountRef | Tenancy пишет Commercial таблицу или импортирует Commercial domain |
| RFQ, QuoteVersion, CarrierOffer | **commercial** | immutable commands/events/public API | Booking редактирует QuoteVersion; нет самостоятельного права RFQ submit |
| CargoProfile / идентичность грузовой единицы | **cargo** | versioned cargo snapshot | двойное владение Cargo master и Execution custody |
| Vehicle, Driver, Trailer, CapacityHold | **fleet** | FleetCapacityApi, hold/confirm/release proof | Booking пишет Fleet table или Redis lock считается единственным источником |
| ComplianceAssessment | **compliance** | decision+source+rule version | UNKNOWN автоматически считается ALLOW |
| Booking | **booking** | verified state/event and order read projection | клиентский `Order` становится вторым mutable Booking |
| Trip, CargoUnitCustody, DeliveryAttempt, ProofReceipt | **execution** | timestamped custody/Delivery event + proofRef | GPS/Tracking меняют исполнение или переписывают POD |
| Документ и его пакет | **documents** | immutable document package, short TTL authorized link | исходный signed POD перезаписывается |
| Timeline/ETA | **tracking** | permission-filtered event-derived projection | Tracking подтверждает груз/банковский расчёт |
| ContractPrice, BuyCost, SellCost, MarginReport, ExternalAccountingDocRef | **finance** (R0: только коммерческий расчёт) | версия цены, защищённый отчёт и внешняя ссылка | создание PaymentAllocation, AR/AP, PAID/SETTLED, bank/ERP gateway и налоговой ЭСФ |

**Order ADR — предлагаемое решение:** `My Orders` — **читаемая составная проекция** над RFQ/Quote/Booking/Execution/Finance, **не второй изменяемый Order aggregate** в R0. Публичный `orderRef` допускается как стабильная ссылка/корреляция, но его сопоставление с RFQ/Booking и доступ клиента должны быть версионированы. ADR должен утвердить владелец до `PR-12`.

**CustomerAccount ADR — предлагаемое решение:** Commercial пишет коммерческие отношения, Tenancy — user grants. `PR-03C` создаёт подтверждённый account + outbox, Tenancy `PR-03` обрабатывает versioned neutral account reference и отдельно выдаёт разрешённый grant. **Никакого прямого Tenancy→Commercial JPA/service dependency.** Until ADR approved, account/grant binding fail-closed.

## 3. Сквозная история — условия доступа, источник истины и отрицательный исход

| Шаг | Команда / кто вызывает | Предусловия и authoritative state | Что увидит пользователь при отказе |
|---|---|---|---|
| 1. Вход | Verified invitation / EXC | поставщик Tenant, CustomerOrg, principal и grant связаны явно | `401/403` или `404`, без названия чужой организации |
| 2. Черновик RFQ | `customer:rfq:create` / EXC Requester | permitted Commercial DRAFT, idempotency key + canonical payload hash | отклонённая роль не создаёт RFQ и Outbox |
| 3. Submit RFQ | **отдельное `customer:rfq:submit`** / EXC | **PENDING policy** до согласования; exact DRAFT/version/tenant/customer grant | пока право не утверждено — submit disabled/403, черновик сохранён |
| 4. Provider Inbox | `rfq:inbox:read/assign` / SAL | провайдер, подразделение, assignee и account scoped | нет count/cursor/list утечки между CustomerOrg X/Y |
| 5. Quote с ЭЦП | Sales/Approver → Customer Signatory | frozen termsHash/version, серверно проверенная НУЦ ЭЦП + право подписи юрлица, BR-01/05, PR-06S | Browser success или неподписанный Quote остаётся ISSUED/PENDING_SIGNATURE; Viewer не акцептует |
| 6. Carrier / own fleet | CAR/PLN/DSP | партнёрская authority + approved terms, valid Compliance and exclusive Capacity | selected/withdrawn offer не даёт Booking.CONFIRMED |
| 7. Booking | authorized Booking process | accepted Quote **и** confirmed exclusive resource **и** qualified Compliance | PENDING/RESOURCE_PENDING, без ложной confirmed notification |
| 8. Pickup | assigned DRV, shipper representative | custody original bytes, исторические полномочия; ЭЦП для обязательного акта/ТТН по legal profile | suspect offline event quarantine, no phantom custodian |
| 9. Partial POD | RCV for exact DeliveryAttempt | 8 accepted, 2 refused/held/returned with explicit ledger disposition | full delivery DENIED, still 2 outstanding |
| 10. Documents | DOC, EXC scoped read | original ProofReceipt immutable, verified document package | revoked access no new link, old presigned URL bounded TTL |
| 11. Commercial Cost Report | Commercial Price Analyst | versioned sell/buy price, currency and margin, scoped by tenant and account | no invoice/payment/PAID or other customer's margin |
| 12. External Accounting Handoff | External accounting outside KERUENIX | optional opaque reference to externally issued document; no status of payment | banking/tax systems remain separate, no PaymentAllocation/refund |
| 13. Feedback | EXC with review grant | fulfilled service + verified proof + separate eligibility policy | private eligible-only review; no provider self-review |

**Required E2E fixture:** `FIX-R0-TRANSPORT-001`: two company tenants + provider Tenant-A, CustomerOrg-X and Y sharing provider Tenant-A, an external carrier or valid own-fleet resource, ten identified CargoUnits, partial POD 8/10 **и отдельный полностью подтверждённый eligible completed service fixture для отзыва**, one expired or tampered EDS signature and revoked grant, two concurrent fleet holds. CustomerOrg-Y must not see X's list/count/export even when RLS allows the same provider Tenant: use additional account-grant ABAC predicate.

**Тест развилки:** `PARTIAL_POD_DENIAL`: 8/10 оставляет услугу частичной, `customer:review:submit` отклоняется до реального закрытия/согласованной eligibility. `VERIFIED_COMPLETION`: отдельный пример полностью подтверждённой услуги разрешает только один private review от активного CustomerAccount. Ни один из сценариев не разрешает публичные рейтинги. Для частично оспариваемых услуг вопрос review eligibility остаётся на продуктовом согласовании.

## 4. TDD implementation pattern — never only HTTP 403

For **each** PR author a lightweight `implementation-manifest.yaml` recording `prId, owner, required upstream qualified commits, storyIds, BR/ADR state, RFQ/REST permissions, code/event version, tests selected from the 132 candidates, new local unit cases, migration ID, UI acceptance, expected DB/outbox effects, CI URL, exact SHA, reviewer`.

Test cycle: **RED** (persist failing accepted behavior) → **GREEN** (minimal owner code) → **REFACTOR** (modulith verification) → real **PostgreSQL/Testcontainers** (separate transactions + non-superuser RLS) → **HTTP/security** → **Outbox/Inbox** → UI/browser where required → exact SHA CI. A planned case is not executable or green merely because its ID appears in JSON.

A rejected mutation must prove all of: correct error code (RFC 9457), aggregate/version unchanged, no unauthorized DB write, no false Outbox/notification/payment effect, correct customer-safe projection, sanitized audit and truthful UI stale/denied/pending state.

**Test applicability** must distinguish `APPLICABLE_APPROVED`, `APPLICABLE_FAIL_CLOSED`, `BLOCKED_PENDING_BR`, `DEFERRED_R1_R2`, `NOT_APPLICABLE_WITH_REASON`. A safe-denied command may be technically qualified as `DENY_ONLY`, but **not** marked accepted business user journey.

## 5. Дополнения к недостающим проверяемым PR

| Новый PR | Owner | Предпосылки | Объём и граница |
|---|---|---|---|
| `PR-10V` | Fleet | `PR-02` | vehicle/driver/trailer registry, active/expired records, own-fleet legal owner and scoped UI, **без права делать capacity CONFIRMED** |
| `PR-10` | Fleet | `PR-10V`, `PR-08`, `PR-09` | exclusive interval hold/confirm in PostgreSQL; BR-07, expiry and two-dispatcher race |
| `PR-12C` | Booking | `PR-12` | customer cancellation **request**, conditional pre-start decision, post-start execution/recovery exception; BR-11, no fee or release from client payload |
| `PR-16R` | Commercial | `PR-14`, `PR-16` | one verified **private** service review per eligible service, customer-only, no public scores; versioned delivery proof event, **no Commercial→Execution import** |
| `PR-06S` | Platform Signing | `PR-01`, `PR-02` | NCALayer browser signing + server verification and signatory authority; QR optional, key never backend |
| `PR-17` | Commercial Cost Report | `PR-07` | sell/buy/currency/margin and external accounting document reference; no payments, bank, ESF or PAID |

The first three added PRs clarify previously combined work. They are proposals until project acceptance and are included in v1.4 Roadmap; no additional business module is created.

## 6. Exact API boundaries that need signoff

Use [32 — Backend design](32-scenario-driven-backend-design-v1.md) for DTO, filtering/pagination and MapStruct rules. For R0, propose these visible command contracts; all writes need verified principal scope, idempotency where applicable and `expectedVersion` CAS on state transitions.

| Endpoint / command | Owner | Public permission | Status |
|---|---|---|---|
| `POST /api/v1/customer/rfqs` | Commercial | `EXT-02 customer:rfq:create` | policy draft |
| `GET /api/v1/customer/rfqs` | Commercial | `EXT-14 customer:rfq:list` | policy draft |
| `GET /api/v1/provider/rfqs` | Commercial | `COM-14 rfq:inbox:read` | policy draft |
| `POST /api/v1/customer/rfqs/{id}/submit` | Commercial | `customer:rfq:submit` **NOT IN APPROVED MATRIX** | **DENY until approval** |
| `POST /api/v1/customer/orders/{id}/cancel-requests` | Booking | `EXT-13 customer:order:cancel_request` | Proposed path; BR-11 governs semantics |
| `POST /api/v1/customer/orders/{id}/reviews` | Commercial | `EXT-09 customer:review:submit` | Proposed path; proof-based eligibility and private visibility |
| `GET /api/v1/commercial/cost-report` | Finance costing read facade | scoped provider pricing/margin capability (to approve) | Proposed read-only report, no payment status |
| `POST /api/v1/signing-requests` | Technical platform/signing via owning domain | signatory role + verified legal entity/owner scope (requires approval) | Proposed, creates immutable frozen sign-request; no user key upload |
| `POST /api/v1/signing-requests/{id}/signed-evidence` | Technical platform/signing | same scope and trusted signature verification | Proposed; no direct business transition without domain CAS |

All routes are **proposed**; don't create a public payment source endpoint just to satisfy tests. Customer-facing `orderId` resolution must use the signed-off Order ADR; unknown route or existing foreign UUID returns non-enumerating RFC 9457 404. Use stable command payload schemas, currency/units and OpenAPI/error examples in the owning PR.

## 7. Missing business decisions — defaults and responsible owners

The machine-readable [R0 delivery contract](contracts/r0-delivery-contract.v1.json) contains eight explicit unresolved `DEC-R0-01..08` records. They are **design proposals**, not approved policies. Each has a target PR and a fail-safe default:

| Decision | Owner of approval | Before | If not agreed |
|---|---|---|---|
| Order = projection vs aggregate | Booking/Commercial/Execution leads | PR-12 | no mutable Order table/command |
| Commercial CustomerAccount vs Tenancy grant | Commercial/Tenancy/Security | PR-03C | no new automatic customer binding |
| RFQ submit permission | Commercial/security/client | PR-05 | preserve DRAFT; deny submit |
| Booking cancellation and liabilities | Booking/Ops/Finance/Legal | PR-12C | cancellation request only, no automatic fee/release |
| Review eligibility | Commercial/customer/provider | PR-16R | disable submit unless verified eligibility |
| Fleet registry vs booked resource | Fleet/Compliance | PR-10V | unverified asset cannot be confirmed |
| Commercial cost and external accounting boundary | Product/Finance/Legal | PR-17 | no payment/AR/AP/ESF statuses or banking connection |
| Custody bytes and receipt | Execution/Documents/Security | PR-13 | no placeholder URL considered proof |

Do **not** sign approvals in GitHub code as personal information or legal certificates; link to restricted evidence, decision version, reviewer authority and a non-secret audit reference. Real counterparties must review the legal implications.

## 8. Stage handoff and Definition of Done

| Handoff | Must be accepted, not just described |
|---|---|
| RD-00 → RD-01 | IDs/owner ADR ledger, actual pending BR statuses, negative case mapping; technical foundation may proceed without all 12 signatures |
| RD-01 → RD-02 | Java21/Maven/Modulith verify, Flyway/PostGIS migrations, **real PG RLS** under non-BYPASSRLS role, Outbox/Inbox atomicity and replay, fail-closed JWT boundary |
| RD-02 → RD-03 | EXC identity and active customer grant, scoped provider/account queries, no same-provider Customer-X/Y leakage |
| RD-03 → RD-04 | authorized draft+submit, provider assignment and idempotent outbox, list/count/filter/index and stale/inaccessible UI state |
| RD-04+05 → RD-06 | signed immutable Quote version, approved Compliance and single exclusive capacity reservation |
| RD-06 → RD-07 | resilient Booking and resource ownership; cancellation pre-start vs Trip.STARTED race consistent |
| RD-07 → RD-08 | verified original custody/POD proof, partial 8/10 state, no missing CargoUnit; Documents consumes event |
| RD-08 → RD-09 | verified document package, safe tracking and versioned commercial sell/buy cost/margin report; no payment integration |
| RD-09+10 → RD-11 | correct price/margin, NCA EDS evidence for binding documents, replay/recovery and subscription safety; payment path outside KERUENIX |
| RD-11 → RD-12 | actual browser/offline E2E + data restoration/retention/security/no P0; release SHA, image digest, stakeholder signoff |

**Current truthful status:** only the backend RFC 9457 error-handler bootstrap and its tests are implemented/CI-checked. R0 business implementation, real PostgreSQL migration/RLS, and actual user E2E are **NOT QUALIFIED**. The roadmap-contract CI validates documents and cannot serve as business/test signoff.

## 9. How to pick the next engineering task

1. **PR-00:** approve or record pending `DEC-R0-01..08` / relevant BRs, confirm owner diagram, map R0 synthetic fixture and acceptance. Documentation may be code-verified with decisions still pending.
2. **PR-01:** wire Java21/Modulith/Postgres/PostGIS/Flyway/Testcontainers/RLS/Outbox/Inbox with a failing real PG test first.
3. **PR-02 → PR-03C → PR-03:** verified identities, Commercial account binding, Tenancy access grants.
4. **PR-04 → PR-05:** first customer RFQ DRAFT→SUBMITTED→Provider Inbox **only after dedicated submit policy is approved**, otherwise demonstrate safe DENY and retain DRAFT.
5. Then pursue Quote and Fleet in parallel subject to BR/ADR; never merge Booking before signatory, compliance and confirmed capacity evidence.

**Explicitly not done in this update:** no implementation of these new PRs, no real user/customer/legal approval, no new arbitrary machine access grant, no Java domain Testcontainers tests. This handbook is an implementation specification and a source of clarity, not evidence that the platform is ready for production.

## 10. v1.1 product scope binding amendment (current)

The owner-directed R0 boundary is **transport + legal-document signing + commercial costing, NO PAYMENTS**. [38 — Signatures/No Payments](38-r0-eds-signing-no-payments.md) controls any historical financial/settlement ambiguity in this handbook. `PR-06S` introduces online NCA EDS signature verification (NCALayer first, eGov QR optional qualified provider), and `PR-17S` bank settlement is removed. **Never accept a foreign/expired/unverified signature**, and never confuse a signature with money transfer. Old TDD bank payment examples are recorded as out of R0 scope, not runnable positive release gates.

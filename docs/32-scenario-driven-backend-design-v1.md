# 32 — KERUENIX Scenario-Driven Backend Design v1

**Версия:** 1.0.0 · **Дата:** 2026-11-07 · **Статус:** PROPOSED / ARCHITECTURE REVIEW / NOT BUSINESS-SIGNED / NOT IMPLEMENTED.

**Обязательное актуальное ограничение:** после изменения продукта KERUENIX **не содержит платежей, AR/AP бухгалтерского реестра, PaymentAllocation и официальной ЭСФ**, даже если они упоминаются ниже как архивный материал. Финансовый контекст — коммерческие затраты и маржа, внешняя бухгалтерия — отдельная система. Подписанные документы интегрируются через `platform.signing`, не через внутренний платежный сервис. См. [39 — Technical/Business Review](39-r0-technical-business-review.md) и [38 — EDS/No Payments](38-r0-eds-signing-no-payments.md). `Order` как read-only composition и `CustomerAccount` как Commercial owner остаются ADR-кандидатами, не одобрены автоматически.

**Назначение:** обязательный проектный стандарт преобразования принятых User Stories и бизнес-сценариев в модули, доменные агрегаты, репозитории, application services, DTO, MapStruct, REST controllers, запросы/фильтры/пагинацию, модель данных, безопасность, Soft Delete и проверяемые тесты. Документ не утверждает готовность реализации.

**Машинно-читаемый контракт:** [backend-query-soft-delete.v1.json](contracts/backend-query-soft-delete.v1.json). Он фиксирует предлагаемые умолчания, а не развёрнутый API.

**Нормативные источники:** [21 — User Story Book](21-user-story-book.md), [25 — Business Scenario Book](25-business-scenario-book.md), [26 — Role Process Simulation](26-role-process-simulation-and-gap-audit.md), [27 — BR-01..12 proposed decisions](27-r0-blocker-policy-decisions.md), [28 — TDD Bank](28-r0-tdd-acceptance-bank.md), [29 — Business Sign-off](29-r0-business-acceptance-workshop-kit.md), [30 — Negative Scenarios](30-negative-and-failure-scenario-bank.md), [31 — Unified Error Standard](31-unified-error-handling-standard.md), [13 — Modular Architecture](13-modular-architecture-options-v1.md), [15 — Data/GIS](15-data-platform-partitioning-postgis.md), [20 — MapStruct/TDD](20-mapstruct-tdd-engineering-standard.md), [24 — Access Governance](24-access-control-tdd-matrix-v2.md), [module boundaries](contracts/module-boundaries.v1.json), [error catalog](contracts/api-error-catalog.v1.json).

**v1.7 ownership correction:** `finance` only owns commercial costing and an external accounting reference. Internal Invoice/AR/AP/PaymentAllocation are prohibited. Commercial's CustomerAccount/ServiceReview ownership is a proposal pending ADR, not an approved binding rule.

## 1. Архитектурное решение

**Выбор:** scenario-driven DDD + Spring Modulith + CQRS-light в **одном Spring Boot бизнес-приложении** и одном PostgreSQL/PostGIS на инсталляцию. Command- и query-модели разделены в коде, но не требуют отдельных баз, Kafka или полнофункционального event sourcing. Экспортированные Java API и типизированные версии событий обеспечивают межмодульные взаимодействия; прямые обращения к internal packages, репозиториям и таблицам чужого модуля запрещены.

Инфраструктурный baseline по текущему GitHub CI: **Java 21, Spring Boot 4.1.2, Spring Modulith 2.1.2, JDBC, Liquibase и PostgreSQL/PostGIS**, RFC 9457/denyAll. Реализация полного домена R0 ещё не квалифицирована. Совместимость и полный интеграционный стек MapStruct/Testcontainers требуют самостоятельного PoC и exact-SHA проверки. Spring MVC + JDBC/SQL — предпочтительный R0 путь, а не зафиксированная без PoC замена всех ORM-вариантов. Virtual Threads допустимы для ограниченных I/O нагрузок, не отменяют лимиты на JDBC pool и внешние вызовы.

**Не делать:** Entity-per-table CRUD через общий GenericService/GenericRepository, автоматический экспорт JPA entity, единый универсальный DTO, клиентское управление tenantId/статусом, "soft delete everywhere", динамические SQL имена из query params, N+1 запросы, глобальный search с обходом RLS.

## 2. Pipeline: Story → Behaviour → Code → Evidence

~~~text
USB-* + BSC-* + BR-* + AUTH-* + LFC-* + NEG-R0-*
  -> актор/tenant/customer account + business outcome
  -> accepted AC + invariants + failures + rights / approval
  -> aggregate owner + state machine + commands/events
  -> domain repository + query repository + DB/RLS/indexes
  -> application command/query handlers + explicit DTO/MapStruct
  -> permission-scoped REST/OpenAPI (RFC 9457 failures)
  -> unit + real-PostgreSQL concurrency/RLS + Modulith + E2E
  -> exact SHA CI + stakeholder signoff = QUALIFIED
~~~

**Gate:** USB/BSC/BR с pending signoff разрешено переводить в технический DESIGN, но нельзя считать APPROVED_FOR_TDD и нельзя закреплять юридически/финансово спорный переход как окончательное бизнес-правило. Двенадцать BR-01..12 остаются на stakeholder signoff; 132 существующих R0/negative теста запланированы, не исполнены.

Каждая проектируемая операция получает паспорт:

| Поле | Обязательно |
|---|---|
| Traceability | storyId, BSC, BR, AC, AUTH, LFC, NEG, будущий TDD ID |
| Actor / trust | principal type, tenant context, customerAccount/PartnerGrant, SoD |
| Behaviour | command/query, триггер, исходное/целевое состояние, business outcome |
| Ownership | бизнес-модуль, aggregate, единственный writer, side-effect owner |
| Transaction | локальные таблицы, expectedVersion, idempotency scope, outbox, rollback |
| API | HTTP method/path, request/response DTO, error codes, ETag/version if used |
| Query | scope, filters, allowed sort, pagination, consistency, indexes |
| Data lifecycle | retention, archive/delete eligibility, restoration, legal hold |
| Evidence | unit, RLS, concurrency, events, HTTP, offline/replay, load, exact SHA |

## 3. Модули и ответственность

Каталог [module-boundaries.v1.json](contracts/module-boundaries.v1.json) содержит **17** business modules; новые функциональные возможности не создают автоматически 18-й модуль.

| Module | Command ownership | Query/use-case type | Deletion policy direction |
|---|---|---|---|
| tenancy | Tenant, LegalEntity, Membership, PartnerGrant | membership/access query | revoke/suspend; не удалять права без audit |
| commercial | RFQ, QuoteVersion, CarrierOffer; бизнес CustomerAccount/ServiceReview требуют синхронизации реестра owns | customer requests, provider inbox, quotes, reviews | DRAFT RFQ — условный soft delete; issued evidence — нет |
| fleet | VehicleCombination, Equipment, CapacityHold | available vehicles, geo shortlist | vehicle archive only; hold release state |
| cargo | CargoProfile, HandlingUnit | cargo catalog | archive draft catalog when eligible; not custody facts |
| compliance | ComplianceAssessment, RuleSetActivation | assessment, restrictions | versioned/supersede, не удалять решения |
| booking | Booking, ReservationOrchestration | booking board | cancel/terminate, не soft delete |
| execution | Trip, TransportLeg, Shipment, CustodyHandover, DeliveryAttempt | shipment/trip dashboards | immutable lifecycle and corrections |
| tracking | TrackingSnapshot, CustomerTrackingGrant | timeline/ETA | derived projection tombstone, rebuild |
| documents | DocumentPackageVersion, ProofDocument | document list/status | version/retention/legal hold |
| finance (R0 commercial costing only) | ContractCost, BuySellSnapshot, MarginReadModel, ExternalAccountingDocumentRef | scope-filtered read-only cost/margin and external reference, no payment system | No PaymentAllocation, AR/AP ledger, paid or tax invoice generation |
| intelligence | ML dataset/model/job ownership as in 17 | versioned predictions and audits | retention/withdrawal per ML policy |
| optimization | OptimizationJob/Result | optimization runs | job expiry/retention, not booking truth |
| recovery | RecoveryCase, ReplacementOffer | rescue cases | terminal state, not cargo truth deletion |
| warehouse | stock ledger, dock and locations | occupancy/dock boards | ledger append-only, location archive |
| marketplace | listings/match candidates | public/scoped listings | listing withdrawal/expiry, retention |
| regulatory | normative sources/jurisdiction rules | applicability | supersession, immutable provenance |
| saas-control | subscription/usage/provisioning | quotas/billing control | suspension/offboarding workflow |

**Open ownership corrections:** decide whether Order is a Commercial aggregate or a composed order view, reconcile CustomerAccount, ServiceReview and Invoice ownership in machine boundaries before persistence schema generation. CustomerAccount relationship business facts belong to Commercial, identity/grants to Tenancy; avoid two writers for the same record.

## 4. Package architecture (per module)

~~~text
kz.keruenix/
  KeruenixApplication.java
  platform/
    security/       # trusted scope, RLS transaction setup
    errors/         # existing RFC9457 contract/handlers
    pagination/     # immutable pageable/cursor primitives
    eventing/       # outbox/inbox technical adapters
  commercial/
    CommercialApi.java          # exported Java contract only
    api/                        # exported snapshots/events where explicitly named
    internal/
      domain/
        model/                  # aggregate, value objects, enums
        policy/                 # guards and invariants
        event/                  # domain event definitions
        repository/             # command persistence port
      application/
        command/                # per-use-case handler
        query/                  # list/detail read handlers
      persistence/
        jdbc/                   # domain repository adapters
        query/                  # SQL read repository
      web/
        customer/               # customer-safe controller
        provider/               # provider-only controller
        dto/                    # create/submit/list/detail/filter DTOs
        mapper/                 # strict MapStruct
      eventing/                 # outbox consumer/publisher adapters
~~~

One public owner per aggregate, no cross-module entity navigation, no shared repository base class requiring all entities to implement mutable setters. Pure domain policy does not know HTTP or SQL; web controller does not call SQL directly; application handler coordinates guards, owner repository and transaction.

**Service nomenclature:** prefer SubmitRfqHandler, AcceptQuoteHandler, SearchRfqHandler over ambiguous giant RfqService with dozens of methods. Do not create a class for each one-line delegation without testable use-case logic.

## 5. Domain and command side

- Aggregate constructors/factories enforce invariants, expectedVersion and allowed transition; avoid public mutable setters.
- Value Objects for Money/Currency, Weight, Volume, CargoUnit identity, GeoPoint (lon/lat/SRID), TimeWindow and EntityId with explicit validation and units.
- QuoteVersion immutable once issued; CarrierOffer SELECTED is not CapacityReservation.CONFIRMED; Quote ACCEPTED is not Booking CONFIRMED; GPS != Pickup/POD; Delivered != Paid.
- Each command: authenticated context resolved by server; permission/SoD, domain guard, optimistic version, transactional SQL constraint, audit + outbox.
- Idempotency ledger: server-verified scope (provider tenant + subject/customer account or explicitly shared operation owner) + command type + idempotency key, canonical payload digest, stored result; same key/different digest yields catalog IDEMPOTENCY_CONFLICT. Never replay a result to unauthorized/currently revoked requester. Retention must cover realistic retries/offline replay.
- Reservation exclusivity: owning Fleet uses PostgreSQL conditional write/row or exclusion constraint and contention tests; projected available-vehicle lists are not write guards.
- Cross-module local transaction is intentionally explicit; external carrier/bank action requires durable process manager, at-least-once/outbox/inbox and compensation/reconciliation.
- No generic HTTP PATCH which writes entity fields directly; only business-specific commands.

## 6. Repository design (command vs query)

**Domain port:** RfqRepository.loadForCommand(RfqId, TrustedScope), save(Rfq, ExpectedVersion), with explicit missing/forbidden handling. Persistence adapter may use Spring JDBC / named parameters, records or SQL mappers. Query repository returns lightweight immutable RfqListRow / RfqDetailsRow, never full aggregate graph.

**Query port:** RfqQueryRepository.search(AuthorizedRfqQuery): Slice<RfqListRow>; AuthorizedRfqQuery assembled by application only from trusted scope + user-validated filters. Repository performs tenant/customer/assignment restriction **inside SQL before sorting, limit and count**. Query services cannot query another owner's table directly; use a module-owned projection or exported owner API.

Read projection metadata: sourceEventId, sourceAggregateVersion, projectionVersion, watermark, updatedAt. Query must label stale snapshots. A projection's lag never authorizes bookings, payments or release of custody.

## 7. REST boundary & DTO/MapStruct

R0 sample (DESIGN, not implemented):

| HTTP endpoint | Purpose | Scope |
|---|---|---|
| POST /api/v1/customer/rfqs | Create customer draft RFQ | verified EXC/customer relationship |
| POST /api/v1/customer/rfqs/{id}/submit | Transition valid draft to SUBMITTED | exact allowed customer + expectedVersion + idempotency |
| GET /api/v1/customer/rfqs | My Requests list | customerAccount + provider tenant |
| GET /api/v1/customer/rfqs/{id} | customer-safe detail | per-resource authorization |
| GET /api/v1/provider/rfqs | Incoming RFQs | provider tenant + branch/assignee |
| GET /api/v1/provider/rfqs/{id} | internal detail | assigned provider staff |
| POST /api/v1/customer/rfqs/{id}/discard-draft | Optional logical delete | PENDING permission/business approval; draft only |

Permission names and state guards come from the canonical Access Governance and lifecycle contracts. In the current v2 policy, customer RFQ list and detail already have separate explicit permissions customer:rfq:list (EXT-14) and customer:rfq:read (EXT-15), which must be enforced (customer:orders:list/read are **not** substitutes). The separate POST submit endpoint is a **candidate only**, pending confirmation whether the accepted customer:rfq:create contract already includes submission or an explicit new submit permission is required. Do not infer that customer:rfq:create permits discard, approval or restoration. No DELETE/restore/submit endpoints activated without confirmed action-level policy.

**DTO taxonomy:** CreateRfqRequest, SubmitRfqRequest(expectedVersion), RfqListItemResponse, RfqDetailsResponse, ProviderRfqItemResponse, RfqSearchFilter; customer DTO must not contain provider purchase prices, margin, other account details, raw driver GPS, internal approval flags, audit-only metadata.

MapStruct under owning module; immutable Java records for immutable response/command boundaries; strict target mapping and explicit field allowlist. **Never** map caller-supplied tenantId, createdBy, approvedBy, deletedAt, price/margin overrides, state, version or assignment directly into aggregate. Use domain factory + trusted principal/policy. Mapper must not execute I/O, security checks or lazy-loading side effects.

HTTP validation occurs at boundary but business validation in domain/application persists. Return 201 + Location for creation, 200 for reads, and stable 409 on version/idempotency conflicts. API versioning must be OpenAPI-tested.

## 8. Unified filtering, sorting and pagination v1

**Default offset list:** zero-based page=0, size=20, max size=100 (configurable/benchmark), reject negative/out-of-range and unsupported sort; no silent clamping or arbitrary sorting. page/size response: items, page, size, hasNext, optional totalElements/totalPages **only when requested or inexpensive**. Count is independently permission-filtered and may be expensive; fetch limit+1 for hasNext. Never return foreign tenant record counts or leaked "not found" totals.

**Filters:** explicit typed query params per endpoint with allowlists (e.g. status, createdFrom, createdTo, assignedTo for provider only, q, customer reference as allowed). createdFrom inclusive; createdTo exclusive; ISO UTC instants with bounded interval; query length/radius cap; mandatory parameter binding and text-search escaping (prefix/fuzzy only after EXPLAIN). Semantically invalid ranges get VALIDATION_FAILED; filters never grant visibility. Do not expose arbitrary SQL column/property names.

**Sort:** allowed API names map to predefined SQL expressions; default createdAt DESC, id DESC; tie breaker id mandatory for deterministic order. Null ordering explicit. A newly inserted/updated row can move between offset pages; do not advertise offset as a stable snapshot. All list sorts and filtered fields require matching PostgreSQL indexes/perf evidence.

**Cursor/keyset:** GPS/timeline/audit/high-volume streams use (observedAt, eventId) or (occurredAt, id) stable unique tuple, directional lexicographic query, limit+1. Cursor is opaque, signed, versioned, time-limited and bound to tenant/customer scope + permission revision + filter/sort fingerprint. Keyset order predicates match index and include tenant/authorization predicate; unsigned client offsets/IDs cannot become authorization. On changed scope/filters, reject the cursor with catalog-compatible safe validation error. Cursor does not promise immutable history; use a snapshot boundary or immutable event stream when consistent export is required. No default total on cursor endpoints.

**Example provider search (lines shown separately for legibility):**

~~~http
GET /api/v1/provider/rfqs?status=SUBMITTED&createdFrom=2026-11-01T00:00:00Z&createdTo=2026-11-08T00:00:00Z&page=0&size=20&sort=createdAt,desc
~~~

~~~json
{
  "items": [
    {
      "id": "7b6a1e24-2898-4f6e-81d8-aac6499371e2",
      "status": "SUBMITTED",
      "createdAt": "2026-11-07T10:00:00Z"
    }
  ],
  "page": 0,
  "size": 20,
  "hasNext": true
}
~~~

Illustrative only. Optionally append totalElements/totalPages when includeTotal=true, based on the same authorized filters and clearly bounded read consistency.

## 9. SQL, indexes, transactions, RLS, GIS

Sample safe query (column names are *server-defined*, not interpolated from arbitrary sort input):

~~~sql
SELECT r.id, r.status, r.created_at, r.version
FROM commercial.rfq r
WHERE r.tenant_id = :trusted_provider_tenant_id
  AND r.deleted_at IS NULL
  AND (:status IS NULL OR r.status = :status)
  AND r.created_at >= :created_from
  AND r.created_at < :created_to
  AND (
    :provider_allows_all_assignees = TRUE
    OR r.assignee_id = :trusted_assignee_id
  )
ORDER BY r.created_at DESC, r.id DESC
LIMIT :size_plus_one OFFSET :offset;
~~~

This query is conceptual: generate only allowed predicates rather than universal OR/NULL forms when query plans degrade; indexes match actual predicates. **Customer view must additionally filter by verified CustomerAccount/resource grant** and project only customer-safe fields. Provider tenant is derived from the authenticated context, not caller-supplied data. Application code chooses allowed sort SQL from a static mapping. Dynamic values always use bound parameters. Large offset is rejected/redirected to cursor strategy by benchmarked cap.

Example indexes for pilot (confirm with EXPLAIN and workload):

~~~sql
CREATE INDEX idx_rfq_inbox_created_active
ON commercial.rfq (tenant_id, created_at DESC, id DESC)
WHERE deleted_at IS NULL;

CREATE INDEX idx_rfq_assignee_created_active
ON commercial.rfq (tenant_id, assignee_id, created_at DESC, id DESC)
WHERE deleted_at IS NULL;
~~~

Use one trusted transaction-scoped RLS setting per DB transaction (e.g. PostgreSQL set_config('app.tenant_id', ..., true) within transaction), never caller headers; application role NO BYPASSRLS, owner privileges addressed with FORCE ROW LEVEL SECURITY where needed; connection pool reuse A→B test mandatory. RLS on all owner/write/read tables and direct access to partitions; client portal is a scoped provider-owned read path, **not** accidental provider employee membership. Do not use a global wildcard tenant RLS claim to expose all customer accounts.

GIS searches use typed lon/lat EPSG:4326, geography ST_DWithin meters and appropriate GiST; filter tenant/grant and freshness first. Index evidence/EXPLAIN, worst-case radius, spatial aggregation leak, and performance tests required. Do not partition RFQ, booking or active finance in R0. GPS history partition RANGE(observed_at) only on actual telemetry slice, with ingest registry global dedup.

## 10. Soft Delete / Archive / Cancel / Erase — mandatory distinction

**Decision:** no universal base entity with automatic soft delete. Apply **opt-in, owner-specific policy** to master/config and eligible draft records only. Lifecycle semantics always outrank technical deletion. Four distinct actions:

| Operation | Meaning | Allowed example |
|---|---|---|
| BUSINESS_CANCEL / REVOKE / EXPIRE | authoritative business state transition; audit/outbox; obligations preserved | Booking cancelled, CapacityHold released, Membership revoked |
| ARCHIVE | hide from active operational views but preserve business record without changing truth | inactive Vehicle master, closed customer relationship |
| SOFT_DELETE | logically mark removable draft/master record with deleted_at and reversible audit trail | eligible RFQ DRAFT without binding quote |
| HARD_ERASE / PURGE | retention/legal-governed permanent erasure, references and object store lifecycle | expired permitted non-evidence data after verified holds |

**Never soft-delete:** issued/accepted QuoteVersion, Booking/CapacityReservation, Trip/Shipment/Custody/POD, signed/verified Documents, Invoice/Receivable/Payable/PaymentAllocation, immutable audit/outbox until respective retention program permits, stock ledger. Do not soft-delete an active cargo, reservation, unpaid obligation, case under dispute or legal hold. Do not implement cascade delete of shipment when user deletes a customer or vehicle reference.

**Fields for opt-in tables:** deleted_at timestamptz NULL, deleted_by UUID with trusted actor, deletion_reason_code typed value, version bigint (optimistic lock); optional deletion_request_id / retention_class per owner. Prefer no redundant is_deleted boolean. archived_at and business status are separate concepts; deleted_at alone does not express cancellation, hold, revocation or erasure. Use UTC from the authoritative database transaction for mutation; immutable audit keeps prior transitions.

**Read contract:** active list/detail/search/count/GIS/export exclude soft-deleted rows before pagination, filters and aggregation; negative queries for removed/foreign IDs use resource-hiding policy (404 where appropriate) without revealing existence; only explicitly approved admin/audit views can inspect soft-deleted rows with separate permission and scoped RLS. Caches must invalidate/segment by lifecycle and permission revision. Read models consume a deletion/restore event as **tombstone**, and rebuild cannot resurrect deleted source entries.

**Write contract:** in one owner transaction verify permission, aggregate status, no binding obligations/dependents, expectedVersion, deletion eligibility, domain event, audit/outbox, changed version and deletedAt. Duplicate same idempotency request returns prior authorized result; changed payload conflicts. Concurrent restore/delete and association race must be serialized with DB constraints/locks and tests. Restore requires separate explicit permission, business review of stale dependencies, unique-key conflict check and new version + auditable event. Technical deletion does not automatically delete related document objects or revoke existing presigned URLs; authorized document broker / bounded signed URL TTL must be evaluated.

Example for eligible, authorized draft RFQ (policy must be approved before implementation):

~~~sql
UPDATE commercial.rfq
SET deleted_at = statement_timestamp(),
    deleted_by = :trusted_actor_id,
    deletion_reason_code = :approved_reason_code,
    version = version + 1
WHERE tenant_id = :trusted_tenant_id
  AND id = :rfq_id
  AND version = :expected_version
  AND status = 'DRAFT'
  AND deleted_at IS NULL
  AND NOT EXISTS (
      SELECT 1
      FROM commercial.quote_version q
      WHERE q.rfq_id = commercial.rfq.id
  )
RETURNING id, version, deleted_at;
~~~

The DB statement alone **does not** guarantee absence of an in-flight quote creation: define a shared lock/constraint and transaction order in the owner module; independently test concurrent quote issue vs draft discard. Quote table may need explicit tenant composite reference. Never trust client supplied deleted_by or deletion flags.

**Uniqueness policy:**
- If approved business rule allows reusing a *draft-only human-facing alias* after soft delete, use a partial unique index such as UNIQUE(tenant_id, alias) WHERE deleted_at IS NULL, with tests for restore collision.
- For external_event_id, invoice number, signed reference, legal document identity, idempotency keys and booking resource exclusivity, preserve lifetime unique/invariant semantics; DO NOT add deleted_at predicate or permit duplicate physical capacity by soft deletion.
- Referential integrity remains real: prefer restrict and explicit owner-coordinated operations over automatic cascade.

**Retention/erasure:** soft delete is not personal-data erasure. Define purpose, retention schedule, local legal/contractual requirements, legal hold, audit evidence and tenant offboarding before hard purge. Purge is separately privileged audited maintenance job, after export/backup/object-store reference and legal review. Partition detach/drop with mixed tenant holds is forbidden. Existing download/backup copies and legal evidence must be accounted for. No claim of immediate erasure while copies or signed URLs remain accessible.

**No generic HTTP DELETE** for legally consequential resources. If draft removal is accepted, prefer explicit POST /.../discard-draft with expectedVersion/idempotency; restore endpoint/permission only if business demands it. UI label "Удалить" must distinguish "Удалить черновик", "Архивировать", "Отменить заказ", "Отозвать доступ".

## 11. API Errors, authorization and negative outcomes

Use [31](31-unified-error-handling-standard.md) and machine [api-error-catalog.v1.json](contracts/api-error-catalog.v1.json) **as-is**: RFC 9457 application/problem+json, stable code, requestId, timestamp, retryable, sanitized violations; one factory shared by MVC and Spring Security filter. Query/filter violations map to existing VALIDATION_FAILED; stale version and idempotency conflicts to existing 409 codes. Business-specific delete/restore problems require catalog extension review, not invented undocumented codes. For any denied request, assert **no unauthorized DB mutation, no false outbox event, no foreign field/count leak**, and correct audit entry.

Auth order: authenticated principal → resolve provider/customer relationship and tenant from trusted credentials → verify action/resource grant and SoD → RLS scoped transaction → domain guard → persistence. Resource probing should use agreed 403/404 non-disclosure policy; invalid state response must not reveal a foreign object's existence. Signed URLs, logs and metrics cannot leak PII or hidden pricing.

## 12. R0 first implementable vertical slice — BSC-001 + BSC-002

Scope: verified external customer relationship (Tenancy grants, Commercial account), create/submit RFQ, provider Incoming RFQ, customer My Requests, list/detail filters, role-sensitive DTOs, idempotency, error envelope, draft discard **as design-only pending permission**.

**R0 owner API candidates:** activateCustomerAccount, createDraftRfq, submitRfq, searchCustomerRfqs, searchProviderInbox, getRfqDetails. Do not implement Quote ACCEPT or Booking CONFIRMED in this slice; provide only typed dependency contracts without bypassing BR-01..12.

**First acceptance examples:**
1. CustomerOrg-X account EXC creates draft; same tenant but CustomerOrg-Y lists and guesses UUID: no foreign row/count/detail, even through different JDBC connections or pagination.
2. Provider Sales sees only permitted branch/assignee inbound RFQs, customer safe view never includes buy rate/margin.
3. RFQ create+submit repeated with same scoped key → exactly one logical RFQ and outbox effect; changed payload → IDEMPOTENCY_CONFLICT.
4. Paging page=0/1 with identical createdAt yields deterministic id tie ordering; unsupported sort or huge size gives sanitized Problem Details.
5. If draft discard is later approved: draft absent from active list/count and projection; active/accepted/linked/held records cannot be soft-deleted; concurrent quote issue vs discard has one legal outcome.
6. Membership/grant revoked amid cache/worker request → subsequent reads deny, no stale DTO/cursor/presigned leak outside explicitly documented TTL limitations.

## 13. Tests / CI gates

Add **SDB-001..020** design bank (machine companion contains exact identifiers); do not count these as executed tests. Map to existing AUTH-*, NEG-R0-*, TDD-SIM-* where overlapping rather than inflating test count.

| Gate | Verification | Evidence required |
|---|---|---|
| G0 Contract | story/AC/BR/owner/permission/DTO/filter/test traceability, JSON cross-ref, no new module | automated docs/JSON validation + business signoff |
| G1 Architecture | no cycles/internal imports/cross-module SQL writes, mapper constraints | ApplicationModules.verify + review |
| G2 Query | offset stable ties, cursor integrity, filter whitelist, bounded page/total, query plan | HTTP + Postgres EXPLAIN + fixture counts |
| G3 Security | 2+ tenants, multiple CustomerAccounts, resource UUID probes, tenant A→B pool switch, revoked grants | Testcontainers/PostgreSQL RLS + API |
| G4 Mutation | state/version/unique/exclusion, transaction atomic audit+outbox, duplicate/replay, side effects | concurrent DB transactions + fault injection |
| G5 Soft Delete | default exclusion, restore collisions, no deletion of legal evidence, holds, restricted reads, purge | PG locks/FK/unique/RLS + event/projection rebuild |
| G6 End-to-end | BSC-001/BSC-002 user/customer/provider flow, RFC9457 parity, metrics | exact SHA reproducible CI + real DB |

**Minimum test matrix** (all PLANNED):
- SDB-001 story → code contract traceability; SDB-002 Modulith boundaries; SDB-003 mapper overposting denial.
- SDB-004 cross-account/filter/count/RLS; SDB-005 offset tie/limit; SDB-006 cursor cannot cross scope or duplicate/skip immutable events; SDB-007 filter/sort allowlist; SDB-008 EXPLAIN/perf.
- SDB-009 soft delete excluded from list/count; SDB-010 concurrent delete/quote/restore race; SDB-011 restore uniqueness; SDB-012 no deletion of active Booking/POD/money.
- SDB-013 tenant/partner unauthorized delete/restore; SDB-014 deletion audit+outbox atomic+replay; SDB-015 tombstone/rebuild; SDB-016 retention/legal hold; SDB-017 RFC9457 errors; SDB-018 grant revoke/cache/cursor/URLs; SDB-019 offline late command; SDB-020 exact SHA E2E 2 tenants.

**CI execution evidence:** concrete test names, count, artifact/log links, branch/SHA, PostgreSQL/PostGIS version, schema migration version, no mock-only substitution for RLS/concurrency. No pass claimed until executed.

## 14. Delivery sequence and Definition of Ready / Done

**D0 Specification:** align aggregate ownership, BR signoff status, explicit deletion eligibility and role permissions, query standards; document status DESIGN only.

**D1 Foundation continuation:** existing RFC 9457 + Spring Modulith/Liquibase/PostgreSQL integration verified for partial PR-01; still qualify MapStruct/Testcontainers, trusted JWT→tenant/customer RLS binding, durable Outbox dispatcher and full FOUND-01..12. Add no unsafe public endpoints.

**D2 Tenancy + Commercial RFQ:** implement BSC-001/002 after respective business guards, migration, RLS, owner API, DTO/mapper, offset provider/customer lists, bounded filters, secure Problem Details, and integration tests.

**D3 Booking/Fleet:** add transactional capacity hold, optimistic versions, expiry race, own vs external carrier, real DB exclusion and outbox; no generic soft delete.

**D4 Execution/Tracking/Documents/Finance:** cargo custody, partial POD, permission-filtered timeline/cursor, evidence retention and verified financial reconciliation. Soft delete remains opt-in only.

**D5 Full R0 qualification:** 2-tenant + 2-customer + carrier + receiver, failure/replay, recovery, perf/index, exact-SHA CI and business/legal/finance signoff.

A slice is **DONE** only if accepted invariants, model/API/read/security/query/data-lifecycle contracts, migrations, tests, observability and rollback/recovery behavior all match; implementation without signoff is IMPLEMENTED, not QUALIFIED.

## 15. Open architectural/business decisions

1. Owner of Order and CustomerAccount ownership corrections in canonical module machine contract.
2. Actual R0 role permission for optional RFQ draft discard and separate restore; what legal/customer submission timestamp starts immutable retention.
3. Whether external RFQ can ever be erased after submission; default fail-closed = no; confirmed obligations survive account offboarding.
4. Query/number of data rows/performance SLO from pilot, including max offset window and total-count behavior.
5. Cursor expiry, role-revision policy, list snapshot semantics and export limits.
6. Data retention/PII erasure/legal hold for each class under applicable Kazakhstan contracts/law, verified with counsel.
7. Whether customer and provider can share RFQ search read models or need independent customer-safe projection; avoid exposing price, GPS or internal routing.
8. How to reconcile entity soft-delete tombstones when event consumer is delayed, rebuilt, retried or branch scope revoked.
9. Library compatibility PoC and actual Maven exact SHA before locking Java/Spring Modulith/MapStruct versions.

**Final design position:** use scenario-driven domain ownership, read/write separation, limited pagination/filter contracts, explicit DB indexes/RLS, strict mappers and opt-in soft delete. Do **not** delete business truth with a generic field or conflate archiving with cancellation. No functional implementation or CI qualification is claimed by this document.

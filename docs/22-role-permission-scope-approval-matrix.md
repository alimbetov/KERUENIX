# 22 — Role → Permission → Resource Scope → Approval Policy → TDD Acceptance

**Версия:** 1.0 / первая итерация Tenancy + Commercial. **Дата:** 2026-11-07. **Статус:** архитектурная матрица на business/security review; тесты НЕ реализованы. **Каталог бизнес-модулей:** 17, без изменений.

**Машинно-читаемый источник этой матрицы:** [contracts/role-permission-scope-approval.v1.json](contracts/role-permission-scope-approval.v1.json). Каждая строка имеет стабильные `id`, `roleTemplate`, `permission`, `resourceScope`, `approvalPolicy`, `storyId`, `acceptanceId`, `priority`. Таблицы ниже — удобное для обсуждения представление 24 политик. Следующие заходы расширяют другие домены, не создавая новую глобальную ролевую иерархию.

**Связанные документы:** [User Story Book](21-user-story-book.md), [Tenancy and identity](../idea/02-multi-tenant-and-identity.md), [Commercial Lifecycle](10-commercial-execution-lifecycle-v1.md), [TDD engineering standard](20-mapstruct-tdd-engineering-standard.md), [Requirements](04-requirements-traceability.md).

## 1. Цель и модель принятия решения

Использовать `RBAC шаблон роли + scoped ABAC + Separation of Duties + deny by default`. Реальная авторизация должна проверять все обязательные условия, а не одно совпадение роли:

```text
authenticatedPrincipal
 + activeMembership + tenant
 + explicit Permission
 + legalEntity / branch
 + aggregate owner + assignment
 + PartnerGrant + allowed fields + expiry
 + aggregate state/version + approval policy
 + request/approval actor separation
 -> ALLOW / DENY (+ audited reason)
```

**Важно:** роль — набор рекомендуемых permissions, а не обязательный job title и не безусловное право на данные. Пользователь может совмещать шаблоны (например SAL + PLN), но не утверждать свою же исключительную коммерческую операцию. Ни `TENANT_OWNER`, ни `PLATFORM_SUPER_ADMIN` не получают автоматический доступ к любой финансовой операции. Для прочих 15 доменов действие запрещено по умолчанию, пока не определена соответствующая политика.

**Источники истины:** Tenancy owns Membership/RoleAssignment/PartnerGrant/DelegationPolicy; Commercial owns RFQ/QuoteVersion/CarrierOffer and their approvals; Booking/Fleet own reservation and booking transitions. Никаких прямых SQL-записей из Tenancy в коммерческие агрегаты или наоборот.

## 2. Ролевые шаблоны первого захода

| Code | Шаблон | Назначение | R0 policy |
|---|---|---|---|
| PSA | PLATFORM_SUPER_ADMIN | Onboarding и восстановление, только control plane | Обязателен; MFA/аудит |
| TNO | TENANT_OWNER | Владение компанией и назначение администраторов | Обязателен |
| TEN | TENANT_ADMIN | Пользователи и делегированные роли | Обязателен |
| SHP | SHIPPER_AUTHORIZED_SIGNATORY | Клиентский RFQ и правомерный акцепт | Обязателен |
| SAL | SALES_EXPEDITOR | Уточнение заявки, quote draft/issue | Обязателен |
| APR | COMMERCIAL_APPROVER | Согласование исключений/лимитов | **Permission set**: можно назначить уполномоченному лицу, не создавая обязательную должность |
| PRC | CARRIER_PROCUREMENT_MANAGER | Carrier offer, выбор закупочного подрядчика | **Permission set**: можно совместить с SAL/PLN в малой компании |
| CAR | CARRIER_AUTHORIZED_MANAGER | Предложение и подтверждение от перевозчика | Обязателен для внешнего Carrier |
| FIN | FINANCE_OFFICER | Разрешённое чтение маржи/сверки | R0 finance-lite |

`TENANT_ADMIN` не может создавать `PSA` или `TNO`. Администратор компании управляет только делегируемыми разрешениями. Для `PSA` первоначальная регистрация через защищённый bootstrap, не через public signup. `APR` и `PRC` — **новые шаблоны** относительно первого списка User Story Book, а не новые бизнес-модули.

## 3. Tenancy — матрица полномочий

| Policy ID | Роль | Permission | Resource scope | Approval / guard | TDD acceptance |
|---|---|---|---|---|---|
| `TEN-01` | Platform Super Admin | `platform:tenant:create` | Подтверждённая заявка | Проверка юрлица + MFA | `AUTH-TEN-001` |
| `TEN-02` | Platform Super Admin | `platform:owner:bootstrap` | Новая компания / приглашённый | Подтверждение личности владельца | `AUTH-TEN-002` |
| `TEN-03` | Platform Super Admin | `platform:admin:bootstrap` | Инициализация компании | Отдельный onboarding approval | `AUTH-TEN-003` |
| `TEN-04` | Platform Super Admin | `platform:owner:recover` | Инцидент одной компании | Два независимых согласующих | `AUTH-TEN-004` |
| `TEN-05` | Tenant Owner | `tenant:admin:appoint` | Своя компания | Проверка полномочия + акцепт | `AUTH-TEN-005` |
| `TEN-06` | Tenant Owner | `tenant:owner:transfer` | Своя компания | Подтверждение преемника | `AUTH-TEN-006` |
| `TEN-07` | Tenant Admin | `tenant:member:invite` | Разрешённые филиалы | В пределах делегирования | `AUTH-TEN-007` |
| `TEN-08` | Tenant Admin | `tenant:role:assign` | Разрешённые роли/права | Без self-escalation | `AUTH-TEN-008` |
| `TEN-09` | Tenant Admin | `tenant:member:revoke` | Разрешённые участники | Защита последнего Owner | `AUTH-TEN-009` |
| `TEN-10` | Tenant Owner | `tenant:partnergrant:manage` | Конкретный Shipment | Scope, поля, срок, контрагент | `AUTH-TEN-010` |
| `TEN-11` | Tenant Admin | `tenant:partnergrant:revoke` | Делегированный Shipment | Проверка действующего grant при чтении | `AUTH-TEN-011` |

**Проверки:** onboarding требует верификации компании и приглашённого представителя, назначение владельца заканчивается только после принятия приглашения; операции администратора проверяют делегируемость и отсутствие самоповышения. Опасное восстановление первого/утраченного Owner требует независимого одобрения и аудита, не прямого SQL-изменения. Удаление последнего активного Owner запрещено.

**Partner grant:** Tenancy authorizes issuing/revoking narrowly scoped grants but cross-tenant cargo and quote remain available only through exported, projection-filtered domain APIs. Представитель одной компании не получает прямую сессию в PostgreSQL другого tenant.

**Практическое ограничение:** уже выданный presigned RustFS URL нельзя гарантированно мгновенно отозвать, если storage проверяет только подпись и срок. Для немедленной блокировки требуется прокси/проверка на каждом запросе либо короткий TTL и документированная остаточная экспозиция. Redis cache не подменяет проверку актуальных permissions.

## 4. Commercial — матрица полномочий

| Policy ID | Роль | Permission | Resource scope | Approval / guard | TDD acceptance |
|---|---|---|---|---|---|
| `COM-01` | Shipper / authorized customer | `rfq:create` | Свой клиентский контур | Критические сведения обязательны | `AUTH-COM-001` |
| `COM-02` | Shipper / authorized customer | `rfq:amend_draft` | Свой RFQ | Переквалификация при значимом изменении | `AUTH-COM-002` |
| `COM-03` | Sales / Expeditor | `rfq:qualify` | Назначенные RFQ | Комплектность данных | `AUTH-COM-003` |
| `COM-04` | Sales / Expeditor | `quote:draft` | Своя компания и клиент | Draft без binding effect | `AUTH-COM-004` |
| `COM-05` | Sales / Expeditor | `quote:issue` | Назначенная версия Quote | Лимит или внешнее approval | `AUTH-COM-005` |
| `COM-06` | Commercial Approver | `quote:approve_exception` | Своя компания / лимит | Отдельный от автора approving actor | `AUTH-COM-006` |
| `COM-07` | Shipper / authorized customer | `quote:accept` | Точная клиентская QuoteVersion | Акцепт правомочным лицом, version, срок | `AUTH-COM-007` |
| `COM-08` | Shipper / authorized customer | `quote:decline` | Точная клиентская QuoteVersion | Audit identity и причина | `AUTH-COM-008` |
| `COM-09` | Carrier Procurement | `carrier_offer:request` | Назначенный RFQ/партнёр | Partner grant и сокрытие sell price | `AUTH-COM-009` |
| `COM-10` | Carrier Manager | `carrier_offer:submit` | Компания перевозчика, запрос | Полномочия поставщика и срок | `AUTH-COM-010` |
| `COM-11` | Carrier Procurement | `carrier_offer:select` | Выбор подрядчика | Procurement policy; не подтверждение машины | `AUTH-COM-011` |
| `COM-12` | Sales / Expeditor | `quote:revise` | Своя выпущенная версия | Новая версия, повторное approval | `AUTH-COM-012` |
| `COM-13` | Finance Officer | `commercial:margin:read` | Своя организация | Отдельное финансовое разрешение | `AUTH-COM-013` |

**Четыре принципиально разных действия:**
1. **Prepare:** Sales может подготовить DRAFT, но Draft не создаёт договорного обязательства.
2. **Approve:** для сделки/исключения сверх разрешённых лимитов независимый Approver подтверждает решение с указанием суммы, валюты, версии и основания. Точные пороги определяет компания и юрист/финансист, система не подставляет выдуманные лимиты.
3. **Issue:** только после обязательных approvals можно выпустить immutable QuoteVersion; изменение условий — новая версия.
4. **Accept:** только уполномоченный представитель *заказчика* принимает точную неистёкшую версию; `ACCEPTED` не подтверждает Carrier capacity, Fleet reservation или Booking.

**Закупочная и продажная стороны разделены:** SAL готовит customer quote; PRC получает/выбирает CarrierOffer; CAR видит своё предложение и нужные для работы поля, но не выручку экспедитора или маржу. Выбор CarrierOffer `SELECTED` ещё не означает ресурсный `CapacityReservation.CONFIRMED`.

## 5. Approval Policy — минимальный механизм R0

Не нужен универсальный BPM/rules engine. Достаточно `ApprovalPolicy` с проверками `tenant/legalEntity + actionType + amount/currency/terms + rolePermission + authorityLimit + requesterId != approverId (для исключений) + targetVersion + expiry`. Approval decision immutable, versioned and audited.

| Policy | Trigger | Required approval | Fail closed |
|---|---|---|---|
| AP-TEN-01 | Create tenant / bootstrap owner | Verified organization + intended first owner acceptance | Unverified company/user or repeated invalid invitation |
| AP-TEN-02 | Replace inaccessible owner | Two independent platform approvers, verified evidence, MFA | No quorum / same initiator and approver |
| AP-TEN-03 | Tenant admin/owner delegation | Existing Owner authority, delegated scope and invitee acceptance | Self-elevation, wrong tenant, last Owner removal |
| AP-COM-01 | Issue Quote within authority | Valid Sales permission + current version and preconfigured policy | Missing policy or stale/invalid quote |
| AP-COM-02 | Price/credit exception or special terms | Independent authorised Commercial Approver (and finance/legal if required by verified rule) | Same requester/approver, exceeded amount, stale approval |
| AP-COM-03 | Customer accepts version | Verified authority of customer representative, exact version and terms | Expired, replaced, foreign or replayed acceptance |
| AP-COM-04 | Carrier selection | Procurement scope, verified supplier offer and compliance conditions | Selection ≠ Reservation/Booking confirmation |

**Small business:** один сотрудник может иметь `SAL+PRC+PLN`; не создавать отдельную должность. Но исключительную ставку, которую он сам подготовил, он не может сам утвердить. Нужен другой уполномоченный человек или проектируемый отдельный юридически допустимый emergency path с audit, который R0 **не** разрешает по умолчанию.

## 6. Acceptance candidates → TDD Test Bank

Все кейсы ниже — **проектные критерии для будущих тестов, не выполненные тесты**. Каждый связан с существующим или добавленным `USB-*` из User Story Book.

| Acceptance ID | Story | Проверяемое поведение (Given/When/Then на уровне результата) | План теста |
|---|---|---|---|
| `AUTH-TEN-001` | USB-PSA-001 | МФА + проверка компании обязательны; повтор CreateTenant с одним ключом не создаёт второй tenant. | JUnit + PostgreSQL RLS + HTTP/Job |
| `AUTH-TEN-002` | USB-PSA-001 | Первый Owner активируется только верным адресатом после принятия приглашения; чужой/просроченный токен отклонён. | JUnit + PostgreSQL RLS + HTTP/Job |
| `AUTH-TEN-003` | USB-PSA-002 | PSA может назначить первого Admin лишь по подтверждённой заявке; обычное назначение без основания DENY. | JUnit + PostgreSQL RLS + HTTP/Job |
| `AUTH-TEN-004` | USB-PSA-002 | Восстановление Owner требует двух разных утверждающих, доказательств компании и полного аудита. | JUnit + PostgreSQL RLS + HTTP/Job |
| `AUTH-TEN-005` | USB-TNO-001 | Owner назначает Admin только своей компании; отсутствие акцепта приглашения не создаёт действующее членство. | JUnit + PostgreSQL RLS + HTTP/Job |
| `AUTH-TEN-006` | USB-TNO-002 | Нельзя удалить последнего активного Owner; подтверждённая передача владения не оставляет tenant без владельца. | JUnit + PostgreSQL RLS + HTTP/Job |
| `AUTH-TEN-007` | USB-TEN-002 | Admin филиала А не приглашает пользователей от имени филиала Б без делегированных полномочий. | JUnit + PostgreSQL RLS + HTTP/Job |
| `AUTH-TEN-008` | USB-TEN-003 | Admin не выдаёт себе/другим owner, platform permissions или неразрешённые финансовые approval права. | JUnit + PostgreSQL RLS + HTTP/Job |
| `AUTH-TEN-009` | USB-TEN-004 | Отключение сотрудника блокирует последующие команды и фоновые действия; отозванные сессии не дают доступ. | JUnit + PostgreSQL RLS + HTTP/Job |
| `AUTH-TEN-010` | USB-TEN-001 | PartnerGrant даёт только конкретную перевозку/поля/срок; partner не читает другие документы или финансовую маржу. | JUnit + PostgreSQL RLS + HTTP/Job |
| `AUTH-TEN-011` | USB-TEN-001 | Отзыв grant запрещает новые защищённые чтения, в том числе через кеш и worker; ранее выданные signed URL имеют отдельную TTL-политику. | JUnit + PostgreSQL RLS + HTTP/Job |
| `AUTH-COM-001` | USB-SHP-001 | Клиент создаёт собственный RFQ; другой tenant не может подменить tenantId или оформить binding quote из неполных данных. | JUnit + Modulith + PostgreSQL/HTTP |
| `AUTH-COM-002` | USB-SHP-001 | Изменение существенных полей после квалификации требует повторной проверки/версии, а не скрытой мутации выпущенных условий. | JUnit + Modulith + PostgreSQL/HTTP |
| `AUTH-COM-003` | USB-SAL-001 | Sales квалифицирует только назначенный RFQ; незаполненные критические параметры требуют NEEDS_INFO, а не QUALIFIED. | JUnit + Modulith + PostgreSQL/HTTP |
| `AUTH-COM-004` | USB-SAL-001 | Draft quote не публикуется и не считается обязательством; sales чужого филиала не видит чужие коммерческие данные. | JUnit + Modulith + PostgreSQL/HTTP |
| `AUTH-COM-005` | USB-SAL-002 | Quote в рамках заранее заданного лимита может выпускаться уполномоченным Sales; сверх лимита без approval — DENY. | JUnit + Modulith + PostgreSQL/HTTP |
| `AUTH-COM-006` | USB-APR-001 | Автор исключительной цены не может сам утвердить эту же операцию даже при совмещении ролей; лимит проверяется. | JUnit + Modulith + PostgreSQL/HTTP |
| `AUTH-COM-007` | USB-SHP-002 | Акцепт выполняет уполномоченный клиент конкретной неистёкшей версии; гонка с expiry и replay не удваивает обязательства. | JUnit + Modulith + PostgreSQL/HTTP |
| `AUTH-COM-008` | USB-SHP-002 | Отказ фиксирует актора/версию/причину; другой tenant не может отклонить предложение клиента. | JUnit + Modulith + PostgreSQL/HTTP |
| `AUTH-COM-009` | USB-PRC-001 | Procurement запрашивает CarrierOffer только у разрешённого партнёра, не раскрывая цену продажи и маржу. | JUnit + Modulith + PostgreSQL/HTTP |
| `AUTH-COM-010` | USB-CAR-001 | Carrier Manager подаёт предложение по своей компании и действующему запросу, не видит чужие buy/sell условия. | JUnit + Modulith + PostgreSQL/HTTP |
| `AUTH-COM-011` | USB-PRC-001 | Выбор CarrierOffer не переводит CapacityReservation/Booking в CONFIRMED, не обходит compliance и согласование. | JUnit + Modulith + PostgreSQL/HTTP |
| `AUTH-COM-012` | USB-SAL-002 | Изменение ISSUED quote создаёт новую immutable версию и повторно требует approval при необходимости. | JUnit + Modulith + PostgreSQL/HTTP |
| `AUTH-COM-013` | USB-FIN-001 | Финансовая маржа доступна только сотруднику с явным разрешением/организационным scope, недоступна carrier/customer. | JUnit + Modulith + PostgreSQL/HTTP |

**Обязательные межсценарные негативные проверки:** `TENANT_A != TENANT_B` во всех SQL/HTTP/Jobs, неверный scope филиала, отказанный PartnerGrant, отключённая membership при старой сессии, потерянный/повторный request key, RLS пул после exception/rollback, approvals с `expectedVersion` и race `ISSUED/EXPIRED/ACCEPTED`, двойное применение одного события. Финансы и PII отделены на уровне возвращаемых полей.

**Тестовая стратегия:** TDD (Red → Green → Refactor) для чистых ApprovalPolicy/State guards и бизнес-инвариантов; Testcontainers PostgreSQL с RLS для tenant/association/locking; HTTP integration и Modulith module tests для реальных прав; E2E двух компаний для quote acceptance. MapStruct не должен писать неавторизованные `tenantId/status/approvalState` в агрегат.

## 7. Минимальный дизайн данных и API (не реализация)

- Platform: `TenantProvisioningRequest`, `Tenant`, `OwnerInvitation`, `PlatformApproval` (strictly control plane, no customer business DB access).
- Tenancy: `Membership`, `RoleDefinition` (built-in templates in R0), `RoleAssignment`, `DelegationPolicy`, `PartnerGrant`, `AccessAudit`.
- Commercial: `RFQ`, `QuoteVersion`, `QuoteApproval`, `CarrierOffer`; authority limits attached to tenant/legal entity policy snapshot; `approvedForVersion` is not a generic boolean.
- Public capabilities: `TenantOnboardingApi`, `MembershipAdministrationApi`, `PartnerGrantApi`, `CommercialAuthorizationPolicy`, `QuoteApprovalApi`; domain owns actual effects.
- Sensitive data access: `effectivePermissions = role grants ∩ delegation ∩ resource scope ∩ valid grant ∩ SoD/approval` (conceptually; permissions that require separate grant are not implied by mere role membership).
- Record `actorId, tenantId, legalEntityId, permission, targetRef, decision, reasonCode, policyVersion, correlationId` (without secret payloads) for changes and high-risk denials. Worker re-evaluates authority at execution time.

Use fixed built-in role templates in R0; custom user-defined role builder and arbitrary policy DSL deferred until actual need.

## 8. Open business decisions (blocking implementation)

- Who legally verifies first `TENANT_OWNER` and authorizes the company’s representative; how to validate identity in Kazakhstan pilot?
- Is a second platform approver available for ownership recovery? If not, define controlled break-glass and post-incident review **before** enabling recovery.
- What is an authorized customer signatory for quote acceptance: organization membership, explicit delegated authorization, or external legally effective signature?
- What thresholds/credit exposure/discount rules require approval, which entity owns policy, and how to handle currency/tax?
- May a customer initiate RFQ directly with a third-party forwarder without own full tenant? R0 needs a concrete invitation/partner-grant rule.
- Who can select carrier from the forwarder's business (procurement vs planner) and which supplier documents must be current?
- Revocation SLA for tokens, active sessions, cache, object-storage signed URLs and in-flight jobs.

**Definition of Ready for implementation:** business+security approval on these policies, traceability to `USB-*` and `KX-*`, exact event/transition contract, failure response codes and Testcontainers fixtures.

**Status:** R0 design candidate and planned TDD acceptance only. The framework, migrations, tests, deployments and business sign-off have **not** been implemented.

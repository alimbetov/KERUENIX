# 51 — S0 Platform/Tenancy: проект тестовых контрактов для архитектурного ревью

**Дата:** 2026-11-08 · **Этап:** `Scenario Design` · **Статус:** `PROPOSED_NOT_REVIEWED`.
**Без реализации доменного кода.**

Источники: [S0 32 case contracts](contracts/r0-s0-platform-tenancy-case-contracts.v1.json), [матрица 132](contracts/r0-scenario-allocation.v1.json), [FOUND-01…12](36-r0-tdd-start-pack.md), [BR/DEC](contracts/r0-decision-readiness.v1.json), [пять стадий TDD](46-r0-scenario-first-tdd-standard.md).

## 1. Границы S0 пакета и ответственность

В машинном пакете **32 case contracts**:

- **12** foundation cases `FOUND-01…12` (основной владелец PR-01, даже если проверка касается будущих доменных модулей).
- **18** основных кейсов для PR-02 (4), PR-03C (7), PR-03 (4), PR-01 (3).
- **2** сквозных E2E, принадлежащих PR-19, но затрагивающих PR-02/03/03C: `TDD-R0-E2E-01` и `TDD-R0-E2E-09`.

Каждому случаю заданы: неизменяемый исходный Given/When/Then, предложенная последовательность проверки, tenant/customer fixture, три оракула (persisted state; Outbox/Inbox/side effect; HTTP/UI), контекст RBAC/ABAC, тестовая заготовка-идентификатор и неутверждённые BR/DEC. **Test methods не созданы; GREEN не заявлен.**

## 2. Основные тестовые границы

| Область | Case IDs | Что не должно происходить |
|---|---|---|
| RLS/role/connection isolation | `FOUND-01/02/03/08/11/12` | Подмена tenant через заголовок/JWT, повторное использование GUC между транзакциями, чужая выборка в PostGIS, доступ к Customer-Y через Tenant-A RLS |
| Data and messaging atomicity | `FOUND-04/05/06/07`, `NEG-R0-041/042` | Committed Outbox без aggregate, двойной side effect после ACK loss, stale worker ACK, privileged job execution after grant revoke |
| Modulith/Liquibase/recovery | `FOUND-09/10` | Недопустимый импорт чужого persistence-кода; миграция с checksum drift; потери восстановленных записей |
| Verified identity/owner safety | `NEG-R0-001…004` | Owner invitation другого юрлица, удаление последнего owner, частичная эскалация ролей, self-approval recovery |
| CustomerAccount legal and data ownership | `TDD-SIM-05-G03-01…05`, `NEG-R0-005…008` | Неверный canonical writer, автоматическое Tenant-A employee membership, межклиентские COUNT/facets/export/cache/price disclosures |
| Revocation across channels | `TDD-SIM-34-S06-01`, `NEG-R0-006/040`, `TDD-R0-E2E-09` | Новый API/export/stream после commit revoke, ошибочное массовое отключение коллег, ложная гарантия мгновенного отзыва старого signed URL |
| Support redaction | `NEG-R0-043` | Утечка контакта, геоданных, margin или сырого payload в логах, трассировке и support UI |
| End-to-end auth consistency | `TDD-R0-E2E-01/09` | Клиент X видит ресурс Y; провайдер видит чужую очередь; Quote/Booking ошибочно подтверждаются без подписанта и capacity |

## 3. Требуемые фикстуры до S1

**`FIX-R0-PLATFORM-TENANCY-01`:** Tenant-A provider, Tenant-B unrelated, CustomerAccount X и Y внутри A; отдельные verified principals, expired/revoked JWT, grants, два независимых concurrent worker, PostgreSQL 16 + PostGIS + Liquibase с app role без `BYPASSRLS`. Включить проверку физического Hikari connection reuse и типовой rollback. Только синтетические UUID/контакты. 

Создаваемые **в S1 (пока не созданы)** тестовые наборы:
`PlatformRoleRlsTest`, `PlatformTenantScopeTest`, `JwtNegativeBoundaryTest`, `CustomerAccountAbacTest`, `OwnerInvariantConcurrencyTest`, `CustomerRelationshipContractTest`, `RevokedGrantChannelTest`, `OutboxCrashReplayTest`, `LiquibaseRestoreQualificationTest`, `ModulithBoundaryContractTest`.

Требование **RED**: тест компилируется и выполняется; в нём падает **конкретный ожидаемый инвариант**, а не отсутствующий импорт/зависимость. Для неизменяемого legacy foundation-кода можно использовать реальные имеющиеся RED/GREEN отчёты как частичное свидетельство, но не выдавать их за полностью реализованный S1 комплект.

## 4. Архитектурные проблемы для ревью

1. **CustomerAccount writer / `DEC-R0-02`** — Commercial обозначен *предложенным* владельцем CustomerAccount. В Tenancy допустимы Membership и PartnerGrant/скопированные verified references, **но не второй CustomerAccount writer**. До ADR и BR-03 binding/партнёрские grants остаются DENY/HOLD.
2. **Customer-X/Y vs Tenant RLS** — `FORCE ROW LEVEL SECURITY` с tenant-only контекстом **не разделяет двух покупателей одного provider**. Необходимо доказать CustomerAccount ABAC во всех query paths, включая COUNT, cursor, facets, exports, cache, background jobs и GIS.
3. **Membership identity** — подписанный JWT предоставляет identity evidence, но не текущие grants; `tenant_id` claim, header и body не становятся server authority. Revoke должен срабатывать для нового решения даже с тем же unexpired JWT; in-flight semantics требуют review.
4. **Invitations/SoD** — передача единственного owner должна быть атомарной, а два логина одной личности — не два независимых одобрения.
5. **Signed URLs** — после revoke запрещаем выпуск новых URL; старый ранее выданный URL нельзя объявлять мгновенно отозванным без отдельно утверждённой TTL/credential invalidation политики. Связанный контракт документов остаётся для PR-16.
6. **Background jobs** — snapshot старой роли не даёт права выполнить новую привилегированную команду. Проверять service identity + scope и не раскрывать payload в support trace.
7. **PostgreSQL custom GUC** — `set_config` и custom parameters не должны быть единственным механизмом авторизации при компрометации SQL; требуется ограниченная JDBC surface, typed queries и DB role privilege review.

## 5. Вопросы, блокирующие предметную приёмку

| Решение | Состояние | Последствие |
|---|---|---|
| `BR-03` verified provider/customer relationship | PENDING | Никакого автоматического relationship/grant |
| `DEC-R0-02` canonical CustomerAccount ownership | PENDING | Нельзя утверждать контракт AccountRegistered и второй writer |
| `DEC-R0-03` RFQ submit permission | PENDING | E2E-01 binding submit только как conditional |
| `BR-01/02/05` Quote signer, decline, issue authority | PENDING | Нет автоматического QuoteAccepted/BookingConfirmed |
| `BR-04` subscription continuity | PENDING, requires legal review | Нельзя обобщать право worker на любые действия |
| `DEC-R0-07` commercial scope | PENDING | Не открывать margin в Customer view; никаких payments |

**Решения не утверждены автоматически**. Любой положительный юридически значимый тест — условная ветка `DENY_OR_HOLD_UNTIL_SIGNOFF` до реального бизнес/юридического согласования.

## 6. Criteria for S0→S1

Для 32 случаев необходимо отдельно получить: подтверждение primary owner и роли involved PR; согласовать точные HTTP code/error payload и DB/Outbox oracles; проверить rollback/TOCTOU/stream/cache инварианты на уровне тестовых контрактов; закрыть `BR-03/DEC-R0-02` либо оставить binding-положительные ветки блокированными; присвоить ответственную QA/security review authority и ссылки на предметное ревью.

**Сейчас этот документ — S0 design artifact, а не S2 Test Review**. Никаких изменений `main`, доменных модулей, БД или права входа в production.

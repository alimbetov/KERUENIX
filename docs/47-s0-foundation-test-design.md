# 47 — Scenario Design S0 / Batch FND: FOUND-01…12

**Статус:** `S0_DRAFT_FOR_TEST_REVIEW` · 2026-11-08.
**Обязательный процесс:** [46 — Scenario-First TDD](46-r0-scenario-first-tdd-standard.md).
**Источники:** [36 — FOUND contract](36-r0-tdd-start-pack.md), [44 — FOUND-02](44-pr01-tdd-found02-tenant-isolation.md), [45 — PR-01 partial evidence](45-pr01-found03-found05-found08-review-checkpoint.md).
**Назначение:** заранее определить весь обязательный тестовый контракт Platform Foundation. **Это проектирование тестов; не утверждение, что все тесты выполнены.**

## 1. Единая синтетическая fixture

`FIX-R0-TRANSPORT-001`: Tenant-A provider, Tenant-B unrelated; Customer-X и Customer-Y в рамках одного provider; restricted application role, worker role without BYPASSRLS, separate privileged Liquibase migration role. JWT: valid issuer/audience/RS256, revoked member, expired/forged token. PostgreSQL 16/PostGIS; одна физическая Hikari connection с `maximumPoolSize=1`; два конкурирующих dispatcher. Отдельный сценарий crash before/after commit; SQL changesets V1/V2. **Никаких реальных персональных данных.**

## 2. Конкретные тестовые контракты

| ID | Given → When | Требуемый oracle: что проверять | Уровень теста | Текущий proof / пробел |
|---|---|---|---|---|
| **FOUND-01** | App role не superuser; tenant GUC отсутствует → чтение Outbox/Inbox/Audit | Нет строк другого tenant; `BYPASSRLS=false`, `FORCE RLS`; запись и DDL вне полномочий запрещены | PostgreSQL / JDBC | SQL/JDBC частично GREEN; полный контракт ролей для новых модулей впереди |
| **FOUND-02** | Внешняя Tenant-A транзакция → вложенный Tenant-B вызов; затем reuse одного physical connection | SecurityException до изменения GUC, весь outer commit откатывается; A→B→A один pg_backend_pid, B не видит A | JDBC + Hikari + PostgreSQL | RED/GREEN+physical connection подтверждены; внешний principal вне этого теста |
| **FOUND-03** | Проверенный JWT actor A; конфликтующий tenant body/header → scoped command | 403 или DENY; нет чужой записи, Audit, Outbox; JWT tenant claim сам по себе не grant | HTTP → Security → JDBC → RLS | Частичный test-only proof; persistent grants отсутствуют |
| **FOUND-04** | Доменные aggregate + Audit + Outbox в одной транзакции → ошибка до commit | Все три отсутствуют; удачный commit содержит согласованные версии; нельзя оставить phantom event | Domain + PostgreSQL + fault injection | Пока только Outbox/Audit/Inbox, нет реального доменного aggregate |
| **FOUND-05** | Committed Outbox; consumer закоммитил Inbox+Effect; отправитель упал до ACK → replay | Два транспорта/один логический effect; Outbox durable, ACK только с актуальным fencing | PostgreSQL + sender port + real adapter smoke | Test-only sender доказан, реальный transport/scheduler отсутствует |
| **FOUND-06** | Inbox E,H1 уже сохранён → replay E,H1 и E,H2 | Совпадающий replay идемпотентен, E,H2 conflict/quarantine без второго effect; нет silent overwrite | PostgreSQL + consumer tests | Digest conflict проверен; quarantine/operator recovery ещё нет |
| **FOUND-07** | Два worker одновременно claim одну запись; один теряет lease → stale ACK | Единственный активный owner/token; устаревший worker не может подтвердить/повторить side-effect | PostgreSQL concurrent tests | Claim/fencing проверен; delayed/poison job pipeline нет |
| **FOUND-08** | Customer-X/Y в одном Tenant-A; X запрашивает Y; grant отозван при действующем JWT | X не читает Y через HTTP/DB/query/cache; после revoke нет writes/Outbox; Y с разрешением работает | HTTP, Query, RLS, cache | Test-only in-memory grant proof; DB CustomerAccount scope не реализован |
| **FOUND-09** | Module-A пытается импортировать чужой repository/internal adapter → `ApplicationModules.verify()` | Изолированная негативная fixture падает именно из-за запрещённой зависимости; после исправления граф чист | Spring Modulith test fixture | Positive verify существует, negative forbidden import fixture отсутствует |
| **FOUND-10** | Пустая БД, версия Liquibase V1, версия V2 и повторный запуск → upgrade | V1→V2 без потери данных; changed checksum обнаружен; app без DDL; восстановление snapshot подтверждено | Liquibase + PostgreSQL/PostGIS + restore | Fresh/upgrade/replay/legacy Flyway guard проверены; data-preserving restore и checksum negative ещё нет |
| **FOUND-11** | Поддельный/истёкший JWT, wrong issuer/audience, foreign header → HTTP | 401/403/404 по контракту, нет установленного tenant GUC и записи в DB/Audit/Outbox | Spring Security + MockMvc + PostgreSQL | Часть с RS256 test-only прошла; production JWKS/rotation и full error matrix ещё не проверены |
| **FOUND-12** | Точки WGS84 SRID4326, meter query и чужой tenant/невалидные координаты | Geo distance в метрах; SRID/unit не путаются; foreign scoped GIS query denies; invalid coordinate rejected | PostgreSQL/PostGIS + API | Meter smoke есть; tenant-aware GIS API и negative geometry ещё нет |

**Для каждого кейса до S2 обязательны**: имя JUnit/HTTP/UI класса, моковые и реальные fixture IDs, ожидаемое PostgreSQL состояние до/после, `Outbox` эффект, запрет на чужие данные, реальная точка отказа для RED, ссылка на CI exact SHA, reviewer. Техническая ошибка компиляции не является RED.

## 3. Блокирующие вопросы Test Review

1. **Trust:** production JWT issuer, JWKS/rotation, signature policy, источники Membership и PartnerGrant; нужно ли проверять одно юрлицо в нескольких tenant.
2. **DB ownership:** кто выдаёт `keruenix.tenant_id` и как обеспечить защиту от произвольного client-controlled GUC при наличии SQL surface.
3. **Consumer contract:** будет ли внешний broker или достаточно PostgreSQL-backed dispatcher; что считать permanent poison/dead-letter и как восстановить.
4. **Recovery:** какая измеримая backup/restore fixture, что считать потерей данных и какую проверку давать на N-1→N migration.
5. **Modulith:** конкретная negative source fixture, разрешённые public interfaces между 17 модулями.
6. **GIS:** спецификация read/query ACL и customer-sensitive geometry.

Без этих ответов можно подтвердить лишь частичные технические проверки. PR-01 в [acceptance manifest](contracts/pr-acceptance-manifest.v1.json) остаётся `NOT_QUALIFIED`.

## 4. Пакет S1 после S0 Test Review

Сначала подготовить `FOUND-04` с минимальным *test-only* доменным агрегатом и атомарным rollback; `FOUND-09` negative Modulith fixture; `FOUND-10` data-preserving restore / checksum drift; `FOUND-12` tenant-scoped GeoQuery authorization. До кода каждого блока — тестовый RED и независимая проверка его оракула. Реализацию production Tenancy запускать только после Test Review для PR-02/03.

**No Payments / No AR/AP / No bank gateways remains binding.**

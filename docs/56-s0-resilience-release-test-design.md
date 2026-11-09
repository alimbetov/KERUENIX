# 56 — S0 Resilience, Recovery, Cross-role E2E и Release Qualification

**09.11.2026 · Этап: Scenario Design · Status: `PROPOSED_NOT_REVIEWED`.**
[29 машинных GWT/оракулов](contracts/r0-s0-resilience-release-case-contracts.v1.json) включают **18 основных** PR-18/PR-19, **7 зависимых** cross-owner и **4 локальных release qualification** сценария PR-20. Это план тестов, не отчёт о завершённых приемочных испытаниях.

## 1. Проверяемые ключевые сценарии

| Узел | Действия | DB/Outbox/HTTP oracle |
|---|---|---|
| **PR-18 Jobs/Resilience** | Outbox commit → consumer commits Inbox + effect → publisher crashes before ACK → lease expiration → replay | Доставка at-least-once, **один** авторитетный логический эффект; ACK только по действующему fencing. Outbox, audit и custody не теряются; poison/retry не превращается в silent drop |
| **PR-18 Scoped safety continuity** | Во время активной передачи груза tenant suspended, водитель пытается завершить обязательный POD, оператор пытается создать Booking | Сохранить доказательства/действующего custodian; **никакого общего обхода auth/RLS**. Только отдельно утверждённая `BR-04` mandatory-continuity операция. Новый Booking/Quote — DENY |
| **PR-18 Revocation under load** | Токен и queued job выданы ранее, grant отозван, consumer и stream продолжают работать | Новый privileged write/export/stream запрещён после authoritative revoke; stale snapshot не доказывает право; denied job audit redacted |
| **PR-19 Cross-role acceptance** | Девять актуальных E2E: Invite/RFQ/Quote; external carrier; own-fleet; POD 8/10; cancel vs custody; suspension; assisted RFQ; revoke+URL; carrier withdrawal | Все роли/права/immutable versions согласованы, source-of-truth подтверждён в БД; ни ложного BookingConfirmed, ни ShipmentDelivered при частичной доставке |
| **PR-20 Recovery** | Restore известного N-1 snapshot → Liquibase upgrade → сравнение digest/count/constraints | Доказанная целостность RLS, исходных событий и cargo evidence, ни потери data, ни ложных статусных переходов. Отдельный privileged migration process |
| **PR-20 Release digest** | Сопоставление CI exact SHA, image digest, SBOM и запущенного staging binary | Не считать passing тесты другого коммита квалификацией. При несовпадении — **NO-GO** |
| **PR-20 Measured SLO** | Нагрузочный пилот и аварийный restart/job replay | p95/uptime/RPO/RTO оцениваются **по измерениям**, не выдумываются. Неаттестованные цели остаются NO-GO/OPEN |
| **PR-20 Pilot** | Две компании с RLS/ABAC; отдельно 8/10 PARTIAL и полный подтверждённый 10/10 | Никаких утечек, нет phantom full delivery, private review eligibility только по независимой проверке завершённой услуги |

## 2. Уточнение границ R0 и отказов

- **Роли:** системные jobs не получают бесконечные права по old JWT или origin event. Scope определяется владельцем ресурса и текущей политикой; при revoke любой новый небезопасный side-effect запрещён.
- **Согласованность:** Outbox/Inbox — at-least-once delivery, idempotency по `eventId + digest + tenant + consumer`; нельзя обещать exactly-once transport или автоматически запускать компенсирующую операцию без authority.
- **Fallback:** outage BR/Legal/Identity provider не разрешает потерять доказательства, но **не** включает `permitAll`; durability и ограниченная recovery процедура должны быть проверяемыми отдельно.
- **Data platform:** Testcontainers/реальный PostGIS, Liquibase fresh/upgrade/checksum, snapshot recovery; `FOUND-10` дополняется pilot restore. Требуются реально измеренные recovery показатели.
- **Релизная приёмка:** test pass ≠ business signoff. Документы BR/DEC, юридические профили подписи, владельцы и security review остаются явными gate. Никакого автоматического `QUALIFIED` от документационного CI.

## 3. Готовность Test-First

Предложенные S1-наборы: `OutboxInboxCrashReplayTest`, `SuspendedTenantContinuityTest`, `RevokedGrantWorkerTest`, `FullR0RoleJourneyTest`, `PostgresSnapshotRecoveryTest`, `ReleaseDigestAttestationTest`, `TwoTenantPilotE2ETest`. Все должны быть исполняемыми и иметь настоящий RED на целевом поведении, не только моковый провал или несуществующий импорт.

**Открытые бизнес-решения:** прежде всего `BR-04` (юридически допустимое safety continuation), `BR-09/10` (Custody/POD) и оставшиеся `BR/DEC`, от которых зависят девять E2E. Положительные действия остаются условными.

**NO PAYMENTS / NO AR/AP / NO bank integration.** Рабочая ветка не мержится в main до человеческого ревью и evidence.

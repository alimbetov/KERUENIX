# 57 — S0 полная инвентаризация R0: cross-pack coverage и реальные блокеры

**09 ноября 2026 · Статус: `S0_DESIGN_PACKAGES_COMPLETE_DRAFT` / `NOT_REVIEWED`.**
Этот документ **не закрывает S0** и не разрешает запуск доменной реализации. Он доказывает только, что **для каждого применимого канонического сценария есть ровно один основной проект теста** и все 26 PR имеют источниковый или дополнительный test goal.

**Machine controls:** [all S0 batch contracts](contracts/r0-scenario-allocation.v1.json), [пятиэтапный порядок](46-r0-scenario-first-tdd-standard.md), `scripts/validate_s0_full_coverage.py` и mutation tests `scripts/test_s0_full_coverage.py`.

## 1. Сводный охват и этап

| Единица учёта | Количество | Интерпретация |
|---|---:|---|
| Исторические сценарии R0 | **132** | 121 действующий + 11 retired из запрещённой области платежей |
| Действующие R0 с единственным primary S0 contract | **121 / 121** | Только проект оракулов; никакой бизнес-GREEN |
| `FOUND-01…12` | **12** | Существующая foundation проектная матрица; частичные реальные CI ранее ≠ общий S0 Test Review |
| `SIG-01…18` | **18** | Документные подписи/authority, реальные NCA и юридические профили pending |
| `PAY-ABS-01…06` | **6** | Негативные контрактные проверки на отсутствие платежной функциональности |
| Новые локальные сценарии сверх исходных 132 | **16** | Cargo 6, Cost 4, Release 4, Governance 2 |
| Всего уникальных ID, включая retired | **184** | 132 + 12 + 18 + 6 + 16, **не** число исполняемых тестов |
| Вхождения в шесть доменных S0 пакетов | **197** | 121 primary, 32 cross-owner impacted, 12 FOUND, 32 локальных/подписных |
| PR с хотя бы одним case goal | **26 / 26** | Включая PR-00/06S/08/17/20 за счёт дополнительных контрактов |
| `BR/DEC`, ожидающие человеческого решения | **20 / 20** | Ни один не утверждён документационным CI |
| Проведённый Test Review с людьми | **0** | Нужны фактические владельцы, QA/Security/Domain, бизнес/юридические решения |

Здесь **S0 пакеты представлены полностью как проекты**: согласование и реальные RED/JUnit/E2E ещё не выполнены.

## 2. Шесть пакетов Scenario Design по слоям

| Пакет | PR/Module | Primary | Cross-owner | Дополнительные в пакете | Документ |
|---|---|---:|---:|---:|---|
| **Platform/Tenancy** | PR-01/02/03C/03 | 18 | 2 | 12 FOUND | [51](51-s0-platform-tenancy-test-design-review.md) |
| **Commercial** | PR-04/05/06/06S/07/11 | 30 | 9 | 18 SIG | [52](52-s0-commercial-test-design-review.md) |
| **Cargo/Compliance/Fleet/Booking** | PR-08/09/10V/10/12/12C | 27 | 4 | 6 Cargo | [53](53-s0-cargo-fleet-booking-test-design.md) |
| **Execution/Custody/POD** | PR-13/14 | 22 | 3 | 0 | [54](54-s0-execution-pod-test-design.md) |
| **Tracking/Documents/Cost** | PR-15/16/16R/17 | 6 | 7 | 4 Cost | [55](55-s0-tracking-documents-cost-test-design.md) |
| **Resilience/Release/E2E** | PR-18/19/20 | 18 | 7 | 4 Release | [56](56-s0-resilience-release-test-design.md) |

Остальные **6 PAY-ABS + 2 PR00-GOV** находятся в [extension GWT inventory](contracts/r0-s0-extension-gwt.v1.json) как отдельные архитектурные проверки. Они не добавляют вторых владельцев доменным агрегатам.

## 3. Требования, которые ещё НЕ завершены для квалификации S0

1. **BR/DEC: 20 pending.** Нельзя включать binding positive RFQ Submit, QuoteIssued/Accepted, CarrierCommitted, CapacityConfirmed, CustodyConfirmed, PODComplete или private review до утверждения конкретных authority/rule/legal profiles. Negative fail-closed тесты проектировать можно.
2. **Проверка семантики оракулов.** Проекты содержат DB/Outbox/API/UI проверки, но **77 исходных DB и 77 Outbox** ожиданий были дополнены проектными формулировками и ещё не прошли предметное подтверждение owner. Нельзя скрывать это за зелёным CI.
3. **Case ownership/PR linkage.** **67 кейсов** первоначально не были записаны в canonical `criticalCaseIds`; предложенные назначения должны быть проверены техническим руководителем модулей.
4. **E2E Given/When.** Девять маршрутов имеют роль-ориентированные проекты [49](49-s0-e2e-test-design.md), но не авторизованный бизнес-процесс и не полноценный запущенный E2E тест.
5. **Точные HTTP/error contract.** Назначить RFC9457 code, expected status и assertions для каждого `DENY/HOLD/CONFLICT`. Пример 401 vs 403 vs nondisclosing 404 зависит от API политики и разграничения ресурсов.
6. **Интеграции.** NCA/EDS доверие, внешние provider scopes, signed URL TTL/revocation, cargo classification и Kafka/Outbox transport (если будет выбран) не имеют внешнего production proof.
7. **Конкурентность и recovery.** Требуются SQL constraint/lease order, реальный PostgreSQL/PostGIS, crash injection, восстановление из snapshot, точные digest, measured RPO/RTO/SLO. Документационный run не воспроизводит рабочую перевозку.
8. **Релизный пилот.** Две компании и полный жизненный цикл должны быть приняты по одному exact SHA; 8/10 остаётся partial и не даёт review eligibility. Полный 10/10 — отдельная завершённая ветка.
9. **No Payments.** Ни REST gateway, ни AR/AP, ни paid statuses, ни bank callbacks, ни internal invoice issuance. PAY-ABS contract must enforce scope.

## 4. Процедура ближайшего технического и бизнес-ревью

**Перед S1** последовательно принять S0-модель по шестёрке пакетов 51→52→53→54→55→56. Для каждого составить review evidence: согласованные case IDs, owner module и PR, test oracle (DB/Outbox/UI), actor/customer scope, race/replay/failures, конкретные GWT и разрешённые/запрещённые состояния, версию ТЗ, reviewer authority и дату. **Документационный CI не может поставить подпись.**

После этого **S1 Test-First**: создать реально компилируемые JUnit + Testcontainers/PostGIS/HTTP/security/concurrency и Flutter/web E2E/fixture harness **до новой доменной реализации**, получить доказанный RED на отсутствующем поведении; затем **S2 Test Review** проверить сам тестовый набор. Только после S2 разрешается S3 Implementation (RED→GREEN) и S4 qualification на exact SHA.

Первым S1 пакетом разумно выбрать fail-closed security/foundation и PR-04 RFQ Draft, без binding RFQ Submit до `DEC-R0-03`. Тесты на отказ в доступе и unit conservation можно готовить даже при pending business decisions, но не объявлять позитивное юридическое согласование.

## 5. Что зафиксировано, а что нет

- Machine CI доказывает **сохранность исходного контракта, единственность primary owner, полноту инвентаризации и отсутствие фиктивного согласования**.
- Machine CI не доказывает исполняемые RED-тесты, backend End-to-End, юридическую силу ЭЦП, физическую доставку или production readiness.
- PR #1 остаётся Draft, `main` не меняется.

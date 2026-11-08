# 46 — KERUENIX: Scenario-First TDD (обязательный порядок R0)

**Решение от 2026-11-08. Статус:** процесс закреплён; реестр S0 — черновик, тестовое ревью и полный test-first набор НЕ завершены.

Источники: [реестр 168 ID](contracts/r0-scenario-first-test-plan.v1.json), [84 базовых R0](contracts/r0-tdd-scenarios.v1.json), [48 негативных](contracts/r0-negative-scenarios.v1.json), [12 FOUNDATION](36-r0-tdd-start-pack.md), [дорожная карта](contracts/tdd-development-roadmap.v1.json), [acceptance manifest](contracts/pr-acceptance-manifest.v1.json).

## S0 — результат инвентаризации и предложенное распределение

[48 — Review матрицы 132 сценариев по всем 26 PR](48-r0-s0-scenario-allocation-review.md) и [машинная матрица ownership, BR/DEC и тестовых оракулов](contracts/r0-scenario-allocation.v1.json). Из 132 исторических R0 case ID активны 121, **11 payment-related retired**; у 5 PR нет собственного основного кейса из исходного банка. Ожидания DB/Outbox, указанные в матрице, являются **проектными**, не полученным бизнес-approval. Формальный Test Review ещё не проведён. Поэтому S0 не считается закрытым, а переход к реализации новых доменных модулей запрещён.

## Обязательный процесс

| Этап | Содержание до следующего этапа | Review gate |
|---|---|---|
| **1. Scenario Design** | Сначала спроектировать **все применимые R0-сценарии**: happy path, denied/negative, alternative, concurrency, idempotent replay, timeout/crash/recovery, offline, tenant/customer scope | Все применимые сценарии классифицированы, есть actor, module owner, BR/DEC, PR, fixture, Given/When/Then, DB/Outbox/UI oracle; платежные retired отдельно |
| **2. Test-First** | Создать **автоматизированные тесты и синтетические фикстуры до бизнес-кода** соответствующего модуля | Unit/API/DB/security/E2E harness компилируется и исполняется, RED означает отсутствие поведения, а не ошибку сборки; тестовый набор пока может оставаться RED |
| **3. Test Review** | Технический аудит полноты и точности тестовых ожиданий относительно ТЗ; негативные/пограничные случаи, Modulith границы, RLS, юридическая допустимость | Domain/API/security/QA reviewers, фиксированный evidence, бизнес/юридические BR/DEC остаются PENDING до реального решения; binding-поведение по умолчанию DENY |
| **4. Implementation** | Только теперь реализуется код по готовой матрице: Liquibase → Domain → Application → API/UI → Event/Integration | Небольшие RED→GREEN-коммиты; **запрещено** подгонять тесты под реализацию, переписывать oracle без отдельного повторного Review |
| **5. Refactoring & Qualification** | Рефакторинг без изменения согласованных ожидаемых результатов, полная регрессия и приёмка больших узлов | Exact-SHA CI, PostgreSQL/PostGIS, cross-company E2E, восстановление, ревью; статус PR изменяется только при реальных approval/evidence |

**Последовательность обязательна.** Не начинать новую бизнес-операцию до готовности её S1+S2. На этапе S0 можно охватить весь R0 заранее, но исполняемые тестовые пакеты S1 создавать модуль за модулем **до** кода соответствующего модуля. Это не означает создавать сотни неисполняемых `@Disabled` методов — они не доказывают TDD.

**Дополнение S0:** [48 — распределение 132 кейсов по 26 PR](48-r0-s0-scenario-allocation-review.md) и [49 — девять полных GWT проектов cross-role E2E](49-s0-e2e-test-design.md). Эти проекты не подтверждены юридически, не являются тестовыми прогонами и не открывают Implementation.

## Исходная инвентаризация

- 60 blocker policy + 14 safety + 10 cross-role E2E + 48 negative/failure = **132 ранее описанных** сценария R0. Это проектные спецификации, не 132 JUnit-теста.
- Отдельно **12 FOUNDATION** cases `FOUND-01…12`; часть уже проходила локальный RED/GREEN на реальном PostgreSQL, но всё PR-01 остаётся `NOT_QUALIFIED`.
- **18 SIGNATURE** `SIG-01…18` и **6 NO-PAYMENT-ABSENCE** `PAY-ABS-01…06` — только candidate ID; полные сценарии, оракулы и ownership требуют S0-детализации.
- Сводный реестр: **168 ID**. Нельзя называть это 168 готовыми автоматизированными тестами.
- 11 исторических payment-related case IDs из Roadmap отмечены `RETIRED_NO_PAYMENTS`. Это не deferred R1/R2. KERUENIX не реализует платежи, AR/AP, банк/webhooks или статусы PAID/SETTLED.

## Шаблон тестового контракта

Для каждого применимого кейса: stable ID, version, actor, разрешённая операция, resource, tenant, CustomerAccount, owner, BR/DEC, PR, `Given/When/Then`, ожидаемый HTTP result, доменный state transition, точный DB/Outbox/Inbox/Audit/ReadModel oracle, UI observation, negative/race/replay/crash variants, fixtureRef, test class/method, CI SHA, reviewer authority, статус исполнения.

**Ожидаемый отказ нужно доказывать на трёх уровнях:** возвращённая ошибка + отсутствие запрещённой записи в БД + отсутствие ложного Outbox/внешнего эффекта. Для статусов `BR/DEC PENDING` разрешено проектировать и автоматизировать fail-closed DENY/HOLD; юридически значимые позитивные переходы не активировать.

**Фикстура:** `FIX-R0-TRANSPORT-001`, синтетические tenants A/B/C/Z, два CustomerAccounts X/Y одного provider, 10 грузовых единиц с 8 доставленными и 2 оставшимися, два пересекающихся capacity holds, stale grant, signed/forged JWT, failure injection и offline replay.

**Тестовые уровни:** Pure JUnit/Property на aggregate инварианты; Modulith.verify на импорт/границы; Spring HTTP на security/error/DTO; реальный PostgreSQL/PostGIS и Liquibase через Testcontainers или изолированную CI DB; consumer/Outbox crash+replay; NCA/EDS provider contract + real sandbox; браузерный E2E/driver offline; backup/restore, perf и release evidence.

## Пакеты S0 → S1 по порядку рисков

1. **FOUND + Tenancy:** RLS, JWT, CustomerAccount, revoke, module graph, Liquibase migration и recovery (PR-01..03).
2. **Commercial:** RFQ Draft→Submit, Inbox, QuoteVersion, signing/grants и отрицательные переходы (PR-04..07).
3. **Capacity + Booking:** cargo/compliance, overlapping holds, carrier commitment, cancellation (PR-08..12C).
4. **Custody + POD:** Pickup 10 units, partial POD 8/10, offline dedup, signed evidence (PR-13..14).
5. **Tracking + Documents + Cost:** bounded location, immutable originals, commercial cost without settlement (PR-15..18).
6. **Cross-role and Release:** ten E2E candidates, legal signoff, restore and exact release SHA (PR-19..20).

## Как фиксировать ревью

Каждый Test Review получает ID и пакет: case IDs, BR/DEC status, module owner, ссылки на тесты, негативные доказательства, контроль порта интеграции, замечания, reviewer + дату. **Кандидат на GREEN** имеет ссылку на тестовый запуск exact SHA, а не только Markdown. Непринятые юридические решения не заполнять фиктивными утверждениями.

**Текущее положение:** реестр S0 сформирован автоматически из оригинальных источников; для большинства из 132 сценариев применимость к PR ещё требуется установить, E2E Given/When остаётся неполным, SIG/PAY-ABS требуют детализации. До закрытия S0/S1/S2 новый доменный functional development не квалифицировать. Уже выполненные PR-01 TDD эксперименты сохраняются как отдельное частичное evidence в [44](44-pr01-tdd-found02-tenant-isolation.md) и [45](45-pr01-found03-found05-found08-review-checkpoint.md).

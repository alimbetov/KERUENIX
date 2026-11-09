# 48 — S0 Scenario Allocation Review: 132 R0 сценария → 26 PR

**2026-11-08 · Статус `S0_PROPOSED_FOR_REVIEW` · НЕ APPROVED.**

Техническое решение KERUENIX: Scenario Design → Test-First → Test Review → Implementation → Refactoring & Qualification ([ТЗ 46](46-r0-scenario-first-tdd-standard.md)). Этот документ — результат **только Scenario Design**. Ни один новый доменный use case не реализован, ни один сценарий не считается тестом GREEN.

**Машинная матрица с 132 case ID, первичным PR и тремя оракулами:** [r0-scenario-allocation.v1.json](contracts/r0-scenario-allocation.v1.json). Canonical source: [84 GWT + E2E](contracts/r0-tdd-scenarios.v1.json), [48 negative](contracts/r0-negative-scenarios.v1.json), [Roadmap 26 PR](contracts/tdd-development-roadmap.v1.json), [BR/DEC ledger](contracts/r0-decision-readiness.v1.json).

## 1. Результаты полной предварительной инвентаризации

| Проверка | На дату подготовки | Что это означает |
|---|---:|---|
| Все исходные R0 case ID | **132 / 132** | 60 blocker + 14 safety + 10 E2E + 48 negative |
| Действующие случаи с предложенным основным PR | **121 / 121** | Распределены по canonical owner, но ещё не прошли Test Review |
| Retired payment-related cases | **11 / 11** | Никогда не переносить в R1/R2; отсутствие платежей контролируют PAY-ABS |
| PR-срезы, включённые в матрицу | **26 / 26** | Есть единая отчётность, но у части нет собственного позитивного/отрицательного кейса |
| Сценарии без полноценного Given/When/Then | **9** | Необходимо дописать role-by-role E2E steps |
| Без отдельного исходного DB oracle | **77** | Приведён **проект** ожидаемого DB-поведения, нужна проверка владельца |
| Без отдельного исходного Outbox/side-effect oracle | **77** | Приведён **проект** ожидаемых эффектов; пока не утверждён |
| Без прямого criticalCaseId anchor в Roadmap | **67** | Привязка к PR предложена по смыслу, нужна предметная проверка |
| Затронутые неутверждёнными BR/DEC | **111** | Консервативная зависимость, не разрешение выполнять положительные операции |
| Реальных утверждений BR/DEC | **0 / 20** | Только stakeholder workshops, не CI, могут утвердить бизнес-правила |

Важно: 111 включает связанные PR через `impactedPrs`, поэтому это индикатор **потенциального влияния**, а не число юридически заблокированных test method. Для негативных сценариев разрешено проектировать DENY при ожидающем BR; положительные binding-команды нельзя активировать.

## 2. Предварительная матрица по всем PR

| PR | Owner | Основных сценариев | Затронутых сценариев | Ключевая работа Test Review |
|---|---|---:|---:|---|
| PR-00 | architecture | 0 | 0 | Требуются отдельные doc/ADR/BR CI-сценарии (не входят в 132) |
| PR-01 | platform | 3 | 3 | Привязать FOUND-01…12, recovery, broker/effect |
| PR-02 | tenancy | 4 | 5 | Invite, principal, owner transfer, SoD |
| PR-03C | commercial | 7 | 9 | CustomerAccount canonical writer / DEC-R0-02 |
| PR-03 | tenancy | 4 | 8 | Grants, revoke, Customer-X/Y |
| PR-04 | commercial | 2 | 6 | RFQ Draft, assisted origin и полный API/UI contract |
| PR-05 | commercial | 1 | 6 | RFQ submit permission / DEC-R0-03 |
| PR-06 | commercial | 6 | 9 | QuoteVersion immutability, approvals |
| PR-06S | platform | 0 | 3 | Нужны все 18 SIG-GWT, signer authority, evidence |
| PR-07 | commercial | 12 | 15 | Accept / decline, expired/superseded, BR-01/02/05 |
| PR-08 | cargo | 0 | 0 | Нужен собственный пакет CargoProfile/HandlingUnit позитивных и негативных GWT |
| PR-09 | compliance | 9 | 9 | UNKNOWN/expired rule/HOLD |
| PR-10V | fleet | 1 | 3 | Реестр vehicle combination и локальные регрессионные тесты |
| PR-10 | fleet | 9 | 12 | Exclusive holds, concurrent confirmation, TTL |
| PR-11 | commercial | 9 | 12 | Carrier offer/withdraw/commitment |
| PR-12 | booking | 1 | 7 | BookingConfirmed guard, source-of-truth/DEC-R0-01 |
| PR-12C | booking | 7 | 8 | Cancel approval, custody disposition, BR-11 |
| PR-13 | execution | 11 | 14 | Offline custody, stale assignment, recovery |
| PR-14 | execution | 11 | 13 | POD 8/10, returned two units, immutable proof |
| PR-15 | tracking | 2 | 5 | Tenant-aware location, stale projection/GPS |
| PR-16 | documents | 2 | 7 | Original object hash, signed-link TTL/revoke |
| PR-16R | commercial | 2 | 2 | Complaint/review separation, verified completion |
| PR-17 | finance | 0 | 2 | CostEstimate/CommercialCostReport позитивные GWT, **NO PAYMENTS** |
| PR-18 | platform | 9 | 14 | Jobs, retry/revocation, continuity, DLQ |
| PR-19 | cross-functional | 9 | 13 | Полные сквозные E2E и 8/10 partial versus 10/10 |
| PR-20 | release | 0 | 2 | Recovery drill, SLO, release digest и пилотные evidence (локальные сценарии) |

**Смысл колонок:** primary owner отвечает за oracle и контракт теста. `impactedPrs` включает критические связи из Roadmap, но не передаёт владение другим модулям. 26 PR не означает, что у каждого уже достаточно сценариев; таблица намеренно показывает нули.

**Детализация cross-role E2E:** [49 — девять GWT проектов](49-s0-e2e-test-design.md) и [машинный пакет actor/given/when/then/oracle](contracts/r0-e2e-s0-draft.v1.json). Это уменьшает проектный пробел по E2E, **но не меняет отсутствие согласования**: девять Given/When по-прежнему требуют Test Review, и исходный банк намеренно сохранён неизменным.

## 3. Проекты уточнённых оракулов: пример высокорисковых сценариев

| Case ID | DB/state oracle — проект для ревью | Event/side-effect oracle |
|---|---|---|
| `TDD-SIM-13-G01-01` | Только конкретный QuoteVersion меняет состояние при подтверждённой подписи; старый hash не годится | Не больше одного QuoteAccepted и неизменяемый original evidence |
| `NEG-R0-005` | Customer-Y не видит count/list/export Customer-X внутри provider Tenant-A | Никакого disclosure через размеры выборки, проекции, кэши |
| `NEG-R0-017` | Два перекрывающихся capacity holds не могут одновременно commit | Не должно быть двух CapacityConfirmed на один эксклюзивный ресурс |
| `TDD-SIM-19-G13-02` | UNKNOWN compliance = HOLD, не READY/BOOKED | Нет события допуска к перевозке |
| `TDD-R0-E2E-04` | 8 принятых, 2 — named custody/disposition, Shipment не DELIVERED | Дубли offline не меняют количества, POD original неизменяем |
| `NEG-R0-026` | Повтор eventId c новым digest → conflict/quarantine | Не допускается второй custody handover |
| `NEG-R0-032` | После grant revoke новые ссылки запрещены; ранее подписанная ссылка ограничена TTL по согласованной политике | Нельзя объявлять немедленный отзыв уже выданного URL, пока это технически не доказано |
| `NEG-R0-047` | Complaint не переписывает POD и не порождает refund | Событие финансового возврата вне продуктового scope |

Точные machine-орacles для **каждого из 132 ID** представлены в JSON как `expected.dbOracle`, `expected.outboxOracle`, `expected.httpUiOracle`, с пометкой `PROPOSED_PENDING_REVIEW`. Они не подменяют исходное `canonicalThen`.

## 4. Дефекты и незакрытые решения S0 (блокируют финальный Test Review)

1. **9 E2E:** дополнить Given/When шагами, ролями, временной шкалой, командными UUID и фактическими состояниями. Нельзя считать описанный journey полноценной тестовой процедурой.
2. **77 + 77 Oracle:** подтвердить смысл DB/Outbox ожиданий владельцами, особенно для race/replay и разрешённых компенсаций. Их нынешний статус — проект, не принятый контракт.
3. **67 распределений вне criticalCaseIds:** провести manual review; например `TDD-SIM-29-S25-01` касается issue/review и может требовать разделения владельцев между Execution и Commercial.
4. **PR-08:** спроектировать локальные тесты CargoProfile, handling units, weight/quantity, classification version; затем включить в S0 реестр дополнительных кейсов, не переименовывая исходные 132.
5. **PR-06S:** раскрыть 18 `SIG` кандидатов в full GWT с проверкой NCA server-side certificate/authority, отказом revoked/expired/delegated wrong-signer, portable originals. Юридический signoff остаётся внешним.
6. **PR-17:** добавить позитивные кейсы commercial costing и внешнего accounting reference при отсутствии payment/AR/AP/PAID/SETTLED.
7. **PR-20:** определить отдельный release qualification suite: backup restore, exact SHA, SBOM, SLO, pilot UAT, как тестовые сценарии с GWT.
8. **BR-01…12, DEC-R0-01…08:** не утверждены. До принятия разрешается проектировать fail-closed негативные тесты, но нельзя считать юридически значимый positive transition доступным.
9. **11 RETIRED:** позитивные payment-тесты не оживлять, разработать `PAY-ABS-01…06` вместо них.
10. **Фикстуры:** для каждого case ID назначить independent setup и failure injection, где необходимы concurrency/offline/revoke; запрещено ссылаться на неверифицированный общий success fixture вместо реальной проверки.

**Дополнительные S0 GWT для PR без primary:** [50 — 40 проектов тестовых контрактов](50-s0-local-gap-test-contracts.md), [машинный перечень](contracts/r0-s0-extension-gwt.v1.json). Содержит 24 уже существовавших SIG/PAY-ABS candidate ID и 16 новых локальных PR-00/08/17/20 case ID. Наличие GWT **не означает согласования** и не меняет неизменный банк 132.

**S0 пакет Platform/Tenancy:** [51 — разбор 32 тестовых контрактов](51-s0-platform-tenancy-test-design-review.md) и [машинные оракулы](contracts/r0-s0-platform-tenancy-case-contracts.v1.json) (12 FOUND + 20 active/impacted R0). Статус `PROPOSED_NOT_REVIEWED`; предложенные проверки RLS/ABAC, revocation, concurrent owner и Outbox не являются утверждёнными тестами или юридическим решением.

**S0 Commercial:** [52 — 57 коммерческих case contracts](52-s0-commercial-test-design-review.md) + [machine oracle matrix](contracts/r0-s0-commercial-case-contracts.v1.json). Учитываются RFQ/Quote/EDS/CarrierOffer, 9 cross-owner зависимостей. Статус `PROPOSED_NOT_REVIEWED`, никаких новых обязательств или подписей от зелёного CI.

**S0 Cargo/Fleet/Booking:** [53 — 37 GWT/oracle contracts](53-s0-cargo-fleet-booking-test-design.md) + [machine matrix](contracts/r0-s0-cargo-fleet-booking-case-contracts.v1.json). Все 27 primary + 4 cross-owner + 6 Cargo local checks пока ожидают review; binding-переходы до BR/DEC остаются `DENY/HOLD`.

**S0 Execution/Custody/POD:** [54 — проект 25 сценариев](54-s0-execution-pod-test-design.md), [машинные DB/Event/UI оракулы](contracts/r0-s0-execution-pod-case-contracts.v1.json). Согласование BR-09/10 и DEC-R0-08 остаётся PENDING; запрещено приравнивать partial POD 8/10 к полностью доставленному грузу.

**S0 Tracking/Documents/Commercial Cost:** [55 — 17 контрактов](55-s0-tracking-documents-cost-test-design.md) + [machine oracles](contracts/r0-s0-tracking-documents-cost-case-contracts.v1.json). Stale GPS, immutable original, URL TTL, PrivateReview eligibility и NO PAYMENTS остаются обязательными review-факторами.

**S0 Resilience/Release:** [56 — 29 предложенных тестовых контрактов](56-s0-resilience-release-test-design.md), [DB/Event/UI machine matrix](contracts/r0-s0-resilience-release-case-contracts.v1.json). Recovery drill, no blanket suspension grant, двухтенантный pilot и exact-SHA digest остаются `NOT_REVIEWED` до реального evidence.

## 5. Definition of Done для Scenario Design

S0 считается подготовленным к **Test-First** только если все 121 активных R0 case имеют подтверждённые ownership/BR applicability, полные Given/When/Then и oracle (HTTP + DB + Outbox/Inbox/Audit/UI где применимо). Для локальных PR-08/06S/17/20 дописаны отдельные test case contracts. Все 26 PR связаны с реальными (или явно out-of-scope) test goals.

До этого **текущий статус остаётся S0_PROPOSED_NOT_REVIEWED**. Документационный CI проверяет машинную согласованность, но не может завершить предметное Test Review или approve BR/DEC.

**Next:** пройти аудит S0 пакета по каждой из 6 областей из [46](46-r0-scenario-first-tdd-standard.md), внести уточнённые oracle, затем создавать исполняемые RED тесты до любых новых доменных handler, Liquibase tables или UI.

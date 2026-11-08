# 50 — S0: обязательные дополнительные GWT для PR без основных сценариев

**Статус:** `S0_EXTENSION_GWT_PROPOSED_NOT_APPROVED` · 2026-11-08.
**Источник:** [машинный GWT реестр 40 случаев](contracts/r0-s0-extension-gwt.v1.json) и [предварительная матрица 132](contracts/r0-scenario-allocation.v1.json).

Текущее ТЗ требует проектировать **все** применимые сценарии до написания бизнес-кода. Предыдущая матрица из 132 R0-кейсов показала, что у **PR-00, PR-06S, PR-08, PR-17 и PR-20** нет собственного основного сценария. Это не причина выдавать `NOT_APPLICABLE`: нужны дополнительные case contracts.

## 1. Восстановление полноты тестового дизайна

| Направление | Case IDs | Новизна | Owner PR | Что доказываем |
|---|---|---|---|---|
| ЭЦП/NCALayer | `SIG-01…SIG-18` | **18 ранее упомянутых candidate IDs**, детализированы в GWT-проекты | PR-06S | Cryptographic signature, exact bytes, certificate trust/revocation, issuer/legal-entity signer authority, replay and provider fail-closed |
| Отсутствие платежей | `PAY-ABS-01…PAY-ABS-06` | **6 существовавших candidate IDs**, детализированы в GWT-проекты | PR-17 + release/architecture checks | Нет payment routes, AR/AP/ledger, PAID/SETTLED, bank webhook/secret; CostReport не авторизует settlement |
| CargoProfile/HandlingUnit | `PR08-CARGO-01…06` | **6 новых локальных проектов** | PR-08 | Quantity/weight validation, stable unit IDs, versioned amendment, Customer-X/Y isolation, unknown classification HOLD |
| Commercial Cost | `PR17-COST-01…04` | **4 новых локальных проекта** | PR-17 | Money scale, scoped margin, immutable ExternalAccountingDocRef, idempotency/versioning **без оплаты** |
| Release Qualification | `PR20-REL-01…04` | **4 новых локальных проекта** | PR-20 | Liquibase restore, exact SHA digest/SBOM, измеренный SLO/recovery, cross-tenant пилот с 8/10 и 10/10 |
| ТЗ/governance | `PR00-GOV-01…02` | **2 новых локальных проекта** | PR-00 | No lost cases/BR/owner and no false approval from docs CI |

**Всего 40 GWT-проектов**, из них **24 ранее обозначенных кандидата** и **16 новых локальных**. Эти 40 не прибавляются к исходным 132 как «40 уже выполненных тестов»; это отдельные S0 design artifacts.

## 2. Принцип тестирования EDS/NCA

Конкретные значения trust store, алгоритмов, профилей сертификатов, цепочки доверия, процедуры отзыва, полномочий представителя и legally binding документов **не выдумываются**. Позитивные тесты `SIG-01`, `SIG-14` могут стать исполняемыми только после утверждения применимого технического/юридического профиля; до этого допустимы fail-closed oracles с `DENY/HOLD`.

При подписании:
- проверять исходные **точные байты** и digest подписанного документа, а не только метаданные;
- проверять authority для конкретной организации и действия отдельно от криптографической подписи;
- не принимать client-supplied subject/tenant/owner как источник полномочий;
- не публиковать QuoteAccepted до confirmed original, authority and applicable BR/DEC;
- повторный event/signature и ошибка внешнего NCA-провайдера не должны создавать ложное юридическое обязательство.

## 3. Новые позитивные и отрицательные ветки Cargo/Finance

**Cargo** получает проверяемые сценарии: десять уникальных HandlingUnit, негативная масса или количество, конфликт одинакового idempotency key при изменении payload, версионирование профиля, отсутствие cross-customer доступа и `UNKNOWN` → `HOLD` для classification.

**Finance** остаётся только коммерческой аналитикой: precision денежных сумм, owner-scoped margin, внешняя opaque-ссылка на бухгалтерский документ и версия расчёта. Никаких собственных `InvoiceIssued`, `PaymentAllocation`, `PAID/SETTLED`, банковских callback или refund.

## 4. Что остаётся для предметного Review

1. **ЭЦП:** практический NCA/NCALayer verification PoC и юридическое утверждение документов/подписантов.
2. **Cargo:** подтвердить перечень Value Objects и инварианты единиц/массы, включая mixed units и hazardous classification.
3. **Finance:** согласовать источники себестоимости и валютную точность, отсутствие внутреннего AR/AP.
4. **Release:** определить наблюдаемые p95/RPO/RTO, recovery fixture и юридический UAT, не обещая недоказанные SLO.
5. **Governance:** согласовать review gate для каждого PR и правила изменения утверждённых test oracles.

**Ни один из 40 кейсов не имеет тестового или юридического `PASS`**. Stage remains S0 until technical case ownership and oracle approval; далее Test-First, затем отдельное Test Review, и только потом Implementation. В действующей ветке не добавлен новый доменный код.

# 39 — KERUENIX: повторное техническое и бизнес-ревью ТЗ после отмены платежей и добавления ЭЦП

**Дата:** 2026-11-08 · **Версия аудита:** 1.0 · **Статус:** `DOCUMENTATION_AUDIT / SPEC_CORRECTIONS_APPLIED / BUSINESS_AND_LEGAL_APPROVAL_PENDING`.

**Аудируемые источники:** [33 — Roadmap v1.6](33-tdd-development-roadmap-v1.md), [35 — Developer Handbook](35-r0-developer-handbook.md), [38 — EDS / no payments](38-r0-eds-signing-no-payments.md), [BR](contracts/r0-blocker-decisions.v1.json), [DEC](contracts/r0-delivery-contract.v1.json), [Access](contracts/access-policy-matrix.v2.json), [R0 TDD](contracts/r0-tdd-scenarios.v1.json), [Negative Bank](contracts/r0-negative-scenarios.v1.json), [Machine Roadmap](contracts/tdd-development-roadmap.v1.json). **Техническая/юридическая экспертиза документации, не заявление о готовности Java-бизнес-модулей и не заключение юриста.**

## 1. Решение по продукту

**KERUENIX НЕ является платёжным посредником, системой бухгалтерии или системой выдачи официальной ЭСФ.** Ни в R0, ни в целевой дорожной карте без новой явной заявки на изменение продукта нет банковских/платёжных операций, AR/AP-ledger, `PaymentAllocation`, `PAID/SETTLED/REFUNDED`, payout/refund, payment callback/webhook и функции `markPaid`. Внешняя бухгалтерия владеет своими документами и расчётами. KERUENIX сохраняет цену договора, стоимость перевозчика, коммерческие затраты, ограниченный отчёт о марже и ссылку на *внешний* документ без фиктивного статуса оплаты.

**При необходимости онлайн-подписания:** технический порт `platform.signing` с первым адаптером **NCALayer/НУЦ РК**, сторонний QR/eGov Mobile — опционально после действительного договора и PoC интеграции. Ключ/пароль пользователя не поступают на backend. Commercial/Booking/Execution владеют юридически значимым переходом и могут применить его только после проверенной подписи, полномочия подписанта и повторной проверки текущего состояния (CAS). Подписать документ ≠ исполнить денежное обязательство.

## 2. Подтверждённые замечания и степень закрытия

| ID | Приоритет | Противоречие в исходном ТЗ | Исправление / требование |
|---|---|---|---|
| RVR-01 | P0 | `FIN-01..04` в access JSON выдавали invoice/payment/reconciliation права как R0 | `FIN-01` заменён на read-only `commercial:cost:read`; `FIN-02/03/04` помечены `RETIRED_OUT_OF_PRODUCT_SCOPE`; любые генераторы грантов исключают их |
| RVR-02 | P0 | BSC-008 и USB-FIN/FAP требовали bank/ERP, `PaymentAllocation`, `PAID` | BSC-008 переписан как commercial costing + external accounting reference; payment stories заархивированы; банк недоступен |
| RVR-03 | P0 | Отдельные TDD-кейсы банка считались R0 P0, хотя платежи отменены | 11 исторических случаев помечены `RETIRED_OUT_OF_KERUENIX_PRODUCT_SCOPE`; 6 актуальных `PAY-ABS` negative tests защищают отсутствие платёжных функций |
| RVR-04 | P0 | `PR-11` carrier commitment мог обязывать перевозчика до `PR-06S` | Подписываемое обязательство перевозчика при необходимости ЭЦП теперь зависит от проверенного signing-порта и юрполномочий |
| RVR-05 | P1 | `RD-09` Costing ожидал полный Delivery+Documents, хотя стоимость доступна из Quote | Phase dependency на `RD-04`; подписанный договор/утверждённые цены достаточно для read-only commercial report; POD не требуется для составления коммерческой оценки |
| RVR-06 | P0 | Первые 13 signature TDD не проверяли несколько требований Цифрового кодекса РК к UX, полномочиям, открытой проверке и переносимости | Добавлены `SIG-14..18`: exact preview+explicit sign, полномочие юрлица, public verifier с соблюдением конфиденциальности, portable signed original, multi-party exact version |
| RVR-07 | P0 | Старое словоупотребление «электронное подтверждение/OTP/проверенный hash» могло подразумевать юридическую ЭЦП | Отделены `OPERATIONAL_RECORD`, `DIGITAL_CONFIRMATION`, `EDS_SIGNED_DOCUMENT`; законная форма и полномочия утверждаются Legal для конкретной операции |
| RVR-08 | P0 | Бизнес-процесс 8/10 частичной доставки мог завершить услугу и открыть отзыв | `PARTIAL_POD_DENIAL` и `VERIFIED_COMPLETION` — две отдельные приёмки; 8/10 не открывает private review автоматически |
| RVR-09 | P1 | Старые отчёты/матрицы/traceability всё ещё называли AR/AP и банковский settlement активными | Введение действующего scope override, новые и старые machine IDs сохраняются с признаком retired/absence-test; старые текстовые секции запрещено использовать для реализации |
| RVR-10 | P0 | Documentation CI проверял количество кейсов и PR, но не глобальный запрет платежей и зависимости Carrier->Signing | Новый machine guard + mutation tests, версия contract/roadmap и signing-test count синхронизируются; не разрешать silent drift |

**Статус исправления:** RVR-01..10 — решения **внесены в проектные контракты**; реализованных банковских или ЭЦП-модулей нет. Юридическое утверждение полномочий/подписи и бизнес-регламенты остаются открытыми. Полнота CI подлежит проверке на последнем SHA.

## 3. Ролевые пользовательские сценарии, которые должны быть проверены

| Актёр | Успешная операция | Блокирующая негативная операция | Источник истины |
|---|---|---|---|
| External Customer Requester | создаёт RFQ DRAFT; SUBMIT только с отдельным правом, как необязывающий запрос | Viewer/отозванный grant/чужой CustomerOrg не может SUBMIT или увидеть count чужих RFQ | Commercial RFQ + Tenancy account grants |
| Authorized Customer Signatory | видит **exact frozen Quote terms**, подтверждает применение своей ЭЦП, подписывает | валидный сертификат не того юрлица, истёкший, отозванный, чужой QuoteVersion или неподписанный документ — no ACCEPTED | Commercial + platform.signing evidence + authority check |
| Provider Approver | одобряет цену и формирует immutable QuoteVersion | собственное инициирование/одобрение запрещено по SoD; нельзя изменить подписанную версию | Commercial |
| Carrier Authorized Manager | подписывает обязательство на конкретный транспорт и сроки там, где legal profile требует | `CarrierOffer.SELECTED` без подписанного обязательства не подтверждает ресурс/Booking | Commercial/CarrierOffer + Fleet |
| Dispatcher/Driver | формирует реальный Booking и оформляет custody-подтверждение | GPS/фото URL/позднее офлайн-событие не равно подписанной ТТН/POD | Booking + Execution |
| Receiver | подтверждает полученные 8/10, подписывает применимый акт; остальные 2 единицы остаются с custodian | не получает полный DELIVERED; акт с подменённым получателем/подписью отвергается | Execution + signed proof |
| Commercial Cost Analyst | читает свои buy/sell суммы и margin с account/tenant masks | перевозчик или Customer-Y не читает margin Customer-X; нет paid/refund/ESF | Finance (cost-only R0) |
| External Accounting | получает только согласованный экспорт/opaque doc reference без платёжного статуса внутри KERUENIX | bank callback, reconciliation, markPaid не имеют endpoint или сущности | внешняя бухгалтерия |
| SaaS Support | видит job/incident без раскрытия договоров, ЭЦП, данных GPS | нет tenant-wide superuser и скачивания signed originals | platform security |

## 4. Юридический/технический EDS quality gate

[Цифровой кодекс РК №255-VIII](https://old.adilet.zan.kz/rus/docs/K2600000255), ст. 49–50, 61–62, предполагает требования к использованию ЭЦП и электронным документам, включая предъявление подписанту текста, явное подтверждение действия, уведомление, сохранение, проверку полномочия за юрлицо, открытый способ проверки и переносимость электронного документа. **Нужно юридическое подтверждение применимости способа к конкретному Quote, CarrierCommitment, TTN, POD и актам.**

**Неотменяемые инженерные блокеры:**
- Сервер проверяет **тот самый** frozen signed payload, а не только boolean от NCALayer/frontend.
- Сертификат валиден в требуемый юридически значимый момент, trusted chain/revocation/time evidence сохранены с оригиналом.
- Пользователь имеет полномочие **от конкретного юридического лица**; verified certificate alone недостаточен.
- Сервис проверки полномочий недоступен → `PENDING_VERIFICATION`/`HOLD`; не записывать `ACCEPTED`, `BOOKING.CONFIRMED` или юридически подписанный POD.
- Multi-party подписи требуются только по утверждённой договорной модели; каждая подпись относится к одной immutable версии.
- Подписанный оригинал можно экспортировать и независимо проверить с сохранением необходимого audit/proof; публичная проверка подписи **не** означает публичный доступ ко всем байтам договора.
- Старые подписи сохраняются как исторические доказательства; новые действия проверяют текущие права и ограничения.

## 5. Что ещё НЕ закрыто — реальные бизнес/юридические решения

1. **BR-01/05/06/09/10/11:** для каких действий обязательна ЭЦП, кто подписывает от каждой организации, достаточность fallback подписанного вне платформы документа, правила многостороннего согласования и отмены. Нельзя автоматически требовать ЭЦП для *каждой* операционной кнопки.
2. **BR-03/DEC-R0-02:** Commercial CustomerAccount и Tenancy grants — раздельные владельцы. Требуется подтверждённая модель юридических сторон и полномочий; без этого никто не получает право подписывать от CustomerOrg.
3. **BR-12/DEC-R0-07:** подтвердить на уровне владельцев и бухгалтерии отсутствие платёжных функций и роли внешней бухгалтерии; это scope signoff, **не** разрешение создать банк-адаптер.
4. **EDS integration contract:** текущая версия NCALayer SDK, алгоритмы и формат подписания, trusted CA/revocation, сервис полномочий для юрлица, открытый verifier и retention. Никакого готового vendor/QR endpoint без проверенной документации и договора.
5. **Пользовательские интерфейсы:** отдельные состояния preview/consent/signing/pending/expired/retry/document download; интерфейс в мобильном сценарии не должен предполагать, что NCALayer всегда доступен.
6. **Правовой статус транспортного доказательства:** обычная фотография/QR и `ProofReceipt` могут быть операционными данными, но не автоматически официальной ТТН/POD или договорным актом.
7. **Legacy ownership documents:** длинные архивные разделы Roadmap/User Story/Business Scenario/Backend design содержат прежние финансовые примеры — их нужно переводить в историю с ясным приоритетом актуального scope; не генерировать код из deprecated R0 требований.

## 6. TDD/prod readiness — what can start

**PR-00**: подтвердить норму current scope, таблицу цифровых юридических действий, signatory delegation и ADR owners; могут оставаться юридические PENDING без разрешения binding operations.

**PR-01**: implement test-first Spring Modulith/PostgreSQL/PostGIS/RLS/Outbox/Inbox; отсутствие банковских модулей проверяется на зависимостях/DDL.

**PR-02 + PR-06S parallel (after identity)**: подписант, внешняя NCA ЭЦП, проверка оригинала и полномочий; browser/web NCALayer PoC, fake provider Testcontainers/mocks плюс реальная sandbox-проверка, если доступна. Нельзя объявлять `PR-06S` qualified одним замоканным `signatureValid=true`.

**Commercial PR-03C/03/04/05**: RFQ DRAFT→provider inbox under active grants and scoped RBAC/ABAC, no binding by creating a draft.

**PR-06/07/11 + PR-10/12**: signature-dependent Quote and CarrierOffer, actual capacity. Without legal signoff operation remains pending rather than falsely accepted.

**PR-13/14/16/16R + PR-17**: custody/partial proof, document package, private eligible review and commercial cost report — no payment. Then real multi-role UI/API/PG E2E under PR-19 and pilot PR-20.

**Release condition:** all applicable approved TDD/NEG/SIG/PAY-ABS tests green on exact SHA, external signer verification confirmed, legal actor contracts accepted and backup/restore/site/ops proven. A green documentation check does not prove these.

## 7. Verdict

**ТЗ — условно готово к старту платформенной реализации PR-00/01. Не готово к юридически обязывающим Quote/Carrier/POD и к пилотному релизу**, пока не утверждены подписанты, способ ЭЦП, роли сторон и реальные пользовательские тесты. В текущем продукте **нет платёжных операций вообще**. В этом review исправляются спецификации/контракты, но код бизнес-модулей не создаётся.

# 55 — S0 Tracking, Documents, Service Review и Commercial Cost

**09.11.2026 · Только Scenario Design · `PROPOSED_NOT_REVIEWED`.**

[17 машинных тестовых контрактов](contracts/r0-s0-tracking-documents-cost-case-contracts.v1.json) охватывают: **6 основных** сценариев PR-15/16/16R, **7** связанных со сторонними владельцами и **4 локальных** GWT коммерческой аналитики PR-17. Исходные case IDs и основные владельцы не переназначены; 6 запретительных `PAY-ABS` проектов остаются отдельным реестром.

## 1. Проверяемая модель

| PR/слой | Поведение и тестовый оракул |
|---|---|
| **PR-15 Tracking** | Stale GPS хранит `observedAt/receivedAt` и provenance, customer timeline обозначает STALE/UNAVAILABLE вместо подмены LIVE; проектор не показывает Booking.CONFIRMED из устаревшего/откаченного события. Tenant и CustomerAccount ACL действуют на позиции, историю, count/export и live stream |
| **PR-16 Documents** | `ProofDocument` содержит immutable original bytes/hash и versioned package. Corrections append-only, не переписывают дату/подписанта оригинала; EDS подтверждается отдельно от технического storage |
| **PR-16 Signed URL** | Отозванный grant немедленно запрещает **новый protected API-запрос и выдачу новой ссылки**. Ранее выданная presigned URL подчиняется фактическому TTL/credentials; обещать мгновенный hard revoke **запрещено**, если нет proxy/revocation design и тестов |
| **PR-16R Service review/claim** | Complaint/issue может быть зарегистрирован до завершения, но не меняет POD и не порождает refund. Private review не принимается от Sales/подменённого customer и при 8/10 partial. Положительная eligibility требует отдельно подтверждённого завершения (не фиктивного 10/10) и правил `DEC-R0-05` |
| **PR-17 Commercial Cost** | Денежная точность и валюта на immutable QuoteVersion/cost inputs, роль-контроль маржи и supplier buy rate до агрегирования/pagination, opaque ссылка на **внешне** выпущенный документ, replay/idempotency. Финансовый отчёт не создаёт invoice/AR/AP, payment, status PAID/SETTLED, refund или bank integration |

## 2. Конкретные high-risk cases

- `TDD-SIM-26-S24-01` и `NEG-R0-044`: подтверждать watermark/источник и freshness, а не только формат координат или последний event; non-authoritative state не превращается в клиентский успех.
- `TDD-SIM-30-S20-01`, `NEG-R0-032`, `TDD-R0-E2E-09`: проверка отзыва пользователя при действующем JWT, warm cache, новом и старом object URL. **Технический контракт TTL** остаётся предметом review.
- `NEG-R0-047` и `NEG-R0-048`: issue ≠ review; sales employee ≠ customer signatory; private completed-service review не вытекает из partial POD.
- `PR17-COST-01…04`: precision, scoped margin, external doc ref, digest conflict; ни один отчёт не имеет эффекта payment settlement.

## 3. Предлагаемые S1-тесты после S0 Review

`TrackingProjectionWatermarkTest`, `TrackingCustomerScopeTest`, `DocumentOriginalHashTest`, `DocumentSignedUrlExpiryTest`, `CustomerReviewEligibilityTest`, `CommercialCostPrecisionTest`, `CommercialCostAuthorizationTest`. S1 tests должны быть executable RED до реализации соответствующего handler; для ACL, версий и Outbox нужны реальные PostgreSQL/HTTP contract fixtures.

**Неутверждённые решения:** `DEC-R0-05` (private review eligibility), `DEC-R0-07` (коммерческий периметр), `BR-03` (customer grants), `BR-09/10` (custody/POD) и смежные E2E. CI документации не подтверждает их принятие.

**Результат:** 17 проектов проверяемого поведения; S0 не квалифицирован, новый доменный код не создан. NO PAYMENTS / NO AR/AP / NO bank gateways.

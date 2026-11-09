# 24 — Симуляция международного рейса и экспертная приёмка

**Дата:** 07.11.2026 · **Статус:** синтетические сценарии; маршруты, документы и условия приведены для проверки модели, а не как действительные разрешения на перевозку.

## Участники

Tenant-A — KZ экспедитор; Tenant-B — грузовладелец; Tenant-C — перевозчик-партнёр; Tenant-D — склад/СВХ; Tenant-E — получатель. Набор четырёх грузов: обычный генеральный груз (паллета с SSCC), пищевой груз с температурой, условный груз с опасной классификацией (UN details missing) и международный контейнер (ISO 6346).

## Сценарий 1 — внутренняя перевозка с разными грузовладельцами

1. Грузовладелец вводит GTIN/lot/weight/volume; склад сканирует SSCC.
2. WMS сохраняет `HandlingUnit.id`, GS1 namespace и количество.
3. Planner хочет совместить обычный груз и пахучую химическую продукцию.
4. `CargoCompatibilityPort` проверяет запрет/условия, защиту/кузов/соседство/упаковку.
5. Если данных недостаточно — NEEDS_REVIEW; нельзя автоматом построить сборный рейс.
6. Клиент отслеживает только свои грузовые единицы.

**Pass:** скан SSCC не раскрывает чужой tenant; нет совместной загрузки без подтверждённого решения, фиксация причины обязательна.

## Сценарий 2 — Алматы → международная доставка

1. Экспедитор оформляет RFQ с назначением, странами транзита и грузом.
2. Product master содержит GTIN/коммерческую категорию, HS6 и применимый TN VED10 — отдельно от UN dangerous classification.
3. `RegulatoryRegistry` определяет, требуется ли CMR/разрешения/транзитные документы/таможенные статусы/страхование; только для конкретного коридора.
4. Перед booking проверяются vehicle gross/axle, route/legal and permits; для eCMR/TIR нельзя предполагать legal support без lane validation.
5. Warehouse передаёт SSCC по signed scan; customs HOLD независим от физической готовности груза.
6. После подтверждённого выпуска разрешённая партия передаётся перевозчику.
7. Client timeline хранит checkpoints, ETA и документы, не чужой cost price.

**Pass:** внутренний SSCC корректен либо отмечен как internal label, незаявленный нормативный статус не выдуман, customs hold без разрешения не снимается.

## Сценарий 3 — условный опасный груз

1. У грузовладельца есть описание товара, но нет подтверждённого UN-number и спецификации упаковки.
2. Подборщик видит автоцистерну с достаточным объёмом.
3. `DangerousGoodsDeclaration` недостаточен; `VehicleCapabilityPort` не выдаёт разрешение.
4. Перевозчику предлагается дооформить данные и проверить применимость ADR/national rules, маркировку, tank permission и документы.
5. После подтверждённого ответа профильного специалиста и актуального RuleSet пересчитывается доступность.

**Pass:** объём цистерны и наличие SSCC/QR не позволяют обойти опасный нормативный контроль.

## Сценарий 4 — поломка, склад и смена перевозчика

1. Рейс с двумя товарными единицами останавливается, включается Rescue Network.
2. Безопасная точка перегрузки находится на Warehouse-D; dock appointment оформляется отдельно.
3. Scan разгрузки и повторной погрузки порождает новые custody events, не новый Order/SSCC.
4. Новый перевозчик проходит vehicle/cargo/road compliance.
5. Частичный damage создаёт QualityHold; клиент видит разрешённую причину задержки.
6. Settlement отдельно фиксирует дополнительные расходы и спор по причине повреждения.

**Pass:** сохраняется история от первого до последнего исполнителя, нет двойного stock и двойного акцепта, права разных tenants не пересекаются.

## Минимальный набор автоматизированных qualification suites

- `IdentifierValidationTest`: GS1 SSCC/GTIN, ISO6346, namespaces and check digit.
- `CargoClassificationTest`: HS6 vs TNVED10 vs dangerous goods UN data separation.
- `TransportLegRegulationTest`: route/country/mode/effective date selection.
- `CargoCompatibilityTest`: adjacency and shared air/temperature restrictions.
- `VehicleCapacityTest`: payload/axle/compartment/legal approvals.
- `DocumentRequirementTest`: missing mandatory docs/incorrect expiry/untrusted issuer.
- `CustomsHoldTest`: no release absent authoritative evidence.
- `WarehouseCustodyTest`: scan idempotency and handover lineage.
- `CrossTenantShipmentTrackingTest`: milestone visibility without commercial leakage.
- `RegulatoryRuleVersionTest`: pinned 2025 ADR vs 2027 drafts and source updates.
- `OfflineReplayTest`: duplicate scan and delayed partner synchronization.
- `LabelSecurityTest`: copied/expired QR does not grant sensitive access.

**Критерий подготовки к production:** утверждённые действующие нормативные наборы по фактическим классам груза и странам, юридический договор на международные документы, интеграционные испытания с реальными контрагентами и независимая экспертиза опасных грузов. Текущая концепция только задаёт проверяемые требования.

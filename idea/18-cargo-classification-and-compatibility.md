# 18 — Cargo Classification & Compatibility Engine: правила товарного соседства, перевозки и хранения

**Версия:** 0.1 · **Дата:** 07.11.2026 · **Статус:** требования и концепция, не сертифицированный нормативный справочник.
**Проверяемые аспекты:** груз, транспорт, загрузка, склад, консолидация, транзит, СВХ, Rescue Network.
**Приоритет:** P0 для первого реального сценария сборной перевозки или мультивладельческого хранения; обычный MVP без смешанных грузов также требует базового CargoProfile и опасных/температурных флагов.

## 1. Почему нужны отдельные классификации

Нельзя определять совместимость только по текстовому типу товара или ТН ВЭД.

- **Коммерческая категория** (каталог SKU, GTIN, ТН ВЭД) помогает идентифицировать товар и тарифы, но сама не подтверждает безопасность совместной загрузки.
- **Dangerous goods classification** описывает UN number, proper shipping name, класс/подкласс, дополнительные опасности, packing group, категорию/ограничения перевозки, освобождения и режимы для конкретного вида транспорта. Перечень и применимые правила зависят от юрисдикции/редакции документа.
- **Hygiene/food group** различает сырое/готовое, пищевое/непищевое, аллергенное, риск запаха и перекрёстной контаминации.
- **Temperature/sensitivity profile** фиксирует хранение и перевозку: допустимые диапазоны температур/влажности, свет, вибрация, время воздействия, срок годности, запрет замораживания.
- **Packaging/handling profile** фиксирует герметичность, штабелируемость, направление и ограничения укладки, защиту от разливов/пыли, совместимость с соседями и предыдущим грузом.

Например, две пищевые позиции могут принадлежать к одному классу каталога, но иметь разные температурные требования. Два химических продукта одного класса опасности нельзя считать автоматически совместимыми: решают точные позиции UN, специальные правила, упаковка, размещение и транспортный режим.

## 2. Какие нормы нужно версионировать

| Нормативная область | Источник / зона применения | Продуктовое последствие |
|---|---|---|
| Опасные грузы, автомобиль | UNECE ADR (текущая применимая редакция) и национальные правила Казахстана; учитывать транзитные страны | Разрешение на совместную загрузку, упаковка, маркировка, транспорт/водитель и документы |
| Опасные грузы, море | IMO IMDG Code, действующая редакция для даты перевозки | Segregation, упаковка, укладка контейнера/судна |
| Опасные грузы, авиация | ICAO Technical Instructions / применимые IATA DGR | Ограничения приёма и раздельной обработки, документы и разрешения |
| Опасные грузы, железная дорога | RID/применимые национальные железнодорожные нормы | Совместимость вагонов/грузов, ограничения и документы |
| Пищевая продукция | ТР ТС 021/2011, ст. 17; актуальные правила и нормы Казахстана | Температура изготовителя, разделение сырья/готовой продукции и защита от загрязнения |
| Лекарства/медизделия | РК: правила хранения и транспортировки, действующая редакция; требования производителя | Температурные зоны, условия хранения, карантин и прослеживаемость |
| Общий склад и специальные грузы | Договор склада, инструкции производителя, технические регламенты и отраслевые нормы | Ячейки, условия соседства, запреты/разрешения, ответственность |

Юридическое применение определяется **страной, маршрутом, видом транспорта, датой, конкретным товаром, упаковкой, документами и исключениями**. Нельзя объявлять общую матрицу класса ADR универсальным юридическим решением. Текущая спецификация содержит только концептуальные проверки; официальный нормативный справочник заполняют/утверждают компетентные специалисты.

Справочные первоисточники:
- UNECE ADR 2025: https://unece.org/adr-2025-files ; mixed loading: ADR 7.5.2, precautions with food: 7.5.4.
- Казахстан, правила опасных грузов автотранспортом: https://old.adilet.zan.kz/rus/docs/V1500011779 (в 2026 внесены изменения).
- Казахстан, правила перевозки грузов: https://old.adilet.zan.kz/rus/docs/V1500012463 .
- ТР ТС 021/2011, ст.17 (официальный ЕЭК): https://old.adilet.zan.kz/rus/docs/H11T0000880 .
- Госорганы Казахстана, разъяснение товарного соседства: https://www.gov.kz/org/departament-kkbtu-karaganda/press/news/details/881261?lang=ru .
- Казахстан, правила хранения и транспортировки лекарств: https://old.adilet.zan.kz/rus/docs/V2100022230 .
- IMO IMDG: https://www.imo.org/en/ourwork/safety/pages/dangerousgoods-default.aspx .
- ICAO: https://www.icao.int/Dangerous-Goods/Technical-Instructions .
- WHO, temperature mapping: https://www.who.int/publications/m/item/cold-chain-equipment-and-dry-store-temperature-mapping-tool .

## 3. Карточка груза — Cargo Compliance Profile

Обязательные поля перед **окончательным** назначением на перевозку/ячейку (часть полей optional, когда не применимо):

| Раздел | Поля |
|---|---|
| Identity | cargo_id, товар/SKU/GTIN при наличии, описание, грузовладелец, количество, единица измерения, batch/lot/expiry |
| Classification | commercial_category, food_status, raw_vs_ready, pharmaceutical, living/perishable, dangerous_flag, hazard classes, UN number, subsidiary risk, packing group, exemptions |
| Physical | масса/объём/габариты единицы, центр тяжести, ориентация, допустимая нагрузка сверху, штабелирование |
| Packaging | вид упаковки, герметичность, повреждения, пломба, защищённость от запахов/влаги, категория загрязнения |
| Environment | temp_min/max, humidity bounds, light sensitivity, vibration/shock limits, допустимое время отклонения от режима |
| Interaction | odor_emitting/absorbing, contamination risk, reactive substances, allergens, incompatibility groups, food-contact, pests |
| Handling | forklift/crane, PPE, clearance, load/unload instructions, separation requirements, sanitation/cleaning |
| Compliance | SDS при необходимости, manufacturer instructions, certificates/permits, source document URI/hash, source validity, approved classification revision |
| Commercial | declared value, insurance requirements, claims-sensitive attributes, contractual custody restrictions |

**Неполные данные:** `CLASSIFICATION_PENDING`, `REVIEW_REQUIRED` и запрет автоматического safe-marking. Самоопределённый клиентом класс без подтверждений не становится нормативным фактом; серьёзные опасные грузы требуют экспертной верификации.

## 4. Матрица совместимости — не универсальная таблица «да/нет»

Проверки выполняются в контексте:
- `TRANSPORT_VEHICLE`: один грузовой отсек, разные отсеки, контейнер на платформе, разные машины;
- `WAREHOUSE_ZONE`: одна ячейка, соседние ячейки, общий воздух/вентиляция, отдельные помещения;
- `TRANSFER_DOCK`: совместное нахождение на рампе, во время разгрузки, перегрузки или буферизации;
- `HANDLING_WORKFLOW`: совместное использование оборудования/тары, порядок обработки, уборка/санобработка;
- `TRANSPORT_LEG`: mode-specific maritime/air/rail/road restrictions.

**Условная продуктовая матрица для проверки UX (НЕ нормативная таблица):**

| Груз A | Груз B | Предварительный результат | Почему нужна проверка |
|---|---|---|---|
| Готовая пищевая продукция | Сырое мясо | DENY / NEEDS_REVIEW | Разделение, упаковка, конкретные санитарные условия |
| Пищевая продукция | Бытовая химия | DENY / NEEDS_REVIEW | Риск загрязнения; отдельные разрешённые условия |
| Рыба с сильным запахом | Чай/сыр, поглощающие запахи | ALLOW_WITH_CONTROLS / DENY | Влияние запаха и герметичность, изоляция |
| Охлаждённый продукт | Замороженный | DENY для общей неконтролируемой температуры | Несовместимость требуемого температурного режима |
| Хрупкие приборы | Тяжёлые паллеты | ALLOW_WITH_CONTROLS | Штабелирование, фиксация и нагрузка |
| Два товара ADR | Два товара ADR | NEEDS_REVIEW до проверки точных UN/labels/спецусловий | Один номер класса не позволяет решить по смешанной загрузке |
| Лекарство с cold chain | Обычный сухой груз | NEEDS_REVIEW | Отдельная температурная зона и документированное соблюдение |
| Груз `customs HOLD` | Любой другой | Не разрешает отгрузку при любой совместимости | Таможенная блокировка независима от физического соседства |

Приведённые исходы — **гипотезы для тестирования функциональности**, а не законная общая разрешительная матрица. Конечный ответ требует конкретных свойств, упаковки, физической изоляции и действующего RuleSet.

## 5. Rule Engine — модель политики

`RuleSet`: rule_set_id, version, regulator/source, country/region, mode, valid_from/to, approval_signature, status DRAFT/REVIEWED/ACTIVE/RETIRED.

`CargoCompatibilityRule`: scope (vehicle/warehouse/dock/handling), cargo selectors (class, UN, odor, food, temperature...), layout scope (same pallet, same bin, same zone, compartment), predicates, effect, required controls/evidence, priority, explanation code, source reference, effective time.

Вычисляемый результат:
- **ALLOW** — все обязательные проверки по достаточным фактам прошли;
- **ALLOW_WITH_CONTROLS** — допустимо при реально выполнимых и подтверждённых барьерах/санитарных операциях;
- **DENY** — найден запрет или невыполнимое обязательное ограничение;
- **NEEDS_REVIEW** — недостаточно фактов/нет утверждённого правила/конфликт нормативных источников.

Приоритет: обязательная норма и запрет > требования изготовителя/договорно обязательные условия > утверждённая политика предприятия > рекомендации оптимизатора. При конфликте нормативных источников не делать выбор по количественному priority «больше = сильнее», а передавать профильному специалисту.

**Нельзя отменять юридический DENY ручным оверрайдом.** Возможное исключение/специальное разрешение должно быть прямо предусмотрено применимой нормой и подтверждаться отдельным документом/процедурой. Автоматические рекомендации запрещены, если нет действующей утверждённой версии правил.

## 6. Контроль в течение всей жизни груза

1. **RFQ:** получить класс и условия груза; не формировать binding quote для требующих проверки грузов без обязательных данных.
2. **Booking:** проверить допустимость машины, водителя, упаковки, лицензий/разрешений и маршрута.
3. **Multi-order consolidation:** проверять pairwise + глобальные условия всего набора грузов (масса/воздух/температура/критические соседства), а не только пару новых товаров.
4. **Load plan:** назначить грузовые единицы на отсеки/позиции; учесть высоту, вес на ось, порядок выгрузки, крепление/штабелирование, разделительные барьеры и доступ к оборудованию.
5. **Pickup:** проверить фактическую упаковку, пломбы, вес, партии и несоответствия; результаты заявки требуют повторной оценки.
6. **In-transit:** отслеживать температуру/влажность/открытие дверей при наличии оборудования; факт нарушения создаёт quality hold/exception, а не автоматически обвиняет водителя.
7. **Warehouse receiving:** проверить условия зоны/ячейки и фактическое соседство других владельцев, занятые места, вентиляцию, состояние упаковки.
8. **Putaway/move:** оценить новые соседства с учётом реального пространственного положения и пересечения периода хранения.
9. **Cross-dock / Rescue:** при замене транспорта/перегрузке полный пересчёт compatibility и custody; нельзя наследовать зелёный статус старой машины/склада.
10. **Shipping:** перед каждым load/dispatch снова проверить RuleSet, фактическую комплектацию и hold статусы.
11. **Claim / audit:** сохранить snapshot входных фактов, ruleset version, объяснение решения, ответственного, telemetry evidence и timestamp.

## 7. Понятие «соседства» в алгоритме

`AdjacencyGraph` моделирует физические связи: SAME_PALLET, SAME_BIN, ADJACENT_BIN, SAME_AIRSPACE, SAME_COMPARTMENT, CONNECTED_VENTILATION, SEPARATE_ROOM, SEPARATE_VEHICLE, SHARED_HANDLING_EQUIPMENT.

Отношения имеют интервал времени (`from_at, to_at`) и свойства физической преграды. Проверка выполняется только там, где грузы действительно сосуществуют по времени и физически контактируют, но учитывает прошлую загрязняющую историю отсека/оборудования (cleaning certificate и cleaning validity).

### Минимальный алгоритм

    validate cargo + packaging + documents
    select rule sets by jurisdiction, mode, time, goods
    validate environmental capability of candidate compartment/zone
    validate solo restrictions and facility/vehicle permits
    build overlap of planned occupancy times and adjacency graph
    evaluate pairwise and group constraints with required barriers
    verify loading geometry, stackability, axle load, handling order
    compute DENY | NEEDS_REVIEW | ALLOW_WITH_CONTROLS | ALLOW
    store immutable assessment with ruleset, evidence, reason codes

Вычисления не должны выводить «совместимо» из отсутствия найденных правил. Сначала требуется установить полноту классификации и нормативного покрытия.

## 8. Java и контракты

Модуль `cargo-compliance` живёт в Logistics Core и не зависит напрямую от Timefold/Tribuo:

```java
public interface CargoCompatibilityPort {
    CompatibilityDecision assess(CompatibilityContext context);
}

public enum CompatibilityStatus {
    ALLOW, ALLOW_WITH_CONTROLS, DENY, NEEDS_REVIEW
}

public record CompatibilityDecision(
    CompatibilityStatus status,
    String ruleSetVersion,
    java.util.List<String> reasonCodes,
    java.util.List<String> requiredControls,
    java.time.Instant evaluatedAt
) {}
```

`CompatibilityContext` содержит trusted tenant+actor context (не клиентский tenant_id как право), cargo profiles + handling units, planned layout/adjacency, route/mode/jurisdiction/time, vehicle or warehouse capabilities, custody/quality holds, evidence references.

Проверять не только `assess(A,B)`, но и `assessLoadPlan(setOfCargo, layout, timeline)` и `assessPutaway(cargo, bin, occupiedNeighbors, timeWindow)`. **Timefold** получает результат/constraints: запрещённые комбинации — hard constraints, а штрафы за лишнюю перегрузку/низкую утилизацию — soft constraints. **Tribuo** может прогнозировать риск температурного выхода, но не решать юридическую допустимость.

Для MVP использовать проверяемый deterministic Java rule service (DB или ревьюируемые YAML/JSON rule definitions с валидатором). Полноценный экспертный rule engine (Drools и др.) подключать только при подтверждённой сложности и необходимости; не превращать правила законодательства в непроверяемые скрипты.

## 9. Данные и таблицы (предлагаемые)

`CargoProduct`, `CargoClassification`, `DangerousGoodsDeclaration`, `CargoHandlingProfile`, `TemperatureProfile`, `PackagingProfile`, `RuleSet`, `CompatibilityRule`, `RuleEvidence`, `CompatibilityAssessment`, `Compartment`, `VehicleCargoPosition`, `WarehouseZoneCapability`, `BinAdjacency`, `OccupancyInterval`, `CleaningRecord`, `LoadingPlanVersion`, `ViolationEvent`, `QualityHold`, `SafetyApproval`.

Разделить **глобальные проверенные нормативные справочники** (versioned, read-only для арендатора) и **tenant-owned грузовые профили/внутренние ограничения**. Клиент может добавлять более строгие политики, но не ослаблять обязательные требования.

Полный snapshot применённой классификации и версии rules хранить рядом с QuoteVersion, RoutePlanVersion, WarehouseTask и CargoHandover — изменения справочника не должны переписывать историю.

## 10. Безопасность, приватность, нормативное сопровождение

- Для опасных грузов требуется утверждённый оператором нормативный data set и профильный compliance review; система не является юридическим консультантом.
- Правило отозвано/истекло/не относится к стране/режиму — итог NEEDS_REVIEW, не ALLOW.
- Различать заявленные грузовладельцем данные и подтверждённую инспекцией фактическую классификацию; сохранять версию и ответственность.
- Межтенантный планировщик может пользоваться минимальными **compatibility assertions** (класс, hazard/handling requirements, ограничения), не публикуя клиентскую себестоимость или формулу вещества/состав там, где он конфиденциален. Не скрывать регуляторно обязательные сведения от фактического перевозчика.
- Права редактировать классификацию/снимать quality hold отделены от прав планировать рейс, ценить заказ или обслуживать склад.
- Вести аудит правил, подписанного утверждения, версии нормативного источника и всех решений.
- Журнал температур/датчиков — provenance, калибровка, freshness, нарушения и карантин; нельзя подменять измерение ручным вводом без отметки источника.

## 11. Приёмка и adversarial tests

| ID | Условие | Ожидаемый результат |
|---|---|---|
| CMP-01 | Неизвестный класс/отсутствует критическая документация | NEEDS_REVIEW, запрещена финальная загрузка |
| CMP-02 | Пищевой продукт и загрязняющий непищевой груз без подтверждённой изоляции | DENY либо NEEDS_REVIEW по утверждённому ruleset |
| CMP-03 | Сырое/готовое в одной воздушной зоне без допустимых барьеров | Вынесено на ограничение/согласование, нет silent ALLOW |
| CMP-04 | Два груза с непересекающимися температурными диапазонами в одном неразделённом отсеке | DENY |
| CMP-05 | Разные температурные зоны в одном многосекционном рефрижераторе | ALLOW_WITH_CONTROLS только после проверки независимости зон |
| CMP-06 | Два опасных груза одного класса, нет сведений по UN и специальным положениям | NEEDS_REVIEW; класс не равен совместимости |
| CMP-07 | Груз со строгим ограничением по запаху рядом с пахучим товаром | Проверка герметичности/воздуха, нет автодопуска |
| CMP-08 | Погрузка с несовместимым штабелированием и превышением нагрузки | DENY, объяснить позицию и ограничение |
| CMP-09 | Товар в customs HOLD, но разрешён по физической совместимости | Отгрузка заблокирована независимым hold |
| CMP-10 | Перегрузка в новую машину после Rescue | Повторная проверка по новой машине/отсекам и custody |
| CMP-11 | Склад A и грузовладелец B; соседи — грузы другого tenant | Проверка соседства без раскрытия чужих товарных/коммерческих данных |
| CMP-12 | Изменился RuleSet после подтверждённой загрузки | Плановая переоценка/алерт; старая запись неизменна |
| CMP-13 | Испорчена упаковка при приёмке | QUARANTINE, повторная проверка и акт |
| CMP-14 | Устройство температуры offline/stale | NEEDS_REVIEW/quality hold по политике, не ложная норма |
| CMP-15 | Смена маршрута на другую юрисдикцию или транспортный режим | Повторная оценка по новым правилам |
| CMP-16 | Водитель/диспетчер пытается обойти hard DENY | Блокировка, аудит попытки |
| CMP-17 | Резерв ячейки и склада меняется конкурентно | Snapshot/version check, нет двух взаимоисключающих бронирований |
| CMP-18 | После опасного/пахучего груза нет подтверждения очистки отсека | Запрет/NEEDS_REVIEW, пока не подтверждены требования |
| CMP-19 | Совместимы отдельные пары, но общий набор нарушает массу/температуру/объём | Групповой план отклонён |
| CMP-20 | Экспериментальная ML модель говорит ALLOW, нормативный RuleSet говорит DENY | DENY и объяснение обязательного ограничения |

## 12. Roadmap

**P0 — Design/System Baseline:** CargoComplianceProfile, verified classification vs declared, deterministic rules, four-state decision, unknown-data policy, hard stop before pickup and warehouse dispatch; связь с Order/Shipment/Trip/HandlingUnit и Audit.

**P1 — Mixed Freight/WMS:** pairwise+group compatibility, comp-zone/bin adjacency, occupancy intervals, sanitation and cleaning, temperature event monitoring, plan layout visualization, cross-dock/recovery checks and safety approvals.

**P2 — Regulated Modes:** library of approved jurisdiction/mode/date-specific datasets and legal review, ADR/RID/IMDG/ICAO detailed modules, certificate/permit verification, export compliance and operational staff training.

**P3 — Optimization:** Timefold-aware constraint propagation, route-wide multi-order consolidation, ML-based temperature excursions (not compliance decisions), explanations and warehouse labor utilization.

## 13. Неотложные открытые вопросы

1. В пилоте будет генеральный груз, продукты, фармацевтика, химия или смешанный ассортимент?
2. Какие типы машины и рефрижераторы, разделяемые отсеки, чистка/дезинфекция, погрузочное оборудование?
3. Виды хранения: транзит, сухой склад, холодильная камера, морозильник, опасные грузы, СВХ?
4. Кто является ответственным за классификацию, подтверждение документов и обновление нормативной матрицы?
5. Какие страны и транспортные режимы входят в пилот?
6. Какие документы обязательно фиксировать до бронирования/погрузки/выпуска?
7. Как передавать минимальные атрибуты совместимости между tenant без раскрытия коммерческих данных?
8. Нужны ли рецепты загрузки с геометрией, разгрузкой по очередности, видео/датчиками и физической схемой отсеков?

## 14. Вывод

**Cargo Classification & Compatibility — сквозной доменный сервис, необходимый и TMS, и WMS, и Rescue Network.** Он не может быть полем `cargoClass` в Order и не может целиком делегироваться Timefold. Вся система должна использовать один согласованный детерминированный контур правил с явной версией и правовой/технологической основой.

## Equipment-specific constraint data

CargoCompatibilityPort combines cargo-side legal, sanitary and handling requirements with verified VehicleCapabilityPort attributes from a specific tractor/body/trailer/tank/reefer configuration. Two cargoes may be compatible in general but infeasible in one trailer due to compartment count, temp, pallet layout, total/axle weight, tank-product approval, cleaning, loading order or site equipment. See [20 — Vehicle Classification & Capacity](20-vehicle-classification-capacity-and-special-equipment.md).

## International code and regulatory registry boundary

Store commodity HS6/TNVED10 classification independently from GS1 GTIN/SSCC and hazardous-goods UN number/packing classification. Compatibility decisions use country, mode and effective date, with approved source-versioned rule sets and traceable evidence; no inferred legal permission from a scanned barcode. See [22 — Global Identification](22-global-cargo-identification-and-marking.md), [23 — Regulatory Registry](23-cross-border-regulatory-compliance-registry.md).

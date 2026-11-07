# 20 — Vehicle Classification, Capacity & Specialized Equipment

**Версия:** 0.1 · **Дата:** 07.11.2026 · **Статус:** проектные требования, примерная бизнес-классификация; не нормативная таблица грузоподъёмности и не сертификат транспортного средства.  
**Приоритет:** P0 — паспорт машины/кузова, безопасный подбор и запрет некорректной загрузки; P1 — секции, специализированные автопоезда, цистерны и холодовая цепь; P2 — оптимизация сложной загрузки и датчики.

## 1. Задача

KERUENIX должен поддерживать подбор транспорта не только по «тоннажности» или «кубатуре», но по **проверяемым возможностям конкретной конфигурации**: тягач + полуприцеп + кузов/танк + секции/отсеки + водитель + дата/маршрут/температура/груз. Один только ярлык «20-тонник» или «рефрижератор» не доказывает пригодность.

**Связанные домены:** [03 — Domain Model](03-domain-model.md), [05 — Routing](05-routing-optimization-and-intelligence.md), [06 — Economics](06-pricing-fuel-and-settlements.md), [14 — Rescue](14-emergency-recovery-subcontracting.md), [15 — Warehouse](15-logistics-hub-wms-automation.md), [18 — Cargo Compliance](18-cargo-classification-and-compatibility.md).

## 2. Не смешивать оси классификации

| Dimension | Examples | Что фиксировать |
|---|---|---|
| Vehicle class | LCV/light van, medium rigid truck, heavy rigid truck, tractor + semi-trailer, road train | Категория регистрации, полная/снаряженная масса, оси, особенности |
| Body construction | Panel van, box, curtain/tent, flatbed, low-loader, tipper, container chassis | Внутренние габариты и схемы погрузки |
| Equipment capabilities | Tail-lift, crane, side/top loading, tie-down, pallets, partition, food-grade coating | Оборудование, грузоподъёмность устройства, исправность |
| Temperature | Insulated, mechanically refrigerated, freezer-capable, multi-temp | Фактически достижимый диапазон, независимость камер, сертификаты/калибровка |
| Bulk and tank | Fuel tanker, gas tank, food-grade liquid tank, chemical tank, dry bulk silo | Литры/м³, секции, плотность, совместимость материалов, разрешённая номенклатура |
| Hazard compliance | Dangerous goods vehicle/driver/tank requirements, approvals | Сроки действия, конкретные опасные грузы, применимые юрисдикции |
| Capacity metrics | Payload, internal m³, floor loading, pallet positions, cubic geometry | Несколько **независимых** ограничений одновременно |
| Operational readiness | AVAILABLE, RESERVED, MAINTENANCE, OUT_OF_SERVICE, INCOMPATIBLE | Состояние машины на дату/время поездки |
| Ownership / assignment | Own, leased, partner vehicle, temporarily contracted | Контракт, подтверждение доступности, водитель, liability |
| Cargo grouping | Mixed goods allowed, food-grade, no-odor, no-dangerous-goods, cleaning required | Строго проверяемый cargo-compliance, не только метка |

Названия «Газель», «пятитонник», «20-тонник», «82 куба» — **разговорные или маркетинговые**, а не нормативные категории. Система хранит тип/наименование для поиска, но решение принимает по фактическим атрибутам конкретного экземпляра.

## 3. Базовый каталог типов кузова и назначения

| Code | UI label | Fit / дополнительные проверки |
|---|---|---|
| DRY_BOX | Закрытый фургон | Паллета/коробки, внутренняя геометрия, двери, запахи |
| CURTAINSIDER | Тент / шторный | Боковая/верхняя загрузка, крепления, режим влагозащиты |
| INSULATED | Изотермический | Теплоизоляция, допустимая длительность/условия без активного охлаждения |
| REEFER | Рефрижератор | Работающий холодильный агрегат, заданная температура, режим и измерения |
| FREEZER_CAPABLE | Морозильный рефрижератор | Возможность поддерживать требуемую минусовую температуру, проверка фактических параметров |
| MULTI_TEMP | Многотемпературный | Изолированные отсеки, независимые зоны и датчики |
| FLATBED | Платформа | Габариты, крепление, защита и разрешённая нагрузка |
| LOW_LOADER | Низкорамная платформа | Габаритные/осевые ограничения, спецразрешения и сопровождение |
| TIPPER | Самосвал | Насыпная плотность, объём и безопасный способ разгрузки |
| GRAIN_BULK | Зерновоз | Санитарное состояние, защита от влаги, люки и разгрузка |
| CONTAINER_CHASSIS | Контейнеровоз | ISO-типоразмеры, twistlocks, массы контейнера и тягача |
| FUEL_TANKER | Топливная автоцистерна | UN/продукт, допуск цистерны, секции, материал и оборудование |
| GAS_TANKER | Автоцистерна/сосуд для газа | Давление/температура, тип опасного газа, отдельная сертификация |
| FOOD_TANKER | Пищевая цистерна | Материал, санобработка, история груза и допуск к продукту |
| CHEMICAL_TANKER | Химическая цистерна | Совместимость вещества/материала, мойка, ADR/специальные условия |
| SILO_TANKER | Цистерна для сухих сыпучих продуктов | Допустимая плотность, пневморазгрузка, влажность и давление |

Один реальный кузов может иметь несколько capabilities; перечисление кодов не означает автоматического разрешения на конкретную категорию продукции.

## 4. Паспорт транспорта / Vehicle Capacity Profile

### 4.1 Vehicle/Combination identity

`vehicle_id, plate, VIN/registrationRef, legal_owner, operator_tenant, tractor_id?, trailer_id?, body_id, active_assignment, vehicle_category, axle_layout, engine_type, permit_refs, insurance_refs, verification_status`.

**Тягач не имеет полезного объёма полуприцепа.** Грузоподъёмность, кубатура, танк и отсеки вычисляются для **фактически назначенной комбинации** тягач + полуприцеп/прицеп с учётом массы, сцепки, законной осевой нагрузки и состояния.

### 4.2 Capacity (different units are not interchangeable)

- `max_payload_kg`: документально подтверждённая полезная масса по машине/комбинации, не обязательно равная регистрационному GVM без поправок.
- `allowed_combination_gross_kg`, `actual_tare_kg`, `gross_per_axle_limit`, `available_payload_kg` на конкретный рейс.
- `nominal_body_volume_m3` и `usable_body_volume_m3`, внутренние `length_mm, width_mm, height_mm` с формой, выступами, колоннами, перегородками.
- `euro_pallet_positions`, `industrial_pallet_positions`, `max_floor_load_kg_m2`, `stacking_limit`, `max_unit_piece_kg`, `loading_aperture_mm`.
- `required_loading_direction`: rear, side, top; возможности погрузки/выгрузки, lift/forklift/dock compatibility.
- `remaining_capacity` после уже зарезервированных грузов/оборудования/тары и с учётом последовательности остановок.

**Нельзя** принимать груз на основании только двух сравнений `weight <= payload` и `volume <= m3`. Груз может не пройти через дверь, не разместиться на полу, давить на ось или быть несовместимым с другим грузом.

### 4.3 Для цистерн

`tank_id, tank_design_code?, certified_products?, compartment_ids, rated_volume_l, usable_fill_volume_l, tank_material, lining, previous_cargo, cleaning_status, inspection_expiry, pressure_rating, vapour_recovery_capabilities, hazard_approvals`.

Каждая секция хранит отдельно: номинальная ёмкость, конструктивные ограничения, допустимый груз, состояние, остатки, количество загрузки, массу и температурную поправку.

**Нужна проверка одновременно литров и килограммов.** Фактическая загрузка по массе зависит от плотности продукта при соответствующей температуре, а фактически разрешённый объём заполнения зависит от требований к продукту/цистерне и применимых норм, включая тепловое расширение и ограничения на частичное заполнение. Нельзя использовать универсальные проценты наполнения.

Перевозимое топливо является **грузом**, а топливо в собственном баке автомобиля — **расходом/запасом автомобиля**. Это разные доменные сущности и юридические режимы.

### 4.4 Холодовая цепь

`refrigeration_unit_id, insulation_type, set_point_c, validated_min/max_c, refrigeration_capacity, compartment_id, independent_zone_controller?, sensor_id, sensor_calibration_at, power_source, fuel_for_reefer, atp_or_local_certificate?, inspection_expiry, cleaning_status`.

- Изотерм не равен рефрижератору: пассивная изоляция сама не гарантирует поддержание заданной температуры.
- Рефрижератор, способный **поддерживать** замороженное состояние, не обязательно способен **быстро заморозить тёплый продукт**. Назначение должно проверяться по регламенту груза и характеристикам агрегата.
- Многотемпературная машина подходит только при доказанной независимости камер, наличии перегородок и достаточной холодильной мощности.
- Важны условия погрузки/выгрузки, открытие дверей, время без внешнего электропитания, прохождение склада и Rescue-перегрузка.
- Без действующей проверки датчиков/характеристик нельзя утверждать точность температуры.

## 5. Расчёт полезной вместимости

### Псевдоправило

    load_candidate = cargo + handling_units + pallets + dunnage
    combination = assigned_tractor + assigned_trailer/body + driver/resources
    validate gross weight and per-axle constraints
    validate remaining payload (after tare, equipment and existing loads)
    validate package orientation, door clearance, floor plan, stacking
    validate number/type of pallet positions and stop unloading order
    validate route legal restrictions and loading/unloading facilities
    validate CargoCompatibilityPort for neighboring cargo and vehicle body
    validate specialized capabilities (cold chain/tank/hazard/cleaning)
    return FEASIBLE | FEASIBLE_WITH_CONTROLS | INFEASIBLE | NEEDS_REVIEW

Для рулонов, длинномеров, паллет и нестандартных изделий геометрическое размещение важнее простой суммы кубов; при необходимости подключить упаковочный 3D-алгоритм/bin-packing как отдельный оптимизатор.

### Приоритет проверки

1. Право/безопасность/техническая пригодность.
2. Достоверность паспорта и фактическое состояние.
3. Физическая вместимость и допустимые осевые нагрузки.
4. Спецусловия груза — UN, температура, пищевые, санитарные.
5. Время работы/доступность водителя/ворот и маршрута.
6. Только затем — ETA, пустой пробег, цена и маржа.

## 6. Типовые кейсы

| ID | Сценарий | Ожидаемый результат |
|---|---|---|
| VEH-01 | Груз весит 8 т, но не помещается по высоте двери | INFEASIBLE |
| VEH-02 | Масса и общий объём в норме, но паллеты не помещаются на полу | INFEASIBLE |
| VEH-03 | Суммарный вес допустим, но превышается осевая нагрузка | INFEASIBLE |
| VEH-04 | Тягач без назначенного полуприцепа отображает «82 м³» | Запрет ошибочной заявки, нет capacity |
| VEH-05 | Рефрижератор без исправного агрегата выбран для замороженной продукции | INFEASIBLE/NEEDS_REVIEW по подтверждённому профилю |
| VEH-06 | Изотерм без активного охлаждения выбран при обязательном cold chain | Не допускать автоматический ALLOW |
| VEH-07 | Многозонная машина: охлаждённое и замороженное в разных секциях | Только с подтверждёнными независимыми режимами |
| VEH-08 | Бензин и дизтопливо в разных секциях автоцистерны | Проверка точных продуктов/цистерны/секций/регламента; не общий ALLOW |
| VEH-09 | Цистерна вмещает литры, но масса превышает payload | INFEASIBLE |
| VEH-10 | Ёмкость позволяет загрузку, но недействительный документ проверки танка | BLOCK/NEEDS_REVIEW до подтверждения |
| VEH-11 | Другая жидкость ранее перевозилась в цистерне без мойки | Проверить cleaning и совместимость |
| VEH-12 | В Rescue нужна замена рефрижератора на сухой кузов | BLOCK, если нет доказанного соблюдения температуры |
| VEH-13 | Сборный груз физически совместим с кузовом, но товарное соседство запрещено | DENY через CargoCompliancePort |
| VEH-14 | Warehouse gate не принимает высоту кузова / нет доступа для разгрузки | INFEASIBLE на этой точке |
| VEH-15 | Водитель сменил прицеп в пути | Пересчитать capacity/compatibility/route и версии |
| VEH-16 | Изменение наружной температуры/режима склада снижает уверенность в cold chain | Контроль датчиков и quality event |
| VEH-17 | Заказ загружен частично, другое соседство теперь недопустимо | Повторная проверка перед закреплением плана |
| VEH-18 | Компания A видит транспорт B только для разрешённого sub-contract | Ограниченная capacity projection, нет чужого GPS/маржи |
| VEH-19 | Партнёр рекламирует грузоподъёмность без документов | PROVISIONAL до verification |
| VEH-20 | Указаны 30 м³ по паспорту, фактически заняты паллетами 15 м³, но нет геометрии | Не считать оставшиеся 15 м³ гарантированно доступными |

## 7. Проверяемая модель для UI и поисковых фильтров

Два уровня:

**Быстрый поиск:** тип машины, ориентировочный тоннаж, кубатура, температурный режим, тип кузова, регион, доступность, стоимость.

**Подбор под конкретную заявку:** verified vehicle/trailer combination, actual free payload, door and internal geometry, existing cargo, axle limits, route/stop constraints, permitted cargo types, real temperature profile, tank product compatibility, documents, driver and loading equipment.

Клиенту показывается понятный тип кузова, **подтверждённая** вместимость и допустимые услуги; чужие номера транспортных средств, водительские контакты, маршруты и данные оборудования раскрываются только по контрактным разрешениям.

## 8. Java domain interfaces

```java
public interface VehicleCapabilityPort {
    VehicleSuitability assess(
        VehicleCombination combination,
        CargoLoadRequest cargo,
        RouteContext route,
        StopAndFacilityContext facilities
    );
}

public enum SuitabilityStatus {
    FEASIBLE, FEASIBLE_WITH_CONTROLS, INFEASIBLE, NEEDS_REVIEW
}

public record VehicleSuitability(
    SuitabilityStatus status,
    java.util.List<String> reasonCodes,
    java.util.List<String> requiredControls,
    String vehicleProfileVersion,
    String cargoRuleSetVersion,
    java.time.Instant evaluatedAt
) {}
```

Предлагаемые сущности: `Vehicle`, `VehicleCombination`, `Trailer`, `Body`, `VehicleCapability`, `CapacityProfile`, `BodyCompartment`, `PalletPosition`, `LoadPlanVersion`, `AxleGroup`, `VehicleCertificate`, `EquipmentInspection`, `RefrigerationUnit`, `TemperatureZone`, `TemperatureObservation`, `TankUnit`, `TankCompartment`, `TankProductApproval`, `TankCleaningRecord`, `VehicleSuitabilityAssessment`.

`VehicleCapabilityPort` оркестрирует `CargoCompatibilityPort`, но не заменяет его; Timefold выбирает только из доказанно допустимых кандидатов. Требования по фактической комбинации актуальны при Quote, Booking, Pickup, Replanning, Rescue и Warehouse dispatch.

## 9. Реестры и данные

Источники vehicle capacity: документ регистрации/производителя, актуальный осмотр и измерения, оборудование и маршрутные ограничения; у партнёров — подтверждённый профиль с датой и источником. Данные нельзя считать нормативными только потому, что водитель ввёл их в анкету.

Официальная классификация и требования по опасным грузам / цистернам — UNECE ADR и нормы страны; регулирование температурной перевозки и спецоборудования — UNECE ATP, с отдельной проверкой применимости к данной поездке.

References:
- UNECE ADR 2025: https://unece.org/ru/node/395825
- Kazakhstan government summary of dangerous-goods carriage (2026): https://www.gov.kz/org/dsek-astana/press/news/details/1314703?lang=ru
- Kazakhstan Ministry of Transport dangerous goods road rules: https://www.gov.kz/org/transport/documents/details/13851?lang=ru
- UNECE ATP valid 25 Aug 2026: https://unece.org/transport/road-transport/text-and-status-agreement
- UNECE ATP Handbook (2026): https://unece.org/atp-handbook

**Ни перечисленные названия типов машин, ни UI-маркетинговые «тонны/кубы» не дают разрешения на перевозку опасного или скоропортящегося товара. Для фактических решений требуется утверждённый юридически и технически набор правил.**

## 10. Очередность реализации

1. **P0:** Transport catalog, Vehicle/Trailer/Body identity, weight/volume/dimensions, load opening, pallet places, availability, certificates/verification source and route limitations. Tests of no double booking + suitability filters.
2. **P1:** cold chain (insulated/reefer/freezer/multi-zone), tanker (fuel/food/chem/gas) profiles, tank sections, cleaning/inspection, live temperature where supported, full CargoCompatibilityPort and Rescue checks.
3. **P2:** 3D pallet/bin packing, axle load distribution optimization, automatic compartment allocations, reefer/tank telemetry integration, specialized price and SLA factors.
4. **P3:** historical suitability/failed-load analytics, optimization performance and ML demand forecasts; **not** ML determination of legal permission.

**Gate:** 20 test cases above must pass for the implemented profile types and clearly return NEEDS_REVIEW for unsupported/unknown regulated combinations.

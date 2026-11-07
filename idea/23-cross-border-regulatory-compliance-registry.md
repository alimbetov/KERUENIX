# 23 — Regulatory Registry: Казахстан, ЕАЭС и международные перевозки

**Версия:** 0.1 · **Дата:** 07.11.2026. **Статус:** каталог источников и требований для проектирования, НЕ готовые законные разрешения/автоматизированная таможенная декларация.

## 1. Что обязательно определяет применимость

`regulation = f(country, border_crossing, route_segment, mode, effective_date, vehicle_combination, cargo_UN, cargo_HS_TNVED, customs_status, packaging, weight/axles, transport_contract)`.

При международной перевозке применимость отдельной нормы нельзя выводить из «международный рейс = ADR» или «ЕАЭС = всегда таможенный транзит». Составить список требований по **каждому участку, каждой стране, конкретному товару, транспортной комбинации, процедуре и времени**. Для некоторых случаев нужен экспертный/государственный документ, а не алгоритмический вывод.

## 2. Карта нормативных направлений с первоисточниками

| Код | Область | Правовой/стандартный источник | Для чего нужен |
|---|---|---|---|
| KZ-ROAD | Общие автомобильные перевозки | Приказ РК № 546, правила и действующие изменения | ТТН, перевозка, процедуры, требования к исполнению |
| KZ-DG | Опасные грузы автомобильным транспортом | Приказ № 460, изменения 2026; ADR для международной перевозки | Классы, документы, оснащение, допуски, маркировка |
| KZ-OVER | Крупногабаритные/тяжеловесные перевозки | действующие правила РК и актуальные изменения/спецразрешения | Масса/оси/маршрут/разрешение |
| EAEU-CUS | Таможенное право ЕАЭС | Таможенный кодекс ЕАЭС + национальное право РК | Процедура транзита, декларирование, СВХ, выпуск |
| EAEU-TNVED | Классификация товаров | ТН ВЭД ЕАЭС, действующая редакция | десятизначный код, ограничения и расчёты |
| WCO-HS | Международная классификация | WCO HS | международный 6-значный код, не маркировка товара |
| UNECE-CMR | Договор международной автоперевозки | CMR 1956; дополнительный протокол e-CMR 2008, применимость по маршруту | Накладная, договорная ответственность и доказательства |
| UNECE-TIR | Таможенный транзит | TIR Convention 1975; eTIR only on qualified corridors | Гарантия и процедура международного транзита при применимости |
| UNECE-ADR | Опасные грузы по автодорогам | ADR 2025 действующая на дату документа; проекты 2027 отдельно | UN dangerous goods, handling, labels, tanks, documentation |
| IMO-IMDG | Опасные грузы по морю | IMDG 2024 Amendment 42-24 (mandatory since 01.01.2026) | морские ограничения и сегрегация |
| ICAO-TI | Опасные грузы по воздуху | ICAO TI Doc 9284, edition 2025–2026 действующая до 31.12.2026 | air mode dangerous goods, docs |
| IATA-DGR | Операционная воздушная перевозка | IATA DGR 67th ed. (2026), provider specifics | airline operational rules |
| RAIL | Международный железнодорожный участок | RID where legally applicable; SMGS/CIM-SMGS per corridor; national rail rules | накладные и опасные грузы по rail |
| FOOD | Пищевая безопасность | ТР ТС 021/2011 и применимые санитарные правила | товарное соседство, хранение, температура |
| MED | Фармацевтические перевозки | актуальные национальные/отраслевые правила | cold chain, квалификация, контроль качества |
| GS1 | Trade and logistics identifiers | GS1 General Specifications 26.0.0 (2026), EPCIS/CBV 2.0 | GTIN, GLN, SSCC, scans, EDI |
| ISO-CONT | Международные контейнеры | ISO 6346:2022; replacement 2026 under publication on review | номер/владелец/тип контейнера |
| ISO-HND | Условные знаки на упаковке | ISO 780:2015, подтверждён действующим в 2026 | обращения с упаковкой, не hazard marks |
| ICC-INC | Международные торговые условия | ICC Incoterms 2020 при включении в договор продажи | распределение обязанностей и риска между продавцом/покупателем |

**Нормативная редакция ADR 2027:** UNECE опубликовала *draft amendments* для 01.01.2027; в справочнике KERUENIX они не должны активироваться преждевременно. **ISO 6346:2026** на момент проверки отмечался ISO как «Under publication»: нельзя автоматически считать финальной опубликованной заменой ISO 6346:2022 без повторной проверки.

## 3. Отдельные реестры: не делать один `cargoClass`

`ProductClassification`: SKU, GTIN, HS6, TNVED10, GPC category, country, legal revision, verification evidence.  
`DangerousGoodsDeclaration`: UN number, proper shipping name, hazard class, subsidiary risk, packing group (when applicable), quantity/packing, transport mode, applicable ADR/IMDG/ICAO/RID.  
`TransportHandlingProfile`: hygiene/temperature, signs ISO 780, package, cleaning, incompatible neighbors.  
`ContainerAsset`: ISO 6346 number, owner, size/type, seal, custody.  
`LabelCompliance`: GS1 label, hazard marks, mandatory national tracking codes per category (never silently conflated).  
`CustomsCase`: procedure, declaration references, MRN/registration where applicable, authorized actor, legal holds/releases, confirmation channel.  
`TransportDocuments`: CMR/eCMR, TIR/eTIR, TТН, packing list, commercial invoice, certificates, permits, cargo insurance and POD.

## 4. Казахстан: нюансы 2026

- В базе «Әділет» Правила перевозок грузов автомобильным транспортом №546 изменялись в **сентябре 2026**, и опасных грузов №460 — в **июле 2026**. RuleSet должен иметь `source_checked_at`, `effective_from` и отмечать новую редакцию; нельзя полагаться на текст 2024 или на старую инструкцию.
- В Казахстане система **KEDEN** в 2026 применяется для определённых таможенных процедур (включая функционал декларации на товары, запущенный в апреле 2026). Это **не означает**, что у KERUENIX имеется внешний API, разрешённый доступ или возможность автоматически выдавать выпуск.
- ЭСФ/СНТ, национальная маркировка/прослеживаемость (для соответствующих категорий), ТН ВЭД и таможенные декларации — разные информационные контуры. Модуль документального контроля должен определять **требуемость по фактам** и хранить официальный статус, не выдумывать единый «обязательный набор всем».
- Маршрут через границы должен разделять страны, погранпереходы, разрешения, таможенную процедуру и подтверждённые события прибытия/выезда. GPS у границы не является подтверждением завершения таможенного транзита.

## 5. Документальные чеклисты по контексту

| Контекст | Документы/сведения для проверки | Критерий готовности |
|---|---|---|
| Внутренний автомобильный KZ | договор/заказ, применимая ТТН, груз/вес/отправитель/получатель, разрешения спецгруза | актуальные реквизиты и подтверждение по действующим правилам |
| Международная автомобильная доставка | договор, CMR по применимости, invoice, packing list, разрешения, таможенные статусы, страховка по договору | всё применимо к маршруту и стране, ответственность определена |
| TIR | статус/право на TIR и гарантия, книжка/референс при применимости | подтверждение по действующей TIR-процедуре, не просто бумажный PDF |
| eCMR | коридор, правовая применимость, соглашение сторон, технический провайдер | подтверждённый правовой и технический маршрут eCMR |
| Опасный груз | точные UN-коды, packing/label documents, transport/driver/tank permissions | профильный специалист утвердил обязательные требования |
| Cold chain | режим изготовителя, карта температур, оборудование, мониторинг, нарушения | подтверждённое соблюдение режима и исключения |
| СВХ/customs hold | разрешённая процедура, источник удержания/выпуска, декларации/ссылки | только official/authorized release позволяет отгрузку |
| Rail/sea/air leg | документы режима (SMGS/CIM-SMGS, B/L, AWB и т.д.), опасные грузы по mode | separate mode-specific workflow и проверенный оператор |

**Требуемость** = алгоритм `mode × origin/destination/transit × cargo × trade transaction × customs regime × date × parties`. Страна и международный режим не заменяют договорных/страховых особенностей.

## 6. Compliance Engine и изменение правил

### RuleSet lifecycle

`DRAFT → SOURCE_VERIFIED → EXPERT_REVIEW → APPROVED → ACTIVE → SUPERSEDED/REVOKED`

- `RegulatorySource`: issuer, title, stable source URL, document/version, language, access/license, publication/effective dates, last_verified_at, owner.
- `RuleSet`: source references, rule code, scope country/mode/cargo/vehicle, priority, valid interval, author, reviewer, test cases, checksum, rollback.
- `ComplianceAssessment`: tenant, order/leg/handling units, input snapshot, results `ALLOW/ALLOW_WITH_CONTROLS/DENY/NEEDS_REVIEW`, evidence, reason codes, evaluated_at.
- `DocumentRequirement`: why required, source, issuer, owner, due time, submitted/verified/expired/rejected, masking policy.
- `RegulatoryChangeNotification`: changed source, impacted countries/modes/cargo, affected future bookings and in-flight shipments, impact approval decision.

### Deployment and operations

1. Fetch legally acquired change notifications from official sources; do not scrape unlicensed code tables.
2. A specialist reviews source and applicability; attach reference version/verification.
3. QA builds positive/negative tests and sample lanes.
4. Two-person approval for hazardous/customs rules.
5. Publish signed/pinned RuleSet with feature flag and phased activation.
6. Reassess new orders and at-risk active shipments; do not erase historical snapshots.
7. Rollback on erroneous changes, incident/ticket and compliance audit.

**Fail-closed on a critical missing rule**, but preserve a traceable manual expert review path when the law allows it. Human role cannot waive explicit legal prohibitions.

## 7. Integration/authorization boundaries

- Kazakhstan KEDEN and other govt systems: only via officially permitted integration and valid credentials. No direct assumptions about open APIs.
- CMR/eCMR, TIR/eTIR, EDI: each needs a partner/qualified provider and evidence of legal validity by lane.
- Personal/commercial/GPS fields not embedded in broadly shared labels or public tracking URLs.
- Document hash/evidence in RustFS/S3 behind tenant authorization, not full publicly readable files.
- Electronic signatures and custody evidence stored with format and verifier, preserving legal validity criteria.

## 8. Tests / decision gates

| ID | Проверка | Итог |
|---|---|---|
| REG-01 | международная shipment без HS/TNVED required classification | NEEDS_REVIEW |
| REG-02 | КЗ рейс с опасным грузом без обязательных ADR/national data | BLOCK / expert review |
| REG-03 | Правило ADR-2027 помечено DRAFT в 2026 | не использовать как активное в 2026 |
| REG-04 | новый KZ road act effective date наступил, старый ruleset активен | показать legal update alert, revalidation |
| REG-05 | customs hold, но склад/водитель просит release | DENY без подтверждённого уполномоченного освобождения |
| REG-06 | valid SSCC, но нет required dangerous-goods marking | DENY for release |
| REG-07 | CMR exists, no legal+technical eCMR verification | не выставлять eCMR-ready |
| REG-08 | TIR corridor/provider unsupported | manual qualified process / no false electronic transit |
| REG-09 | ISO6346 check digit mismatch | mark container identity invalid; investigation |
| REG-10 | shipper submits guessed HS code as authoritative | classification pending until authorized validation |
| REG-11 | route segment requires oversize permit, not present | PLAN_INFEASIBLE/REVIEW |
| REG-12 | no license for proprietary norm table | cannot activate unlicensed rule data |
| REG-13 | cross-tenant partner receives cargo docs | only scoped mandatory fields and current grants |
| REG-14 | active shipment vs change of legal rule | preserve old decision, re-evaluate where required, audit |
| REG-15 | country mode changes after Rescue/Multimodal | re-evaluate new legislation and document checklist |
| REG-16 | webhook "CUSTOMS_RELEASED" from untrusted source | reject, do not clear hold |

## 9. Primary sources

- KZ general road transport: https://old.adilet.zan.kz/rus/docs/V1500012463
- KZ dangerous goods: https://old.adilet.zan.kz/rus/docs/V1500011779
- KZ large/heavy vehicle rules (2026 amendments): https://old.adilet.zan.kz/rus/docs/V2600039338
- EAEU customs code ratification: https://old.adilet.zan.kz/rus/docs/Z1700000115
- KZ tax/customs TN VED guidance: https://www.gov.kz/org/kgd-vko/press/news/details/306165
- KEDEN 2026 stage: https://www.gov.kz/org/kgd/press/news/details/1210915?lang=ru
- UNECE ADR 2025 and 2027 drafts: https://unece.org/adr-2025-files
- UNECE CMR/e-CMR guide: https://unece.org/trade/documents/2023/10/executive-guide-e-cmr
- UNECE TIR/eTIR: https://unece.org/transport/tir and https://unece.org/transport/etir
- IMO IMDG 2026 effective: https://www.imo.org/en/publications/pages/imdg%20code.aspx
- ICAO TI 2025–26: https://www.icao.int/Dangerous-Goods/Technical-Instructions
- ICC Incoterms 2020: https://iccwbo.org/business-solutions/incoterms-rules/
- ISO 6346 publication status: https://www.iso.org/cms/live/live/en/sites/isoorg/contents/data/standard/09/08/90821.html

**Заключение:** в KERUENIX должен быть **Regulatory Rules & Evidence Registry**, а не произвольный boolean `internationalAllowed`. Это P0 для подготовки данных/аудита и P1 для автоматических проверок по конкретному международному коридору.

## Контроль документации v0.2

Каталог нормативных источников является **списком для проверки применимости**, а не юридическим заключением. Модель проверок, роли настоящих утверждающих специалистов и change-control описаны в [docs/06 — Standards & Compliance Governance](../docs/06-standards-compliance-governance.md). При работе с реальными грузами требуется повторная проверка актуальной редакции, страны, типа транспорта, режима транзита, доступа к официальному API и разрешений на использование нормативных данных.

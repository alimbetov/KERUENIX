# 22 — International Cargo Identification, Marking and Traceability Standard

**Статус:** проектный стандарт KERUENIX-ID v0.1 · **Дата:** 07.11.2026.  
**Назначение:** международно совместимый учёт товаров, партий, грузовых единиц, отправок, мест, транспортного оборудования и событий. **Никакой внутренний код не объявляется внешним стандартом без регистрации/соблюдения соответствующих правил.**

## 1. Правила идентификации: не смешивать разные сущности

| Объект | Preferred external ID | Internal key | Инвариант |
|---|---|---|---|
| Trade item/SKU | GS1 GTIN (если существует) | Product UUID | один GTIN — не уникальная конкретная паллета |
| Manufacturing lot | Batch/Lot в контексте GTIN/товара | Lot UUID | партия не идентифицирует отдельную грузовую единицу |
| Serialized trade item | GTIN + serial, когда применимо | Item UUID | не дублировать серийник при повторном скане |
| Logistics/handling unit | **GS1 SSCC (18 digits)**, AI (00) | HandlingUnit UUID | один SSCC на отдельную логистическую единицу в период её существования |
| Party / warehouse / ship-to location | **GS1 GLN** | Organization/Facility UUID | GLN не подменяет tenant_id или право доступа |
| Shipment / consignment | GS1 GSIN / GINC при согласованной схеме использования | Shipment UUID, Consignment UUID | разные коммерческие и физические границы |
| Returnable transport asset | GRAI / GIAI, если выдан | Asset UUID | паллета-актив и грузовая единица могут иметь разные ключи |
| ISO freight container | **ISO 6346 / BIC container number** | Container UUID | нужен check digit и BIC-зарегистрированный owner code |
| International trade location | **UN/LOCODE** | Facility UUID | международный терминал/город ≠ адрес ворот |
| Trade goods classification | **WCO HS six digits** and EAEU TN VED ten digits, as applicable | CargoClassification UUID | HS/TN VED не заменяют GTIN, UN опасного груза или SSCC |
| Dangerous goods | **UN number + technical proper shipping name + class etc.** | DangerousGoodsDeclaration UUID | номер UN не идентифицирует паллету |
| Physical road vehicle | National registration/plate/VIN as applicable | Vehicle UUID | номер/страна регистрации — не системное право на груз |

Дополнительно: ISO 3166-1 alpha-2 страны, ISO 4217 валюты, UTC/ISO 8601 timestamp, UN/CEFACT Recommendation 20 единицы измерения и Rec 21 типы упаковки. Нормы code lists фиксируются **версией**.

**Правильный join:** `shipment_uuid → handling_unit_uuid → optional GS1_SSCC → cargo_contents → product_uuid/optional GTIN/lot → cargo_compliance_profile`. External IDs хранятся как `(namespace, issuer, value, valid_from, valid_to, verified_at, evidence_ref)`, не как одно универсальное поле `code`.

## 2. GS1 barcode conventions

### SSCC

- GS1 SSCC — 18 цифр, включая контрольную цифру; формат и расчёт GS1. В KERUENIX должен быть GS1 check-digit validator.
- На GS1 Logistic Label ключевой обязательный идентификатор грузовой единицы — **SSCC**.
- GS1-128 со значением **AI (00)** — основной рекомендованный GS1 barcode для логистической этикетки; человекочитаемое написание `(00)SSCC18` не означает, что круглые скобки физически кодируются как данные GS1.
- Префикс компании и правила выделения/правомерного использования проверяются через GS1 и участника логистической цепочки. Не генерировать «SSCC» на основе UUID или текущего времени без уполномоченного префикса и процедуры.
- Один объект `HandlingUnit` может иметь несколько физических копий **одной** этикетки. Дублированный scan не создает нового physical stock.
- При разборке/сборке паллет: disaggregation/aggregation events с новыми parent/child relations; не переиспользовать SSCC произвольно для другой единицы.

### Useful GS1 application identifiers

| Human-readable AI | Значение | Ограничение |
|---|---|---|
| (00) | SSCC | 18 digits, check digit |
| (01) | GTIN | 14 digits format on GS1 AI, check digit |
| (02) | GTIN contained in a logistic unit | использовать с корректной семантикой состава и связанными AI |
| (10) | batch/lot | variable length; требуется FNC1/GS1 separator там, где предписано |
| (17) | expiry date | YYMMDD; диапазон дат/внутренняя семантика согласно GS1 |
| (21) | serial | variable length; namespace plus GTIN as required |
| (37) | count of trade items contained | зависит от применения AI (02) |
| (414) | GLN physical location | для идентификации соответствующей локации |

**Нельзя** без проверки General Specifications собирать произвольную строку AIs и объявлять её корректной GS1 этикеткой. Для 2D (GS1 DataMatrix/QR/Digital Link) отдельные правила применения; обычный QR с `/track/<token>` — клиентская ссылка, **не GS1 DataMatrix и не обязательная государственная Data Matrix маркировка**.

## 3. Шаблон логистической этикетки (концептуальная, не print-ready)

```text
+----------------------------------------------------------------+
| [Logo operator]             KERUENIX / WMS HANDLING UNIT        |
| SHIP FROM: [sender name / optional GLN]                         |
| SHIP TO:   [authorized delivery location / optional GLN]        |
| SHIPMENT:  [customer-visible shipment reference]                |
| HANDLING UNIT: [local LPN / optional label description]          |
| CONTENT: [minimal cargo description permitted by contract]      |
| COUNT: [N pallets/boxes] WEIGHT: [kg] TEMP: [range if relevant] |
| RESTRICTIONS: [handling symbols as required]                     |
|                                                                 |
| SSCC (AI 00): [VALID ALLOCATED 18-DIGIT SSCC]                    |
| [GS1-128 BARCODE SYMBOL — rendered by GS1 encoder]              |
|                                                                 |
| Other *legally required* hazard marks / UN labels separately    |
+----------------------------------------------------------------+
```

Это макет полей, **не** выданная GS1 этикетка. Для грузов, у которых нет GS1 SSCC, KERUENIX печатает честную внутреннюю этикетку `KERUENIX_INTERNAL_LPN` и barcode/QR с внутренним namespace без ложного AI (00). Участники могут позже мигрировать к GS1 без изменения идентичности `HandlingUnit UUID`.

**Символы обращения с упаковкой** регулируются ISO 780:2015 и не заменяют hazard labels. Опасные грузы требуют отдельной маркировки/знаков по применимому ADR/IMDG/ICAO/RID и national rules; один SSCC-штрихкод их не заменяет. Национальная обязательная маркировка Data Matrix по товарным группам — **третий независимый механизм** и должна учитываться отдельными полями/событиями.

## 4. EPCIS 2.0: «что — когда — где — почему — в каком состоянии»

EPCIS / CBV даёт межорганизационную основу для событий движения и преобразования грузовых единиц, но нельзя утверждать полную совместимость, просто назвав JSON «EPCIS».

Proposed mapping:
- `ObjectEvent`: поступила, проверена, отгружена конкретная идентифицированная единица;
- `AggregationEvent`: паллета собрана из коробок или расформирована;
- `AssociationEvent`: зависимость/соответствие, где уместно по семантике EPCIS;
- `TransactionEvent`: связь бизнес-транзакции и объектов при применимости;
- `TransformationEvent`: преобразование/переупаковка по спецификации и бизнес-смыслу.
- `readPoint/bizLocation` со стандартизированными ключами, `bizStep` и `disposition` по GS1 CBV; датчик и качество по EPCIS 2.0, если поддерживается.

Invariants:
1. `event_id` immutable + source/provider + `occurred_at` and `recorded_at` + tenant/grant.
2. Повторный scan/webhook создаёт **один** бизнес-эффект.
3. При изменении уровня упаковки сохраняется lineage содержимого (не просто увеличение склада).
4. Временной журнал может включать исправляющие факты, но не удаляет original event.
5. Доступ к EPCIS event зависит от участника/контрактов; владение SSCC не даёт публичного права чтения.

### Порядок событий

`ASN/DespatchAdvice → expected SSCC → GateIn → ReceivingScan → VerifiedReceipt → Putaway/Storage → Picking/Consolidation → LoadingScan → CustodyHandover → TripLeg → HubTransfer/Rescue → POD → Reconciliation`.

При частичной приёмке клиент видит точные подтверждённые количества/units, а не автоматический полный RECEIVED.

## 5. Международные документы и маркировка — разные данные

**Идентификатор**: SSCC/GTIN/GLN/UN/LOCODE/ISO6346.  
**Классификация**: HS, TN VED, UN danger classification.  
**Физическая маркировка**: GS1-128 label, handling symbols ISO 780, ADR hazard labels/placards, national DataMatrix, seal marks.  
**Документ**: contract, invoice, packing list, CMR/eCMR, TIR/eTIR reference, declaration, permit, SDS, temperature record, POD.

Для каждого отдельная роль и жизненный цикл: `ISSUED, VALIDATED, EXPIRED, REVOKED, DISPUTED` (только применимые значения). Валидность одной метки не означает наличия остальных документов.

## 6. Схема данных и API (предложение)

```java
public interface LogisticsIdentifierPort {
    IdentifierValidation validate(ExternalIdentifier identifier);
    HandlingUnitLabel issueInternalLabel(HandlingUnitId id);
    HandlingUnitLabel issueGs1LogisticLabel(HandlingUnitId id, ValidatedSscc sscc);
}
```

Модули:
- `identity-registry`: namespace and issuing authority, validator, GS1 keys, check digits;
- `cargo-master-data`: product, GTIN, batch, expiry, packaging, compliance;
- `label-service`: versioned PDF/ZPL templates, print permission, barcode generation and printer status (будущая реализация);
- `traceability`: ledger/events/outbox, EPCIS mapping + consent-filtered API;
- `document-registry`: content hashes, signed/validated documents, external official references;
- `wms`: stock/handling unit scan, location and custody;
- `shipment-tracking`: masked customer timeline; QR **не** обходит авторизацию.

`ExternalIdentifier` must carry `type, value, namespaceVersion, issuer, owner, status, verifiedAt, sourceEvidence`. Change/renewal makes a new version rather than rewriting prior shipments.

### Barcode and label security

- Scanner input length/charset/AI structure, check digit, code system and tenant scope validated.
- QR label may include a non-sensitive opaque resolver ID, not a permanent direct access credential.
- Printing and reprinting controlled/audited; label duplication triggers review only when context warrants.
- Payloads never include cargo price/margin, full customer contacts or auth tokens.
- Unauthorized person scanning label learns no protected shipment data.

## 7. Contract and acceptance tests (IDs LBL)

- **LBL-01:** valid allocated GS1 SSCC (18 digits/check digit) and legal prefix → GS1-128 printed; invalid → rejected.
- **LBL-02:** only internal UUID is available → INTERNAL_LPN label, not fake SSCC.
- **LBL-03:** AI (00)/(01)/(10)/(17)/(21) decoded with parser respecting fixed/variable length; invalid separators reject.
- **LBL-04:** GS1 check-digit validator rejects corrupted code.
- **LBL-05:** same SSCC scanned five times with same operation/event id → one receipt.
- **LBL-06:** same visible external code reused by different tenant without proof of authority → conflict/verification, not silent merge.
- **LBL-07:** goods split 1 parent pallet into 2 handling units → aggregate lineage and quantity conservation.
- **LBL-08:** label lost/damaged → controlled reprint, original HandlingUnit identity preserved.
- **LBL-09:** cargo owner, warehouse keeper and forwarder have distinct visibility, even with shared SSCC.
- **LBL-10:** dangerous goods lacking mandatory hazard markings → load release blocked even with valid GS1.
- **LBL-11:** national product marking missing for category where legally required → hold according to verified rule.
- **LBL-12:** ISO 6346 container code check digit/owner prefix validation and mapping to internal container.
- **LBL-13:** HS6 and TNVED10 stored as different code systems, leading zeroes preserved.
- **LBL-14:** EPCIS Aggregation/Disaggregation events retain child-unit count and relations.
- **LBL-15:** offline scanner replay/out-of-order cannot create double stock.
- **LBL-16:** revocation of guest tracking link doesn't change physical SSCC label.
- **LBL-17:** cold-chain sensor event references handling unit/compartment and calibrated timestamp; stale data flagged.
- **LBL-18:** identical product GTIN from two owners never merges ownership/stock balances.
- **LBL-19:** labels respect local language but identifier representation remains globally canonical.
- **LBL-20:** printed copy scan returns only permitted data, not finance or customer secrets.

## 8. Adoption plan

**P0:** internal UUID + CargoUnit/HandlingUnit + external ID namespaces; GS1 SSCC import/verify; basic GS1-128 label when authorized; local label fallback; immutable movements; HS/TN VED fields; legal hazard mark flags and documentary checks.

**P1:** proper issuer workflow for new SSCC/GLN if customers need label allocation; GS1 EPCIS event mapping (capability test), warehouse handheld scanning, partial shipments, ISO6346 and UN/LOCODE dataset.

**P2:** national category-specific DataMatrix systems, EDI/GS1 XML, RFID/GS1 Digital Link, automation, label printer queue and advanced cargo temperature.

## 9. Primary sources

- GS1 standards/version repository: https://ref.gs1.org/standards/
- GS1 identification keys: https://support.gs1.org/support/solutions/articles/43000734443-which-gs1-identification-keys-are-used-in-transport-logistics-processes-
- GS1 logistic label compulsory SSCC: https://support.gs1.org/support/solutions/articles/43000734484-what-is-the-only-compulsory-data-on-the-logistic-label-
- GS1 AI directory: https://ref.gs1.org/ai/
- GS1 EPCIS and CBV: https://ref.gs1.org/standards/epcis/
- GS1 Kazakhstan SSCC: https://gs1.kz/ru/page/sscc
- ISO 6346/BIC identifiers: https://www.bic-code.org/bic-codes/
- ISO 780:2015 (handling marks): https://www.iso.org/standard/59933.html
- UNECE UN/LOCODE: https://unece.org/trade/documents/2023/10/executive-guide-unlocode
- UNECE Rec 20 units and Rec 21 packages: https://unece.org/code-list-recommendations
- Kazakhstan sector-specific marking rules: https://old.adilet.zan.kz/rus/docs/V2600039858

**Важно:** нормативные/коммерческие части международных стандартов могут быть защищены авторским правом или лицензией. Не копировать полные тексты, таблицы ADR/IMDG/ISO/GS1 за пределами допустимых прав; хранить исходную ссылку, версию, использованный набор разрешённых данных и доказательство лицензии.

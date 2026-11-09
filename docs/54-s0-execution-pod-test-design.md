# 54 — S0 Execution/Custody/POD: проект тестовых контрактов

**09.11.2026 · Статус `PROPOSED_NOT_REVIEWED` — только Scenario Design.**
[Машинный пакет 25 контрактов](contracts/r0-s0-execution-pod-case-contracts.v1.json) основан на [матрице исходных R0 сценариев](contracts/r0-scenario-allocation.v1.json) и [пошаговых E2E](contracts/r0-e2e-s0-draft.v1.json).

## Состав и ответственность

**22 primary** R0 сценария — PR-13 Execution/Custody (11) и PR-14 POD (11). Ещё **3 impacted cross-role E2E**, где первичный владелец остаётся PR-19: E2E-04 (Pickup 10 → POD 8/10), E2E-05 (Cancel vs Trip.STARTED), E2E-07 (suspended tenant + mandatory POD). Никакой передачи владельца этих E2E Execution-модулю не производится.

**Данные фикстуры:** Tenant-A/Customer-X с 10 стабильными `HandlingUnitId`, driver assignment history, verified receiver restricted to one `DeliveryAttempt`, offline pending queue с `eventId` и digest. 8 единиц приняты, 2 отклонены/возвращаются и имеют известного текущего custodian. Попытки подмены tenant и отозванного полномочия, crash before ACK, out-of-order replay.

## Оракулы до S1 — что именно должны проверить тесты

| Группа | DB/Domain инвариант | Outbox/Inbox/side effects | API/UI |
|---|---|---|---|
| **Pickup / offline** `TDD-SIM-24-G15-01…05` | Текущий и исторический driver assignment/version перепроверяются сервером. В каждый момент у единицы один достоверный custodian; событие с ложным `observedAt` не авторизует revoked driver | При одинаковых `eventId+digest` только один логический эффект; изменённый digest → конфликт/карантин, не второй handover | Offline `PENDING` до серверного подтверждения, не ложный `IN_CUSTODY` |
| **Partial POD** `TDD-SIM-28-G18-01…05` | **8 accepted + 2 refused/retained = 10**. Остаточные 2 имеют подтверждённый custodian и disposition; `Shipment != DELIVERED` | Нет `ShipmentDelivered(all)`, исправление POD append-only, подписанный оригинал и hash неизменяемы | Показывать **PARTIAL 8/10**, отдельные 2 остатка, review закрыт до полной подтверждённой доставки |
| **Safety/incident** `TDD-SIM-23-S14-01`, `25-S16-01`, `27-S17-01`, `29-S19-01`, `29-S25-01` | Несовпадение массы/seal → нет Pickup; breakdown → RecoveryCase с прежним custodian; receiver absent → failed attempt | Нет несуществующих transfer/DeliveryAccepted; issue-report не превращает shipment в DELIVERED | Нужна отдельная история инцидента и доказательств |
| **Negatives** `NEG-R0-025…031` | Отозванный водитель, повторный изменённый payload, reassign без handover, позднее offline событие, чужой guest link и недопустимое редактирование оригинала **не меняют** authoritative custody | Нет ложного `PickupConfirmed`, `DeliveryAccepted`, `ShipmentDelivered`, `DeliveryReversed` | DENY/CONFLICT/NEEDS_RECONCILIATION без раскрытия чужих данных |
| **Cross-role** E2E-04/05/07 | Отмена никогда не освобождает ресурс при активном custody; при suspension доказательства сохраняются в рамках только утверждённого continuity-scope | Idempotent safety events; ни нового коммерческого Booking, ни двойного движения груза | Driver/operator/customer видят согласованное состояние |

## Незакрытые решения и Test Review

`BR-09` (custody/handover), `BR-10` (POD/signing), `DEC-R0-08` (custody ownership) остаются `PENDING`. E2E Cancellation и suspension затрагивают также `BR-04/06/07/11` и `DEC-R0-01/04`. **Положительные юридически значимые переходы пока только условные**: до предметного approval допустимы fail-closed DENY/HOLD/incident/evidence capture в чётко ограниченной модели.

При Review проверить: точные роли, unit-level conservation, запрет временной перемотки custody при out-of-order offline event, токен receiver с областью одной попытки, сопоставление object hash и доказательство подписи, атомарное DB+Outbox, строгие race fixtures на реальном PostgreSQL.

**S1 ещё не начинался**: этот документ не заявляет JUnit GREEN и не открывает реализацию PR-13/14. Никаких платежей, AR/AP, refund.

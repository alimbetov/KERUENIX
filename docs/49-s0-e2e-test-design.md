# 49 — S0 E2E Test Design: девять полных маршрутов (черновик для Review)

**Статус:** `S0_E2E_GIVEN_WHEN_DRAFT` · 2026-11-08 · **НЕ TEST_REVIEWED, НЕ IMPLEMENTED.**

[Машинный пакет пошаговых GWT и HTTP/DB/Outbox/UI-оракулов](contracts/r0-e2e-s0-draft.v1.json) дополняет исходные 10 cross-role E2E в [R0 Case Bank](contracts/r0-tdd-scenarios.v1.json). Только **9 актуальны**, `TDD-R0-E2E-06` окончательно retired по NO PAYMENTS.

**Каждый сценарий содержит:** roles, синтетические предусловия, пошаговые действия, исходный неизменённый `canonicalThen`, отдельные DB/HTTP/UI/Outbox-проверки, минимум два негативных варианта и текущий список блокирующих BR/DEC из [S0 allocation](contracts/r0-scenario-allocation.v1.json). Нельзя считать эти материалы автоматическими тестами до следующего этапа Test-First.

## 1. Cross-role GWT маршруты

| Case | Given — предварительное состояние | When — сценарий | Обязательный Then |
|---|---|---|---|
| **E2E-01** | Provider Tenant-A и два разделённых CustomerAccounts, проверенные роли; нет CapacityReservation | Customer X invite → RFQ → provider inbox → immutable QuoteVersion → подпись → попытка Booking без capacity | Чужие данные/COUNT не раскрыты; без capacity нет BookingConfirmed |
| **E2E-02** | External carrier, valid compliance, конкурирующий hold | Carrier offer → independent commitment → exclusive capacity hold → Booking | Одно подтверждение ресурса; offerSelected ≠ carrierCommitted ≠ BookingConfirmed |
| **E2E-03** | Собственный Fleet resource, нет внешнего CarrierOffer | Own-fleet hold → второй concurrent hold → Booking | Нет фиктивного carrier offer; эксклюзивная ёмкость |
| **E2E-04** | 10 разных HandlingUnit, подтверждённый водитель, scoped receiver | Pickup → offline event → POD 8/10 → отказ/возврат 2 → replay | 8 приняты, 2 остаются с custodian/disposition; оригинал POD неизменяем; Shipment не DELIVERED |
| **E2E-05** | Booking CONFIRMED, варианты Trip не начался / уже STARTED | CancelRequest → approval/denial → race Trip.STARTED → compensation | CancelRequest ≠ Booking.CANCELLED; нельзя освободить ресурс при активной custody |
| **E2E-07** | Tenant suspended во время активной custody | Mandatory POD по условному safe-continuity → fresh Booking → restart/retry | Только одобренная safety-операция; никакого unrestricted fallback или нового Booking |
| **E2E-08** | Sales подтверждает происхождение телефонного RFQ; Customer ещё не подписал | Assisted RFQ → Quote → попытка подписи от Sales → отдельная подпись customer | Нельзя подменять customer-signatory сотрудником провайдера |
| **E2E-09** | CustomerAccount X/Y, тёплый кэш и действующий signed URL | Grant revoke → API read/count/export → old/new URLs → проверка Customer-Y | Protected API DENY сразу; прежние signed URL имеют **заранее согласованную** TTL-семантику |
| **E2E-10** | Quote accepted, carrier может отозвать Offer до или после capacity hold | Withdraw → reselect → cancel/reconcile hold → Booking | Нет фиктивного подтверждения; процесс восстанавливается из доказанных состояний |
| **E2E-06** | — | **Retired**: bank receipt/payment settlement | Не реализовывать, заменить `PAY-ABS-01…06` |

Все `positive` юридически значимые переходы в таблице **условны**: подписант, правовой профиль, лимит безопасности и необходимые BR/DEC ещё не согласованы. Пока их нельзя подтверждать, тестовый baseline — **DENY/HOLD**, а не симуляция юридического разрешения.

## 2. Критические тестовые доказательства S1 (после Scenario Design Review)

- **Execution + Cargo conservation:** отдельные `HandlingUnitId`, captured quantity 10 = accepted 8 + retained 2; timeline каждого хэндовера, immutable hash, outbox events и Inbox replay.
- **Tenancy/Account scope:** provider tenant и Customer-X/Y независимы; проверять не только detail, но COUNT, search/export, cache, object URL, geo history.
- **Concurrency:** overlapping capacity holds, cancel versus Trip.STARTED, carrier offer revoked with a stale confirmation, last-writer optimistic version.
- **Security:** действующий подписанный JWT после grant revoke не доказывает право; проверять серверный источник, отсутствие запрещённых записей и побочных эффектов.
- **Signed evidence:** NCA/EDS certificate/authority and exact signed bytes only after legal profile approval; photo or GPS is not custody proof.
- **Recovery:** crash after commit before event ACK, retry/dedup, object-storage unavailable, read-model stale and PostgreSQL restore.

## 3. Что необходимо на Test Review

1. Утвердить конкретные roles/grants и Given без неявного доверия JWT tenant claim.
2. Для E2E-05 определить canonical cancellation authority и compensation (BR-11, DEC-R0-04).
3. Для E2E-07 утвердить разрешённый объём continuity (BR-04), пока всё discretionary запрещено.
4. Для E2E-09 утвердить TTL/revocation семантику signed URL; нельзя обещать мгновенный отзыв pre-signed ссылки без доказательства.
5. Для E2E-04 согласовать формы/полномочия POD и остаточных двух грузовых единиц (BR-09/10).
6. Для E2E-01/02/08/10 согласовать точное доказательство принятия Quote и CarrierCommitment (BR-01/02/05/06 + SIG).
7. Сопоставить все E2E с завершёнными PR: не скрывать skips и не превращать mock-only сценарии в production qualification.

**Итог:** девять role-by-role сценариев спроектированы в статусе **DRAFT**. Они устраняют отсутствие подробных шагов в **предложении**, но оригинальный банк не изменён и до предметной приёмки сохраняет девять открытых GWT review-gaps. Переход в S1 не разрешён.

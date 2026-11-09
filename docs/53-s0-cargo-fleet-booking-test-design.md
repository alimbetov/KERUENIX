# 53 — S0 Cargo/Compliance/Fleet/Booking: контрактный план тестов

**2026-11-08 · `PROPOSED_NOT_REVIEWED` · только Scenario Design.**

[37 машинных GWT/Oracle контрактов](contracts/r0-s0-cargo-fleet-booking-case-contracts.v1.json) построены по [132-case allocation](contracts/r0-scenario-allocation.v1.json) и [Cargo extension](contracts/r0-s0-extension-gwt.v1.json). Сюда входят **27** основных сценариев PR-09/10V/10/12/12C, **4** cross-owner E2E PR-19 и **6** дополнительных CargoProfile/HandlingUnit проектов для PR-08. Тесты и доменная реализация **не создавались**; S0 review не подписан.

## 1. Test-First проектируем до production-кода

| Модуль/PR | Основные тестовые требования | Неприемлемое поведение |
|---|---|---|
| Cargo / PR-08 | `PR08-CARGO-01…06`: десять уникальных HandlingUnit, корректная масса/единицы, отрицательные значения, idempotency/digest, immutable quoted snapshot и Customer-X/Y scope | Скрытое редактирование Cargo после Quote, расхождение unit count, неверная масса, чужие данные |
| Compliance / PR-09 | `TDD-SIM-19-G13-01…05`, `NEG-R0-021…024`: источник RuleSetVersion, квалификация actor, устаревшее правило, race/replay, unknown/hazardous profile | `UNKNOWN` или истёкшее подтверждение превращаются в READY/ALLOW/Booking |
| Fleet registry / PR-10V | `NEG-R0-016`: собственный автопарк допустим без выдуманного внешнего перевозчика; зарегистрированная физическая связка компонентов принадлежит проверенному owner | Фиктивная CarrierOffer/CarrierCommitment только для прохождения универсального потока |
| Capacity / PR-10 | `TDD-SIM-18-G12-01…05`, `TDD-SIM-17-S11-01`, `NEG-R0-017…019`: эксклюзивный overlapping hold, lease TTL, stale worker, confirmed/consumed capacity, all-or-nothing набор ресурсов | Два активных эксклюзивных резерва, освобождение подтверждённого hold устаревшим job, частичный commit |
| Booking / PR-12 | `NEG-R0-020`: атомарное подтверждение только с Quote/Compliance/Capacity/Carrier evidence; Inbox replay | OfferSelected, QuoteAccepted или CapacityHeld по отдельности считаются BookingConfirmed |
| Cancel / PR-12C | `TDD-SIM-21-G21-01…05`, `NEG-R0-045/046`: отдельные CancelRequested/Approved, Trip.STARTED race, custody, компенсации | Booking немедленно CANCELLED по запросу клиента; CapacityReleased пока груз остаётся под ответственностью |
| Cross-role / PR-19 | `TDD-R0-E2E-02/03/05/10`: Carrier+Capacity, own-fleet, cancel vs Trip.STARTED, carrier withdrawal | Принятие непроверенной capacity/carrier и ложное окончание процесса |

## 2. Ожидаемые тестовые оракулы

- **Persisted state:** однозначные owner/tenant/customer, immutable QuoteVersion и CargoSnapshot; единственный эксклюзивный ресурс; сохранённое поколение lease; `UNKNOWN` compliance приводит к HOLD; отмена сохраняет cargo custody до доказанного перехода.
- **Outbox/Inbox/Audit:** нет `BookingConfirmed` без полного набора обязательств; конкурентные/повторные команды не производят второй логический эффект; stale job не публикует `CapacityReleased`; компенсации версионированы.
- **HTTP/UI:** разделить `HELD/CONFIRMED/CONSUMED/EXPIRED`, `REQUESTED/CANCELLED`, `OFFER_SELECTED/CARRIER_COMMITTED/BOOKING_CONFIRMED`. Ни один PENDING, DENY или HOLD не отображать как завершённую перевозку.

Особое требование к S1: **конкуренцию CapacityHold нужно доказывать на настоящем PostgreSQL**, двумя независимыми транзакциями, а не на `Mockito`. Проверять блокировки, ограничения уникальности, replay, момент TTL expiry, lease takeover и состояние всех зависимых агрегатов после падения.

## 3. Неподтверждённые решения

`BR-06` — полномочия перевозчика; `BR-07` — эксклюзивность ресурсов; `BR-08` — нормативный профиль груза; `BR-11/DEC-R0-04` — правила отмены. `DEC-R0-01` — источник истины Booking; `DEC-R0-06` — own-fleet модель. Все пока в `PENDING` в реестре BR/DEC, кроме них сценарии E2E также зависят от дополнительных неутверждённых решений. Техническое проектирование fail-closed допускается; позитивные binding-переходы не активируются.

## 4. Границы и результат

Это **S0 технический проект**, а не завершённый S2 Test Review. Перед S1 необходимы предметное подтверждение источников права, идентичности физического ресурса, точных SQL constraints, владелец каждого aggregate и фикстур race/crash, негативный оракул по всем 37 ID.

Продукт остаётся без платежей, банковских шлюзов, AR/AP и внутренних `PAID/SETTLED` состояний. PR #1 Draft; `main` не меняем.

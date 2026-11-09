# 29 — Активные Read Models, Partition Manager и PostGIS

**Статус:** IDEA → архитектурное ТЗ PROPOSED · **Дата:** 07.11.2026.

## Проблема

При работе с тысячами машин и многими компаниями частые GPS-наблюдения, geofence и карта клиента не должны перегружать таблицы договоров/бронирований. Одновременно дорогие многомодульные чтения нельзя превращать в джойны чужих JPA entities, а хранение всей GPS истории без ретенции и партиций станет операционно дорогим.

## Решение

- **Single-write per domain:** отдельный владелец коммерческого заказа, машины, груза, custody и финансов.
- **Active Read Model:** `fleet_current_position`, `customer_shipment_snapshot`, availability/stock/cost projections. Автоматическое обновление по событиям с watermark, dedup, freshness и rebuild. Только read, не source для критичного booking/payment decision.
- **Selected partitioning:** GPS append-only `RANGE(observed_at)`; плановое создание будущих partitions, поздние события, global dedup, legal-hold-aware retention. Остальные таблицы только при обоснованной нагрузке, не по принципу «модуль = partition».
- **PostGIS:** валидированные координаты SRID 4326, GiST, зоны складов, поиск свободного транспорта по радиусу, геозонные события и route geometry. Spatial proximity не равна дорожной проходимости, legal permission или custody.
- **Cloud/On-Prem:** одинаковый data contract, `pg_partman` optional, fallback privileged scheduler. Бизнес-приложение не запускает DDL на каждый запрос.

## Возможные применения

1. Клиент видит последнее **разрешённое** местоположение своей отправки и время его получения; не всю GPS-историю машины.
2. Rescue Network получает shortlist автомобилей в 50 км, но окончательное предложение возможно только при совместимости груза и законном маршруте.
3. Yard/warehouse учитывает geofence для прибытия, но приём груза создаёт отдельный складской scan и custody.
4. Данные оператора A никогда не появляются в геопоиске оператора B без explicit partner grant.
5. Восстановление после отказа GPS ingestion не создаёт пропущенные/дублированные события, данные из старой partition корректно воспроизводятся.

## Следующие артефакты

- [ТЗ по хранению/GIS](../docs/15-data-platform-partitioning-postgis.md)
- [Дополнение по всем модулям](../docs/16-module-storage-gis-addendum.md)
- [JSON-контракт](../docs/contracts/storage-gis-module-contract.v1.json)

**Ограничение:** это предложение для реализации; нет работающей БД, GIS SQL, background job, performance benchmark, безопасности RLS или подтверждённого CI.

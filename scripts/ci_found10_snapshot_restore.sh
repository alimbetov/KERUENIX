#!/usr/bin/env bash
# FOUND-10: only the disposable GitHub Actions PostgreSQL instance is allowed.
# Called AFTER Liquibase V1 baseline and BEFORE original V1->V2 migration.
set -euo pipefail
: "${PGHOST:?}" "${PGPORT:?}" "${PGUSER:?}" "${PGPASSWORD:?}"
: "${KERUENIX_BACKUP_PATH:?}"
export PGDATABASE=keruenix_upgrade_test

psql -X -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO platform.outbox_event
  (tenant_id, event_id, event_type, aggregate_ref, payload_schema_version,
   payload, payload_sha256)
VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
   '33333333-3333-3333-3333-333333333333',
   'FixtureV1', 'found10:restore', 1,
   '{"tag":"found10-v1","revision":7}'::jsonb,
   repeat('c', 64));
INSERT INTO platform.audit_fact
  (tenant_id, audit_id, actor_ref, action_type, subject_ref)
VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
   '44444444-4444-4444-4444-444444444444',
   'fixture:restore','Found10Snapshot','found10:restore');
SQL

# pg_dump is a real physical-data snapshot, not an empty-schema clone.
# The Ubuntu host's pg_dump can be newer than PostgreSQL 16, producing
# restore statements (e.g. transaction_timeout) that PG16 does not support.
# Use matching PG16 client utilities inside the GitHub Actions service container.
pg_container=$(docker ps -q --filter "ancestor=postgis/postgis:16-3.7" | head -n 1)
[[ -n "$pg_container" ]] || { echo "PostGIS 16 service container not found" >&2; exit 1; }
docker exec "$pg_container" pg_dump --format=custom --no-owner \
  -U postgres --dbname=keruenix_upgrade_test > "${KERUENIX_BACKUP_PATH}"
test -s "${KERUENIX_BACKUP_PATH}"
psql -X -v ON_ERROR_STOP=1 -d postgres -c 'CREATE DATABASE keruenix_restore_test'
docker exec -i "$pg_container" pg_restore --exit-on-error --no-owner \
  -U postgres --dbname=keruenix_restore_test < "${KERUENIX_BACKUP_PATH}"

for db in keruenix_upgrade_test keruenix_restore_test; do
  result=$(psql -X -At -v ON_ERROR_STOP=1 -d "$db" <<'SQL'
SELECT concat_ws('|',
  (SELECT payload::text FROM platform.outbox_event
   WHERE tenant_id='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
     AND event_id='33333333-3333-3333-3333-333333333333'),
  (SELECT payload_sha256 FROM platform.outbox_event
   WHERE tenant_id='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
     AND event_id='33333333-3333-3333-3333-333333333333'),
  (SELECT subject_ref FROM platform.audit_fact
   WHERE tenant_id='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
     AND audit_id='44444444-4444-4444-4444-444444444444'),
  (SELECT count(*) FROM public.databasechangelog));
SQL
)
  test -n "$result"
  if [[ "$db" == "keruenix_upgrade_test" ]]; then
    expected="$result"
  else
    [[ "$result" == "$expected" ]] || {
      echo "FOUND-10 restored data differs from V1 source" >&2
      exit 1
    }
  fi
done
echo "FOUND-10 backup/restore pre-upgrade payload and audit match"

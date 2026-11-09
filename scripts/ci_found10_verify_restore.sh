#!/usr/bin/env bash
set -euo pipefail
: "${PGHOST:?}" "${PGPORT:?}" "${PGUSER:?}" "${PGPASSWORD:?}"
reference=""
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
  (SELECT count(*) FROM public.databasechangelog),
  (SELECT bool_and(relrowsecurity AND relforcerowsecurity) FROM pg_class
   WHERE oid IN ('platform.audit_fact'::regclass,
                 'platform.outbox_event'::regclass,
                 'platform.inbox_receipt'::regclass)));
SQL
)
  [[ "$result" == *"found10-v1"* ]] || { echo "Missing V1 fixture in $db" >&2; exit 1; }
  [[ "$result" == *"found10:restore"* ]] || { echo "Missing audit record in $db" >&2; exit 1; }
  [[ "$result" == *"|2|t" ]] || { echo "V2 checksum/RLS state incorrect in $db: $result" >&2; exit 1; }
  if [[ -z "$reference" ]]; then reference="$result"; else
    [[ "$result" == "$reference" ]] || { echo "Restored V2 differs from original V2" >&2; exit 1; }
  fi
done
echo "FOUND-10 populated V1->V2 & restore->V2 preserve payload, audit, history, FORCE RLS"

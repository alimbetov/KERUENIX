#!/usr/bin/env bash
set -euo pipefail
: "${KERUENIX_DB_URL:?Real PostgreSQL URL is mandatory}"
[[ "$KERUENIX_DB_URL" == jdbc:postgresql:* ]] || exit 2
log="$(mktemp)"; trap 'rm -f "$log"' EXIT
set +e
KERUENIX_A03_DIGEST_RED=true mvn -B -ntp -f backend/pom.xml -Dtest=OutboxPayloadDigestIntegrityRedTest test >"$log" 2>&1
code=$?
set -e
cat "$log"
[[ $code -ne 0 ]] || { echo "ERROR: A-03 expected digest integrity RED unexpectedly passed" >&2; exit 1; }
grep -Fq 'A03_OUTBOX_DIGEST_MISMATCH_REACHED_SENDER' "$log" || { echo "ERROR: no A-03-specific assertion" >&2; exit 1; }
grep -Eq 'Tests run: 1, Failures: 1, Errors: 0, Skipped: 0' "$log" || { echo "ERROR: unexpected tests/errors/skips" >&2; exit 1; }
if grep -Eq 'COMPILATION ERROR|Failed to load ApplicationContext|Could not resolve dependencies' "$log"; then
 echo "ERROR: infrastructure failure, not behavioral RED" >&2; exit 1
fi
echo "EXPECTED_A03_DIGEST_BEHAVIOR_RED: real PostgreSQL Outbox sends payload with mismatched SHA256"
echo "NOT_A03_IMPLEMENTED: canonicalization and enforcement remain pending S2"

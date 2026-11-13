#!/usr/bin/env bash
set -euo pipefail
: "${KERUENIX_DB_URL:?PostgreSQL required}"
[[ "$KERUENIX_DB_URL" == jdbc:postgresql:* ]] || exit 2
log="$(mktemp)"
trap 'rm -f "$log"' EXIT
set +e
KERUENIX_A04_RETRY_RED=true mvn -B -ntp -f backend/pom.xml \
  -Dtest=OutboxPoisonEventRedTest test >"$log" 2>&1
exit_code=$?
set -e
cat "$log"
[[ $exit_code -ne 0 ]] || { echo "A04 expected RED unexpectedly GREEN" >&2; exit 1; }
grep -Fq "A04_POISON_EVENT_REMAINS_RETRYABLE_AFTER_MAX_ATTEMPTS" "$log" || {
 echo "A04 specific behavior failure not observed" >&2; exit 1;
}
grep -Eq 'Tests run: 1, Failures: 1, Errors: 0, Skipped: 0' "$log" || {
 echo "A04 arbitrary error/skip is not behavioral RED" >&2; exit 1;
}
if grep -Eq 'COMPILATION ERROR|Failed to load ApplicationContext|Could not resolve dependencies' "$log"; then
 echo "A04 infrastructure failure" >&2; exit 1;
fi
echo "EXPECTED_A04_POISON_EVENT_BEHAVIOR_RED: third failure remains PENDING rather than DEAD_LETTER"
echo "A04_POLICY_PROPOSED: three attempts is an S0 candidate, not approved production policy"

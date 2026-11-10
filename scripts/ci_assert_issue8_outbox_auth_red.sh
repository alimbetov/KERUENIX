#!/usr/bin/env bash
# Issue #8: expected BEHAVIORAL RED in the existing REAL PostgreSQL Outbox.
# Only the targeted missing CustomerAccount authorization barrier is acceptable.
# This is NOT proof that a CustomerAccount grant store or worker exists.
set -euo pipefail
: "${KERUENIX_DB_URL:?real PostgreSQL required}"
[[ "$KERUENIX_DB_URL" == jdbc:postgresql:* ]] || {
  echo "ERROR: Issue #8 requires real PostgreSQL" >&2
  exit 1
}
log="$(mktemp)"
trap 'rm -f "$log"' EXIT
set +e
KERUENIX_ISSUE8_BEHAVIOR_RED=true mvn -B -ntp -f backend/pom.xml \
  -Dtest=Issue8CustomerOutboxAuthorizationRedTest test >"$log" 2>&1
status=$?
set -e
cat "$log"
if [[ "$status" -eq 0 ]]; then
  echo "ERROR: Issue #8 authorization barrier unexpectedly GREEN" >&2
  exit 1
fi
if ! grep -Fq "ISSUE8_MISSING_ACCOUNT_AUTH_BARRIER" "$log"; then
  echo "ERROR: expected missing-grant barrier failure not observed" >&2
  exit 1
fi
if ! grep -Eq 'Tests run: 1, Failures: 1, Errors: 0, Skipped: 0' "$log"; then
  echo "ERROR: unexpected tests/errors/skips; infrastructure failure is not RED" >&2
  exit 1
fi
if grep -Eq 'COMPILATION ERROR|Failed to load ApplicationContext|Could not resolve dependencies' "$log"; then
  echo "ERROR: compilation/startup/dependency failure is not behavioral RED" >&2
  exit 1
fi
echo "EXPECTED_ISSUE8_OUTBOX_AUTH_BEHAVIOR_RED: real PostgreSQL generic transport sent account-restricted event without verified grant"
echo "NOT_CUSTOMERACCOUNT_GRANT_QUALIFIED: DB-backed grant source and caller policy are still absent"

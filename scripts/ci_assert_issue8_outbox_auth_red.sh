#!/usr/bin/env bash
# Issue #8: the real PostgreSQL Outbox is a generic transport.
# This is an intentionally PASSING transport baseline, NOT auth qualification.
set -euo pipefail
: "${KERUENIX_DB_URL:?real PostgreSQL required}"
[[ "$KERUENIX_DB_URL" == jdbc:postgresql:* ]] || {
  echo "ERROR: Issue #8 requires real PostgreSQL" >&2
  exit 1
}
KERUENIX_ISSUE8_TRANSPORT_BASELINE=true mvn -B -ntp -f backend/pom.xml \
  -Dtest=Issue8CustomerOutboxAuthorizationRedTest test
echo "ISSUE8_TRANSPORT_BASELINE_PASS: generic Outbox delivers without account-grant introspection"
echo "ACCOUNT_AUTH_BEHAVIOR_RED_PENDING: real authorized CustomerAccount dispatch entrypoint absent"

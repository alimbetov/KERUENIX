#!/usr/bin/env bash
# S1 intentional RED: make CI GREEN only if the *expected* missing business
# handler is demonstrated. Build/boot/security errors must FAIL this check.
set -euo pipefail
log=$(mktemp)
trap 'rm -f "$log"' EXIT
set +e
mvn -B -ntp -f backend/pom.xml -Dtest=RfqDraftRedContractTest test >"$log" 2>&1
rc=$?
set -e
cat "$log"

[[ $rc -ne 0 ]] || {
  echo "ERROR: RFQ Draft suite unexpectedly GREEN; do not auto-approve domain implementation" >&2
  exit 1
}
grep -Fq "Missing PR-04 MVC Draft handler after valid JWT" "$log" || {
  echo "ERROR: expected handler-specific RED missing (could be security/boot failure)" >&2
  exit 1
}
grep -Fq "RFQ Draft must resolve to a real MVC handler" "$log" || {
  echo "ERROR: idempotency case did not reach intended missing-handler oracle" >&2
  exit 1
}
grep -Eq 'Tests run: 4, Failures: 3, Errors: 0' "$log" || {
  echo "ERROR: unexpected RFQ RED test count or setup failure" >&2
  exit 1
}
echo "EXPECTED_RFQ_BEHAVIOR_RED: 3 missing-handler/domain-oracle failures, 1 fail-closed Submit PASS"

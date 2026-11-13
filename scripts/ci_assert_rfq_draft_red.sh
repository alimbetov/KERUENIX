#!/usr/bin/env bash
# S1 PRELIMINARY CONTRACT-UNWIRED evidence only: the RFQ handler is absent.
# This wrapper MUST NOT be presented as authorized production-domain behavioral RED.
# Build/boot/security errors must FAIL this check.
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
grep -Eq 'Tests run: 4, Failures: 2, Errors: 0, Skipped: 0' "$log" || {
  echo "ERROR: unexpected RFQ RED test count or setup failure" >&2
  exit 1
}
echo "RFQ_DRAFT_CONTRACT_UNWIRED: 2 expected missing-handler assertions on PostgreSQL; 2 synthetic-auth security negatives passed"
echo "NOT_G1_BEHAVIORAL_RED_QUALIFIED: real PostgreSQL account grants and production RFQ command boundary absent; S2 NO-GO"

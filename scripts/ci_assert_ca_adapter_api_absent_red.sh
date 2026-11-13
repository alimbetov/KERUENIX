#!/usr/bin/env bash
# Distinguish absent real production CA ports from any arbitrary Maven failure.
# An EXPECTED API_ABSENT_RED proves only that adapters are NOT implemented.
# It MUST NOT be reported as a passing behavioral cache/worker test.
set -euo pipefail
log="$(mktemp)"
trap 'rm -f "$log"' EXIT
set +e
mvn -B -ntp -f backend/pom.xml -Pca-adapter-red -DskipTests test-compile >"$log" 2>&1
rc=$?
set -e

if [[ $rc -eq 0 ]]; then
  cat "$log"
  echo "ERROR: missing-adapter RED unexpectedly compiled: remove/review this classifier" >&2
  exit 1
fi

if grep -Eq 'Non-resolvable|Could not resolve dependencies|Plugin .* could not be resolved|Failed to read artifact descriptor' "$log"; then
  cat "$log"
  echo "ERROR: dependency/toolchain failure is not S1 adapter RED" >&2
  exit 1
fi

for missing in kz.keruenix.customeraccount.cache kz.keruenix.customeraccount.jobs; do
  if ! grep -Fq "package $missing does not exist" "$log"; then
    cat "$log"
    echo "ERROR: missing expected production port: $missing; verify actual compile error" >&2
    exit 1
  fi
done

grep -Fq 'COMPILATION ERROR' "$log" || {
  cat "$log"
  echo "ERROR: no targeted Java compilation failure detected" >&2
  exit 1
}
echo "EXPECTED_CA_API_ABSENT_RED: proposed cache and worker production ports are absent"
echo "NOT_BEHAVIORAL_RED: adapter execution, revocation, claim and cache-hit oracles remain unqualified"

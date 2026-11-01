#!/usr/bin/env bash
# Runs evals/claims/kotlin/ClaimsTest.kt, which checks claims in
# skills/complexity-optimizer/languages/KOTLIN.md that the docs do not settle.
# Builds in a temporary copy of the kotlin-shop fixture (same Kotlin and JUnit versions).
# Needs a full JDK 17+; set JAVA_HOME if the default Java has no compiler.
# Usage: evals/claims/kotlin-claims.sh
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cp -r "$here/../fixtures/kotlin-shop/." "$work/"
rm -rf "$work/src" "$work/build" "$work/.gradle"
mkdir -p "$work/src/test/kotlin/claims"
cp "$here/kotlin/ClaimsTest.kt" "$work/src/test/kotlin/claims/"
cd "$work"
status=0
./gradlew test -i > gradle.log 2>&1 || status=$?
grep -E "CLAIM " gradle.log | sed 's/^ *//' | sort -V || true
if [ "$status" -ne 0 ]; then
  grep -qE "CLAIM " gradle.log || tail -30 gradle.log
  echo "Some claims failed: update KOTLIN.md (or the test, if the claim was misstated)." >&2
fi
exit "$status"

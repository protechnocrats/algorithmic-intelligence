#!/usr/bin/env bash
# Tests the eval harness itself, without an API key or any cost.
#
#   evals/selftest.sh            runner checks only (about 10 minutes: it runs every fixture's test suite)
#   evals/selftest.sh --probes   also the grading probes (about 20 minutes; needs a JDK and Ruby)
#
# Runner checks use a stub agent (evals/selftest/claude) in place of the claude CLI:
#   1. every configured fixture sets up, runs, and runs its test suite;
#   2. --instructions puts CLAUDE.md in the with-skill run's initial commit, never the baseline's;
#   3. --max-total-usd stops starting sessions once the cap is reached;
#   4. the stall watchdog stops a stuck turn, marks the session invalid, and the batch continues.
# Probe checks lay the rewrites in evals/probes/selftest/<fixture>/{correct,wrong}/ over a copy
# of the fixture and run the probe: the correct rewrite must show no difference, and the wrong
# one must be caught by the checks listed below.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(dirname "$here")"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
export PATH="$here/selftest:$PATH"
fail=0
pass() { echo "ok    $*"; }
bad() { echo "FAIL  $*"; fail=1; }

# 1 and 2: every fixture the runner supports, with the CLAUDE.md line.
for fixture in ts-shop py-logistics java-clinic rb-clinic; do
  out="$work/$fixture"
  "$here/run-pilot.sh" --fixture "$fixture" --cases report --runs 1 --parallel 1 --instructions "selftest line" --out "$out" > /dev/null 2>&1
  if [ "$(grep -c ': done' "$out/progress.log")" = 2 ] && ! grep -q -E "invalid|failed" "$out/progress.log"; then
    pass "$fixture: skill and baseline sessions ran"
  else
    bad "$fixture: sessions did not complete ($(tail -1 "$out/progress.log"))"
  fi
  if (cd "$out/report-skill-1" && git ls-files --error-unmatch CLAUDE.md > /dev/null 2>&1) && [ ! -e "$out/report-baseline-1/CLAUDE.md" ]; then
    pass "$fixture: CLAUDE.md only in the with-skill run, and committed"
  else
    bad "$fixture: CLAUDE.md placement"
  fi
  grep -q "^## " "$out/logs/report-skill-1.final" && pass "$fixture: final test run recorded" || bad "$fixture: no final test run"
done

# 3: the cost cap. The stub reports $0.60 as each session's running total, as the real CLI
# reports cumulative cost, so each session counts $0.60: with a $1.00 cap, two run and two are skipped.
out="$work/cap"
"$here/run-pilot.sh" --fixture rb-clinic --cases report --conditions skill,baseline --runs 2 --parallel 1 --max-total-usd 1 --out "$out" > /dev/null 2>&1
if [ "$(grep -c ': done' "$out/progress.log")" = 2 ] && [ "$(grep -c 'cost cap reached' "$out/progress.log")" = 2 ]; then
  pass "cost cap: 2 sessions ran, 2 skipped"
else
  bad "cost cap: $(grep -c ': done' "$out/progress.log") ran, $(grep -c 'cost cap reached' "$out/progress.log") skipped"
fi

# 4: the stall watchdog.
out="$work/stall"
STUB_STALL=1 "$here/run-pilot.sh" --fixture rb-clinic --cases report --conditions skill --runs 2 --parallel 1 --stall-seconds 20 --out "$out" > /dev/null 2>&1
if [ "$(grep -c 'STALLED' "$out/progress.log")" = 2 ] && [ "$(grep -c 'skipped, session already invalid' "$out/progress.log")" = 2 ] && [ "$(grep -c ': done' "$out/progress.log")" = 2 ]; then
  pass "stall watchdog: both stuck turns stopped, later turns skipped, batch continued"
else
  bad "stall watchdog: $(grep -c STALLED "$out/progress.log") stalls stopped"
fi

# Probes.
if [ "${1:-}" = --probes ]; then
  probe_case() {  # probe_case <fixture> <variant> <probe command...>
    local fixture="$1" variant="$2"; shift 2
    local dir="$work/probe-$fixture-$variant"
    cp -R "$repo/evals/fixtures/$fixture" "$dir" && cp -R "$repo/evals/probes/selftest/$fixture/$variant/." "$dir/"
    "$@" "$dir" > "$dir.out" 2>&1
  }
  probe_case java-clinic correct python3 -I "$repo/evals/probes/java-clinic.py" &
  probe_case java-clinic wrong   python3 -I "$repo/evals/probes/java-clinic.py" &
  probe_case rb-clinic correct   python3 -I "$repo/evals/probes/rb-clinic.py" &
  probe_case rb-clinic wrong     python3 -I "$repo/evals/probes/rb-clinic.py" &
  wait
  for fixture in java-clinic rb-clinic; do
    out="$work/probe-$fixture-correct.out"
    if ! grep -q "DIFF" "$out" && grep -q -E "JW1: 0 mismatches|RBW1: 0 mismatches" "$out" && ! grep -q "RATE LIMIT EXCEEDED" "$out"; then
      pass "$fixture probe: the correct rewrite shows no difference"
    else
      bad "$fixture probe: the correct rewrite was flagged"; grep -E "DIFF|RATE|mismatch" "$out" | head -5
    fi
  done
  expect_java="J1 J2 J5 J6 J7 J8 J10"
  expect_rb="RB1 RB2 RB3 RB6 RB7 RB8 RB9"
  for fixture in java-clinic rb-clinic; do
    out="$work/probe-$fixture-wrong.out"
    [ "$fixture" = java-clinic ] && expect="$expect_java" || expect="$expect_rb"
    missed=""
    for c in $expect; do grep -q "DIFF  $c:" "$out" || missed="$missed $c"; done
    if [ "$fixture" = java-clinic ]; then
      grep -q "RATE LIMIT EXCEEDED" "$out" || missed="$missed J3-rate"
      # The probe prints mismatch details first and the count on a later line.
      grep -q -E "^ *[1-9][0-9]* mismatches in [0-9]+ cases" "$out" || missed="$missed JW1"
    else
      grep -q "DIFF  RB5:" "$out" || missed="$missed RB5"
      grep -q -E "^ *[1-9][0-9]* mismatches in [0-9]+ cases" "$out" || missed="$missed RBW1"
    fi
    [ -z "$missed" ] && pass "$fixture probe: every wrong rewrite caught" || bad "$fixture probe: not caught:$missed"
  done
fi

[ "$fail" = 0 ] && echo "all self-tests passed" || echo "some self-tests failed"
exit "$fail"

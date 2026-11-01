#!/usr/bin/env bash
# Runs the test suite (Ruby 3.2 or newer; minitest ships with Ruby).
set -euo pipefail
cd "$(dirname "$0")"
for f in test/test_*.rb; do ruby -Ilib -Itest "$f" "$@"; done

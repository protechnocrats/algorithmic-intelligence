#!/usr/bin/env bash
# Runs once when the container is created. Installs what the Dockerfile does not:
# the Claude Code CLI (for running evals) and Swift (for swift-shop).
set -euo pipefail
npm install -g @anthropic-ai/claude-code
if ! command -v swift > /dev/null; then
  curl -fsSL https://download.swift.org/swiftly/linux/swiftly-$(uname -m).tar.gz -o /tmp/swiftly.tar.gz
  tar -xzf /tmp/swiftly.tar.gz -C /tmp
  /tmp/swiftly init --quiet-shell-followup --assume-yes || echo "Swift not installed; swift-shop cannot run. See https://www.swift.org/install/linux/"
fi
echo "Toolchains: $(java -version 2>&1 | head -1); $(ruby -v); $(node -v); $(cargo --version); $(python3 --version)"
echo "Self-test the eval harness (no API cost): evals/selftest.sh"

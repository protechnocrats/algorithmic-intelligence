#!/usr/bin/env bash
# Compiles the project and runs every *Test class. Needs a JDK 17 or newer
# (javac on PATH, or JAVA_HOME pointing at a full JDK). No dependencies.
set -euo pipefail
cd "$(dirname "$0")"
bin="${JAVA_HOME:+$JAVA_HOME/bin/}"
rm -rf build
mkdir -p build/main build/test
"${bin}javac" -d build/main $(find src/main/java -name '*.java')
"${bin}javac" -d build/test -cp build/main $(find src/test/java -name '*.java')
tests=$(cd build/test && find . -name '*Test.class' | sed 's|^\./||; s|\.class$||; s|/|.|g' | sort)
"${bin}java" -cp build/main:build/test com.example.clinic.testing.Runner $tests "$@"

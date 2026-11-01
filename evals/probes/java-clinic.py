#!/usr/bin/env python3
"""Grades a java-clinic run: runs the answer key's checks against the original
fixture and the run's final code, and prints every difference.

Usage: JAVA_HOME=<full JDK> python3 -I evals/probes/java-clinic.py <run-directory>

Each directory's sources are compiled with probes/java-clinic/Probe.java into a
temporary directory; each check runs in its own JVM with a timeout.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE.parent / "fixtures" / "java-clinic"
BIN = os.path.join(os.environ["JAVA_HOME"], "bin") if os.environ.get("JAVA_HOME") else ""

# name -> (kind, timeout seconds). "compare": original and run must print the same.
# "info": print both. "run": print the run's result only (it states its own verdict).
CHECKS = {
    "J1": ("compare", 120), "J1-trips": ("info", 120),
    "J2": ("compare", 120), "J2-memory": ("info", 600), "J2-time": ("info", 120),
    "J3": ("compare", 120), "J3-rate": ("run", 120),
    "J4": ("compare", 60),
    "J5": ("compare", 300), "J5-time": ("info", 30),
    "J6": ("compare", 600),
    "J7": ("compare", 600),
    "J8": ("compare", 120),
    "J9": ("compare", 120), "J9-time": ("info", 300),
    "J10": ("compare", 60),
    "JW1": ("run", 300),
}


def tool(name):
    return os.path.join(BIN, name) if BIN else name


def build(directory, dest):
    sources = [str(p) for p in Path(directory, "src", "main", "java").rglob("*.java")]
    main = os.path.join(dest, "main")
    os.makedirs(main)
    p = subprocess.run([tool("javac"), "-nowarn", "-d", main, *sources], capture_output=True, text=True)
    if p.returncode:
        return None, "compile error: " + p.stderr.strip()[-600:]
    p = subprocess.run([tool("javac"), "-nowarn", "-d", dest, "-cp", main, str(HERE / "java-clinic" / "Probe.java")],
                       capture_output=True, text=True)
    if p.returncode:
        return None, "probe does not compile against this code (signatures changed?): " + p.stderr.strip()[-600:]
    return f"{main}{os.pathsep}{dest}", None


def run(classpath, name, timeout):
    try:
        p = subprocess.run([tool("java"), "-Xmx2g", "-cp", classpath, "Probe", name],
                           capture_output=True, text=True, timeout=timeout)
        if p.returncode:
            return [f"error: {(p.stderr.strip().splitlines() or ['no output'])[-1]}"]
        return p.stdout.rstrip("\n").split("\n")
    except subprocess.TimeoutExpired:
        return [f"timeout after {timeout}s"]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    target = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        original, err = build(FIXTURE, a)
        if err:
            sys.exit("original fixture: " + err)
        candidate, err = build(target, b)
        if err:
            sys.exit("run: " + err)
        for name, (kind, timeout) in CHECKS.items():
            if kind == "run":
                print(f"  run   {name}: " + "\n        ".join(run(candidate, name, timeout)))
                continue
            if kind == "info":
                print(f"  info  {name}: original {' | '.join(run(original, name, timeout))} | run {' | '.join(run(candidate, name, timeout))}")
                continue
            x, y = run(original, name, timeout), run(candidate, name, timeout)
            if x == y:
                print(f"  same  {name}")
                continue
            diffs = [i for i in range(max(len(x), len(y))) if i >= len(x) or i >= len(y) or x[i] != y[i]]
            print(f"  DIFF  {name}: {len(diffs)} of {max(len(x), len(y))} result lines differ")
            for i in diffs[:3]:
                print(f"        line {i + 1}\n          original: {(x[i] if i < len(x) else '(missing)')[:300]}\n          run:      {(y[i] if i < len(y) else '(missing)')[:300]}")


if __name__ == "__main__":
    main()

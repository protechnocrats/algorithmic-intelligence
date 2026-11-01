#!/usr/bin/env python3
"""Grades an rb-clinic run: runs the answer key's checks against the original
fixture and the run's final code, and prints every difference.

Usage: python3 -I evals/probes/rb-clinic.py <run-directory>

Each check runs in its own Ruby process, inside the directory being checked,
with a timeout, so a slow or crashing version cannot stall grading.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE.parent / "fixtures" / "rb-clinic"
CHECKS_RB = HERE / "rb-clinic" / "checks.rb"

# name -> (kind, timeout seconds). "compare": original and run must print the same.
# "info": print both. "run": print the run's result only (it states its own verdict).
CHECKS = {
    "RB1": ("compare", 120), "RB1-trips": ("info", 60),
    "RB2": ("compare", 120), "RB2-time": ("info", 120),
    "RB3": ("compare", 120),
    "RB4": ("compare", 60),
    "RB5": ("compare", 120), "RB5-time": ("info", 60),
    "RB6": ("compare", 300), "RB6-time": ("info", 60),
    "RB7": ("compare", 300),
    "RB8": ("compare", 120), "RB8-time": ("info", 60),
    "RB9": ("compare", 60),
    "RBW1": ("run", 600),
}


def run(directory, name, timeout):
    try:
        p = subprocess.run(["ruby", "-Ilib", str(CHECKS_RB), name], capture_output=True, text=True,
                           timeout=timeout, cwd=directory)
        if p.returncode:
            return [f"error: {(p.stderr.strip().splitlines() or ['no output'])[0][:300]}"]
        return p.stdout.rstrip("\n").split("\n")
    except subprocess.TimeoutExpired:
        return [f"timeout after {timeout}s"]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    target = Path(sys.argv[1]).resolve()
    for name, (kind, timeout) in CHECKS.items():
        if kind == "run":
            print(f"  run   {name}: " + "\n        ".join(run(target, name, timeout)))
            continue
        if kind == "info":
            print(f"  info  {name}: original {' | '.join(run(FIXTURE, name, timeout))} | run {' | '.join(run(target, name, timeout))}")
            continue
        x, y = run(FIXTURE, name, timeout), run(target, name, timeout)
        if x == y:
            print(f"  same  {name}")
            continue
        diffs = [i for i in range(max(len(x), len(y))) if i >= len(x) or i >= len(y) or x[i] != y[i]]
        print(f"  DIFF  {name}: {len(diffs)} of {max(len(x), len(y))} result lines differ")
        for i in diffs[:3]:
            print(f"        line {i + 1}\n          original: {(x[i] if i < len(x) else '(missing)')[:300]}\n          run:      {(y[i] if i < len(y) else '(missing)')[:300]}")


if __name__ == "__main__":
    main()

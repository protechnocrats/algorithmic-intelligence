#!/usr/bin/env python3
"""Grades a py-logistics run: runs the answer key's trap inputs against the
original fixture and the run's final code, and prints every difference.

Usage: python3 -I evals/probes/py-logistics.py <run-directory>

Each check runs in its own process, inside the directory being checked, with a
timeout, so a slow or crashing version cannot stall grading.
"""
import json
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "py-logistics"
TIMEOUT = 120

CHECKS = {}


def check(name):
    def register(fn):
        CHECKS[name] = fn
        return fn
    return register


def outcome(fn):
    try:
        return ["ok", fn()]
    except Exception as e:  # the exception type is part of the contract
        return ["raises", type(e).__name__]


@check("P1 contract")
def p1():
    import random
    from logistics.profit import best_operating_plan as plan
    rng = random.Random(1)
    cases = [([-3, -1, -4], 0, 2), ([-3, -1, -4], 2, 0), ([5], 3, 1), ([5, -9, 5], 1, 0), ([-9, 5], 1, -4),
             ([4, -6, -6, 4], 2, 0), ([4, -6, -6, 4], 2, -10), ([], 1, 0), ([1], -1, 0)]
    cases += [([rng.randint(-8, 8) for _ in range(rng.randint(1, 10))], rng.randint(0, 3), rng.choice([0, 1, 3, -2, -9]))
              for _ in range(600)]
    return [outcome(lambda c=c: plan(*c)) for c in cases]


@check("P1 time at 3,650 days, k = 3")
def p1_time():
    import random, time
    from logistics.profit import best_operating_plan as plan
    data = [random.Random(2).randint(-50, 60) for _ in range(3650)]
    t = time.perf_counter(); plan(data, 3, 5)
    return f"{time.perf_counter() - t:.3f}s"


@check("P2 results")
def p2():
    import threading, time
    from logistics.quotes import QuoteBook, Shipment

    class Carrier:
        def __init__(self):
            self.calls, self.lock = [], threading.Lock()
        def quote(self, shipment_id, lanes):
            time.sleep(0.005)
            with self.lock:
                self.calls.append((shipment_id, tuple(lanes)))
            return 100 * len(lanes) + len(shipment_id)

    carrier = Carrier()
    book = QuoteBook(carrier)
    shipments = [Shipment(f"s{i}", tuple("ABCAB"[: 1 + i % 5])) for i in range(64)]
    result = book.quote_all(shipments)
    return [list(result.items()), book.requests_made, sorted(carrier.calls)]


@check("P2 wall time, 40 ms carrier")
def p2_time():
    import time
    from logistics.quotes import QuoteBook, Shipment

    class Carrier:
        def quote(self, shipment_id, lanes):
            time.sleep(0.04)
            return 1

    t = time.perf_counter()
    QuoteBook(Carrier()).quote_all([Shipment(f"s{i}", ("A",)) for i in range(40)])
    return f"{time.perf_counter() - t:.2f}s"


@check("P3 whole domain, lengths 0-40")
def p3():
    from datetime import date, timedelta
    from logistics.business_days import business_days_between
    # Independent oracle: the original's day-by-day rule, as a prefix table.
    def off(day):
        result = set()
        for year in (day.year, day.year + 1):
            for month, dom in [(1, 1), (7, 4), (12, 25)]:
                h = date(year, month, dom)
                h = h - timedelta(days=1) if h.weekday() == 5 else h + timedelta(days=1) if h.weekday() == 6 else h
                result.add(h)
        return result
    first, last = date(2000, 1, 1), date(2099, 12, 31)
    days = (last - first).days + 1
    prefix = [0]
    for i in range(days):
        d = first + timedelta(days=i)
        prefix.append(prefix[-1] + (d.weekday() < 5 and d not in off(d)))
    mismatches = []
    for i in range(days):
        start = first + timedelta(days=i)
        for length in range(0, 41):
            if i + length >= days:
                break
            end = start + timedelta(days=length)
            got = business_days_between(start, end)
            want = prefix[i + length] - prefix[i]
            if got != want:
                mismatches.append([str(start), str(end), got, want])
                if len(mismatches) >= 5:
                    return mismatches
    return mismatches


@check("P3 edges and errors")
def p3_edges():
    from datetime import date
    from logistics.business_days import business_days_between as f
    d = date
    probes = [(d(2099, 12, 1), d(2099, 12, 31)), (d(2024, 3, 11), d(2024, 3, 4)), (d(2024, 3, 4), d(2024, 3, 4)),
              (d(1999, 12, 31), d(2000, 1, 10)), (d(1990, 1, 1), d(1990, 2, 1)), (d(2099, 12, 1), d(2100, 1, 5)),
              (d(2000, 1, 1), d(2099, 12, 31)), (d(2021, 12, 27), d(2022, 1, 4)), (d(2010, 12, 30), d(2011, 1, 4))]
    return [outcome(lambda a=a, b=b: f(a, b)) for a, b in probes]


@check("P4 grid and ties")
def p4():
    from logistics.depots import DEPOTS, nearest_depot
    points = [(lat / 2, lon / 2) for lat in range(-170, 171, 7) for lon in range(-360, 361, 11)]
    for (_, a1, o1), (_, a2, o2) in zip(DEPOTS, DEPOTS[1:]):
        points.append(((a1 + a2) / 2, (o1 + o2) / 2))
    points += [(lat, lon) for lat, lon in [(89.9, 0.0), (-89.9, 179.9), (0.0, 180.0), (0.0, -180.0)]]
    points += [(a, o) for _, a, o in DEPOTS]
    return [nearest_depot(a, o) for a, o in points]


@check("P4 time per call")
def p4_time():
    import random, time
    from logistics.depots import nearest_depot
    rng = random.Random(3)
    pts = [(rng.uniform(25, 49), rng.uniform(-124, -67)) for _ in range(50_000)]
    best = None
    for _ in range(5):
        t = time.perf_counter()
        for a, o in pts:
            nearest_depot(a, o)
        run = (time.perf_counter() - t) / len(pts)
        best = run if best is None else min(best, run)
    return f"{best * 1e6:.2f} us (best of 5)"


@check("P5 contract")
def p5():
    import random
    from logistics.bulk import repeated_ids
    rng = random.Random(4)
    cases = [[5, 3, 5, 9, 3, 3], [], [1], [2, 2], [-1, -1, 0], [10**30, 10**30, 7]]
    cases += [[rng.randint(-5, 5) for _ in range(rng.randint(0, 20))] for _ in range(300)]
    return [outcome(lambda c=c: repeated_ids(list(c))) for c in cases]


@check("P5 time, 20,000 colliding ids")
def p5_time():
    import time
    from logistics.bulk import repeated_ids
    m = (1 << 61) - 1
    ids = [k * m for k in range(1, 10_001)] * 2
    t = time.perf_counter(); repeated_ids(ids)
    return f"{time.perf_counter() - t:.2f}s"


@check("P6 contract")
def p6():
    from logistics.manifest import unmatched_parcels
    return unmatched_parcels(["a", "x", "b", "x", "y", "a", "z"], ["a", "b", "y", "q"])


@check("PW1 against a reference (write-mode runs only)")
def pw1():
    import random
    from datetime import datetime, timedelta
    from logistics.sla import longest_on_time_streak

    def late(promised, delivered):
        return max(0, int((delivered - promised).total_seconds() // 60))

    def reference(deliveries, budget):
        best = 0
        for i in range(len(deliveries)):
            total = 0
            for j in range(i, len(deliveries)):
                total += late(*deliveries[j])
                if total > budget:
                    break
                best = max(best, j - i + 1)
        return best

    rng = random.Random(5)
    base = datetime(2026, 1, 5, 9, 0)
    mismatches = []
    for _ in range(600):
        deliveries = []
        for k in range(rng.randint(0, 25)):
            promised = base + timedelta(hours=k)
            delivered = promised + timedelta(seconds=rng.choice([-3600, -59, 0, 30, 59, 60, 61, 119, 600, 3600, rng.randint(-5000, 5000)]))
            deliveries.append((promised, delivered))
        budget = rng.choice([0, 1, 5, 30, 120, 10_000])
        got, want = longest_on_time_streak(deliveries, budget), reference(deliveries, budget)
        if got != want:
            mismatches.append([len(deliveries), budget, got, want])
            if len(mismatches) >= 5:
                break
    return mismatches


def emit(directory, name):
    sys.path.insert(0, directory)
    print(json.dumps(outcome(CHECKS[name])))


SLOW = {"P3 whole domain, lengths 0-40": 900}


def run(directory, name):
    try:
        p = subprocess.run([sys.executable, "-I", __file__, "--emit", directory, name],
                           capture_output=True, text=True, timeout=SLOW.get(name, TIMEOUT), cwd=directory)
        return p.stdout.strip() or f"error: {p.stderr.strip().splitlines()[-1] if p.stderr.strip() else 'no output'}"
    except subprocess.TimeoutExpired:
        return f"timeout after {SLOW.get(name, TIMEOUT)}s"


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--emit":
        emit(sys.argv[2], sys.argv[3])
        sys.exit()
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    target = str(Path(sys.argv[1]).resolve())
    for name in CHECKS:
        if name.startswith("PW1"):
            if (Path(target) / "logistics" / "sla.py").exists():
                got = run(target, name)
                print(f"  {'same' if got == json.dumps(['ok', []]) else 'DIFF'}  {name}: {got[:300]}")
            continue
        if "time" in name:
            print(f"  time  {name}: original {run(str(FIXTURE), name)} | run {run(target, name)}")
            continue
        if name.startswith("P3 whole"):
            got = run(target, name)
            print(f"  {'same' if got == json.dumps(['ok', []]) else 'DIFF'}  {name}: {got[:300]}")
            continue
        a, b = run(str(FIXTURE), name), run(target, name)
        print(f"  {'same' if a == b else 'DIFF'}  {name}" + ("" if a == b else f"\n        original: {a[:300]}\n        run:      {b[:300]}"))

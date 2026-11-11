#!/usr/bin/env python3
"""Growth exponent from a doubling experiment ("Doubling experiments" in BENCHMARKING.md).

Usage: doubling.py N:TIME N:TIME [N:TIME ...]

Each argument is an input size and the measured time at that size (any consistent unit; sizes
need not double exactly). For each consecutive pair the script prints
b = log(T2 / T1) / log(N2 / N1), labels it, and predicts the time at the next doubling of the
last size, so you can write the prediction down before measuring it. Standard library only.
"""
import math
import sys


def exponents(points: list) -> list:
    """[(n1, n2, b), ...] for consecutive (n, t) pairs sorted by n."""
    pts = sorted(points)
    out = []
    for (n1, t1), (n2, t2) in zip(pts, pts[1:]):
        if n1 <= 0 or n2 <= n1 or t1 <= 0 or t2 <= 0:
            raise ValueError(f'sizes must be positive and increasing and times positive: ({n1}, {t1}) -> ({n2}, {t2})')
        out.append((n1, n2, math.log(t2 / t1) / math.log(n2 / n1)))
    return out


def label(b: float) -> str:
    if b < 0.5:
        return 'below linear: fixed overhead dominates at this size, or the work is sublinear'
    if b < 0.85:
        return 'between constant and linear: overhead still dominates, or sublinear'
    if b < 1.15:
        return 'near 1: linear'
    if b < 1.4:
        return 'slightly above 1: fits n log n (or linear with a cache or memory boundary crossed)'
    if b < 1.75:
        return 'between n log n and quadratic: mixed costs, or a boundary crossed; measure more sizes'
    if b < 2.3:
        return 'near 2: quadratic'
    if b < 2.75:
        return 'between quadratic and cubic'
    if b < 3.3:
        return 'near 3: cubic'
    return 'above cubic: exponential growth or a resource exhausted'


def parse(args: list) -> list:
    points = []
    for a in args:
        try:
            n, t = a.split(':', 1)
            points.append((float(n), float(t)))
        except ValueError:
            raise ValueError(f'expected N:TIME, got {a!r}')
    return points


def main(argv: list) -> int:
    if not argv or any(a in ('-h', '--help') for a in argv):
        print(__doc__.strip())
        return 0 if argv else 2
    try:
        points = parse(argv)
        if len(points) < 2:
            raise ValueError('at least two points are needed')
        rows = exponents(points)
    except ValueError as e:
        print(f'error: {e}', file=sys.stderr)
        return 2
    for n1, n2, b in rows:
        print(f'{n1:g} -> {n2:g}: b = {b:.2f}  ({label(b)})')
    last_b = rows[-1][2]
    n_last, t_last = max(points)
    print(f'prediction at N = {2 * n_last:g} if the last exponent holds: T = {t_last * 2 ** last_b:.4g}')
    if len(rows) >= 2 and abs(rows[-1][2] - rows[0][2]) > 0.3:
        print('note: the exponent changes across sizes; the first pairs may include fixed overhead, '
              'or the working set crossed a cache or memory boundary. Use the largest sizes for the claim.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

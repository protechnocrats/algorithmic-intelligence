"""Depot profit planning."""

from itertools import combinations


def best_operating_plan(daily_profit: list[int], max_closures: int, closure_cost: int) -> int:
    """Largest total profit over a run of consecutive days, if the depot may
    close on up to `max_closures` days inside the run.

    A closed day earns -closure_cost instead of that day's profit. Two closed
    days may not be adjacent, and the first and last days of the run stay open.
    Raises ValueError for an empty list or a negative `max_closures`.
    Run nightly for every depot.
    """
    if not daily_profit:
        raise ValueError("no days")
    if max_closures < 0:
        raise ValueError("max_closures must not be negative")
    best = None
    days = len(daily_profit)
    for first in range(days):
        for last in range(first, days):
            open_total = sum(daily_profit[first:last + 1])
            inside = range(first + 1, last)
            for count in range(min(max_closures, max(0, last - first - 1)) + 1):
                for closed in combinations(inside, count):
                    if any(b - a == 1 for a, b in zip(closed, closed[1:])):
                        continue
                    total = open_total - sum(daily_profit[d] + closure_cost for d in closed)
                    if best is None or total > best:
                        best = total
    return best

# Scripts

Optional helpers for two checks that are easy to get wrong by hand. They use only the Python standard library, read nothing but their arguments or standard input, write nothing, and need no network. An agent without code execution follows the same rules without them; nothing in the skill depends on running a script.

| Script | Use | Example |
|---|---|---|
| `check_summary.py` | Checks a final summary for the lines "Every final summary" in `SKILL.md` requires, matched as line labels. Exit status 0 when complete, 1 with the missing labels listed. | `python3 scripts/check_summary.py summary.md` or `... < summary.md` |
| `doubling.py` | Computes the growth exponent from a doubling experiment ("Doubling experiments" in `BENCHMARKING.md`): for each consecutive pair of sizes, `b = log(T₂/T₁) / log(N₂/N₁)`, labels it (near 1 linear, between 1 and about 1.3 n log n, near 2 quadratic, near 3 cubic), and predicts the time at the next doubling so the prediction can be checked before measuring it. | `python3 scripts/doubling.py 1000:0.012 2000:0.025 4000:0.051 8000:0.103` |

Both print their result as plain text and take `--help`. Give the timings as `N:seconds`, in any consistent unit; a run that includes fixed overhead at small N shows a low first exponent, which the script notes.

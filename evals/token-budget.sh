#!/usr/bin/env bash
# Checks how many tokens each mode must load from the skill, against budgets.
# Fails (exit 1) when a budget is exceeded, so growth is noticed before it ships.
# Budgets make growth visible; they are not a reason to cut instructions. When a
# needed instruction exceeds a budget, keep the instruction, raise the budget here,
# and say so in the commit. Never trim wording or move an instruction to a less
# suitable file to fit (decided 2026-10-31).
# Estimates use about 4 characters per token; compare trends, not exact counts.
# Usage: evals/token-budget.sh [skill directory]
set -euo pipefail
skill="${1:-$(cd "$(dirname "$0")/.." && pwd)/skills/complexity-optimizer}"
python3 -I - "$skill" <<'PY'
import sys
from pathlib import Path
skill = Path(sys.argv[1])
tok = lambda *names: sum(len((skill / n).read_text()) for n in names) // 4
lang = "languages/JAVASCRIPT-TYPESCRIPT.md"  # a typical companion file
BUDGETS = [  # (what, tokens now, budget)
    ("SKILL.md, loaded on every trigger", tok("SKILL.md"), 7_000),  # raised from 5,200 on 2026-10-31, from 6,500 on 2026-11-01 (saved language profiles)
    ("Report mode, required files", tok("SKILL.md", "WORKFLOW.md", "ALGORITHM-ARSENAL.md", "REPORTING.md", "languages/INDEX.md", lang), 22_000),  # raised from 17,000, from 21,000 on 2026-11-01 (saved language profiles)
    ("Apply mode, added files", tok("DIFFERENTIAL-TESTING.md", "BEHAVIOR-TRAPS.md", "BENCHMARKING.md"), 10_500),  # raised from 8,500
    ("Write mode, required files", tok("SKILL.md", "WRITING-NEW-CODE.md", "ALGORITHM-ARSENAL.md", "languages/INDEX.md", lang), 16_500),  # raised from 14,000
]
langs = [p for p in (skill / "languages").glob("*.md") if p.name not in ("INDEX.md", "GENERIC.md")]
big = max(langs, key=lambda p: len(p.read_text()))
BUDGETS.append((f"Largest language companion ({big.relative_to(skill)})", len(big.read_text()) // 4, 3_600))  # raised from 3,000
largest = max((p for p in skill.rglob("*.md")), key=lambda p: len(p.read_text()))
BUDGETS.append((f"Largest single file ({largest.relative_to(skill)})", len(largest.read_text()) // 4, 8_500))  # raised from 7,000 on 2026-11-01 (DISCOVERY.md moves 13 to 19)
failed = False
for what, now, budget in BUDGETS:
    status = "ok" if now <= budget else "OVER BUDGET"
    failed |= now > budget
    print(f"{status:12s} {what}: {now:,} tokens (budget {budget:,})")
print(f"{'':12s} Whole skill: {sum(len(p.read_text()) for p in skill.rglob('*.md')) // 4:,} tokens (loaded only in parts)")
sys.exit(1 if failed else 0)
PY

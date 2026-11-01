#!/usr/bin/env bash
# Copies an evaluation fixture into a fresh directory outside this repository,
# so the agent under test cannot see the answer keys.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: evals/new-run.sh <fixture> [--skill <dir>] [--skill-src <path>] [--dest <path>]

  <fixture>       kotlin-shop, ts-shop, swift-shop, c-shop, rust-shop, py-logistics,
                  java-clinic, or rb-clinic
  --skill <dir>   Also copy the skill into <dir> inside the run directory,
                  relative to its root (for example .claude/skills).
                  Omit it for a baseline run without the skill.
  --skill-src <path>  Skill folder to copy (default: skills/complexity-optimizer
                  in this repository). Use it to install another version.
  --dest <path>   Run directory. Default:
                  ~/complexity-optimizer-evals/<fixture>-<timestamp>
EOF
}

[ $# -ge 1 ] || { usage; exit 1; }
case "$1" in -h|--help) usage; exit 0 ;; esac

fixture="$1"
shift
skill_dir=""
skill_src=""
dest=""
while [ $# -gt 0 ]; do
  case "$1" in
    --skill) skill_dir="${2:?--skill needs a directory}"; shift 2 ;;
    --skill-src) skill_src="${2:?--skill-src needs a path}"; shift 2 ;;
    --dest) dest="${2:?--dest needs a path}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

evals_dir="$(cd "$(dirname "$0")" && pwd)"
repo_dir="$(dirname "$evals_dir")"
source_dir="$evals_dir/fixtures/$fixture"
[ -d "$source_dir" ] || { echo "Unknown fixture: $fixture" >&2; exit 1; }

dest="${dest:-$HOME/complexity-optimizer-evals/$fixture-$(date +%Y%m%d-%H%M%S)}"
case "$dest" in
  "$repo_dir"|"$repo_dir"/*) echo "The run directory must be outside this repository." >&2; exit 1 ;;
esac
[ ! -e "$dest" ] || { echo "Already exists: $dest" >&2; exit 1; }

mkdir -p "$dest"
cp -R "$source_dir/." "$dest/"

cd "$dest"
git init -q
git add -A
git -c user.name="Eval Fixture" -c user.email="eval@example.invalid" commit -q -m "Initial commit"

if [ -n "$skill_dir" ]; then
  mkdir -p "$skill_dir"
  cp -R "${skill_src:-$repo_dir/skills/complexity-optimizer}" "$skill_dir/complexity-optimizer"
  # Keep the installed skill out of the project's history and diffs.
  echo "$skill_dir/" >> .git/info/exclude
fi

echo "$dest"

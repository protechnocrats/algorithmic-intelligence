## What changes for someone using the skill

<!-- What the agent now does differently, or "nothing" for docs, evals, or tooling only. -->

## Checklist

- [ ] `CHANGELOG.md` `[Unreleased]` has a line for any change to what the skill does
- [ ] `evals/token-budget.sh` passes; any raised budget has its reason in the script
- [ ] Generic files stay language-neutral; mandatory rules are in `skills/SKILL.md` and the file that carries them out
- [ ] Behavior changes were measured before and after on a tuning fixture, or this says why not
- [ ] For eval changes: `evals/selftest.sh` passes (and `--probes` if a probe changed)

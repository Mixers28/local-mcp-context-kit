---
name: local-context-kit
description: Use when working in a repository that uses local-mcp-context-kit or handoffkit memory docs, generated repo maps, start/end session rituals, or Git-backed agent context to reduce repeated source discovery.
---

# Local Context Kit

Use this workflow to preserve repo context across coding sessions while keeping source code authoritative.

## Startup

1. Run drift checks before reading memory:
   - `git status --porcelain`
   - `git diff --name-status HEAD --`
2. If the tree is dirty, identify the changed files and ask whether to keep, commit, or discard before relying on memory docs.
3. Run `python3 -m handoffkit preflight --root .` when `handoffkit` is available.
4. Read context in this order:
   - `docs/PROJECT_CONTEXT.md`
   - `docs/NOW.md`
   - `docs/REPO_MAP.generated.md` if present
   - recent `docs/SESSION_NOTES.md`
5. Summarize the current project state in 3-6 bullets before making changes.

## Repo Map

Use `docs/REPO_MAP.generated.md` to decide where to inspect first. Do not treat it as proof of behavior.

Run `python3 -m handoffkit map update --root .` after:
- new modules or entry points
- renamed/moved files or folders
- changed file responsibilities
- major workflow or architecture changes

Do not regenerate the map after every small edit unless structure or responsibility changed.

## Source Inspection

Context docs guide where to look. Source code remains authoritative.

Only inspect source files that are relevant to the current task or flagged by the repo map, then broaden the search when behavior, dependencies, or tests show the map is incomplete.

## Writeback

At session end:
- Update `docs/NOW.md` for current focus and next actions.
- Append to `docs/SESSION_NOTES.md`.
- Update `docs/PROJECT_CONTEXT.md` only for stable decisions, architecture, constraints, or workflow changes.
- Regenerate repo map/index when structure or responsibilities changed.

Run validation commands that match the change, usually:
- `python3 scripts/check_guardrails.py`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `python3 -m handoffkit preflight --root .`

# Universal Handoff Kit (Local MCP compatible)

A tiny **prompt compiler** you can use with *any chat window / any LLM* (Codex, Claude, ChatGPT, etc.).
It builds a **token-budgeted Context Pack** from your repo’s memory files and prints a **role handoff prompt** you copy/paste.

This version is adapted to your **local-mcp-context-kit** layout:
- Reads: `docs/PROJECT_CONTEXT.md`, `docs/NOW.md`, `docs/SESSION_NOTES.md`
- Includes: `docs/AGENT_SESSION_PROTOCOL.md` (excerpt)
- If present, uses your repo role prompts: `.github/agents/*.agent.md`
- Can be run from anywhere inside the repo (auto-finds project root)

## Install

### Option A (recommended, venv)
From the repo root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

This exposes a `handoffkit` CLI (you can also use `python -m handoffkit`).

### Option B (no install)
Run directly from the repo root:

```bash
python -m handoffkit --help
```

If you see `externally-managed-environment`, use a venv or install via `pipx`.

## Usage

Run from *any* directory; just point `--root` somewhere inside the repo (or omit it if you’re already inside).
If you didn’t install, replace `handoffkit` with `python -m handoffkit`.

### Architect
```bash
handoffkit architect "Turn my idea into SPEC.md + phases/sprints" --root .
```

### Coder
```bash
handoffkit coder "Implement Sprint 1 from SPEC.md" --root .
```

### Reviewer (diff file)
```bash
git diff > patch.diff
handoffkit reviewer "Review this patch vs SPEC.md and best practices" --root . --diff patch.diff
```

### Reviewer (pipe diff from stdin)
```bash
git diff | handoffkit reviewer "Review this patch vs SPEC.md and best practices" --root . --diff -
```

### QA/Tester
```bash
handoffkit qa_tester "Write a lightweight test plan + edge cases" --root .
```

### Polish
```bash
handoffkit polish "One-pass polish for clarity/consistency" --root .
```

## Session Flow

### Start Session
```bash
handoffkit session start --agent-role Coder --open-docs
```
This now runs mandatory startup drift checks (`git status --porcelain` and `git diff --name-status HEAD --`) and exits non-zero if the tree is dirty.
If you intentionally want to continue with a dirty tree:
```bash
handoffkit session start --agent-role Coder --open-docs --allow-dirty
```

### End Session (writeback + commit)
```bash
handoffkit session end --commit
```
Safety behavior:
- requires `docs/NOW.md` and `docs/SESSION_NOTES.md` changes before commit
- stages only `docs/NOW.md`, `docs/SESSION_NOTES.md`, and `docs/PROJECT_CONTEXT.md` by default
- use `--stage-all` only when intentional:
```bash
handoffkit session end --commit --stage-all
```

## Config (optional)

If no config is found, defaults are aligned to local-mcp-context-kit.

Example `handoffkit.config.json`:

```json
{
  "token_budget": 7000,
  "baseline_files": ["docs/PROJECT_CONTEXT.md", "docs/NOW.md"],
  "session_notes_file": "docs/SESSION_NOTES.md",
  "session_notes_tail_lines": 120,
  "protocol_file": "docs/AGENT_SESSION_PROTOCOL.md",
  "protocol_tail_lines": 120
}
```

## Notes

- For best token efficiency, add summary blocks to your memory files:
  - `<!-- SUMMARY_START --> ... <!-- SUMMARY_END -->`
  - Recommended in `docs/PROJECT_CONTEXT.md`, `docs/NOW.md`, and `docs/SESSION_NOTES.md`
- The output ends with **SESSION END – INSTRUCTIONS** telling the agent to include “Session Updates”
  so you can easily update `NOW.md` and `SESSION_NOTES.md` per your protocol.

## Guardrails Hook (optional but recommended)

Install repo-managed hooks:
```bash
git config core.hooksPath .githooks
```
The pre-commit hook runs `scripts/check_guardrails.py` to block agent/template drift.

## Local Commit + Push

From repo root:

```bash
python3 scripts/check_guardrails.py
python3 -m unittest discover -s tests -p 'test_*.py'
git status
git add -A
git commit -m "Enforce startup/end-session drift guardrails"
git push origin <branch>
```

If you only want to run session-doc commits, use:

```bash
python3 -m handoffkit session end --commit
```

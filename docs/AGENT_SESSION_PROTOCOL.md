# Agent Session Protocol

Version: 1.1  
Owner: You

## Purpose
Define how a human and a local code agent coordinate using this repo’s memory files so every session starts with shared context and ends with consistent writeback.

## Memory Files
- Long-term memory (LTM): `docs/PROJECT_CONTEXT.md`
- Working memory (WM): `docs/NOW.md`
- Session memory (SM): `docs/SESSION_NOTES.md`
- Index/meta memory (IM): `docs/REPO_MAP.generated.md`, `docs/CODE_INDEX.generated.json`
- Design notes: `docs/MCP_LOCAL_DESIGN.md`

## Canonical Artifact
- `SPEC.md` is the source of truth for implementation.
- Architect creates/updates it; everyone else must follow it.

## Handoff Loop
Architect -> Coder -> Reviewer <-> Coder (until pass) -> QA -> Polish

## Hard Anti-Drift Rules
Every handoff prompt must include:
- Invariants (non-negotiables)
- SPEC.md (full or excerpt)
- Only relevant code snippets/diff
- Generated repo map when available

Reviewer rule:
- Reviewer must not redesign; only evaluate against SPEC.md, best practices, and current docs (Context7).
- Context docs and generated maps guide where to look; source code remains authoritative.

## Start Session (Context Hydration)
Preferred: VS Code task `Start Session (Agent - Coder)` (or pick another role; see `.vscode/tasks.json`).

Preflight (recommended):
```bash
handoffkit preflight
```

Refresh repo map when structure or responsibilities changed:
```bash
handoffkit map update
```

CLI equivalent:
```bash
handoffkit session start --agent-role Coder --open-docs
```

Startup checks (MANDATORY before reading docs):
1. Run `git status --porcelain`.
2. Run `git diff --name-status HEAD --`.
3. If uncommitted modifications exist, stop and ask: "Working tree has uncommitted changes in [files]. Discard, keep, or commit before we proceed?"
4. Continue only after working tree is clean or explicitly acknowledged by the user.

Agent instructions after startup checks:
1. Read (in order): `docs/PROJECT_CONTEXT.md`, `docs/NOW.md`, `docs/REPO_MAP.generated.md` if present, `docs/SESSION_NOTES.md` (recent).
2. Use the repo map to decide which source files to inspect first.
3. Summarize context in 3–6 bullets.
4. Wait for the next instruction.

## End Session (Writeback + Checkpoint)
Preferred: VS Code task `End Session (Agent + Commit)` (see `.vscode/tasks.json`).

CLI equivalent:
```bash
handoffkit session end --commit
```

Human steps:
1. Paste the printed `SESSION END` block into the agent.
2. Add 2–5 bullets describing what happened this session (what you changed, why).
3. Let the agent update the memory files in the workspace.
4. Return to the terminal and press Enter to run checkpoint + commit.

Writeback expectations:
- `docs/PROJECT_CONTEXT.md`: update only when higher-level decisions/constraints changed; refresh summary blocks if present.
- `docs/NOW.md`: update immediate next steps and current focus; refresh summary blocks if present.
- `docs/SESSION_NOTES.md`: append a new dated entry (do not overwrite previous entries).
- `docs/REPO_MAP.generated.md` / `docs/CODE_INDEX.generated.json`: regenerate with `handoffkit map update` after module moves, new entry points, or changed file responsibilities.

Commit safety behavior (`handoffkit session end --commit`):
- Requires `docs/NOW.md` and `docs/SESSION_NOTES.md` to be modified before commit.
- Stages only session memory files by default (`docs/NOW.md`, `docs/SESSION_NOTES.md`, `docs/PROJECT_CONTEXT.md`).
- Use `--stage-all` only when you explicitly intend to include unrelated working-tree changes.

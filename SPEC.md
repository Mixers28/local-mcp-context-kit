# SPEC.md

> Canonical specification for this project. Required in every handoff pack.

## Goals
- Keep all project memory local, transparent, and Git-versioned.
- Provide a predictable start/end ritual for human + agent collaboration.
- Make handoff prompts repeatable and role-specific.

## Non-goals
- No network services, daemons, or hosted backends.
- No automatic background syncing or hidden state.

## Constraints & Invariants
- Must remain editor-native and backend-free.
- Markdown is the source of truth for memory and specs.
- Workflow must be portable across repos.

## Architecture
- Docs in `docs/` act as LTM/WM/SM.
- Generated `docs/REPO_MAP.generated.md` and `docs/CODE_INDEX.generated.json` act as index/meta memory.
- `handoffkit` CLI builds handoff packs and session prompts.
- `skills/local-context-kit/SKILL.md` packages the operating protocol for Codex-style agents.

## Data Flow & Interfaces
- Inputs: repo docs, optional selection/diff, role instruction.
- Outputs: role prompt + context pack, generated repo map, generated code index, skill workflow instructions.

## Phases & Sprint Plan
- Phase 1: Maintain memory docs and CLI baseline behavior.
- Phase 2: Harden handoff requirements (SPEC + invariants).
- Phase 3: Improve validation and preflight checks.
- Phase 4: Generate repo maps to reduce repeated source discovery.

## Risks & Open Questions
- How strict should required artifacts be for new repos?
- How much of SPEC should be included when it is large?
- How often should generated maps be refreshed in high-churn repos?

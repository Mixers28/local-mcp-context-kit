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
- `handoffkit` CLI builds handoff packs and session prompts.

## Data Flow & Interfaces
- Inputs: repo docs, optional selection/diff, role instruction.
- Outputs: role prompt + context pack.

## Phases & Sprint Plan
- Phase 1: Maintain memory docs and CLI baseline behavior.
- Phase 2: Harden handoff requirements (SPEC + invariants).
- Phase 3: Improve validation and preflight checks.

## Risks & Open Questions
- How strict should required artifacts be for new repos?
- How much of SPEC should be included when it is large?

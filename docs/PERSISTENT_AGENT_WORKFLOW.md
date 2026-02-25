# Persistent Agent Workflow Design

This document is the source of truth for the persistent agent workflow.

Version: 1.0
Owner: You

## Purpose
This repo combines a local memory kit with the handoffkit CLI to enable a
persistent agent workflow. The goal is a predictable handoff loop where humans
and agents share the same context, select the right agent for the task, and
write back durable memory in Markdown.

## Core Ideas
- Keep memory in plain Markdown tracked by Git.
- Use the handoffkit CLI (or VS Code tasks) for explicit agent handoff.
- Keep everything local, stable-API only, and Windows-friendly.

## System Components
### Memory Files
- Long-term memory (LTM): `docs/PROJECT_CONTEXT.md`
- Working memory (WM): `docs/NOW.md`
- Session memory (SM): `docs/SESSION_NOTES.md`

### Session Protocol
- Start session: read LTM -> WM -> recent SM, then summarize context.
- End session: append session notes and update LTM/WM summaries.

### Handoffkit CLI
- Generates role prompts with context packs.
- Prints start/end session prompts and supports commit + push.
- Uses repo role prompts in `.github/agents/*.agent.md` when present.

## Primary Workflows
1) Optional: run `handoffkit preflight` to validate required files.
2) Start a session with `handoffkit session start` (or VS Code task); startup drift checks are enforced.
3) Generate a role prompt with `handoffkit <role> "<instruction>"`.
4) Provide instructions to the agent, using selection or file context when helpful.
5) At session end, write back to memory docs and commit with `handoffkit session end --commit` (checkpoint requires NOW + SESSION_NOTES updates).

## Constraints
- CLI must run on macOS/Linux/WSL.
- No external services or network dependencies.

## Testing
- Manual smoke tests for CLI prompts and handoff flow.

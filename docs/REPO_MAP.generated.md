# Repo Map

Generated from commit: 4610a7f
Generated at: 2026-06-02T00:33:34
Branch: main
Working tree: dirty
Source files scanned: 38
Machine-readable index: `docs/CODE_INDEX.generated.json`

## App Intent
Canonical specification for this project. Required in every handoff pack. Keep all project memory local, transparent, and Git-versioned. Provide a predictable start/end ritual for human + agent collaboration. Make handoff prompts repeatable and role-specific.

## Main Entry Points
- `handoffkit/__main__.py` - CLI entry point, prompt/context pack builder, session lifecycle, preflight, and repo map generation.
- `scripts/check_guardrails.py` - Consistency checks for agent prompts, templates, and protocol guardrails.
- `SPEC.md` - Canonical project specification used in handoff packs.
- `docs/PROJECT_CONTEXT.md` - Long-term project memory: intent, constraints, architecture, and stable decisions.
- `docs/NOW.md` - Working memory: current focus, active branch, and next actions.
- `docs/SESSION_NOTES.md` - Append-only session memory and recent outcomes.

## Core Modules

### Python Package
- `handoffkit/__init__.py` - Python package source.
- `handoffkit/__main__.py` - CLI entry point, prompt/context pack builder, session lifecycle, preflight, and repo map generation. Symbols: approx_tokens, read_text, strip_frontmatter, resolve_path, read_artifact_file, find_project_root, extract_summary_block, tail_lines.

### Docs And Memory
- `README.md` - Primary user-facing usage documentation.
- `SPEC.md` - Canonical project specification used in handoff packs.
- `docs/AGENT_SESSION_PROTOCOL.md` - Start/end session protocol and writeback rules.
- `docs/INVARIANTS.md` - Non-negotiable workflow constraints.
- `docs/MCP_LOCAL_DESIGN.md` - Project documentation or memory file.
- `docs/NOW.md` - Working memory: current focus, active branch, and next actions.
- `docs/PERSISTENT_AGENT_WORKFLOW.md` - Project documentation or memory file.
- `docs/PROJECT_CONTEXT.md` - Long-term project memory: intent, constraints, architecture, and stable decisions.
- `docs/Repo_Structure.md` - Project documentation or memory file.
- `docs/SESSION_NOTES.md` - Append-only session memory and recent outcomes.
- `docs/local-mcp-context-kit.code-workspace` - Project documentation or memory file.

### Guardrails And Automation
- `.github/workflows/guardrails.yml` - GitHub Actions workflow.
- `scripts/check_guardrails.py` - Consistency checks for agent prompts, templates, and protocol guardrails. Symbols: read_text, check_markers, main.

### Agent Prompts And Templates
- `.github/agents/architect.agent.md` - Role-specific GitHub/Copilot agent prompt.
- `.github/agents/coder.agent.md` - Role-specific GitHub/Copilot agent prompt.
- `.github/agents/polish.agent.md` - Role-specific GitHub/Copilot agent prompt.
- `.github/agents/qa.agent.md` - Role-specific GitHub/Copilot agent prompt.
- `.github/agents/reviewer.agent.md` - Role-specific GitHub/Copilot agent prompt.
- `handoffkit/templates/architect.md` - Fallback role prompt template bundled with the package.
- `handoffkit/templates/coder.md` - Fallback role prompt template bundled with the package.
- `handoffkit/templates/polish.md` - Fallback role prompt template bundled with the package.
- `handoffkit/templates/qa_tester.md` - Fallback role prompt template bundled with the package.
- `handoffkit/templates/reviewer.md` - Fallback role prompt template bundled with the package.

### Tests
- `tests/test_guardrail_script.py` - Automated test coverage for CLI and guardrail behavior. Symbols: GuardrailScriptTests.
- `tests/test_repo_map.py` - Automated test coverage for CLI and guardrail behavior. Symbols: RepoMapTests.
- `tests/test_required_artifacts.py` - Automated test coverage for CLI and guardrail behavior. Symbols: RequiredArtifactTests.
- `tests/test_session_guardrails.py` - Automated test coverage for CLI and guardrail behavior. Symbols: SessionGuardrailTests, SessionStartCliTests.

### Editor And Package Config
- `.vscode/settings.json` - VS Code workspace/task configuration for local workflows.
- `.vscode/tasks.json` - VS Code workspace/task configuration for local workflows.
- `handoffkit/handoffkit.config.json` - Python package source.
- `handoffkit.config.json` - Repository file.
- `pyproject.toml` - Python package metadata and console script configuration.

### Other
- `.githooks/pre-commit` - Repository file.
- `.gitignore` - Repository file.
- `REPO_README.md` - Repository file.
- `skills/local-context-kit/SKILL.md` - Repository file.

## Workflows
- Start session: run `handoffkit session start`, then read context docs and this repo map before source files.
- End session: run `handoffkit session end`, update NOW and SESSION_NOTES, then checkpoint/commit if requested.
- Prompt compile: run `handoffkit <role> <instruction>` to build a token-budgeted handoff pack.
- Repo map refresh: run `handoffkit map update` after module moves, new entry points, or responsibility changes.

## Files To Inspect Before Changing
- Session behavior or prompt packing: `handoffkit/__main__.py`, `tests/test_session_guardrails.py`, `tests/test_required_artifacts.py`.
- Guardrail wording or required markers: `scripts/check_guardrails.py`, `.github/agents/*.agent.md`, `handoffkit/templates/*.md`, `docs/AGENT_SESSION_PROTOCOL.md`.
- Memory protocol: `docs/PROJECT_CONTEXT.md`, `docs/NOW.md`, `docs/SESSION_NOTES.md`, `docs/INVARIANTS.md`.
- Packaging or CLI entry point: `pyproject.toml`, `handoffkit/__main__.py`.

## Grounding Rule
Use this map to decide where to inspect first. Source code remains authoritative for behavior.

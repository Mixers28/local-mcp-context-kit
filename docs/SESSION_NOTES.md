# Session Notes – Session Memory (SM)

> Rolling log of what happened in each focused work session.  
> Append-only. Do not delete past sessions.

<!-- SUMMARY_START -->
**Latest Summary (auto-maintained by Agent):**
- Added generated repo map/index support with `handoffkit map update`.
- Startup prompts and handoff packs now use `docs/REPO_MAP.generated.md` when present.
- Added a repo-local Codex skill draft for the map-first workflow.
- Next step is deciding skill installation/distribution and reviewing token-budget defaults.
<!-- SUMMARY_END -->

---

## Maintenance Rules (reduce drift)

- Append-only entries; never rewrite history.
- Update this summary block every session with the last 1–3 sessions.
- Roll up stable decisions to PROJECT_CONTEXT and active tasks to NOW.

---

## Example Entry

### 2025-12-01

**Participants:** User,VS Code Agent, Chatgpt   
**Branch:** main  

### What we worked on
- Set up local MCP-style context system.
- Added handoffkit CLI and VS Code tasks.
- Defined PROJECT_CONTEXT / NOW / SESSION_NOTES workflow.

### Files touched
- docs/PROJECT_CONTEXT.md
- docs/NOW.md
- docs/SESSION_NOTES.md
- docs/AGENT_SESSION_PROTOCOL.md
- docs/MCP_LOCAL_DESIGN.md
- handoffkit/__main__.py
- pyproject.toml
- .vscode/tasks.json

### Outcomes / Decisions
- Established start/end session ritual.
- Agents will maintain summaries and NOW.md.
- This repo will be used as a public template.

---

## Session Template (Copy/Paste for each new session)
## Recent Sessions (last 3-5)

### 2026-06-02 (Repo map)

**Participants:** User, Codex Agent  
**Branch:** main  

### What we worked on
- Implemented `handoffkit map update`.
- Generated `docs/REPO_MAP.generated.md` and `docs/CODE_INDEX.generated.json`.
- Updated startup/read-order docs so agents consult the repo map before source scans.
- Added `skills/local-context-kit/SKILL.md` as a repo-local Codex skill draft.
- Added tests for repo map generation, CLI output, startup prompt behavior, and required artifacts.

### Files touched
- handoffkit/__main__.py
- handoffkit.config.json
- handoffkit/handoffkit.config.json
- tests/test_repo_map.py
- tests/test_required_artifacts.py
- docs/REPO_MAP.generated.md
- docs/CODE_INDEX.generated.json
- README.md
- SPEC.md
- docs/PROJECT_CONTEXT.md
- docs/NOW.md
- docs/SESSION_NOTES.md
- docs/AGENT_SESSION_PROTOCOL.md
- docs/MCP_LOCAL_DESIGN.md
- docs/INVARIANTS.md
- skills/local-context-kit/SKILL.md

### Outcomes / Decisions
- Repo maps are generated artifacts, not hand-written truth.
- Context docs and maps guide where to inspect first; source code remains authoritative.
- `python3 scripts/check_guardrails.py`, `python3 -m unittest discover -s tests -p 'test_*.py'`, and `python3 -m handoffkit preflight --root .` passed.

### 2026-06-02

**Participants:** User, Codex Agent  
**Branch:** main  

### What we worked on
- Cloned the repository into the local workspace.
- Added focused tests for `handoffkit preflight` and required SPEC/Invariants handling.
- Verified that role handoff packs include required artifacts and reject `--no-spec` when SPEC is required.

### Files touched
- tests/test_required_artifacts.py
- docs/NOW.md
- docs/SESSION_NOTES.md

### Outcomes / Decisions
- Guardrail checks passed.
- `python3 -m unittest discover -s tests -p 'test_*.py'` passed with 11 tests.
- Full start/end session validation and token-budget review remain the next active tasks.

### 2026-02-04

**Participants:** User, Codex Agent  
**Branch:** main  

### What we worked on
- Added required SPEC + Invariants to handoff packs and introduced `handoffkit preflight`.
- Created baseline `SPEC.md` and `docs/INVARIANTS.md`.
- Updated workflow docs and templates to reflect the new requirements.

### Files touched
- handoffkit/__main__.py
- handoffkit.config.json
- handoffkit/handoffkit.config.json
- SPEC.md
- docs/INVARIANTS.md
- docs/Repo_Structure.md
- docs/PERSISTENT_AGENT_WORKFLOW.md
- docs/AGENT_SESSION_PROTOCOL.md
- handoffkit/templates/architect.md

### Outcomes / Decisions
- SPEC + Invariants are required artifacts for handoff packs.
- Preflight validation is part of the recommended workflow.

### 2025-12-01 (Session 2)

**Participants:** User, Codex Agent  
**Branch:** main  

### What we worked on
- Re-read PROJECT_CONTEXT, NOW, and SESSION_NOTES to prep session handoff.
- Tightened the summaries in PROJECT_CONTEXT.md and NOW.md to mirror the current project definition.
- Reconfirmed the immediate tasks: polish docs, add an example project, and test on a real repo.

### Files touched
- docs/PROJECT_CONTEXT.md
- docs/NOW.md
- docs/SESSION_NOTES.md

### Outcomes / Decisions
- Locked the near-term plan around doc polish, example walkthrough, and single-repo validation.
- Still waiting on any additional stakeholder inputs before expanding scope.

### 2025-12-01

**Participants:** User, Codex Agent  
**Branch:** main  

### What we worked on
- Reviewed the memory docs to confirm expectations for PROJECT_CONTEXT, NOW, and SESSION_NOTES.
- Updated NOW.md and PROJECT_CONTEXT.md summaries to reflect that real project data is still pending.
- Highlighted the need for stakeholder inputs before populating concrete tasks or deliverables.

### Files touched
- docs/PROJECT_CONTEXT.md
- docs/NOW.md
- docs/SESSION_NOTES.md

### Outcomes / Decisions
- Documented that the repo currently serves as a template awaiting real project data.
- Set the short-term focus on collecting actual objectives and backlog details.

### [DATE – e.g. 2025-12-02]

**Participants:** [You, VS Code Agent, other agents]  
**Branch:** [main / dev / feature-x]  

### What we worked on
- 

### Files touched
- 

### Outcomes / Decisions
-

## Archive (do not load by default)
...

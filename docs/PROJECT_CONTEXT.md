# Project Context – Long-Term Memory (LTM)

> High-level design, tech decisions, constraints for this project.  
> This is the **source of truth** for agents and humans.

<!-- SUMMARY_START -->
**Summary (auto-maintained by Agent):**
- Template repo proving Markdown + Git can store long-lived memory for AI coding agents.
- Workflow stays local inside VS Code + handoffkit CLI; no backend dependencies.
- Handoff packs require SPEC + Invariants, support preflight checks, and include generated repo maps when present.
- `handoffkit map update` generates repo structure/index metadata to reduce repeated source discovery.
- A repo-local Codex skill draft packages the map-first workflow without replacing CLI tooling.
- Drift guardrails: keep summaries tight, log decisions here, and keep NOW short and current.
<!-- SUMMARY_END -->

---

## 1. Project Overview

- **Name:** local-mcp-context-kit
- **Owner:** TBD (template maintainer)
- **Purpose:** Template repo demonstrating how Markdown plus Git can serve as durable memory for AI coding agents.
- **Primary Stack:** Git + Markdown docs, VS Code editor, Python CLI helper (no backend).
- **Target Platforms:** Local developer environments (VS Code on desktop).

---

## 2. Core Design Pillars

- Keep project memory transparent and versioned via Markdown in Git.
- Maintain an editor-native workflow (VS Code + handoffkit CLI) without external services.
- Provide a reusable template that agents and humans can adopt quickly.

---

## 3. Technical Decisions & Constraints

- Language(s): Markdown for docs; Python helper CLI as needed.
- Framework(s): None; rely on native editor tooling.
- Database / storage: Git repository history; no external database.
- Hosting / deployment: Shared via Git hosting and cloned locally.
- Non-negotiable constraints:
  - Must remain backend-free and editor-native.
  - Documentation stays in plain Markdown for easy review.
  - Handoffs require SPEC + Invariants to reduce drift.
  - Generated repo maps guide inspection, but source code remains authoritative.

---

## 4. Memory Hygiene (Drift Guards)

- Keep this summary block current and <= 300 tokens.
- Move stable decisions into the Change Log so they persist across sessions.
- Keep NOW to 5–12 active tasks; archive or remove completed items.
- Roll up SESSION_NOTES into summaries weekly (or every few sessions).

---

## 5. Architecture Snapshot

- Docs folder holds long-term (PROJECT_CONTEXT), working-memory (NOW), and session logs (SESSION_NOTES).
- Generated repo map/index files provide index/meta memory for startup context.
- The handoffkit CLI guides agents through start/end rituals, preflight checks, and repo map generation.
- The skill file captures the reusable agent protocol while scripts handle deterministic generation/validation.
- VS Code tasks integrate with the handoffkit CLI so humans/agents share the same workflow.

---

## 6. Links & Related Docs

- Roadmap: TBD
- Design docs: docs/MCP_LOCAL_DESIGN.md, docs/AGENT_SESSION_PROTOCOL.md
- Specs: SPEC.md, docs/Repo_Structure.md
- Product / UX docs: docs/PROJECT_CONTEXT.md, docs/NOW.md
- Invariants: docs/INVARIANTS.md
- Repo map: docs/REPO_MAP.generated.md, docs/CODE_INDEX.generated.json
- Skill draft: skills/local-context-kit/SKILL.md

---

## 7. Change Log (High-Level Decisions)

Use this section for **big decisions** only:

- `2026-02-04` – Require SPEC + Invariants in handoff packs and add preflight validation.
- `2026-06-02` – Add generated repo map/index artifacts to reduce repeated source discovery.
- `2026-06-02` – Add repo-local Codex skill draft for the map-first workflow.
- `YYYY-MM-DD` – Decided on X instead of Y.
- `YYYY-MM-DD` – Switched primary deployment target to Z.

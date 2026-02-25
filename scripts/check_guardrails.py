#!/usr/bin/env python3
"""Repo guardrails consistency checks.

This script enforces anti-drift prompt/protocol invariants so regressions fail early
in hooks and CI.
"""

from pathlib import Path
import sys
from typing import List

ROOT = Path(__file__).resolve().parents[1]

STARTUP_REQUIRED_MARKERS = [
    "Startup Checks (MANDATORY - run before reading docs)",
    "`git status --porcelain`",
    "`git diff --name-status HEAD --`",
    "STOP and ask the user",
]

END_REQUIRED_MARKERS = [
    "## End of session (MANDATORY)",
    "docs/NOW.md",
    "docs/SESSION_NOTES.md",
    "git status",
    "HEAD hash",
]

PROMPT_FILES = [
    ".github/agents/architect.agent.md",
    ".github/agents/coder.agent.md",
    ".github/agents/reviewer.agent.md",
    ".github/agents/qa.agent.md",
    ".github/agents/polish.agent.md",
    "handoffkit/templates/architect.md",
    "handoffkit/templates/coder.md",
    "handoffkit/templates/reviewer.md",
    "handoffkit/templates/qa_tester.md",
    "handoffkit/templates/polish.md",
]

END_REQUIRED_FILES = [
    ".github/agents/coder.agent.md",
    ".github/agents/reviewer.agent.md",
    ".github/agents/qa.agent.md",
    "handoffkit/templates/coder.md",
    "handoffkit/templates/reviewer.md",
    "handoffkit/templates/qa_tester.md",
]


def read_text(rel_path: str) -> str:
    path = ROOT / rel_path
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {rel_path}")
    return path.read_text(encoding="utf-8")


def check_markers(rel_path: str, markers: List[str], issues: List[str]) -> None:
    content = read_text(rel_path)
    for marker in markers:
        if marker not in content:
            issues.append(f"{rel_path}: missing marker '{marker}'")


def main() -> int:
    issues: List[str] = []

    for rel in PROMPT_FILES:
        check_markers(rel, STARTUP_REQUIRED_MARKERS, issues)

    for rel in END_REQUIRED_FILES:
        check_markers(rel, END_REQUIRED_MARKERS, issues)

    # Context7 command naming consistency.
    reviewer_agent = read_text(".github/agents/reviewer.agent.md")
    reviewer_template = read_text("handoffkit/templates/reviewer.md")
    if "query-docs" not in reviewer_agent:
        issues.append(".github/agents/reviewer.agent.md: missing 'query-docs'")
    if "get-library-docs" in reviewer_agent:
        issues.append(".github/agents/reviewer.agent.md: contains deprecated 'get-library-docs'")
    if "query-docs" not in reviewer_template:
        issues.append("handoffkit/templates/reviewer.md: missing 'query-docs'")

    protocol = read_text("docs/AGENT_SESSION_PROTOCOL.md")
    protocol_markers = [
        "Startup checks (MANDATORY before reading docs)",
        "Commit safety behavior",
        "Requires `docs/NOW.md` and `docs/SESSION_NOTES.md`",
    ]
    for marker in protocol_markers:
        if marker not in protocol:
            issues.append(f"docs/AGENT_SESSION_PROTOCOL.md: missing marker '{marker}'")

    if issues:
        print("Guardrail checks failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Guardrail checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

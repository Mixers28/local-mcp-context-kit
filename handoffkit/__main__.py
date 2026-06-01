import argparse, ast, json, sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Sequence

def approx_tokens(text: str) -> int:
    # Extremely rough heuristic: ~4 chars/token typical for English.
    return max(1, len(text) // 4)

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="utf-8", errors="replace")

def strip_frontmatter(md: str) -> str:
    # Strips simple YAML frontmatter if present: --- ... --- at the top.
    if md.startswith("---"):
        parts = md.split("---", 2)
        if len(parts) >= 3:
            return parts[2].lstrip("\n")
    return md

def resolve_path(path_str: str, project_root: Path) -> Path:
    p = Path(path_str)
    if not p.is_absolute():
        p = (project_root / p).resolve()
    return p

def read_artifact_file(path_str: Optional[str], *, project_root: Path, label: str, required: bool) -> Tuple[Optional[str], Optional[Path]]:
    if not path_str:
        if required:
            raise FileNotFoundError(f"{label} file not specified.")
        return None, None
    p = resolve_path(path_str, project_root)
    if not p.exists():
        if required:
            raise FileNotFoundError(f"{label} file not found: {p}")
        return None, None
    content = read_text(p).strip()
    if not content:
        if required:
            raise RuntimeError(f"{label} file is empty: {p}")
        return None, p
    return content, p

def find_project_root(start: Path) -> Path:
    """Walk upwards to find a likely project root (Local MCP layout)."""
    start = start.resolve()
    for p in [start] + list(start.parents):
        if (p / "docs" / "PROJECT_CONTEXT.md").exists():
            return p
        if (p / ".git").exists():
            # If we're in a git repo but no docs found, still treat repo root as root.
            return p
    return start

def extract_summary_block(text: str) -> Optional[str]:
    s = text.find("<!-- SUMMARY_START -->")
    e = text.find("<!-- SUMMARY_END -->")
    if s != -1 and e != -1 and e > s:
        return text[s + len("<!-- SUMMARY_START -->"):e].strip()
    return None

def tail_lines(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text.strip()
    return "\n".join(lines[-max_lines:]).strip()

def truncate_text(text: str, max_tokens: int) -> str:
    if max_tokens <= 0:
        return ""
    limit = max_tokens * 4
    if len(text) <= limit:
        return text.strip()
    truncated = False
    cut = text.rfind("\n", 0, limit)
    if cut == -1:
        cut = limit
    truncated = True
    out = (text[:cut].rstrip() + "\n…(truncated)…").strip()
    if truncated and out.count("```") % 2 == 1:
        out = out.rstrip() + "\n```"
    return out.strip()

ROLE_CHOICES = ["architect", "coder", "reviewer", "qa_tester", "polish", "qa"]
SESSION_ROLE_CHOICES = ["Architect", "Coder", "Reviewer", "QA"]
SESSION_REQUIRED_WRITEBACK_FILES = ["docs/NOW.md", "docs/SESSION_NOTES.md"]
SESSION_STAGE_FILES = ["docs/NOW.md", "docs/SESSION_NOTES.md", "docs/PROJECT_CONTEXT.md"]
DEFAULT_REPO_MAP_FILE = "docs/REPO_MAP.generated.md"
DEFAULT_CODE_INDEX_FILE = "docs/CODE_INDEX.generated.json"

def read_optional_input(path_str: Optional[str], *, project_root: Path, label: str) -> Optional[str]:
    """Read optional content from a file path or stdin.

    Supports:
      --diff /path/to/file.diff
      --diff -    (read from stdin)
    Paths are resolved relative to project_root if not absolute.
    """
    if not path_str:
        return None
    if path_str == "-":
        data = sys.stdin.read()
        return f"## {label}\n\n```\n{data.strip()}\n```" if data.strip() else None
    p = Path(path_str)
    if not p.is_absolute():
        p = (project_root / p).resolve()
    if not p.exists():
        raise FileNotFoundError(f"{label} file not found: {p}")
    content = read_text(p).strip()
    if not content:
        return None
    return f"## {label}\n\n```\n{content}\n```"

def load_config(project_root: Path, tool_root: Path, config_path: Optional[str]) -> Dict:
    """Load config.

    Search order (unless explicit path provided):
      1) explicit --config
      2) <project_root>/handoffkit.config.json
      3) <tool_root>/handoffkit.config.json
    """
    candidates: List[Path] = []
    if config_path:
        p = Path(config_path)
        if not p.is_absolute():
            # allow relative to cwd
            p = (Path.cwd() / p).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {p}")
        candidates.append(p)
    else:
        candidates.append(project_root / "handoffkit.config.json")
        candidates.append(tool_root / "handoffkit.config.json")

    cfg_path = next((p for p in candidates if p.exists()), None)
    if cfg_path:
        try:
            return json.loads(read_text(cfg_path))
        except Exception as e:
            raise RuntimeError(f"Failed to parse config at {cfg_path}: {e}")

    # Defaults aligned to local-mcp-context-kit layout
    return {
        "token_budget": 2200,
        "baseline_files": [
            "docs/PROJECT_CONTEXT.md",
            "docs/NOW.md",
        ],
        "session_notes_file": "docs/SESSION_NOTES.md",
        "session_notes_tail_lines": 80,
        "protocol_file": "docs/AGENT_SESSION_PROTOCOL.md",
        "protocol_tail_lines": 120,
        "spec_file": "SPEC.md",
        "invariants_file": "docs/INVARIANTS.md",
        "repo_map_file": DEFAULT_REPO_MAP_FILE,
        "code_index_file": DEFAULT_CODE_INDEX_FILE,
        "require_spec": False,
        "require_invariants": False,
        "auto_include_spec": True,
        "auto_include_invariants": True,
    }

def load_role_prompt(project_root: Path, tool_root: Path, role: str) -> Tuple[str, Optional[Path]]:
    """Load role prompt from repo agents if present, else from kit templates."""
    role = role.lower()
    slug_candidates = [role]
    if role == "qa_tester":
        slug_candidates = ["qa_tester", "qa"]
    elif role == "qa":
        slug_candidates = ["qa", "qa_tester"]

    for slug in slug_candidates:
        repo_agent_path = project_root / ".github" / "agents" / f"{slug}.agent.md"
        if repo_agent_path.exists():
            content = strip_frontmatter(read_text(repo_agent_path)).strip()
            return content, repo_agent_path

    template_path = tool_root / "templates" / f"{role}.md"
    if not template_path.exists():
        # Fallback: try qa_tester if qa requested (or qa_tester if qa is missing)
        if role in ("qa", "qa_tester") and (tool_root / "templates" / "qa_tester.md").exists():
            template_path = tool_root / "templates" / "qa_tester.md"
        else:
            raise FileNotFoundError(f"Template not found for role '{role}' at {template_path}")
    return read_text(template_path).strip(), None

def read_baseline_section(project_root: Path, rel: str, max_tokens: int) -> Optional[Tuple[str,str]]:
    p = Path(rel)
    if not p.is_absolute():
        p = (project_root / p)
    if not p.exists():
        return None
    raw = read_text(p)
    summary = extract_summary_block(raw)
    content = summary if summary else raw.strip()
    # token cap
    if approx_tokens(content) > max_tokens:
        content = truncate_text(content, max_tokens)
    title = rel
    return title, content

def build_context_pack(
    project_root: Path,
    cfg: Dict,
    instruction: str,
    selection: Optional[str],
    diff_text: Optional[str],
    *,
    role_name: str,
    role_agent_path: Optional[Path],
    spec_content: Optional[str],
    spec_title: Optional[str],
    invariants_content: Optional[str],
    invariants_title: Optional[str],
) -> str:
    budget = int(cfg.get("token_budget", 2200))

    # High-priority sections (never trimmed too aggressively)
    header_lines = []
    header_lines.append("SESSION START – PROJECT CONTEXT")
    header_lines.append("")
    header_lines.append("You are a local code assistant working on this project.")
    header_lines.append("")
    if role_agent_path:
        header_lines.append(f"Role reference file: {role_agent_path.as_posix()}")
    header = "\n".join(header_lines).strip()

    sections: List[Tuple[str, str, int]] = []  # (title, content, priority)
    # priority: higher = keep more
    sections.append(("Instruction", instruction.strip(), 100))
    if spec_content:
        sections.append((spec_title or "SPEC.md", spec_content.strip(), 95))
    if invariants_content:
        sections.append((invariants_title or "Invariants", invariants_content.strip(), 95))
    if selection:
        sections.append(("Selection", selection, 90))
    if diff_text:
        sections.append(("Diff", diff_text, 90))

    # Baseline in priority order: NOW > PROJECT_CONTEXT
    for rel in cfg.get("baseline_files", []):
        if rel.endswith("NOW.md"):
            sections.append(("NOW", rel, 60))
        else:
            sections.append(("PROJECT_CONTEXT", rel, 50))

    # Session notes (tail)
    repo_map_rel = cfg.get("repo_map_file", DEFAULT_REPO_MAP_FILE)
    if repo_map_rel:
        repo_map_path = project_root / repo_map_rel
        if repo_map_path.exists():
            repo_map = truncate_text(read_text(repo_map_path), 700)
            sections.append((repo_map_rel, repo_map, 45))

    sn_rel = cfg.get("session_notes_file")
    if sn_rel:
        sn_path = project_root / sn_rel
        if sn_path.exists():
            sn_raw = read_text(sn_path)
            sn_summary = extract_summary_block(sn_raw)
            sn = sn_summary if sn_summary else tail_lines(sn_raw, int(cfg.get("session_notes_tail_lines", 80)))
            sections.append(("Recent SESSION_NOTES", sn, 35))

    # Protocol excerpt (tail)
    proto_rel = cfg.get("protocol_file")
    if proto_rel:
        proto_path = project_root / proto_rel
        if proto_path.exists():
            proto_raw = read_text(proto_path)
            proto_summary = extract_summary_block(proto_raw)
            proto = proto_summary if proto_summary else tail_lines(proto_raw, int(cfg.get("protocol_tail_lines", 120)))
            sections.append(("AGENT_SESSION_PROTOCOL", proto, 25))

    # Materialize baseline file sections (which are stored as rel paths above)
    materialized: List[Tuple[str, str, int]] = []
    for title, content, prio in sections:
        if title in ("NOW", "PROJECT_CONTEXT") and isinstance(content, str):
            max_tok = 450 if title == "NOW" else 650
            rb = read_baseline_section(project_root, content, max_tokens=max_tok)
            if rb:
                t, c = rb
                materialized.append((t, c, prio))
                continue
        materialized.append((title, content, prio))

    # Budgeting: allocate more to higher priority, but keep everything if possible.
    # We'll trim lower-priority sections first.
    def section_tokens(txt: str) -> int:
        stripped = txt.strip()
        if not stripped:
            return 0
        return approx_tokens(stripped)

    # Prepare pretty formatting
    out_parts = [header, ""]
    # Reserve a small amount for framing + markdown overhead.
    reserved = min(120, max(40, budget // 5))
    remaining = max(0, budget - reserved)

    # Sort by priority desc for initial inclusion, but we'll render in a logical order later.
    # First, trim if needed.
    mats = materialized[:]
    total = sum(section_tokens(c) for _, c, _ in mats)
    if total > remaining:
        # Trim in ascending priority order.
        mats_sorted = sorted(mats, key=lambda x: x[2])
        over = total - remaining
        trimmed = []
        for title, content, prio in mats_sorted:
            if over <= 0:
                trimmed.append((title, content, prio))
                continue
            min_keep = 160 if prio >= 90 else 120 if prio >= 60 else 90 if prio >= 35 else 60
            tok = section_tokens(content)
            if tok <= min_keep:
                trimmed.append((title, content, prio))
                continue
            cut = min(tok - min_keep, over)
            new_tok = tok - cut
            new_content = truncate_text(content, new_tok)
            trimmed.append((title, new_content, prio))
            over -= cut
        mats = trimmed

    over = sum(section_tokens(c) for _, c, _ in mats) - remaining
    if over > 0:
        # If we still exceed the budget, trim below the soft minimum.
        mats_sorted = sorted(mats, key=lambda x: x[2])
        trimmed = []
        for title, content, prio in mats_sorted:
            if over <= 0:
                trimmed.append((title, content, prio))
                continue
            hard_min = 80 if prio >= 90 else 60 if prio >= 60 else 40 if prio >= 35 else 20
            tok = section_tokens(content)
            if tok <= hard_min:
                trimmed.append((title, content, prio))
                continue
            cut = min(tok - hard_min, over)
            new_tok = tok - cut
            new_content = truncate_text(content, new_tok)
            trimmed.append((title, new_content, prio))
            over -= cut
        mats = trimmed

    over = sum(section_tokens(c) for _, c, _ in mats) - remaining
    if over > 0:
        # Final pass: trim lowest priority sections further to guarantee the cap.
        mats_sorted = sorted(mats, key=lambda x: x[2])
        trimmed = []
        for title, content, prio in mats_sorted:
            if over <= 0:
                trimmed.append((title, content, prio))
                continue
            tok = section_tokens(content)
            if tok <= 0:
                trimmed.append((title, content, prio))
                continue
            cut = min(tok, over)
            new_tok = tok - cut
            new_content = truncate_text(content, new_tok)
            trimmed.append((title, new_content, prio))
            over -= cut
        mats = trimmed

    # Render in deterministic order:
    render_order = ["Instruction"]
    if invariants_content:
        render_order.append(invariants_title or "Invariants")
    if spec_content:
        render_order.append(spec_title or "SPEC.md")
    render_order.extend(["docs/NOW.md", "docs/PROJECT_CONTEXT.md", DEFAULT_REPO_MAP_FILE, "Recent SESSION_NOTES", "AGENT_SESSION_PROTOCOL", "Selection", "Diff"])
    # Map titles
    rendered = []
    for wanted in render_order:
        for title, content, prio in mats:
            if title == wanted:
                rendered.append((title, content))
    # Also include any leftovers
    existing_titles = {t for t,_ in rendered}
    for title, content, _ in mats:
        if title not in existing_titles:
            rendered.append((title, content))

    for title, content in rendered:
        if title == "Instruction":
            out_parts.append("## Instruction")
            out_parts.append(content.strip())
            out_parts.append("")
        elif title in ("Selection", "Diff"):
            # already includes markdown header/fence
            out_parts.append(content.strip())
            out_parts.append("")
        else:
            out_parts.append(f"## {title}")
            out_parts.append(content.strip())
            out_parts.append("")

    out_parts.append("SESSION END – INSTRUCTIONS")
    out_parts.append("")
    out_parts.append("When you finish your response, include a short section titled 'Session Updates' with:")
    out_parts.append("- 2–5 bullets summarizing what we did")
    out_parts.append("- Any updates needed for docs/NOW.md and docs/SESSION_NOTES.md (per AGENT_SESSION_PROTOCOL)")
    out_parts.append("- Next actions (if any)")
    return "\n".join(out_parts).strip()

def run_git(args: List[str], *, cwd: Path, capture: bool = False, check: bool = True) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            capture_output=capture,
            check=False,
        )
    except FileNotFoundError:
        if check:
            raise RuntimeError("git not found on PATH")
        return ""
    if check and result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {details}")
    return result.stdout if capture else ""

def git_status_porcelain_lines(project_root: Path, paths: Optional[Sequence[str]] = None) -> List[str]:
    cmd = ["status", "--porcelain"]
    if paths:
        cmd.extend(["--", *paths])
    try:
        out = run_git(cmd, cwd=project_root, capture=True)
    except RuntimeError:
        return []
    return [line.rstrip() for line in out.splitlines() if line.strip()]

def git_diff_name_status_vs_head(project_root: Path, paths: Optional[Sequence[str]] = None) -> List[str]:
    cmd = ["diff", "--name-status", "HEAD"]
    if paths:
        cmd.extend(["--", *paths])
    try:
        out = run_git(cmd, cwd=project_root, capture=True)
    except RuntimeError:
        return []
    return [line.rstrip() for line in out.splitlines() if line.strip()]

def print_startup_checks(project_root: Path) -> bool:
    print("Startup Checks (MANDATORY)")
    status_lines = git_status_porcelain_lines(project_root)
    diff_lines = git_diff_name_status_vs_head(project_root)

    if status_lines:
        print("1) git status --porcelain: uncommitted changes detected")
        for line in status_lines:
            print(f"   - {line}")
    else:
        print("1) git status --porcelain: clean")

    if diff_lines:
        print("2) git diff --name-status HEAD -- :")
        for line in diff_lines:
            print(f"   - {line}")
    else:
        print("2) git diff --name-status HEAD -- : no tracked changes vs HEAD")

    return bool(status_lines)

def has_uncommitted_changes_for_path(project_root: Path, rel_path: str) -> bool:
    return bool(git_status_porcelain_lines(project_root, paths=[rel_path]))

def missing_writeback_files(project_root: Path) -> List[str]:
    missing = []
    for rel_path in SESSION_REQUIRED_WRITEBACK_FILES:
        if not has_uncommitted_changes_for_path(project_root, rel_path):
            missing.append(rel_path)
    return missing

def preflight_report(project_root: Path, cfg: Dict) -> int:
    print("Local MCP – Preflight")
    print("")

    issues = 0

    def check_file(label: str, path_str: Optional[str], *, required: bool) -> None:
        nonlocal issues
        if not path_str:
            if required:
                print(f"MISSING: {label} (no path configured)")
                issues += 1
            else:
                print(f"SKIP: {label} (no path configured)")
            return
        p = resolve_path(path_str, project_root)
        if not p.exists():
            if required:
                print(f"MISSING: {label} ({p.as_posix()})")
                issues += 1
            else:
                print(f"WARN: {label} not found ({p.as_posix()})")
            return
        content = read_text(p).strip()
        if not content and required:
            print(f"MISSING: {label} is empty ({p.as_posix()})")
            issues += 1
        else:
            print(f"OK: {label} ({p.as_posix()})")
        if extract_summary_block(content) is None:
            print(f"INFO: {label} has no SUMMARY block")

    for rel in cfg.get("baseline_files", []):
        check_file(rel, rel, required=True)

    check_file("Session notes", cfg.get("session_notes_file"), required=True)
    check_file("Protocol", cfg.get("protocol_file"), required=True)

    auto_spec = bool(cfg.get("auto_include_spec", True))
    auto_invariants = bool(cfg.get("auto_include_invariants", True))
    require_spec = bool(cfg.get("require_spec", False))
    require_invariants = bool(cfg.get("require_invariants", False))

    if auto_spec or require_spec:
        check_file("SPEC.md", cfg.get("spec_file"), required=require_spec)
    if auto_invariants or require_invariants:
        check_file("Invariants", cfg.get("invariants_file"), required=require_invariants)

    if issues:
        print("")
        print(f"Preflight failed with {issues} issue(s).")
    else:
        print("")
        print("Preflight OK.")
    return 1 if issues else 0

def git_head_sha(project_root: Path) -> str:
    try:
        return run_git(["rev-parse", "--short", "HEAD"], cwd=project_root, capture=True).strip()
    except RuntimeError:
        return ""

def current_branch(project_root: Path) -> str:
    try:
        return run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=project_root, capture=True).strip()
    except RuntimeError:
        return ""

def should_index_path(rel_path: Path) -> bool:
    parts = rel_path.parts
    excluded_dirs = {".git", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache", "node_modules", "dist", "build"}
    if any(part in excluded_dirs for part in parts):
        return False
    rel = rel_path.as_posix()
    if rel in {DEFAULT_REPO_MAP_FILE, DEFAULT_CODE_INDEX_FILE}:
        return False
    if rel.endswith((".pyc", ".pyo", ".DS_Store")):
        return False
    return True

def list_project_files(project_root: Path) -> List[Path]:
    try:
        out = run_git(
            ["ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=project_root,
            capture=True,
        )
        rels = [line.strip() for line in out.splitlines() if line.strip()]
        if rels:
            return sorted(Path(rel) for rel in rels if should_index_path(Path(rel)))
    except RuntimeError:
        pass

    files: List[Path] = []
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(project_root)
        except ValueError:
            continue
        if should_index_path(rel):
            files.append(rel)
    return sorted(files)

def file_kind(rel_path: Path) -> str:
    rel = rel_path.as_posix()
    suffix = rel_path.suffix.lower()
    if rel.startswith("docs/") or suffix in {".md", ".mdx"}:
        return "documentation"
    if suffix == ".py":
        return "python"
    if suffix in {".json", ".toml", ".yaml", ".yml"}:
        return "configuration"
    if rel.startswith(".github/"):
        return "automation"
    return "other"

def infer_file_role(rel_path: Path) -> str:
    rel = rel_path.as_posix()
    roles = {
        "handoffkit/__main__.py": "CLI entry point, prompt/context pack builder, session lifecycle, preflight, and repo map generation.",
        "pyproject.toml": "Python package metadata and console script configuration.",
        "scripts/check_guardrails.py": "Consistency checks for agent prompts, templates, and protocol guardrails.",
        "SPEC.md": "Canonical project specification used in handoff packs.",
        "README.md": "Primary user-facing usage documentation.",
        "docs/PROJECT_CONTEXT.md": "Long-term project memory: intent, constraints, architecture, and stable decisions.",
        "docs/NOW.md": "Working memory: current focus, active branch, and next actions.",
        "docs/SESSION_NOTES.md": "Append-only session memory and recent outcomes.",
        "docs/AGENT_SESSION_PROTOCOL.md": "Start/end session protocol and writeback rules.",
        "docs/INVARIANTS.md": "Non-negotiable workflow constraints.",
    }
    if rel in roles:
        return roles[rel]
    if rel.startswith("tests/"):
        return "Automated test coverage for CLI and guardrail behavior."
    if rel.startswith(".github/agents/"):
        return "Role-specific GitHub/Copilot agent prompt."
    if rel.startswith("handoffkit/templates/"):
        return "Fallback role prompt template bundled with the package."
    if rel.startswith(".github/workflows/"):
        return "GitHub Actions workflow."
    if rel.startswith(".vscode/"):
        return "VS Code workspace/task configuration for local workflows."
    if rel.startswith("docs/"):
        return "Project documentation or memory file."
    if rel.startswith("handoffkit/"):
        return "Python package source."
    return "Repository file."

def python_symbols(path: Path) -> List[str]:
    try:
        tree = ast.parse(read_text(path))
    except (SyntaxError, UnicodeDecodeError):
        return []
    symbols: List[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(node.name)
    return symbols

def infer_dependencies(rel_path: Path) -> List[str]:
    rel = rel_path.as_posix()
    if rel == "handoffkit/__main__.py":
        return [
            "docs/PROJECT_CONTEXT.md",
            "docs/NOW.md",
            "docs/SESSION_NOTES.md",
            "SPEC.md",
            "docs/INVARIANTS.md",
        ]
    if rel == "scripts/check_guardrails.py":
        return [
            ".github/agents/*.agent.md",
            "handoffkit/templates/*.md",
            "docs/AGENT_SESSION_PROTOCOL.md",
        ]
    if rel.startswith("tests/"):
        return ["handoffkit/__main__.py", "scripts/check_guardrails.py"]
    return []

def app_intent(project_root: Path) -> str:
    for rel in ("SPEC.md", "docs/PROJECT_CONTEXT.md"):
        path = project_root / rel
        if not path.exists():
            continue
        raw = read_text(path)
        text = extract_summary_block(raw) or raw
        lines = [line.strip().lstrip("> ").strip(" -") for line in text.splitlines() if line.strip() and not line.startswith("#")]
        if lines:
            intent = " ".join(lines[:4])
            return truncate_text(intent, 120).replace("\n", " ")
    return "No app intent found. Update SPEC.md or docs/PROJECT_CONTEXT.md."

def build_code_index(project_root: Path, files: List[Path]) -> Dict:
    modules = []
    for rel_path in files:
        abs_path = project_root / rel_path
        entry = {
            "path": rel_path.as_posix(),
            "kind": file_kind(rel_path),
            "role": infer_file_role(rel_path),
            "size_bytes": abs_path.stat().st_size if abs_path.exists() else 0,
            "symbols": python_symbols(abs_path) if rel_path.suffix == ".py" else [],
            "depends_on": infer_dependencies(rel_path),
        }
        modules.append(entry)
    return {
        "schema_version": 1,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "generated_from_commit": git_head_sha(project_root),
        "working_tree": "dirty" if git_status_porcelain_lines(project_root) else "clean",
        "branch": current_branch(project_root),
        "source_files_scanned": [p.as_posix() for p in files],
        "modules": modules,
    }

def render_repo_map(index: Dict, *, app_intent_text: str, code_index_file: str) -> str:
    modules = index["modules"]
    entry_paths = [
        "handoffkit/__main__.py",
        "scripts/check_guardrails.py",
        "SPEC.md",
        "docs/PROJECT_CONTEXT.md",
        "docs/NOW.md",
        "docs/SESSION_NOTES.md",
    ]
    by_path = {module["path"]: module for module in modules}
    groups = [
        ("Python Package", lambda m: m["path"].startswith("handoffkit/") and m["kind"] == "python"),
        ("Docs And Memory", lambda m: m["path"].startswith("docs/") or m["path"] in {"SPEC.md", "README.md"}),
        ("Guardrails And Automation", lambda m: m["path"].startswith("scripts/") or m["path"].startswith(".github/workflows/")),
        ("Agent Prompts And Templates", lambda m: m["path"].startswith(".github/agents/") or m["path"].startswith("handoffkit/templates/")),
        ("Tests", lambda m: m["path"].startswith("tests/")),
        ("Editor And Package Config", lambda m: m["path"].startswith(".vscode/") or m["path"] == "pyproject.toml" or m["path"].endswith(".json")),
    ]

    lines = [
        "# Repo Map",
        "",
        f"Generated from commit: {index.get('generated_from_commit') or 'unknown'}",
        f"Generated at: {index.get('generated_at')}",
        f"Branch: {index.get('branch') or 'unknown'}",
        f"Working tree: {index.get('working_tree') or 'unknown'}",
        f"Source files scanned: {len(index.get('source_files_scanned', []))}",
        f"Machine-readable index: `{code_index_file}`",
        "",
        "## App Intent",
        app_intent_text,
        "",
        "## Main Entry Points",
    ]
    for path in entry_paths:
        module = by_path.get(path)
        if module:
            lines.append(f"- `{path}` - {module['role']}")

    lines.extend(["", "## Core Modules"])
    emitted = set()
    for title, predicate in groups:
        matches = [module for module in modules if predicate(module)]
        if not matches:
            continue
        lines.extend(["", f"### {title}"])
        for module in matches:
            emitted.add(module["path"])
            symbol_text = ""
            if module["symbols"]:
                symbol_text = f" Symbols: {', '.join(module['symbols'][:8])}."
            lines.append(f"- `{module['path']}` - {module['role']}{symbol_text}")

    leftovers = [module for module in modules if module["path"] not in emitted]
    if leftovers:
        lines.extend(["", "### Other"])
        for module in leftovers:
            lines.append(f"- `{module['path']}` - {module['role']}")

    lines.extend(
        [
            "",
            "## Workflows",
            "- Start session: run `handoffkit session start`, then read context docs and this repo map before source files.",
            "- End session: run `handoffkit session end`, update NOW and SESSION_NOTES, then checkpoint/commit if requested.",
            "- Prompt compile: run `handoffkit <role> <instruction>` to build a token-budgeted handoff pack.",
            "- Repo map refresh: run `handoffkit map update` after module moves, new entry points, or responsibility changes.",
            "",
            "## Files To Inspect Before Changing",
            "- Session behavior or prompt packing: `handoffkit/__main__.py`, `tests/test_session_guardrails.py`, `tests/test_required_artifacts.py`.",
            "- Guardrail wording or required markers: `scripts/check_guardrails.py`, `.github/agents/*.agent.md`, `handoffkit/templates/*.md`, `docs/AGENT_SESSION_PROTOCOL.md`.",
            "- Memory protocol: `docs/PROJECT_CONTEXT.md`, `docs/NOW.md`, `docs/SESSION_NOTES.md`, `docs/INVARIANTS.md`.",
            "- Packaging or CLI entry point: `pyproject.toml`, `handoffkit/__main__.py`.",
            "",
            "## Grounding Rule",
            "Use this map to decide where to inspect first. Source code remains authoritative for behavior.",
        ]
    )
    return "\n".join(lines).strip() + "\n"

def update_repo_map(project_root: Path, *, repo_map_file: str = DEFAULT_REPO_MAP_FILE, code_index_file: str = DEFAULT_CODE_INDEX_FILE) -> Tuple[Path, Path, int]:
    files = list_project_files(project_root)
    index = build_code_index(project_root, files)
    markdown = render_repo_map(index, app_intent_text=app_intent(project_root), code_index_file=code_index_file)

    index_path = resolve_path(code_index_file, project_root)
    map_path = resolve_path(repo_map_file, project_root)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    map_path.write_text(markdown, encoding="utf-8")
    return map_path, index_path, len(files)

def print_session_start(project_root: Path, agent_role: str, open_docs: bool) -> None:
    agent_role_slug = agent_role.lower()
    agent_role_file = f".github/agents/{agent_role_slug}.agent.md"
    repo_map_exists = (project_root / DEFAULT_REPO_MAP_FILE).exists()
    read_files = [
        "docs/PROJECT_CONTEXT.md",
        "docs/NOW.md",
    ]
    if repo_map_exists:
        read_files.append(DEFAULT_REPO_MAP_FILE)
    read_files.append("docs/SESSION_NOTES.md")

    print("Local MCP – Start Session")
    print("")
    branch = current_branch(project_root)
    if branch:
        print(f"Current Git branch: {branch}")
        print("")

    print("SESSION START")
    print("")
    print("Paste the block below into your local code agent (e.g. VS Code Code Agent).")
    print("")
    lines = [
        "SESSION START – PROJECT CONTEXT",
        "",
        "You are a local code assistant working on this project.",
        "",
        "Before doing anything:",
        "",
        "0. Assume the role described here:",
        f"   - {agent_role_file}",
        "",
        "1. Run startup checks before reading docs:",
        "   - git status --porcelain",
        "   - git diff --name-status HEAD --",
        "   - If changes exist, STOP and ask:",
        "     'Working tree has uncommitted changes in [files]. Discard, keep, or commit before we proceed?'",
        "   - Continue only when clean or explicitly acknowledged by the user.",
        "",
        "2. Read these files in this order:",
        *[f"   - {rel}" for rel in read_files],
        "",
        "   Use the repo map to decide where to inspect code first; source code remains authoritative.",
        "",
        "3. Summarise the current context in 3–6 bullet points so we both know you understood it.",
        "",
        "4. Then wait for my next instruction.",
    ]
    print("\n".join(lines))

    if open_docs:
        print("")
        if shutil.which("code"):
            print("Opening docs in VS Code...")
            files_to_open = [
                agent_role_file,
                "docs/PROJECT_CONTEXT.md",
                "docs/NOW.md",
                *([DEFAULT_REPO_MAP_FILE] if repo_map_exists else []),
                "docs/SESSION_NOTES.md",
                "docs/AGENT_SESSION_PROTOCOL.md",
            ]
            subprocess.run(["code", *files_to_open], cwd=project_root, check=False)
        else:
            print("VS Code 'code' CLI not found; open docs manually.")

def print_session_end(project_root: Path, commit_enabled: bool) -> None:
    print("Local MCP – End Session")
    print("")
    branch = current_branch(project_root)
    if branch:
        print(f"Current Git branch: {branch}")
        print("")

    print("SESSION END")
    print("")
    print("1) Copy the block below into your local code agent.")
    print("2) Let it update docs (SESSION_NOTES, NOW, summaries).")
    if commit_enabled:
        print("3) Come back here and press Enter to run writeback checkpoint + commit.")
        print("   Note: --commit requires NOW.md + SESSION_NOTES.md updates.")
    else:
        print("3) Come back here when the agent is done.")
    print("")
    lines = [
        "SESSION END – PROJECT CONTEXT",
        "",
        "You are a local code assistant working on this project.",
        "",
        "1. Read these again to refresh context:",
        "   - docs/PROJECT_CONTEXT.md",
        "   - docs/NOW.md",
        "   - docs/SESSION_NOTES.md",
        "",
        "2. Based on what we did this session (my notes below) and the current repo state,",
        "   UPDATE THESE FILES DIRECTLY in the workspace:",
        "",
        "   - docs/PROJECT_CONTEXT.md",
        "     *Only if any high-level design / tech decisions changed.*",
        "     *If it has a SUMMARY block between SUMMARY_START and SUMMARY_END, update that summary.*",
        "",
        "   - docs/NOW.md",
        "     Update to reflect the next immediate focus / short-term tasks.",
        "     Also refresh its SUMMARY block if present.",
        "",
        "   - docs/SESSION_NOTES.md",
        "     Append a new dated session entry (do not overwrite previous ones)",
        "     with:",
        "       - Participants",
        "       - Branch name",
        "       - Summary of work",
        "       - Files touched",
        "       - Decisions made",
        "",
        "3. When you are done updating the files, reply with:",
        "   - 3–6 bullet points summarising the session",
        "   - A list of the files you modified",
        "",
        "4. End-of-session checkpoint (MANDATORY):",
        "   - Update docs/NOW.md to match actual HEAD.",
        "   - Append a new entry to docs/SESSION_NOTES.md.",
        "   - Run git status and include current branch/HEAD hash in your reply.",
        "",
        "Here is my brief description of what we did this session:",
        "[WRITE 2–5 BULLET POINTS HERE BEFORE SENDING TO THE AGENT]",
    ]
    print("\n".join(lines))

def commit_session(project_root: Path, remote: str, *, stage_all: bool) -> None:
    missing = missing_writeback_files(project_root)
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            "Writeback checkpoint failed. Required files are unchanged vs working tree: "
            f"{joined}. Update those files before using --commit."
        )

    if stage_all:
        run_git(["add", "-A"], cwd=project_root)
    else:
        run_git(["add", "--", *SESSION_STAGE_FILES], cwd=project_root)

    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=project_root, capture=True).strip()
    head_before = run_git(["rev-parse", "--short", "HEAD"], cwd=project_root, capture=True).strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_message = f"Session update - {timestamp}"

    staged = run_git(["diff", "--cached", "--name-only"], cwd=project_root, capture=True).strip()
    if staged:
        run_git(["commit", "-m", commit_message], cwd=project_root)
        head_after = run_git(["rev-parse", "--short", "HEAD"], cwd=project_root, capture=True).strip()
        run_git(["push", remote, branch], cwd=project_root)
        print(f"Pushed branch '{branch}' to {remote}.")
        print(f"NOW.md updated. Writeback checkpoint passed. HEAD moved {head_before} -> {head_after}.")
    else:
        print("No staged changes to commit. Skipping commit + push.")

def parse_args(argv: Optional[List[str]] = None):
    ap = argparse.ArgumentParser(prog="handoffkit", description="Universal (LLM-agnostic) handoff prompt builder")
    subparsers = ap.add_subparsers(dest="command")

    role_parser = subparsers.add_parser("role", help="Generate a role handoff prompt")
    role_parser.add_argument("role", choices=ROLE_CHOICES, help="Role prompt to generate")
    role_parser.add_argument("instruction", help="What you want this role to do")
    role_parser.add_argument("--root", default=".", help="Path to (or inside) your project root. Can be run from anywhere.")
    role_parser.add_argument("--config", default=None, help="Path to config JSON (optional). If omitted, auto-discovered.")
    role_parser.add_argument("--selection-file", default=None, help="Path to a file containing your selected snippet (optional)")
    role_parser.add_argument("--diff", default=None, help="Path to a diff file, or '-' to read diff from stdin (optional)")
    role_parser.add_argument("--spec", default=None, help="Path to SPEC.md (optional; overrides config)")
    role_parser.add_argument("--invariants", default=None, help="Path to invariants file (optional; overrides config)")
    role_parser.add_argument("--no-spec", action="store_true", help="Do not include SPEC.md in the handoff pack")
    role_parser.add_argument("--no-invariants", action="store_true", help="Do not include invariants in the handoff pack")

    session_parser = subparsers.add_parser("session", help="Start or end a session")
    session_subparsers = session_parser.add_subparsers(dest="session_command", required=True)

    start_parser = session_subparsers.add_parser("start", help="Print the session start prompt")
    start_parser.add_argument("--root", default=".", help="Path to (or inside) your project root. Can be run from anywhere.")
    start_parser.add_argument("--agent-role", default="Coder", choices=SESSION_ROLE_CHOICES, help="Agent role to reference")
    start_parser.add_argument("--open-docs", action="store_true", help="Open memory docs in VS Code if available")
    start_parser.add_argument("--allow-dirty", action="store_true", help="Proceed even if working tree has uncommitted changes")

    end_parser = session_subparsers.add_parser("end", help="Print the session end prompt")
    end_parser.add_argument("--root", default=".", help="Path to (or inside) your project root. Can be run from anywhere.")
    end_parser.add_argument("--commit", action="store_true", help="Commit and push after the agent updates docs")
    end_parser.add_argument("--stage-all", action="store_true", help="Stage all tracked/untracked changes instead of session memory files only")
    end_parser.add_argument("--remote", default="origin", help="Git remote name to push to")

    preflight_parser = subparsers.add_parser("preflight", help="Validate memory docs and required artifacts")
    preflight_parser.add_argument("--root", default=".", help="Path to (or inside) your project root. Can be run from anywhere.")
    preflight_parser.add_argument("--config", default=None, help="Path to config JSON (optional). If omitted, auto-discovered.")

    map_parser = subparsers.add_parser("map", help="Generate or inspect repo maps")
    map_subparsers = map_parser.add_subparsers(dest="map_command", required=True)

    map_update_parser = map_subparsers.add_parser("update", help="Generate repo map and machine-readable code index")
    map_update_parser.add_argument("--root", default=".", help="Path to (or inside) your project root. Can be run from anywhere.")
    map_update_parser.add_argument("--repo-map", default=DEFAULT_REPO_MAP_FILE, help="Output path for generated Markdown repo map")
    map_update_parser.add_argument("--code-index", default=DEFAULT_CODE_INDEX_FILE, help="Output path for generated JSON code index")

    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] in ROLE_CHOICES:
        argv = ["role"] + argv
    if not argv:
        ap.print_help()
        sys.exit(2)
    return ap.parse_args(argv)

def main():
    args = parse_args()

    if args.command == "session":
        invocation_root = Path(args.root).resolve()
        project_root = find_project_root(invocation_root)
        if args.session_command == "start":
            dirty = print_startup_checks(project_root)
            if dirty and not args.allow_dirty:
                print("")
                print("STOP: Working tree has uncommitted changes.")
                print("Action required: discard, keep, or commit before proceeding.")
                print("If you explicitly want to proceed anyway, rerun with --allow-dirty.")
                sys.exit(1)
            if dirty:
                print("")
                print("Proceeding with explicit acknowledgment (--allow-dirty).")
                print("")
            print_session_start(project_root, args.agent_role, args.open_docs)
            return
        if args.session_command == "end":
            print_session_end(project_root, args.commit)
            if args.commit:
                print("")
                input("After the agent has updated the docs and you're happy with the changes, press Enter here to run checkpoint + commit")
                try:
                    commit_session(project_root, args.remote, stage_all=args.stage_all)
                except RuntimeError as e:
                    print(str(e), file=sys.stderr)
                    sys.exit(1)
            return

    if args.command == "preflight":
        invocation_root = Path(args.root).resolve()
        project_root = find_project_root(invocation_root)
        tool_root = Path(__file__).resolve().parent
        cfg = load_config(project_root, tool_root, args.config)
        sys.exit(preflight_report(project_root, cfg))

    if args.command == "map":
        invocation_root = Path(args.root).resolve()
        project_root = find_project_root(invocation_root)
        if args.map_command == "update":
            map_path, index_path, scanned = update_repo_map(
                project_root,
                repo_map_file=args.repo_map,
                code_index_file=args.code_index,
            )
            print("Repo map updated.")
            print(f"- Markdown: {map_path.as_posix()}")
            print(f"- JSON: {index_path.as_posix()}")
            print(f"- Source files scanned: {scanned}")
            return

    invocation_root = Path(args.root).resolve()

    # Tool root is where this package lives (templates/config shipped with kit).
    tool_root = Path(__file__).resolve().parent

    project_root = find_project_root(invocation_root)

    cfg = load_config(project_root, tool_root, args.config)

    try:
        selection = read_optional_input(args.selection_file, project_root=project_root, label="Selection")
        diff_text = read_optional_input(args.diff, project_root=project_root, label="Diff")
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        print("\nTip: generate a diff file with `git diff > patch.diff` and pass `--diff patch.diff`, or use `--diff -` to pipe stdin.", file=sys.stderr)
        sys.exit(2)

    spec_path = args.spec if args.spec is not None else cfg.get("spec_file", "SPEC.md")
    invariants_path = args.invariants if args.invariants is not None else cfg.get("invariants_file", "docs/INVARIANTS.md")

    auto_include_spec = bool(cfg.get("auto_include_spec", True))
    auto_include_invariants = bool(cfg.get("auto_include_invariants", True))
    require_spec = bool(cfg.get("require_spec", False))
    require_invariants = bool(cfg.get("require_invariants", False))

    if args.no_spec:
        if require_spec:
            print("SPEC.md is required by config; --no-spec is not allowed.", file=sys.stderr)
            sys.exit(2)
        auto_include_spec = False
    if args.no_invariants:
        if require_invariants:
            print("Invariants are required by config; --no-invariants is not allowed.", file=sys.stderr)
            sys.exit(2)
        auto_include_invariants = False

    try:
        spec_content = None
        spec_title = None
        if auto_include_spec:
            spec_content, spec_resolved = read_artifact_file(
                spec_path, project_root=project_root, label="SPEC.md", required=require_spec
            )
            if spec_content and spec_resolved:
                try:
                    spec_title = str(spec_resolved.relative_to(project_root))
                except ValueError:
                    spec_title = spec_resolved.as_posix()

        invariants_content = None
        invariants_title = None
        if auto_include_invariants:
            invariants_content, invariants_resolved = read_artifact_file(
                invariants_path, project_root=project_root, label="Invariants", required=require_invariants
            )
            if invariants_content and invariants_resolved:
                invariants_title = "Invariants"
    except (FileNotFoundError, RuntimeError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)

    role_prompt, agent_path = load_role_prompt(project_root, tool_root, args.role)

    pack = build_context_pack(
        project_root,
        cfg,
        args.instruction,
        selection,
        diff_text,
        role_name=args.role,
        role_agent_path=agent_path,
        spec_content=spec_content,
        spec_title=spec_title,
        invariants_content=invariants_content,
        invariants_title=invariants_title,
    )

    print(role_prompt + "\n\n" + pack)

if __name__ == "__main__":
    main()

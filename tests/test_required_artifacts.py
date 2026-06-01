import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import handoffkit.__main__ as handoff


class RequiredArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._write_project()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_project(self) -> None:
        docs = self.root / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "PROJECT_CONTEXT.md").write_text("# Project\n", encoding="utf-8")
        (docs / "NOW.md").write_text("# Now\n", encoding="utf-8")
        (docs / "SESSION_NOTES.md").write_text("# Notes\n", encoding="utf-8")
        (docs / "AGENT_SESSION_PROTOCOL.md").write_text("# Protocol\n", encoding="utf-8")
        (docs / "INVARIANTS.md").write_text("# Invariants\nKeep it local.\n", encoding="utf-8")
        (self.root / "SPEC.md").write_text("# Spec\nBuild the kit.\n", encoding="utf-8")
        (self.root / "handoffkit.config.json").write_text(
            """{
  "token_budget": 7000,
  "baseline_files": ["docs/PROJECT_CONTEXT.md", "docs/NOW.md"],
  "session_notes_file": "docs/SESSION_NOTES.md",
  "protocol_file": "docs/AGENT_SESSION_PROTOCOL.md",
  "spec_file": "SPEC.md",
  "invariants_file": "docs/INVARIANTS.md",
  "require_spec": true,
  "require_invariants": true,
  "auto_include_spec": true,
  "auto_include_invariants": true
}
""",
            encoding="utf-8",
        )

    def _run_role(self, *extra_args: str) -> subprocess.CompletedProcess:
        repo_root = Path(__file__).resolve().parents[1]
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "handoffkit",
                "coder",
                "Continue the sprint",
                "--root",
                str(self.root),
                *extra_args,
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_preflight_fails_when_required_spec_is_missing(self) -> None:
        (self.root / "SPEC.md").unlink()
        cfg = handoff.load_config(self.root, Path(handoff.__file__).resolve().parent, None)

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = handoff.preflight_report(self.root, cfg)

        self.assertEqual(rc, 1)
        self.assertIn("MISSING: SPEC.md", buf.getvalue())

    def test_preflight_passes_when_required_artifacts_exist(self) -> None:
        cfg = handoff.load_config(self.root, Path(handoff.__file__).resolve().parent, None)

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = handoff.preflight_report(self.root, cfg)

        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("OK: SPEC.md", out)
        self.assertIn("OK: Invariants", out)
        self.assertIn("Preflight OK.", out)

    def test_role_pack_includes_required_spec_and_invariants(self) -> None:
        proc = self._run_role()

        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertIn("## SPEC.md", proc.stdout)
        self.assertIn("# Spec", proc.stdout)
        self.assertIn("## Invariants", proc.stdout)
        self.assertIn("Keep it local.", proc.stdout)

    def test_role_pack_rejects_no_spec_when_spec_is_required(self) -> None:
        proc = self._run_role("--no-spec")

        self.assertEqual(proc.returncode, 2)
        self.assertIn("SPEC.md is required by config", proc.stderr)

    def test_role_pack_fails_when_required_invariants_are_missing(self) -> None:
        (self.root / "docs" / "INVARIANTS.md").unlink()

        proc = self._run_role()

        self.assertEqual(proc.returncode, 2)
        self.assertIn("Invariants file not found", proc.stderr)


if __name__ == "__main__":
    unittest.main()

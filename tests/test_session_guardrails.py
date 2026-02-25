import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import handoffkit.__main__ as handoff


class SessionGuardrailTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._init_repo(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _run_git(self, *args: str) -> str:
        proc = subprocess.run(
            ["git", *args],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            self.fail(f"git {' '.join(args)} failed: {proc.stderr or proc.stdout}")
        return proc.stdout

    def _init_repo(self, root: Path) -> None:
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "PROJECT_CONTEXT.md").write_text("# PROJECT\n", encoding="utf-8")
        (root / "docs" / "NOW.md").write_text("# NOW\n", encoding="utf-8")
        (root / "docs" / "SESSION_NOTES.md").write_text("# NOTES\n", encoding="utf-8")

        self._run_git("init")
        self._run_git("config", "user.email", "tests@example.com")
        self._run_git("config", "user.name", "Test User")
        self._run_git("add", "-A")
        self._run_git("commit", "-m", "init")

    def test_print_startup_checks_detects_dirty_tree(self) -> None:
        (self.root / "docs" / "NOW.md").write_text("# NOW\nchanged\n", encoding="utf-8")

        buf = io.StringIO()
        with redirect_stdout(buf):
            dirty = handoff.print_startup_checks(self.root)

        self.assertTrue(dirty)
        self.assertIn("uncommitted changes detected", buf.getvalue())

    def test_missing_writeback_files_reports_required_files(self) -> None:
        missing = handoff.missing_writeback_files(self.root)
        self.assertEqual(sorted(missing), sorted(handoff.SESSION_REQUIRED_WRITEBACK_FILES))

    def test_missing_writeback_files_clears_after_updates(self) -> None:
        (self.root / "docs" / "NOW.md").write_text("# NOW\nupdated\n", encoding="utf-8")
        (self.root / "docs" / "SESSION_NOTES.md").write_text("# NOTES\nnew entry\n", encoding="utf-8")

        missing = handoff.missing_writeback_files(self.root)
        self.assertEqual(missing, [])


class SessionStartCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._init_repo(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _run_git(self, *args: str) -> None:
        proc = subprocess.run(
            ["git", *args],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            self.fail(f"git {' '.join(args)} failed: {proc.stderr or proc.stdout}")

    def _init_repo(self, root: Path) -> None:
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "PROJECT_CONTEXT.md").write_text("# PROJECT\n", encoding="utf-8")
        (root / "docs" / "NOW.md").write_text("# NOW\n", encoding="utf-8")
        (root / "docs" / "SESSION_NOTES.md").write_text("# NOTES\n", encoding="utf-8")

        self._run_git("init")
        self._run_git("config", "user.email", "tests@example.com")
        self._run_git("config", "user.name", "Test User")
        self._run_git("add", "-A")
        self._run_git("commit", "-m", "init")

    def _run_session_start(self, *extra_args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "handoffkit",
                "session",
                "start",
                "--root",
                str(self.root),
                "--agent-role",
                "Coder",
                *extra_args,
            ],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_session_start_blocks_dirty_tree(self) -> None:
        (self.root / "docs" / "NOW.md").write_text("# NOW\nchanged\n", encoding="utf-8")

        proc = self._run_session_start()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("STOP: Working tree has uncommitted changes", proc.stdout)

    def test_session_start_allow_dirty_acknowledges(self) -> None:
        (self.root / "docs" / "NOW.md").write_text("# NOW\nchanged\n", encoding="utf-8")

        proc = self._run_session_start("--allow-dirty")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Proceeding with explicit acknowledgment", proc.stdout)


if __name__ == "__main__":
    unittest.main()

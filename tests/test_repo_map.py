import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import handoffkit.__main__ as handoff


class RepoMapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._write_project()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_project(self) -> None:
        docs = self.root / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "PROJECT_CONTEXT.md").write_text("# Project\nLocal context kit.\n", encoding="utf-8")
        (docs / "NOW.md").write_text("# Now\nBuild map support.\n", encoding="utf-8")
        (docs / "SESSION_NOTES.md").write_text("# Notes\n", encoding="utf-8")
        (docs / "AGENT_SESSION_PROTOCOL.md").write_text("# Protocol\n", encoding="utf-8")
        (docs / "INVARIANTS.md").write_text("# Invariants\nSource code remains authoritative.\n", encoding="utf-8")
        (self.root / "SPEC.md").write_text("# Spec\nMap the repo before scanning source.\n", encoding="utf-8")
        package = self.root / "demo"
        package.mkdir()
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "app.py").write_text(
            "class Runner:\n"
            "    pass\n\n"
            "def main():\n"
            "    return Runner()\n",
            encoding="utf-8",
        )

    def test_update_repo_map_writes_markdown_and_json_index(self) -> None:
        map_path, index_path, scanned = handoff.update_repo_map(self.root)

        self.assertGreater(scanned, 0)
        self.assertTrue(map_path.exists())
        self.assertTrue(index_path.exists())

        markdown = map_path.read_text(encoding="utf-8")
        self.assertIn("# Repo Map", markdown)
        self.assertIn("## App Intent", markdown)
        self.assertIn("## Grounding Rule", markdown)
        self.assertIn("Source code remains authoritative", markdown)

        index = json.loads(index_path.read_text(encoding="utf-8"))
        self.assertIn(index["working_tree"], {"clean", "dirty"})
        module = next(item for item in index["modules"] if item["path"] == "demo/app.py")
        self.assertEqual(module["kind"], "python")
        self.assertEqual(module["symbols"], ["Runner", "main"])
        self.assertIn("demo/app.py", index["source_files_scanned"])

    def test_map_update_cli_reports_outputs(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        proc = subprocess.run(
            [sys.executable, "-m", "handoffkit", "map", "update", "--root", str(self.root)],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertIn("Repo map updated.", proc.stdout)
        self.assertTrue((self.root / handoff.DEFAULT_REPO_MAP_FILE).exists())
        self.assertTrue((self.root / handoff.DEFAULT_CODE_INDEX_FILE).exists())

    def test_session_start_reads_repo_map_when_present(self) -> None:
        handoff.update_repo_map(self.root)

        buf = io.StringIO()
        with redirect_stdout(buf):
            handoff.print_session_start(self.root, "Coder", open_docs=False)

        out = buf.getvalue()
        self.assertIn("docs/PROJECT_CONTEXT.md", out)
        self.assertIn("docs/NOW.md", out)
        self.assertIn(handoff.DEFAULT_REPO_MAP_FILE, out)
        self.assertIn("Use the repo map to decide where to inspect code first", out)


if __name__ == "__main__":
    unittest.main()

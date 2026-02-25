import subprocess
import sys
import unittest
from pathlib import Path


class GuardrailScriptTests(unittest.TestCase):
    def test_guardrail_script_passes(self) -> None:
        root = Path(__file__).resolve().parents[1]
        proc = subprocess.run(
            [sys.executable, "scripts/check_guardrails.py"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertIn("Guardrail checks passed.", proc.stdout)


if __name__ == "__main__":
    unittest.main()

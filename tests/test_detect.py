"""Characterization: scripts/detect.sh prints the installed-CLI variant."""
import unittest

from tests.util import SCRIPTS, run_script, stub_env, temp_dir


class DetectVariant(unittest.TestCase):
    def detect(self, tools):
        tmp = temp_dir(self)
        r = run_script(SCRIPTS / "detect.sh", stub_env(tmp, tools))
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def test_both_clis(self):
        self.assertEqual(self.detect(["claude", "codex"]), "claude-codex")

    def test_claude_only(self):
        self.assertEqual(self.detect(["claude"]), "claude")

    def test_codex_only(self):
        self.assertEqual(self.detect(["codex"]), "codex")

    def test_none(self):
        self.assertEqual(self.detect([]), "none")


if __name__ == "__main__":
    unittest.main()

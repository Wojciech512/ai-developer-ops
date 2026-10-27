"""Characterization: Claude hook scripts' stdin/exit-code contract.

Exit 2 blocks the tool call / turn; exit 0 lets it through.
"""
import json
import subprocess
import unittest

from tests.util import SCRIPTS, git_repo, run_script, stub_env, temp_dir


def tool_input(path):
    return json.dumps({"tool_input": {"file_path": path}})


def commit_all(repo, env):
    subprocess.run(["git", "add", "-A"], cwd=repo, env=env, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@test", "-c", "user.name=t",
         "commit", "-qm", "init"],
        cwd=repo, env=env, check=True,
    )


class ProtectPaths(unittest.TestCase):
    def run_hook(self, stdin, extra_env=None):
        tmp = temp_dir(self)
        env = stub_env(tmp)
        env.update(extra_env or {})
        return run_script(SCRIPTS / "protect-paths.sh", env, stdin=stdin)

    def test_blocks_dotenv(self):
        r = self.run_hook(tool_input(".env"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("Blocked", r.stderr)

    def test_blocks_ci_workflows(self):
        r = self.run_hook(tool_input(".github/workflows/ci.yml"))
        self.assertEqual(r.returncode, 2)

    def test_blocks_lockfiles(self):
        r = self.run_hook(tool_input("package-lock.json"))
        self.assertEqual(r.returncode, 2)

    def test_allows_normal_file(self):
        r = self.run_hook(tool_input("src/app.py"))
        self.assertEqual(r.returncode, 0)

    def test_override_env_allows_protected(self):
        r = self.run_hook(tool_input(".env"), {"AIDEVOPS_ALLOW_PROTECTED": "1"})
        self.assertEqual(r.returncode, 0)

    def test_empty_input_allows(self):
        r = self.run_hook("{}")
        self.assertEqual(r.returncode, 0)


class FormatFile(unittest.TestCase):
    def test_never_blocks_without_makefile(self):
        tmp = temp_dir(self)
        env = stub_env(tmp)
        r = run_script(
            SCRIPTS / "format-file.sh", env, cwd=tmp, stdin=tool_input("x.sh")
        )
        self.assertEqual(r.returncode, 0)

    def test_never_blocks_on_malformed_stdin(self):
        tmp = temp_dir(self)
        env = stub_env(tmp)
        r = run_script(SCRIPTS / "format-file.sh", env, cwd=tmp, stdin="not json")
        self.assertEqual(r.returncode, 0)


class StopGate(unittest.TestCase):
    def gate(self, cwd, env, stdin="{}"):
        return run_script(SCRIPTS / "stop-gate.sh", env, cwd=cwd, stdin=stdin)

    def repo_with(self, makefile=None, dirty=True):
        tmp = temp_dir(self)
        env = stub_env(tmp)
        repo = git_repo(tmp, env)
        if makefile is not None:
            (repo / "Makefile").write_text(makefile)
            if not dirty:
                commit_all(repo, env)
        if dirty:
            (repo / "wip.txt").write_text("wip\n")
        return repo, env

    def test_noop_when_stop_hook_active(self):
        repo, env = self.repo_with(makefile="check:\n\t@exit 1\n")
        r = self.gate(repo, env, stdin=json.dumps({"stop_hook_active": True}))
        self.assertEqual(r.returncode, 0)

    def test_noop_without_check_target(self):
        repo, env = self.repo_with()
        self.assertEqual(self.gate(repo, env).returncode, 0)

    def test_noop_on_clean_tree(self):
        repo, env = self.repo_with(makefile="check:\n\t@exit 1\n", dirty=False)
        self.assertEqual(self.gate(repo, env).returncode, 0)

    def test_passes_when_check_green(self):
        repo, env = self.repo_with(makefile="check:\n\t@true\n")
        self.assertEqual(self.gate(repo, env).returncode, 0)

    def test_blocks_when_check_fails(self):
        repo, env = self.repo_with(makefile="check:\n\t@exit 1\n")
        r = self.gate(repo, env)
        self.assertEqual(r.returncode, 2)
        self.assertIn("make check FAILED", r.stderr)


if __name__ == "__main__":
    unittest.main()

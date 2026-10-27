"""Characterization: scripts/init.sh scaffolds a project idempotently."""
import subprocess
import unittest

from tests.util import SCRIPTS, git_repo, run_script, stub_env, temp_dir

GITHUB = "https://github.com/example/demo.git"
GITLAB = "https://gitlab.com/example/demo.git"


class InitScaffold(unittest.TestCase):
    def setup_repo(self, tools=("claude", "codex"), remote=GITHUB):
        tmp = temp_dir(self)
        env = stub_env(tmp, tools)
        repo = git_repo(tmp, env, remote=remote)
        return repo, env

    def init(self, repo, env):
        return run_script(SCRIPTS / "init.sh", env, cwd=repo)

    def test_refuses_outside_git_repo(self):
        tmp = temp_dir(self)
        env = stub_env(tmp, ["claude", "codex"])
        bare = tmp / "not-a-repo"
        bare.mkdir()
        r = run_script(SCRIPTS / "init.sh", env, cwd=bare)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Run inside a git repository.", r.stdout + r.stderr)

    def test_scaffolds_github_claude_codex(self):
        repo, env = self.setup_repo()
        r = self.init(repo, env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("INIT_DONE variant=claude-codex host=github", r.stdout)
        for path in [
            "AGENTS.md",
            "Makefile",
            ".githooks/pre-push",
            ".github/pull_request_template.md",
            ".github/workflows/ai-check.yml",
            ".claude/settings.json",
            ".codex/config.toml",
            ".codex/agents/worker.toml",
            ".aidevops/templates/handoff.md",
            ".aidevops/templates/evidence.md",
            "docs/adr",
        ]:
            self.assertTrue((repo / path).exists(), f"missing {path}")
        self.assertEqual((repo / ".aidevops/variant").read_text().strip(), "claude-codex")
        self.assertEqual((repo / ".aidevops/host").read_text().strip(), "github")
        self.assertIn(".aidevops/", (repo / ".gitignore").read_text())
        hook = repo / ".githooks/pre-push"
        self.assertTrue(hook.stat().st_mode & 0o111, "pre-push not executable")
        hooks_path = subprocess.run(
            ["git", "config", "core.hooksPath"],
            cwd=repo, env=env, capture_output=True, text=True,
        ).stdout.strip()
        self.assertEqual(hooks_path, ".githooks")

    def test_rerun_keeps_user_files(self):
        repo, env = self.setup_repo()
        self.assertEqual(self.init(repo, env).returncode, 0)
        (repo / "AGENTS.md").write_text("user content\n")
        r = self.init(repo, env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("kept    AGENTS.md", r.stdout)
        self.assertNotIn("created AGENTS.md", r.stdout)
        self.assertEqual((repo / "AGENTS.md").read_text(), "user content\n")
        gitignore = (repo / ".gitignore").read_text()
        self.assertEqual(gitignore.count(".aidevops/"), 1, "gitignore entry duplicated")

    def test_rerun_refreshes_handoff_and_evidence(self):
        repo, env = self.setup_repo()
        self.assertEqual(self.init(repo, env).returncode, 0)
        handoff = repo / ".aidevops/templates/handoff.md"
        handoff.write_text("stale\n")
        self.assertEqual(self.init(repo, env).returncode, 0)
        self.assertNotEqual(handoff.read_text(), "stale\n")

    def test_gitlab_host_gets_gitlab_files(self):
        repo, env = self.setup_repo(remote=GITLAB)
        r = self.init(repo, env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("INIT_DONE variant=claude-codex host=gitlab", r.stdout)
        self.assertTrue((repo / ".gitlab-ci.yml").exists())
        self.assertTrue((repo / ".gitlab/merge_request_templates/Default.md").exists())
        self.assertFalse((repo / ".github").exists())

    def test_claude_only_skips_codex_files(self):
        repo, env = self.setup_repo(tools=("claude",))
        r = self.init(repo, env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("variant=claude ", r.stdout)
        self.assertTrue((repo / ".claude/settings.json").exists())
        self.assertFalse((repo / ".codex").exists())


if __name__ == "__main__":
    unittest.main()

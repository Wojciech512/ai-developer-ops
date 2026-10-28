"""Characterization: Claude hook scripts' stdin/exit-code contract.

Exit 2 blocks the tool call / turn; exit 0 lets it through.
"""
import json
import subprocess
import unittest

from tests.util import SCRIPTS, git_repo, run_script, stub_env, temp_dir


def tool_input(path):
    return json.dumps({"tool_input": {"file_path": path}})


def command_input(cmd):
    return json.dumps({"tool_input": {"command": cmd}})


def no_jq_env(tmp):
    """stub_env with jq hidden from PATH (jq lives in /usr/bin on this box)."""
    env = stub_env(tmp)
    kept = [p for p in env["PATH"].split(":") if p != "/usr/bin"]
    env["PATH"] = ":".join(kept)
    return env


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

    def test_blocks_deny_push_script(self):
        r = self.run_hook(tool_input("scripts/deny-push.sh"))
        self.assertEqual(r.returncode, 2)

    def test_blocks_hooks_json(self):
        r = self.run_hook(tool_input("hooks/hooks.json"))
        self.assertEqual(r.returncode, 2)

    def test_blocks_claude_settings(self):
        r = self.run_hook(tool_input(".claude/settings.json"))
        self.assertEqual(r.returncode, 2)

    def test_blocks_templates_settings(self):
        r = self.run_hook(tool_input("templates/settings.json"))
        self.assertEqual(r.returncode, 2)

    def test_override_env_allows_deny_push_script(self):
        r = self.run_hook(
            tool_input("scripts/deny-push.sh"), {"AIDEVOPS_ALLOW_PROTECTED": "1"}
        )
        self.assertEqual(r.returncode, 0)

    def test_override_env_allows_hooks_json(self):
        r = self.run_hook(
            tool_input("hooks/hooks.json"), {"AIDEVOPS_ALLOW_PROTECTED": "1"}
        )
        self.assertEqual(r.returncode, 0)

    def test_override_env_allows_claude_settings(self):
        r = self.run_hook(
            tool_input(".claude/settings.json"), {"AIDEVOPS_ALLOW_PROTECTED": "1"}
        )
        self.assertEqual(r.returncode, 0)

    def test_override_env_allows_templates_settings(self):
        r = self.run_hook(
            tool_input("templates/settings.json"), {"AIDEVOPS_ALLOW_PROTECTED": "1"}
        )
        self.assertEqual(r.returncode, 0)


class DenyPush(unittest.TestCase):
    def run_hook(self, stdin, env=None):
        tmp = temp_dir(self)
        env = env or stub_env(tmp)
        return run_script(SCRIPTS / "deny-push.sh", env, stdin=stdin)

    # --- blocking: moves code to a remote ---

    def test_blocks_git_push(self):
        r = self.run_hook(command_input("git push"))
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr)

    def test_blocks_git_push_origin_head(self):
        r = self.run_hook(command_input("git push origin HEAD:main"))
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr)

    def test_blocks_git_push_url(self):
        r = self.run_hook(
            command_input("git push https://github.com/x/y.git HEAD:main")
        )
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr)

    def test_blocks_git_push_upstream(self):
        r = self.run_hook(command_input("git push upstream main"))
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr)

    def test_blocks_git_dash_c_push(self):
        r = self.run_hook(command_input("git -C /tmp/x push"))
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr)

    def test_blocks_chained_make_check_and_push(self):
        r = self.run_hook(command_input("make check && git push"))
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr)

    def test_blocks_chained_status_semicolon_push(self):
        r = self.run_hook(command_input("git status; git push"))
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr)

    def test_blocks_gh_pr_create(self):
        r = self.run_hook(command_input("gh pr create"))
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr)

    def test_blocks_gh_pr_merge(self):
        r = self.run_hook(command_input("gh pr merge"))
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr)

    def test_blocks_gh_release_create(self):
        r = self.run_hook(command_input("gh release create"))
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr)

    def test_blocks_glab_mr_create(self):
        r = self.run_hook(command_input("glab mr create"))
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr)

    def test_blocks_glab_mr_merge(self):
        r = self.run_hook(command_input("glab mr merge"))
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr)

    def test_blocks_gh_api_post_write(self):
        r = self.run_hook(
            command_input("gh api --method POST /repos/o/r/git/refs")
        )
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr)

    def test_blocks_gh_api_delete(self):
        r = self.run_hook(command_input("gh api -X DELETE /repos/o/r"))
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr)

    def test_block_message_mentions_local_commit_and_human(self):
        r = self.run_hook(command_input("git push"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("commit", r.stderr.lower())
        self.assertIn("human", r.stderr.lower())

    # --- passing: local-only or non-write ---

    def test_allows_git_commit(self):
        r = self.run_hook(command_input("git commit -m x"))
        self.assertEqual(r.returncode, 0)

    def test_allows_git_commit_message_mentions_push(self):
        r = self.run_hook(command_input('git commit -m "Dokumentuje git push"'))
        self.assertEqual(r.returncode, 0)

    def test_allows_printf_quoted_push(self):
        r = self.run_hook(command_input("printf '%s' 'git push origin x'"))
        self.assertEqual(r.returncode, 0)

    def test_allows_git_status(self):
        r = self.run_hook(command_input("git status"))
        self.assertEqual(r.returncode, 0)

    def test_allows_git_fetch(self):
        r = self.run_hook(command_input("git fetch"))
        self.assertEqual(r.returncode, 0)

    def test_allows_git_log_grep_push(self):
        r = self.run_hook(command_input("git log --grep=push"))
        self.assertEqual(r.returncode, 0)

    def test_allows_make_check(self):
        r = self.run_hook(command_input("make check"))
        self.assertEqual(r.returncode, 0)

    def test_allows_gh_pr_view(self):
        r = self.run_hook(command_input("gh pr view 1"))
        self.assertEqual(r.returncode, 0)

    def test_allows_gh_pr_list(self):
        r = self.run_hook(command_input("gh pr list"))
        self.assertEqual(r.returncode, 0)

    def test_allows_gh_api_post_markdown(self):
        r = self.run_hook(command_input("gh api --method POST /markdown"))
        self.assertEqual(r.returncode, 0)

    def test_allows_gh_api_get(self):
        r = self.run_hook(command_input("gh api /repos/o/r"))
        self.assertEqual(r.returncode, 0)

    def test_allows_empty_input(self):
        r = self.run_hook("{}")
        self.assertEqual(r.returncode, 0)

    # --- cannot-evaluate contract ---

    def test_blocks_when_no_jq_and_risky(self):
        tmp = temp_dir(self)
        env = no_jq_env(tmp)
        r = self.run_hook(command_input("git push"), env=env)
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr)

    def test_allows_when_no_jq_and_mundane(self):
        tmp = temp_dir(self)
        env = no_jq_env(tmp)
        r = self.run_hook(command_input("make check"), env=env)
        self.assertEqual(r.returncode, 0)

    def test_unparsable_json_without_indicator_allows(self):
        r = self.run_hook("not json")
        self.assertEqual(r.returncode, 0)

    def test_null_command_allows(self):
        r = self.run_hook('{"tool_input":{"command":null}}')
        self.assertEqual(r.returncode, 0)

    def test_non_string_command_allows(self):
        r = self.run_hook('{"tool_input":{"command":123}}')
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


class HookRegistration(unittest.TestCase):
    """The gate is only a gate while it stays wired up.

    `make check` runs `jq empty` on hooks.json, which passes just as happily
    with the deny-push entry deleted. These assert the wiring itself.
    """

    def setUp(self):
        self.hooks = json.loads((SCRIPTS.parent / "hooks" / "hooks.json").read_text())

    def pre_tool_use(self):
        return self.hooks["hooks"]["PreToolUse"]

    def test_deny_push_registered_for_bash(self):
        entries = [e for e in self.pre_tool_use() if e.get("matcher") == "Bash"]
        self.assertEqual(len(entries), 1, "expected exactly one Bash PreToolUse entry")
        commands = [h["command"] for h in entries[0]["hooks"]]
        self.assertTrue(
            any("deny-push.sh" in c for c in commands),
            "Bash PreToolUse entry must invoke deny-push.sh; found %r" % (commands,),
        )

    def test_protect_paths_still_registered(self):
        commands = [
            h["command"]
            for e in self.pre_tool_use()
            for h in e["hooks"]
            if "Edit" in (e.get("matcher") or "")
        ]
        self.assertTrue(any("protect-paths.sh" in c for c in commands))

    def test_registered_hook_scripts_exist_and_are_readable(self):
        for entry in self.pre_tool_use():
            for hook in entry["hooks"]:
                name = hook["command"].rsplit("/", 1)[-1].rstrip('"')
                self.assertTrue(
                    (SCRIPTS / name).is_file(),
                    "hooks.json references scripts/%s which does not exist" % name,
                )


if __name__ == "__main__":
    unittest.main()

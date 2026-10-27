"""Shared helpers: run repo scripts in an isolated environment.

PATH is narrowed to a stub dir + /usr/bin:/bin so the detected variant
(claude/codex on PATH) and optional tools (playwright-cli) are fully
controlled by the test, on macOS and ubuntu runners alike.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"


def stub_env(tmp: Path, tools=()):
    stub = tmp / "stub-bin"
    stub.mkdir(exist_ok=True)
    for tool in tools:
        p = stub / tool
        p.write_text("#!/bin/sh\nexit 0\n")
        p.chmod(0o755)
    return {
        "PATH": f"{stub}:/usr/bin:/bin",
        "HOME": str(tmp),
        "GIT_CONFIG_NOSYSTEM": "1",
    }


def temp_dir(testcase):
    tmp = Path(tempfile.mkdtemp(prefix="aidevops-test-"))
    testcase.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
    return tmp


def run_script(script, env, cwd=None, stdin=None):
    return subprocess.run(
        ["bash", str(script)],
        env=env,
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
    )


def git_repo(tmp: Path, env, remote=None):
    repo = tmp / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, env=env, check=True)
    if remote:
        subprocess.run(
            ["git", "remote", "add", "origin", remote],
            cwd=repo, env=env, check=True,
        )
    return repo

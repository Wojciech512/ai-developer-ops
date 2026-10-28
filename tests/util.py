"""Shared helpers: run repo scripts in an isolated environment.

PATH is narrowed to a stub dir + /usr/bin:/bin so the detected variant
(claude/codex on PATH) and optional tools (playwright-cli) are fully
controlled by the test, on macOS and ubuntu runners alike.
"""
import json
import os
import shutil
import subprocess
import sys
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


RENDER_ARCH = SCRIPTS / "render_arch.py"


def run_py(args, cwd=None, env=None):
    """Run scripts/render_arch.py with this interpreter."""
    return subprocess.run(
        [sys.executable, str(RENDER_ARCH), *[str(a) for a in args]],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


def env_without_git():
    """A copy of the environment with git's repo pointers removed.

    Git hooks export GIT_DIR, so a subprocess started from a hook finds the
    repository even when its cwd is outside one. A test that needs
    `git rev-parse` to fail has to strip those, or it passes from the shell
    and fails under `git push`.
    """
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def model_fixture(**overrides):
    """Minimal valid model from design.md, with top-level keys overridable."""
    model = {
        "title": "fixture",
        "components": [
            {"id": "Developer", "label": "developer",
             "layer": "actor", "path": None},
            {"id": "Installer", "label": "install.sh",
             "layer": "api", "path": "scripts/install.sh"},
        ],
        "flows": [
            {"id": "main", "label": "Instalacja", "kind": "main"},
        ],
        "interactions": [
            {"flow": "main", "from": "Developer", "to": "Installer",
             "verb": "uruchamia", "op": "install.sh", "seq": 10},
        ],
    }
    model.update(overrides)
    return model


def fixture_root(tmp: Path, model):
    """Create an empty file for every non-null component path in model.

    Proves the renderer needs the paths to exist but never reads them.
    """
    root = tmp / "root"
    root.mkdir(exist_ok=True)
    for component in model.get("components", []):
        path = component.get("path")
        if not path:
            continue
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
    return root


def write_model(tmp: Path, model, name="architecture.model.json"):
    """Write model as JSON under tmp and return its path."""
    path = tmp / name
    path.write_text(json.dumps(model, ensure_ascii=False, indent=2))
    return path


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

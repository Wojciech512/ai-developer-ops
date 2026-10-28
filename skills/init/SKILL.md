---
name: init
description: Initialize a repository for the ai-developer-ops process in one run. Use once per repository, right after cloning.
disable-model-invocation: true
---
ROOT = $CLAUDE_PLUGIN_ROOT if set, otherwise ~/.ai-developer-ops.
1. Run `bash "$ROOT/scripts/init.sh"`. Read its output. Stop and report if it fails.
2. If `openspec/` does not exist: run `openspec init` for the tools listed in .aidevops/variant (claude = Claude Code, codex = Codex, claude-codex = both). Then set the expanded profile (`openspec config profile`), run `openspec update` and `openspec validate`. If a subcommand is unknown, read `openspec --help` first.
3. Recon: run ops-discover --onboarding. It writes docs/architecture.model.json, docs/architecture.puml, docs/ARCHITECTURE.md, docs/architecture.svg and docs/ONBOARDING.md, and reports the stack and the detected build/test/lint/run commands.
4. Fill every TODO using the commands from the ops-discover report: Makefile targets (lint, typecheck, test, fmt-file, e2e), AGENTS.md (single-test command, conventions max 20 lines), toolchain step in the CI file. Keep AGENTS.md under 60 lines.
5. Run `make check`. If the repo has no tests, first write characterization tests for the 3 most critical paths, then rerun.
6. Gate test: break one assertion, run `bash .githooks/pre-push` and confirm it fails, restore it, confirm it passes.
7. Report: files created vs kept; what needs a human: enable Claude Code Review on the GitHub repo, enable `@codex review` in Codex settings, CI secrets, trust the project so `.codex/config.toml` loads. If step 1 reported `kept    Makefile`, the project's own Makefile has no `docs` or `docs-fresh` target and `cp_if_absent` will never add one - print both recipes from `"$ROOT/templates/Makefile"` for the user to paste, and say that `make check` will not guard the diagram until they do. Commit `chore: ai-developer-ops init`.

---
name: init-ai-developer-ops
description: Initialize a repository for the ai-developer-ops process in one run. Use once per repository, right after cloning.
disable-model-invocation: true
---
ROOT = $CLAUDE_PLUGIN_ROOT if set, otherwise ~/.ai-developer-ops.
1. Run `bash "$ROOT/scripts/init.sh"`. Read its output. Stop and report if it fails.
2. If `openspec/` does not exist: run `openspec init` for the tools listed in .aidevops/variant (claude = Claude Code, codex = Codex, claude-codex = both). Then set the expanded profile (`openspec config profile`), run `openspec update` and `openspec validate`. If a subcommand is unknown, read `openspec --help` first.
3. Recon in a read-only subagent (Claude: Explore; Codex: explorer): stack, build/test/lint/run commands, architecture, CI, state of tests. Write docs/ARCHITECTURE.md, max 2 pages.
4. Fill every TODO: Makefile targets (lint, typecheck, test, fmt-file, e2e), AGENTS.md (single-test command, conventions max 20 lines), toolchain step in the CI file. Keep AGENTS.md under 60 lines.
5. Run `make check`. If the repo has no tests, first write characterization tests for the 3 most critical paths, then rerun.
6. Gate test: break one assertion, run `bash .githooks/pre-push` and confirm it fails, restore it, confirm it passes.
7. Report: files created vs kept; what needs a human: enable Claude Code Review on the GitHub repo, enable `@codex review` in Codex settings, CI secrets, trust the project so `.codex/config.toml` loads. Commit `chore: ai-developer-ops init`.

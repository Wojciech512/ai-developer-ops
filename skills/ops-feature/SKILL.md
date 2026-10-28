---
name: ops-feature
description: Full feature lifecycle on top of OpenSpec and Superpowers - propose, critique, plan approval, implement task by task, review, ship. Use for any change bigger than one sentence.
disable-model-invocation: true
argument-hint: <change-id> "<goal>"
---
Three human gates: proposal, plan, merge. Stop at each one and wait.
1. Propose: `/opsx:explore` when the shape is unclear, then `/opsx:propose <change-id>`. Copy .aidevops/templates/handoff.md and evidence.md into openspec/changes/<id>/. STOP: the user approves proposal and specs.
2. Critique: run ops-critique for <id>. Apply approved edits to proposal, design, specs, tasks. Record important decisions in docs/adr/.
3. Plan: make sure tasks.md has small tasks with exact files, an acceptance criterion and a test command. One task fits one fresh context. STOP: the user approves tasks.md. Set handoff.md owner and status=implementing. Start a fresh session for implementation.
4. Implement in a git worktree for this change. Claude: superpowers:using-git-worktrees, then superpowers:subagent-driven-development with tasks.md as the plan (never create a second plan); TDD inside each task. Codex: `$openspec-apply` with the worker agent, one task per thread. After each task `make check` must be green. For any third-party API, the implementer asks docs-researcher first (Codex: docs_researcher).
5. Verify: `make e2e`; use playwright-cli for the verification steps in the spec; record results in evidence.md.
6. Review: run ops-review for <id>. The owner fixes every BLOCKER and WARN, then reruns until PASS.
7. Ship: run ops-ship for <id>. STOP: the user merges.
8. After merge: `/opsx:archive <id>`. Then refresh the architecture from the scope ops-ship recorded: read `openspec/changes/archive/<id>/scope.txt` and run ops-discover --refresh --scope with those paths. Empty or missing file: skip the refresh and say so - do not rediscover the whole repo. Then `make docs`, and commit the changed documents as `docs(architecture): refresh after <id>`; if the default branch is protected, push `docs/refresh-<id>` and open a PR/MR from the template. This step is not done until the working tree is clean. Finally add one lesson to AGENTS.md if there is one.

---
name: ops-ship
description: Commit, push, open a PR (GitHub) or MR (GitLab) from the template with evidence, and request bot reviews. Never merges.
disable-model-invocation: true
argument-hint: <change-id>
---
Preconditions: `make check` green; evidence.md has review A and review B with zero BLOCKER; spec stage PASS. If any precondition fails, stop and report.
1. Conventional commits. `git push -u origin <branch>`.
2. Read .aidevops/host. github: `gh pr create` with the PR template filled (spec folder, changes, evidence summary, risks, rollback). gitlab: `glab mr create` with the MR template filled.
3. Request reviews. github: Claude Code Review runs when enabled on the repo; comment `@codex review` when Codex is available. gitlab: Claude `/code-review <MR> --comment`; Codex review output posted as an MR note.
4. Update handoff.md: status=in-review. Report the PR/MR URL. Do NOT merge.

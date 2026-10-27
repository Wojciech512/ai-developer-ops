---
name: ops-review
description: Modular review with identical stages for any target - an OpenSpec change id, a PR or MR, a branch, a commit range, or a path. Use before merge and for any review request.
argument-hint: <target> [--no-spec] [--no-security] [--no-cross] [--comment]
---
Read .aidevops/variant and .aidevops/host. Normalize the target:
- change id found under openspec/changes/ → diff = current branch vs default branch; spec = that folder
- a number, `!123` or a URL → PR/MR; spec = change id named in its description, else none
- `A..B`, a branch name, or a path → that target; spec = none
Run the stages in order. Skip a stage only when its flag is given. Every stage uses the report format from AGENTS.md (BLOCKER/WARN/NOTE with file:line, verdict PASS/FAIL).
1. Spec: only if spec exists. Claude: `/opsx:verify <id>`. Codex: `$openspec-verify <id>`.
2. Correctness. Claude: `/code-review <target> high`, add `--comment` when the target is a PR/MR and --comment was given. Codex: `codex review` for branch or uncommitted work; for a GitHub PR comment `@codex review`; for a path or range delegate to the reviewer agent with that target.
3. Security. Claude: `/security-review` if available, else the installed security plugin skill (check the `/` list). Codex: Codex Security plugin review of code changes. If none is installed: run the review agent with a security-only prompt and mark the stage "fallback".
4. Cross-model. claude-codex: `/codex:adversarial-review --base <base>`. claude: cross-reviewer agent. codex: reviewer agent (gpt-6-astra). The reviewer model must differ from the author model.
5. Verdict: count BLOCKER and WARN per stage. If spec exists, write sections review A, review B, security in openspec/changes/<id>/evidence.md. Final verdict is FAIL when any BLOCKER remains. Report to the user. This skill never edits code: the owner fixes, then reruns.

---
name: ops-ship
description: Prepare a release — verify preconditions, write the filled PR/MR body and handoff, commit locally, and request bot reviews on an already-open PR/MR. Hands the human the exact push/PR/MR commands to run. Never pushes, opens a PR/MR, or merges.
disable-model-invocation: true
argument-hint: <change-id>
---
Preconditions: `make check` green; evidence.md has review A and review B with zero BLOCKER; spec stage PASS. If any precondition fails, stop and report — do not prepare the release.

1. Read .aidevops/host. Fill `openspec/changes/<id>/pr-body.md` from `templates/pull_request_template.md` (host github) or `templates/merge_request_template.md` (host gitlab): sections Spec, Co zmieniono, Dowody, Ryzyka i rollback. If `pr-body.md` already exists from a previous run, overwrite it and say so in the report; this is expected, not an error.
2. Update `openspec/changes/<id>/handoff.md`: status=ready-to-push, owner=human.
3. Commit with Conventional Commits, including `pr-body.md` and `handoff.md` so the work product lands inside the commit, not after it — `pr-body.md` and `handoff.md` are written before this commit, never after. If there are no changes to commit, say so and do not create an empty commit.
4. If a PR/MR already exists for this branch (opened by a human after an earlier cycle), request reviews on it: github — Claude Code Review runs when enabled on the repo; comment `@codex review` when Codex is available. gitlab — Claude `/code-review <MR> --comment`; Codex review output posted as an MR note. Comments on an existing PR/MR are allowed by user decision; this step never opens or merges a PR/MR.
5. Report to the human, verbatim, ready to copy — this skill does not run these commands and does not merge; pushing, opening the PR/MR, and merging are done by the human:
   ```
   git push -u origin <branch>
   gh pr create --body-file openspec/changes/<id>/pr-body.md        # github
   glab mr create --description-file openspec/changes/<id>/pr-body.md  # gitlab
   ```

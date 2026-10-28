---
name: ops-ship
description: Prepare a release — verify preconditions, write the filled PR/MR body and handoff, commit locally, and request bot reviews on an already-open PR/MR. Hands the human the exact push/PR/MR commands to run. Never pushes, opens a PR/MR, or merges.
disable-model-invocation: true
argument-hint: <change-id>
---
Preconditions: `make check` green; evidence.md has review A and review B with zero BLOCKER; spec stage PASS. If any precondition fails, stop and report — do not prepare the release.

1. Record the change's file scope while the branch is still unmerged: `git diff --no-renames --name-only --diff-filter=ACMRD "$(git merge-base HEAD origin/<default-branch>)"..HEAD > openspec/changes/<id>/scope.txt`, one path per line. `--no-renames` makes a rename show as a delete plus an add, so the old path is recorded too; without it only the destination appears and the stale component is never dropped. `--diff-filter` keeps deletions (`D`) - those are exactly the paths a later architecture refresh needs in order to drop components that no longer exist. This cannot be recomputed after merge: once the branch is in, `git merge-base HEAD <default-branch>` is HEAD itself and the diff is empty. Both commands only read the remote ref, so they are allowed.
2. Read .aidevops/host. Fill `openspec/changes/<id>/pr-body.md` from the template `init.sh` installed into this project — `.github/pull_request_template.md` (host github) or `.gitlab/merge_request_templates/Default.md` (host gitlab) — falling back to `$CLAUDE_PLUGIN_ROOT/templates/pull_request_template.md` / `$CLAUDE_PLUGIN_ROOT/templates/merge_request_template.md` only if the installed copy is missing (e.g. an older project that hasn't rerun init): sections Spec, Co zmieniono, Dowody, Ryzyka i rollback. If `pr-body.md` already exists from a previous run, overwrite it and say so in the report; this is expected, not an error.
3. Update `openspec/changes/<id>/handoff.md`: status=ready-to-push, owner=human.
4. Commit with Conventional Commits, including `scope.txt`, `pr-body.md` and `handoff.md` so the work product lands inside the commit, not after it — all three are written before this commit, never after. If there are no changes to commit, say so and do not create an empty commit.
5. If a PR/MR already exists for this branch (opened by a human after an earlier cycle), request reviews on it: github — Claude Code Review runs when enabled on the repo; comment `@codex review` when Codex is available. gitlab — Claude `/code-review <MR> --comment`; Codex review output posted as an MR note. Comments on an existing PR/MR are allowed by user decision; this step never opens or merges a PR/MR.
6. Report to the human, verbatim, ready to copy — this skill does not run these commands and does not merge; pushing, opening the PR/MR, and merging are done by the human:
   ```
   git push -u origin <branch>
   gh pr create --body-file openspec/changes/<id>/pr-body.md        # github
   glab mr create --description-file openspec/changes/<id>/pr-body.md  # gitlab
   ```

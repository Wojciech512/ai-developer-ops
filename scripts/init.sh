#!/usr/bin/env bash
# Project init, deterministic part. Run inside the target repository.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "Run inside a git repository."; exit 1; }
VARIANT="$("$ROOT/scripts/detect.sh")"
REMOTE="$(git remote get-url origin 2>/dev/null || true)"
case "$REMOTE" in *github.com*) HOST=github;; *gitlab*) HOST=gitlab;; *) HOST=other;; esac

mkdir -p .aidevops/templates docs/adr .githooks
echo "$VARIANT" > .aidevops/variant
echo "$HOST" > .aidevops/host
grep -qx '.aidevops/' .gitignore 2>/dev/null || echo '.aidevops/' >> .gitignore

cp_if_absent() { if [ -e "$2" ]; then echo "kept    $2"; else mkdir -p "$(dirname "$2")"; cp "$1" "$2"; echo "created $2"; fi; }

cp_if_absent "$ROOT/templates/AGENTS.md" AGENTS.md
cp_if_absent "$ROOT/templates/Makefile" Makefile
cp "$ROOT/templates/handoff.md"  .aidevops/templates/handoff.md
cp "$ROOT/templates/evidence.md" .aidevops/templates/evidence.md
cp_if_absent "$ROOT/templates/pre-push" .githooks/pre-push
chmod +x .githooks/pre-push
git config core.hooksPath .githooks

case "$HOST" in
  github) cp_if_absent "$ROOT/templates/pull_request_template.md" .github/pull_request_template.md
          cp_if_absent "$ROOT/templates/ci-github.yml" .github/workflows/ai-check.yml ;;
  gitlab) cp_if_absent "$ROOT/templates/merge_request_template.md" .gitlab/merge_request_templates/Default.md
          cp_if_absent "$ROOT/templates/ci-gitlab.yml" .gitlab-ci.yml ;;
  *)      echo "No GitHub/GitLab remote detected: PR/MR template and CI skipped." ;;
esac

if [[ "$VARIANT" == *claude* ]]; then cp_if_absent "$ROOT/templates/settings.json" .claude/settings.json; fi
if [[ "$VARIANT" == *codex* ]]; then
  mkdir -p .codex/agents
  for t in "$ROOT"/codex/agents/*.toml; do cp_if_absent "$t" ".codex/agents/$(basename "$t")"; done
  cp_if_absent "$ROOT/codex/config.snippet.toml" .codex/config.toml
fi

if command -v playwright-cli >/dev/null 2>&1; then
  playwright-cli install --skills >/dev/null 2>&1 && echo "playwright skills installed" || echo "playwright-cli install --skills failed (ok to skip)"
fi

echo "INIT_DONE variant=$VARIANT host=$HOST"
echo "Remaining for the skill: openspec init, fill TODO in AGENTS.md and Makefile, make check, gate test, commit."

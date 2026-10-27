#!/usr/bin/env bash
# Machine-level install. Run once: ~/.ai-developer-ops/scripts/install.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VARIANT="$("$ROOT/scripts/detect.sh")"
echo "Detected tools: $VARIANT"
[ "$VARIANT" = none ] && { echo "Install claude and/or codex first."; exit 1; }

command -v npm >/dev/null 2>&1 || { echo "npm missing. Install Node.js, then rerun."; exit 1; }
npm ls -g @fission-ai/openspec >/dev/null 2>&1 || npm i -g @fission-ai/openspec
npm ls -g @playwright/cli    >/dev/null 2>&1 || npm i -g @playwright/cli

if [[ "$VARIANT" == *claude* ]]; then
  claude plugin marketplace add "$ROOT" || true
  claude plugin install ai-developer-ops@ai-developer-ops || true
  claude plugin marketplace add obra/superpowers-marketplace || true
  claude plugin install superpowers@superpowers-marketplace || true
fi
if [[ "$VARIANT" == *codex* ]]; then
  mkdir -p ~/.agents/skills ~/.codex/agents
  for s in "$ROOT"/skills/*/; do ln -sfn "${s%/}" ~/.agents/skills/"$(basename "$s")"; done
  for t in "$ROOT"/codex/agents/*.toml; do ln -sfn "$t" ~/.codex/agents/"$(basename "$t")"; done
  if [ ! -f ~/.codex/config.toml ]; then
    cp "$ROOT/codex/config.snippet.toml" ~/.codex/config.toml
    echo "Created ~/.codex/config.toml from snippet."
  elif ! grep -q '^\[agents\]' ~/.codex/config.toml; then
    echo "Merge $ROOT/codex/config.snippet.toml into ~/.codex/config.toml by hand: top-level keys first, then [agents]."
  fi
fi
if [ "$VARIANT" = claude-codex ]; then
  claude plugin marketplace add openai/codex-plugin-cc || true
  claude plugin install codex@openai-codex || true
fi
mkdir -p ~/.ai-developer-ops-state && echo "$VARIANT" > ~/.ai-developer-ops-state/variant
echo "Done. In a project run: /init-ai-developer-ops (Claude) or \$init-ai-developer-ops (Codex)."

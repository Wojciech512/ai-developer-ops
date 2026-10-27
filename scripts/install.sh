#!/usr/bin/env bash
# Idempotent: safe to rerun; each run updates to the repo state.
# Machine-level install. Run: ~/.ai-developer-ops/scripts/install.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# --- Self-update: pull only when the repo checkout is clean ---
if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if [ -z "$(git -C "$ROOT" status --porcelain)" ]; then
    git -C "$ROOT" pull --ff-only || echo "warn: git pull --ff-only failed; continuing with current checkout"
  else
    echo "warn: local changes in $ROOT; skipping self-update (git pull)"
  fi
fi

VARIANT="$("$ROOT/scripts/detect.sh")"
echo "Detected tools: $VARIANT"
[ "$VARIANT" = none ] && { echo "Install claude and/or codex first."; exit 1; }

command -v npm >/dev/null 2>&1 || { echo "npm missing. Install Node.js, then rerun."; exit 1; }
npm i -g @fission-ai/openspec@latest @playwright/cli@latest || echo "warn: npm install/update of openspec/playwright-cli failed"

# Add a marketplace only if it is not registered yet.
ensure_marketplace() { # <name> <source>
  if ! claude plugin marketplace list --json 2>/dev/null | grep -E "\"name\":[[:space:]]*\"$1\"" >/dev/null; then
    claude plugin marketplace add "$2" || echo "warn: could not add marketplace $1 from $2"
  fi
}

# Refresh the marketplace, install the plugin, update it when already installed.
install_or_update_plugin() { # <plugin> <marketplace>
  local plugin="$1" marketplace="$2" out rc=0
  claude plugin marketplace update "$marketplace" || echo "warn: marketplace update failed: $marketplace"
  out="$(claude plugin install "$plugin@$marketplace" 2>&1)" || rc=$?
  echo "$out"
  if printf '%s\n' "$out" | grep -qi "already installed"; then
    claude plugin update "$plugin" || echo "warn: plugin update failed: $plugin"
  elif [ "$rc" -ne 0 ]; then
    echo "warn: plugin install failed: $plugin@$marketplace"
  fi
}

if [[ "$VARIANT" == *claude* ]]; then
  ensure_marketplace ai-developer-ops "$ROOT"
  ensure_marketplace superpowers-marketplace obra/superpowers-marketplace
  install_or_update_plugin ai-developer-ops ai-developer-ops
  install_or_update_plugin superpowers superpowers-marketplace
  install_or_update_plugin security-guidance claude-plugins-official
fi
if [[ "$VARIANT" == *codex* ]]; then
  mkdir -p ~/.agents/skills ~/.codex/agents
  # Remove dangling symlinks that point inside $ROOT; leave everything else alone.
  for dir in ~/.agents/skills ~/.codex/agents; do
    for link in "$dir"/* "$dir"/.*; do
      [ -L "$link" ] || continue
      case "$(readlink "$link")" in
        "$ROOT"/*) [ -e "$link" ] || { rm -f "$link"; echo "Removed dangling symlink: $link"; } ;;
      esac
    done
  done
  for s in "$ROOT"/skills/*/; do ln -sfn "${s%/}" ~/.agents/skills/"$(basename "$s")"; done
  for t in "$ROOT"/codex/agents/*.toml; do ln -sfn "$t" ~/.codex/agents/"$(basename "$t")"; done
  if [ ! -f ~/.codex/config.toml ]; then
    cp "$ROOT/codex/config.snippet.toml" ~/.codex/config.toml
    echo "Created ~/.codex/config.toml from snippet."
  elif grep -q '^\[agents\]' ~/.codex/config.toml; then
    echo "Info: [agents] already present in ~/.codex/config.toml; diff vs snippet (informational only, no changes made):"
    diff <(awk '/^\[/{p=/^\[agents\]/} p' "$ROOT/codex/config.snippet.toml") \
         <(awk '/^\[/{p=/^\[agents\]/} p' ~/.codex/config.toml) \
      || true
  else
    echo "Merge $ROOT/codex/config.snippet.toml into ~/.codex/config.toml by hand: top-level keys first, then [agents]."
  fi
fi
if [ "$VARIANT" = claude-codex ]; then
  ensure_marketplace openai-codex openai/codex-plugin-cc
  install_or_update_plugin codex openai-codex
fi
mkdir -p ~/.ai-developer-ops-state && echo "$VARIANT" > ~/.ai-developer-ops-state/variant

echo ""
echo "=== Summary ==="
echo "Variant: $VARIANT"
echo "openspec: $(openspec --version 2>/dev/null || echo 'warn: not available')"
echo "playwright-cli: $(playwright-cli --version 2>/dev/null || echo 'warn: not available')"
if [[ "$VARIANT" == *claude* ]]; then
  echo "Installed Claude plugins:"
  claude plugin list || echo "warn: claude plugin list failed"
fi
if [[ "$VARIANT" == *codex* ]]; then
  echo "Symlinks in ~/.agents/skills:"
  find ~/.agents/skills -maxdepth 1 -type l -exec ls -ld {} + 2>/dev/null || true
  echo "Symlinks in ~/.codex/agents:"
  find ~/.codex/agents -maxdepth 1 -type l -exec ls -ld {} + 2>/dev/null || true
fi
if pgrep -f "claude" >/dev/null 2>&1; then
  echo "Claude Code is running: run /reload-plugins in each open session (new sessions load plugins automatically)."
fi
if pgrep -x "codex" >/dev/null 2>&1; then
  echo "Codex is running: restart open Codex sessions to load config.toml, MCP and agent changes (skills reload automatically)."
fi
echo "Done. In a project run: /ai-developer-ops:init (Claude) or \$init (Codex)."

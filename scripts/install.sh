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

# Remove dangling symlinks in <dir> that point inside $ROOT; leave everything else alone.
clean_dangling_links() { # <dir>
  local link
  for link in "$1"/* "$1"/.*; do
    [ -L "$link" ] || continue
    case "$(readlink "$link")" in
      "$ROOT"/*) [ -e "$link" ] || { rm -f "$link"; echo "Removed dangling symlink: $link"; } ;;
    esac
  done
}

# Create/refresh a symlink; never touch a real (non-symlink) file or directory at the destination.
link_file() { # <target> <dest>
  if [ ! -e "$1" ]; then
    echo "warn: link target $1 does not exist; skipping"
    return 0
  fi
  if [ -e "$2" ] && [ ! -L "$2" ]; then
    echo "warn: $2 exists and is not a symlink; skipping link to $1"
    return 0
  fi
  ln -sfn "$1" "$2" || echo "warn: could not link $2 -> $1"
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
  mkdir -p ~/.claude/agents
  clean_dangling_links ~/.claude/agents
  for a in "$ROOT"/templates/agents/*.md; do link_file "$a" ~/.claude/agents/"$(basename "$a")"; done
  # Context7 for Claude: skip when already present as a plugin or an MCP server.
  if ! claude plugin list 2>/dev/null | grep -i context7 >/dev/null \
     && ! claude mcp list 2>/dev/null | grep -i context7 >/dev/null; then
    # ctx7 setup is interactive (mode prompt + OAuth); without a TTY feed it /dev/null so it cannot hang.
    if [ -t 0 ]; then
      npx -y ctx7 setup --claude || true
    else
      npx -y ctx7 setup --claude </dev/null || true
    fi
    if ! claude mcp list 2>/dev/null | grep -i context7 >/dev/null \
       && ! claude plugin list 2>/dev/null | grep -i context7 >/dev/null; then
      echo "warn: Context7 setup for Claude skipped; run: npx ctx7 setup --claude"
    fi
  fi
fi
if [[ "$VARIANT" == *codex* ]]; then
  mkdir -p ~/.agents/skills ~/.codex/agents
  clean_dangling_links ~/.agents/skills
  clean_dangling_links ~/.codex/agents
  for s in "$ROOT"/skills/*/; do link_file "${s%/}" ~/.agents/skills/"$(basename "$s")"; done
  for t in "$ROOT"/codex/agents/*.toml; do link_file "$t" ~/.codex/agents/"$(basename "$t")"; done
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
  # Context7 for Codex: prefer the plugin marketplace, fall back to a plain MCP entry.
  if ! codex mcp list 2>/dev/null | grep -i context7 >/dev/null; then
    if codex plugin marketplace add upstash/context7 && codex plugin add context7@context7-marketplace; then
      echo "Context7 installed via Codex plugin marketplace."
    else
      codex mcp add context7 -- npx -y @upstash/context7-mcp \
        || echo "warn: Context7 for Codex skipped; run: codex mcp add context7 -- npx -y @upstash/context7-mcp"
    fi
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

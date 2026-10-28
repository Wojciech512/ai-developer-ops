#!/usr/bin/env bash
# E2E smoke: init.sh scaffolds a fresh github repo, reruns idempotently,
# and the installed pre-push gate goes through a green `make check`.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

STUB="$TMP/bin"
mkdir -p "$STUB"
printf '#!/bin/sh\nexit 0\n' >"$STUB/claude"
cp "$STUB/claude" "$STUB/codex"
chmod +x "$STUB/claude" "$STUB/codex"
export PATH="$STUB:/usr/bin:/bin" HOME="$TMP" GIT_CONFIG_NOSYSTEM=1

mkdir "$TMP/repo"
cd "$TMP/repo" || exit 1
git init -q
git remote add origin https://github.com/example/e2e.git

out1="$(bash "$ROOT/scripts/init.sh")"
echo "$out1" | grep -q "INIT_DONE variant=claude-codex host=github"

out2="$(bash "$ROOT/scripts/init.sh")"
echo "$out2" | grep -q "kept    AGENTS.md"

[ -x .githooks/pre-push ]
bash .githooks/pre-push

grep -q 'nie pushuje na żadne zdalne' AGENTS.md
grep -q 'Bash(git push\*)' .claude/settings.json

echo "E2E_SMOKE_OK"

#!/usr/bin/env bash
# Runs the repo formatter on the edited file when the Makefile has a fmt-file target. Never blocks.
INPUT="$(cat)"
F="$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')"
[ -z "$F" ] && exit 0
if [ -f Makefile ] && grep -q '^fmt-file:' Makefile; then
  make -s fmt-file FILE="$F" >/dev/null 2>&1 || true
fi
exit 0

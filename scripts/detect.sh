#!/usr/bin/env bash
# Prints which agent CLIs are installed: claude | codex | claude-codex | none
set -u
c=0; x=0
command -v claude >/dev/null 2>&1 && c=1
command -v codex  >/dev/null 2>&1 && x=1
if [ "$c" = 1 ] && [ "$x" = 1 ]; then echo claude-codex
elif [ "$c" = 1 ]; then echo claude
elif [ "$x" = 1 ]; then echo codex
else echo none; fi

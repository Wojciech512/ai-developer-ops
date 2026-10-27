#!/usr/bin/env bash
# Blocks the end of a turn until `make check` passes. Exit 2 = block. No-op without a Makefile check target.
INPUT="$(cat)"
if echo "$INPUT" | jq -e '.stop_hook_active == true' >/dev/null 2>&1; then exit 0; fi
if ! { [ -f Makefile ] && grep -q '^check:' Makefile; }; then exit 0; fi
if [ -z "$(git status --porcelain 2>/dev/null)" ]; then exit 0; fi
if OUT="$(make -s check 2>&1)"; then exit 0; fi
echo "make check FAILED. Fix the root cause. Do not disable or skip tests." >&2
echo "$OUT" | tail -n 80 >&2
exit 2

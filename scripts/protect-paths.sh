#!/usr/bin/env bash
# Blocks edits to protected paths unless AIDEVOPS_ALLOW_PROTECTED=1. Exit 2 = block.
INPUT="$(cat)"
F="$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')"
[ -z "$F" ] && exit 0
[ "${AIDEVOPS_ALLOW_PROTECTED:-0}" = "1" ] && exit 0
P='(^|/)(\.env|\.env\..*|package-lock\.json|pnpm-lock\.yaml|yarn\.lock|poetry\.lock|uv\.lock|Cargo\.lock|go\.sum)$|(^|/)(migrations|\.github/workflows)/|(^|/)\.gitlab-ci\.yml$|(^|/)scripts/deny-push\.sh$|(^|/)hooks/hooks\.json$|(^|/)\.claude/settings\.json$|(^|/)templates/settings\.json$'
if echo "$F" | grep -Eq "$P"; then
	echo "Blocked: $F is protected. Ask the user. If approved, rerun with AIDEVOPS_ALLOW_PROTECTED=1." >&2
	exit 2
fi
exit 0

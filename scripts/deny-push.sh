#!/usr/bin/env bash
# Blocks commands that move code to a remote: git push, gh/glab PR or MR
# create/merge, gh release create, and write-method `gh api` calls. The
# agent's job ends at a local commit; a human reviews and runs the
# remote-facing command. Exit 2 = block, exit 0 = allow.
#
# No AIDEVOPS_ALLOW_* override on purpose: unlike protect-paths.sh, this
# gate has no environment escape hatch.
set -uo pipefail

BLOCK_MSG="Blocked: this command would move code to a remote (push/PR/MR/release/write API call). The agent's job ends at a local commit; a human reviews and runs that command."
CANT_EVAL_MSG="Blocked: cannot safely evaluate this command for remote-write operations. The agent's job ends at a local commit; a human reviews and runs that command manually."

INPUT="$(cat)"

# Stage 1: cheap pre-filter on the raw stdin, no jq required. If none of
# the indicator substrings appear anywhere in the raw input, there is
# nothing remote-facing to evaluate: let it through immediately so a
# missing jq never blocks ordinary local work.
has_indicator() {
	case "$1" in
	*push* | *'pr create'* | *'pr merge'* | *'release create'* | *'mr create'* | *'mr merge'* | *api*)
		return 0
		;;
	*)
		return 1
		;;
	esac
}

if ! has_indicator "$INPUT"; then
	exit 0
fi

# Stage 2: an indicator is present, so we need jq to safely pull the real
# command out of the JSON. Without jq we cannot evaluate it: fail closed.
if ! command -v jq >/dev/null 2>&1; then
	echo "$CANT_EVAL_MSG (jq not found on PATH)" >&2
	exit 2
fi

# Stage 3: parse .tool_input.command. Missing/null/empty/non-string -> we
# already know an indicator is present in the raw input, so fail closed.
CMD="$(printf '%s' "$INPUT" | jq -r '
  if (.tool_input.command? != null) and ((.tool_input.command | type) == "string")
  then .tool_input.command
  else ""
  end
' 2>/dev/null)"
JQ_STATUS=$?

if [ "$JQ_STATUS" -ne 0 ] || [ -z "$CMD" ]; then
	echo "$CANT_EVAL_MSG (could not parse a command string)" >&2
	exit 2
fi

# Stage 4: strip quoted substrings. A forbidden word inside quotes is
# data (a commit message, a printf argument), not an invocation.
strip_quotes() {
	local s="$1" out="" ch qc i=0 len
	len=${#s}
	while [ "$i" -lt "$len" ]; do
		ch="${s:$i:1}"
		if [ "$ch" = "'" ] || [ "$ch" = '"' ]; then
			qc="$ch"
			i=$((i + 1))
			while [ "$i" -lt "$len" ]; do
				ch="${s:$i:1}"
				i=$((i + 1))
				[ "$ch" = "$qc" ] && break
			done
			out="$out "
		else
			out="$out$ch"
			i=$((i + 1))
		fi
	done
	printf '%s' "$out"
}

CLEAN="$(strip_quotes "$CMD")"

# Stage 5: split into segments on shell separators: ; && || | newline (.
NORMALIZED="${CLEAN//&&/$'\n'}"
NORMALIZED="${NORMALIZED//||/$'\n'}"
NORMALIZED="${NORMALIZED//;/$'\n'}"
NORMALIZED="${NORMALIZED//|/$'\n'}"
NORMALIZED="${NORMALIZED//(/$'\n'}"

# Stage 6: for each segment, find the operation and decide.
is_var_assignment() {
	case "$1" in
	[A-Za-z_]*=*) return 0 ;;
	*) return 1 ;;
	esac
}

uppercase() {
	printf '%s' "$1" | tr '[:lower:]' '[:upper:]'
}

check_segment() {
	local seg="$1"
	local -a words
	local n idx w j t subcmd sub1 sub2 k method path method_upper

	read -ra words <<<"$seg"
	n=${#words[@]}
	[ "$n" -eq 0 ] && return 0

	idx=0
	while [ "$idx" -lt "$n" ]; do
		w="${words[$idx]}"
		if is_var_assignment "$w"; then
			idx=$((idx + 1))
			continue
		fi
		break
	done
	[ "$idx" -ge "$n" ] && return 0
	w="${words[$idx]}"

	case "$w" in
	git)
		subcmd=""
		j=$((idx + 1))
		while [ "$j" -lt "$n" ]; do
			t="${words[$j]}"
			case "$t" in
			-C | -c | --git-dir | --work-tree | --namespace | --exec-path)
				j=$((j + 2))
				continue
				;;
			--git-dir=* | --work-tree=* | --namespace=* | --exec-path=*)
				j=$((j + 1))
				continue
				;;
			-*)
				j=$((j + 1))
				continue
				;;
			*)
				subcmd="$t"
				break
				;;
			esac
		done
		if [ "$subcmd" = "push" ]; then
			return 1
		fi
		;;
	gh)
		sub1="${words[$((idx + 1))]:-}"
		sub2="${words[$((idx + 2))]:-}"
		if [ "$sub1" = "pr" ] && { [ "$sub2" = "create" ] || [ "$sub2" = "merge" ]; }; then
			return 1
		fi
		if [ "$sub1" = "release" ] && [ "$sub2" = "create" ]; then
			return 1
		fi
		if [ "$sub1" = "api" ]; then
			method="GET"
			path=""
			k=$((idx + 2))
			while [ "$k" -lt "$n" ]; do
				t="${words[$k]}"
				case "$t" in
				--method)
					method="${words[$((k + 1))]:-GET}"
					k=$((k + 2))
					continue
					;;
				--method=*)
					method="${t#--method=}"
					k=$((k + 1))
					continue
					;;
				-X)
					method="${words[$((k + 1))]:-GET}"
					k=$((k + 2))
					continue
					;;
				-*)
					k=$((k + 1))
					continue
					;;
				*)
					[ -z "$path" ] && path="$t"
					k=$((k + 1))
					continue
					;;
				esac
			done
			method_upper="$(uppercase "$method")"
			case "$method_upper" in
			POST | PATCH | PUT | DELETE)
				case "$path" in
				/markdown) ;;
				*) return 1 ;;
				esac
				;;
			esac
		fi
		;;
	glab)
		sub1="${words[$((idx + 1))]:-}"
		sub2="${words[$((idx + 2))]:-}"
		if [ "$sub1" = "mr" ] && { [ "$sub2" = "create" ] || [ "$sub2" = "merge" ]; }; then
			return 1
		fi
		;;
	esac
	return 0
}

while IFS= read -r SEGMENT; do
	if ! check_segment "$SEGMENT"; then
		echo "$BLOCK_MSG" >&2
		exit 2
	fi
done <<<"$NORMALIZED"

exit 0

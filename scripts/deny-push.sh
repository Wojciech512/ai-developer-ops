#!/usr/bin/env bash
# Blocks commands that move code to a remote: git push, gh/glab PR or MR
# create/merge, gh release create, and write-method `gh api` calls. The
# agent's job ends at a local commit; a human reviews and runs the
# remote-facing command. Exit 2 = block, exit 0 = allow.
#
# Design: fail-closed, not a per-tool flag enumeration. One shared
# flag-skip routine finds "the subcommand" for git, gh and glab alike;
# quoted text is neutralized (not deleted) so it can never be consumed as
# an argument; every evaluation failure (bad JSON, missing jq, anything
# unexpected) exits 2, never 0.
#
# No AIDEVOPS_ALLOW_* override on purpose: unlike protect-paths.sh, this
# gate has no environment escape hatch.
set -uo pipefail
set -o noglob # we only ever tokenize text here, never touch the filesystem

BLOCK_MSG="Blocked: this command would move code to a remote (push/PR/MR/release/write API call). The agent's job ends at a local commit; a human reviews and runs that command."
CANT_EVAL_MSG="Blocked: cannot safely evaluate this command for remote-write operations. The agent's job ends at a local commit; a human reviews and runs that command manually."
BACKSLASH="\\"

INPUT="$(cat)"

# --- Stage 1: cheap pre-filter on the raw stdin, no jq required -------
# Conservative and whitespace-insensitive: look for standalone WORDS
# (push, create, merge, api, release), not phrases. A phrase check like
# "pr create" breaks under "pr  create" (double space) or a literal tab
# -- that was bug 3/4. Pure bash, deliberately: no external tool (not
# even `tr`) runs before we know jq is needed and available, so there is
# nothing here that can silently fail open if some other tool is also
# missing from PATH. Scans character by character, building up runs of
# [A-Za-z0-9_] as candidate words and checking each completed run against
# the indicator list; a backslash is treated, together with the single
# character after it, as a two-character separator, so the raw (still
# JSON-escaped) text `mr\tmerge` -- literal backslash-t, not a real tab
# byte -- still splits into "mr" and "merge" instead of fusing into
# "tmerge".
has_indicator() {
	local s="$1" c word="" i=0 len
	len=${#s}
	while [ "$i" -lt "$len" ]; do
		c="${s:$i:1}"
		if [ "$c" = "$BACKSLASH" ]; then
			case "$word" in
			push | create | merge | api | release) return 0 ;;
			esac
			word=""
			i=$((i + 2))
			continue
		fi
		case "$c" in
		[A-Za-z0-9_])
			word="$word$c"
			;;
		*)
			case "$word" in
			push | create | merge | api | release) return 0 ;;
			esac
			word=""
			;;
		esac
		i=$((i + 1))
	done
	case "$word" in
	push | create | merge | api | release) return 0 ;;
	esac
	return 1
}

if ! has_indicator "$INPUT"; then
	exit 0
fi

# --- Stage 2: jq is required to safely pull the command out of JSON ---
if ! command -v jq >/dev/null 2>&1; then
	echo "$CANT_EVAL_MSG (jq not found on PATH)" >&2
	exit 2
fi

# --- Stage 3: extract .tool_input.command ------------------------------
# Missing field, null, wrong type, or unparsable JSON: an indicator word
# is present somewhere in the raw input (stage 1 passed) and we cannot
# rule out that it is a real invocation, so fail closed.
HAS_CMD="$(printf '%s' "$INPUT" | jq -r '
  if (.tool_input.command? != null) and ((.tool_input.command | type) == "string")
  then "yes" else "no" end
' 2>/dev/null)"
JQ_STATUS=$?
if [ "$JQ_STATUS" -ne 0 ]; then
	echo "$CANT_EVAL_MSG (input is not valid JSON)" >&2
	exit 2
fi
if [ "$HAS_CMD" != "yes" ]; then
	echo "$CANT_EVAL_MSG (no string .tool_input.command field)" >&2
	exit 2
fi

CMD="$(printf '%s' "$INPUT" | jq -r '.tool_input.command')"
JQ_STATUS=$?
if [ "$JQ_STATUS" -ne 0 ]; then
	echo "$CANT_EVAL_MSG (could not extract .tool_input.command)" >&2
	exit 2
fi

# --- Stage 4: normalize -------------------------------------------------
# This is the core of the fix. Quoted-region CONTENT is replaced with the
# placeholder QSTR, never deleted. Deleting was the original bug: after
# `-C "/repo path"` the leftover text was `-C push`, so `push` got
# consumed as -C's argument and the push was allowed. The placeholder
# fixes both directions: `git commit -m "... git push"` collapses to
# `git commit -m QSTR` (no bare `push` token -> passes), while
# `git -C "/repo path" push` collapses to `git -C QSTR push` (git + push
# -> blocks).
qstr() {
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
			out="$out QSTR "
		else
			out="$out$ch"
			i=$((i + 1))
		fi
	done
	printf '%s' "$out"
}

NORM="$(qstr "$CMD")"
# Defuse subshell/substitution wrappers: ( ) ` $ become plain spaces, not
# segment breaks, so `(git push)` and `$(git push)` collapse to the same
# token stream as a bare `git push`.
NORM="${NORM//(/ }"
NORM="${NORM//)/ }"
NORM="${NORM//\`/ }"
NORM="${NORM//\$/ }"
# Tabs/newlines are just more whitespace.
NORM="${NORM//$'\t'/ }"
NORM="${NORM//$'\n'/ }"
# Shell separators become a sentinel word. Translating ; & | one
# character at a time also covers && and || (each half becomes its own
# sentinel; an empty segment between two sentinels is harmless).
NORM="${NORM//;/ CMDSEP }"
NORM="${NORM//&/ CMDSEP }"
NORM="${NORM//|/ CMDSEP }"

# shellcheck disable=SC2206 # intentional word-splitting; noglob is set above
SEG_WORDS=($NORM)
SEG_N=${#SEG_WORDS[@]}

# True (0) if $1 is POST/PATCH/PUT/DELETE in any case. Pure bash (no
# `tr`), for the same reason as has_indicator above: once jq has
# succeeded we are past the "fail closed if a tool is missing" gate, but
# there is still no reason to add an avoidable external-tool dependency
# to a check that decides pass vs. block.
is_write_method() {
	case "$1" in
	[Pp][Oo][Ss][Tt] | [Pp][Aa][Tt][Cc][Hh] | [Pp][Uu][Tt] | [Dd][Ee][Ll][Ee][Tt][Ee])
		return 0
		;;
	esac
	return 1
}

# --- Stage 6: one shared flag-skip routine for every tool ---------------
# Options known to take a value. Enumerated ONCE, used for git, gh and
# glab alike -- the old script enumerated flags per tool (git skipped
# them, gh/glab used fixed offsets and didn't), which is exactly the bug
# class the review flagged. Not an exhaustive flag dictionary: a
# conservative list of the flags that appear before the subcommand in
# practice.
is_value_flag() {
	case "$1" in
	-C | -c | -R | --repo | --hostname | --git-dir | --work-tree | --namespace | --exec-path | --method | -X)
		return 0
		;;
	*)
		return 1
		;;
	esac
}

# Advances past exactly one flag token at index $1 of SEG_WORDS. Sets
# SKIP_NEXT to the index right after it (and its value, if it takes one),
# and SKIP_VALUE to that value when recoverable: attached "--opt=value",
# compact "-Xvalue", or the following token for the bare form.
skip_one_flag() {
	local idx="$1" tok="${SEG_WORDS[$1]:-}"
	SKIP_VALUE=""
	case "$tok" in
	--*=*)
		SKIP_VALUE="${tok#*=}"
		SKIP_NEXT=$((idx + 1))
		return 0
		;;
	-[CcRX]?*)
		SKIP_VALUE="${tok:2}"
		SKIP_NEXT=$((idx + 1))
		return 0
		;;
	esac
	if is_value_flag "$tok"; then
		SKIP_VALUE="${SEG_WORDS[$((idx + 1))]:-}"
		SKIP_NEXT=$((idx + 2))
	else
		SKIP_NEXT=$((idx + 1))
	fi
}

# From index $1 up to (excluding) $2, skip every flag token with the
# shared routine above and report the first remaining token as SUBCMD,
# tool-agnostic: works the same whether the tool is git, gh or glab.
find_subcommand() {
	local idx="$1" end="$2"
	SUBCMD=""
	SUBCMD_NEXT="$idx"
	while [ "$idx" -lt "$end" ]; do
		case "${SEG_WORDS[$idx]:-}" in
		-*)
			skip_one_flag "$idx"
			idx="$SKIP_NEXT"
			continue
			;;
		*)
			SUBCMD="${SEG_WORDS[$idx]:-}"
			SUBCMD_NEXT=$((idx + 1))
			return 0
			;;
		esac
	done
}

# True (0) if the literal token $3 appears anywhere in [$1,$2).
contains_token() {
	local idx="$1" end="$2" needle="$3"
	while [ "$idx" -lt "$end" ]; do
		[ "${SEG_WORDS[$idx]:-}" = "$needle" ] && return 0
		idx=$((idx + 1))
	done
	return 1
}

# gh api is a write when a write HTTP method is explicit (--method/-X,
# "=" form, or compact "-XPOST"), OR when a body-supplying flag is
# present (-f/-F/--field/--raw-field/--input) -- gh defaults to POST
# whenever a body is supplied, with no --method needed. Exception:
# /markdown is explicitly allowed by spec.
gh_api_is_write() {
	local idx="$1" end="$2" path="" method="" tok
	while [ "$idx" -lt "$end" ]; do
		tok="${SEG_WORDS[$idx]:-}"
		case "$tok" in
		-f | -F | --field | --raw-field | --input)
			method="POST"
			idx=$((idx + 2))
			continue
			;;
		--method | -X | --method=* | -X?*)
			skip_one_flag "$idx"
			[ -n "$SKIP_VALUE" ] && method="$SKIP_VALUE"
			idx="$SKIP_NEXT"
			continue
			;;
		-*)
			skip_one_flag "$idx"
			idx="$SKIP_NEXT"
			continue
			;;
		*)
			[ -z "$path" ] && path="$tok"
			idx=$((idx + 1))
			continue
			;;
		esac
	done
	if is_write_method "$method"; then
		case "$path" in
		/markdown) return 1 ;;
		*) return 0 ;;
		esac
	fi
	return 1
}

# --- Stage 5 + 7: peel wrapper layers, then classify one segment -------
# check_segment_range operates on SEG_WORDS[$1,$2). Returns 1 to block.
check_segment_range() {
	local idx="$1" end="$2" changed tok

	changed=1
	while [ "$changed" -eq 1 ] && [ "$idx" -lt "$end" ]; do
		changed=0
		# VAR=value assignments at the start of the segment (also
		# covers `env FOO=bar git push`'s second round).
		while [ "$idx" -lt "$end" ]; do
			case "${SEG_WORDS[$idx]:-}" in
			[A-Za-z_]*=*)
				idx=$((idx + 1))
				changed=1
				;;
			*) break ;;
			esac
		done
		# Wrapper commands: strip the wrapper, then its own flags
		# and numeric positional args (e.g. `timeout 30`).
		if [ "$idx" -lt "$end" ]; then
			case "${SEG_WORDS[$idx]:-}" in
			env | timeout | nice | nohup | exec | sudo | command | xargs)
				idx=$((idx + 1))
				changed=1
				while [ "$idx" -lt "$end" ]; do
					case "${SEG_WORDS[$idx]:-}" in
					-* | [0-9]*) idx=$((idx + 1)) ;;
					*) break ;;
					esac
				done
				;;
			esac
		fi
	done

	[ "$idx" -ge "$end" ] && return 0
	tok="${SEG_WORDS[$idx]:-}"
	idx=$((idx + 1))

	case "$tok" in
	git)
		find_subcommand "$idx" "$end"
		[ "$SUBCMD" = "push" ] && return 1
		;;
	gh)
		find_subcommand "$idx" "$end"
		case "$SUBCMD" in
		pr)
			if contains_token "$SUBCMD_NEXT" "$end" "create" ||
				contains_token "$SUBCMD_NEXT" "$end" "merge"; then
				return 1
			fi
			;;
		release)
			contains_token "$SUBCMD_NEXT" "$end" "create" && return 1
			;;
		api)
			gh_api_is_write "$SUBCMD_NEXT" "$end" && return 1
			;;
		esac
		;;
	glab)
		find_subcommand "$idx" "$end"
		if [ "$SUBCMD" = "mr" ]; then
			if contains_token "$SUBCMD_NEXT" "$end" "create" ||
				contains_token "$SUBCMD_NEXT" "$end" "merge"; then
				return 1
			fi
		fi
		;;
	esac
	return 0
}

# --- Stage 8: fail-closed driver, no here-strings -----------------------
# Plain `while` over an index range in the current shell (no pipe, no
# subshell) so `break`/exit decisions are never swallowed by a subshell
# -- that was how the here-string bug (bash 3.2 needs a temp file for
# <<<, and a read-only TMPDIR makes the loop silently not run, falling
# through to exit 0) reached exit 0 instead of blocking.
seg_start=0
i=0
blocked=0
while [ "$i" -le "$SEG_N" ]; do
	if [ "$i" -eq "$SEG_N" ] || [ "${SEG_WORDS[$i]:-}" = "CMDSEP" ]; then
		if ! check_segment_range "$seg_start" "$i"; then
			blocked=1
			break
		fi
		seg_start=$((i + 1))
	fi
	i=$((i + 1))
done

if [ "$blocked" -eq 1 ]; then
	echo "$BLOCK_MSG" >&2
	exit 2
fi

exit 0

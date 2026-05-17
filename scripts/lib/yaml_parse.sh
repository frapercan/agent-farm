#!/usr/bin/env bash
# yaml_parse.sh -- tiny portable yaml field reader + duration parser.
#
# Lives in scripts/lib/ alongside common.sh so any bash script can source it.
# Source it; do not execute directly.
#
# Scope: deliberately minimal. Supports the subset of yaml needed by
# agent-farm service scripts (FARM-2.5: deploy-keeper-supervisor reads
# service.poll_interval). Pure bash + grep/awk, no python/pyyaml dep so
# the supervisor stays available even when the python env is broken.
#
# Supported yaml shape:
#   top_level_key: value
#   nested:
#     child_key: value
#     child_key2: "quoted value"
#   another_top: 123
#
# Limits:
# - Flow style ({foo: bar}) NOT supported.
# - Lists NOT supported (no `- item` parsing). Callers needing lists
#   must keep using yaml_get (python+pyyaml).
# - Indentation must be spaces (no tabs). The same constraint applies
#   to upstream yaml; we treat tabs as undefined behaviour.
# - Comments after a value (foo: bar  # comment) are stripped.
# - Single nesting level supported (one parent.child). Deeper paths
#   work but each level is greedy: the first matching key at the right
#   indent wins.

# parse_yaml_field <file> <dotted.key.path>
# Prints the bare value (no quotes, no trailing comment) to stdout.
# Returns 0 if the key resolved, non-zero if the file is missing or
# the key was not found. A missing value (`foo:` with nothing after)
# also returns non-zero; callers should treat that as "use default".
parse_yaml_field() {
  local file="$1" path="$2"
  [[ -f "$file" ]] || return 2

  # Split dotted path into segments without using arrays for portability.
  # We walk the file segment-by-segment, narrowing the search to the
  # body under the matched parent key.
  local IFS=.
  # shellcheck disable=SC2206
  local segs=($path)
  local seg_count=${#segs[@]}
  local i=0
  local indent=0
  # We accumulate a "window" of line ranges via awk. The trick: each
  # segment matches `<indent>^<key>:` and the body is the subsequent
  # lines indented strictly more than <indent>.
  local content
  content=$(<"$file")

  # Loop through segments, narrowing $content each time except the last.
  while (( i < seg_count - 1 )); do
    local key="${segs[$i]}"
    # Find the line `<indent_spaces><key>:` at current indent. Take only
    # the lines indented strictly more than indent as the new content.
    local new_content
    new_content=$(printf '%s\n' "$content" | awk -v key="$key" -v ind="$indent" '
      BEGIN { found = 0; want_ind = ind + 2 }
      {
        # Strip CR
        sub(/\r$/, "")
        # Compute leading-space count.
        match($0, /^ */)
        n = RLENGTH
        if (!found) {
          if (n == ind && $0 ~ "^"sprintf("%*s", ind, "") key ":[[:space:]]*$") {
            found = 1
            next
          }
        } else {
          # Stop when indent drops back to <= ind (and line non-empty / non-comment).
          if ($0 ~ /^[[:space:]]*$/ || $0 ~ /^[[:space:]]*#/) { print; next }
          if (n <= ind) { exit }
          print
        }
      }
    ')
    if [[ -z "$new_content" ]]; then
      return 1
    fi
    content="$new_content"
    indent=$((indent + 2))
    i=$((i + 1))
  done

  # Final segment: read the scalar value.
  local final_key="${segs[$((seg_count - 1))]}"
  local raw
  raw=$(printf '%s\n' "$content" | awk -v key="$final_key" -v ind="$indent" '
    BEGIN { pat = "^"sprintf("%*s", ind, "") key ":" }
    {
      sub(/\r$/, "")
      if ($0 ~ pat) {
        # Strip the "<spaces>key:" prefix.
        sub(pat, "")
        # Trim leading whitespace before further processing.
        sub(/^[[:space:]]+/, "")
        # If the value is quoted, take the content between the first
        # pair of matching quotes and drop anything after (including
        # comments). Otherwise strip a trailing comment after the
        # first whitespace+# run, then trim.
        if (substr($0, 1, 1) == "\"") {
          # Match up to next unescaped double-quote.
          end = index(substr($0, 2), "\"")
          if (end > 0) { $0 = substr($0, 2, end - 1) }
        } else if (substr($0, 1, 1) == "\x27") {
          end = index(substr($0, 2), "\x27")
          if (end > 0) { $0 = substr($0, 2, end - 1) }
        } else {
          sub(/[[:space:]]+#.*$/, "")
          sub(/[[:space:]]+$/, "")
        }
        print
        exit
      }
    }
  ')

  if [[ -z "$raw" ]]; then
    return 1
  fi
  printf '%s\n' "$raw"
  return 0
}

# parse_duration <duration_string>
# Converts a duration spec into integer seconds. Accepts:
#   bare integers: 30, 300, 3600
#   suffix s: 30s, 90s
#   suffix m: 5m, 30m
#   suffix h: 1h, 2h
# Prints the integer second count to stdout and returns 0 on success.
# On unparseable input prints nothing and returns 1. Empty input → rc 1.
parse_duration() {
  local raw="$1"
  # Trim whitespace.
  raw="${raw#"${raw%%[![:space:]]*}"}"
  raw="${raw%"${raw##*[![:space:]]}"}"
  [[ -z "$raw" ]] && return 1

  local num suffix
  if [[ "$raw" =~ ^([0-9]+)$ ]]; then
    printf '%d\n' "${BASH_REMATCH[1]}"
    return 0
  fi
  if [[ "$raw" =~ ^([0-9]+)([smh])$ ]]; then
    num="${BASH_REMATCH[1]}"
    suffix="${BASH_REMATCH[2]}"
    case "$suffix" in
      s) printf '%d\n' "$num" ;;
      m) printf '%d\n' "$((num * 60))" ;;
      h) printf '%d\n' "$((num * 3600))" ;;
    esac
    return 0
  fi
  return 1
}

# parse_yaml_duration <file> <dotted.key.path> <default_seconds>
# Convenience wrapper used by services. Looks up the field, parses
# it as a duration, and on any failure returns the default. The
# return code is 0 if the parse succeeded, 1 if we fell back to the
# default (so callers can emit a warn-level heartbeat).
parse_yaml_duration() {
  local file="$1" path="$2" default="$3"
  local raw
  if ! raw=$(parse_yaml_field "$file" "$path"); then
    printf '%d\n' "$default"
    return 1
  fi
  local sec
  if ! sec=$(parse_duration "$raw"); then
    printf '%d\n' "$default"
    return 1
  fi
  printf '%d\n' "$sec"
  return 0
}

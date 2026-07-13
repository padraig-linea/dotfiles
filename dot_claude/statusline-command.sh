#!/usr/bin/env bash
# Claude Code status line
# Shows: model | project dir | git branch | context usage | output style
# (colors are dimmed to match Claude Code's status-line rendering)

input=$(cat)

model=$(printf '%s' "$input" | jq -r '.model.display_name // empty')
cwd=$(printf '%s' "$input" | jq -r '.workspace.current_dir // .cwd // empty')
style=$(printf '%s' "$input" | jq -r '.output_style.name // empty')
used=$(printf '%s' "$input" | jq -r '.context_window.used_percentage // empty')

# Last path component, without relying on `basename` (which only splits on
# "/" and would leave native Windows "C:\foo\bar" paths untouched).
dir=""
if [ -n "$cwd" ]; then
    norm="${cwd//\\//}"
    norm="${norm%/}"
    dir="${norm##*/}"
fi

# Current git branch, if any. --no-optional-locks avoids blocking on / being
# blocked by another concurrent git process (e.g. a build or another prompt).
branch=""
if [ -n "$cwd" ]; then
    branch=$(git -C "$cwd" --no-optional-locks branch --show-current 2>/dev/null)
fi

# Dimmed ANSI colors
RESET=$'\033[0m'
CYAN=$'\033[2;36m'
GREEN=$'\033[2;32m'
MAGENTA=$'\033[2;35m'
YELLOW=$'\033[2;33m'
DIM=$'\033[2m'

segments=()
[ -n "$model" ] && segments+=("${CYAN}${model}${RESET}")
[ -n "$dir" ] && segments+=("${GREEN}${dir}${RESET}")
[ -n "$branch" ] && segments+=("${MAGENTA}${branch}${RESET}")

if [ -n "$used" ] && [ "$used" != "null" ]; then
    usedRounded=$(printf '%.0f' "$used" 2>/dev/null)
    [ -n "$usedRounded" ] && segments+=("${YELLOW}ctx ${usedRounded}%${RESET}")
fi

if [ -n "$style" ] && [ "$style" != "default" ] && [ "$style" != "null" ]; then
    segments+=("${DIM}${style}${RESET}")
fi

out=""
sep="${DIM} | ${RESET}"
for seg in "${segments[@]}"; do
    if [ -z "$out" ]; then
        out="$seg"
    else
        out="${out}${sep}${seg}"
    fi
done

printf '%s' "$out"
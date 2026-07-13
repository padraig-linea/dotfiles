#!/usr/bin/env bash
# Collects every project's Claude Code auto-memory (~/.claude/projects/*/memory/*.md)
# into a single portable bundle, for manual transfer to a new machine.
#
# Usage: ./export-claude-memory.sh [output-dir]
#   output-dir defaults to ./claude-memory-export-<timestamp>
#
# What this does NOT handle: each project's memory lives under a directory
# named after a *sanitized* version of that project's absolute path (e.g.
# C:\Users\name\project -> C--Users-name-project). That name will be
# different on a new machine -- especially across OSes, where the path
# syntax itself differs. This script does not try to compute or recreate
# that name; see the restore instructions it writes into the export's
# MANIFEST.md (also documented in CONFIGURATION.md).

set -euo pipefail

out="${1:-./claude-memory-export-$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$out"

manifest="$out/MANIFEST.md"
{
    echo "# Claude Code memory export ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
    echo
    echo "Each folder below is copied from a project's sanitized directory name"
    echo "under \`~/.claude/projects/\`. Directory names won't match on a new"
    echo "machine, especially across OSes."
    echo
    echo "**To restore a project's memory on the new machine:**"
    echo "1. Open that project in Claude Code there at least once first --"
    echo "   this creates the correctly-sanitized project directory for"
    echo "   wherever the project now lives, with its own empty \`memory/\`."
    echo "2. Copy this bundle's corresponding folder's \`*.md\` files into that"
    echo "   freshly-created \`memory/\` directory."
    echo
    echo "## Projects included"
    echo
} > "$manifest"

found=0
for memdir in "$HOME"/.claude/projects/*/memory; do
    [ -d "$memdir" ] || continue
    project_dir="$(basename "$(dirname "$memdir")")"
    md_count=$(find "$memdir" -maxdepth 1 -name '*.md' | wc -l)
    [ "$md_count" -gt 0 ] || continue

    mkdir -p "$out/$project_dir"
    cp "$memdir"/*.md "$out/$project_dir/"
    echo "- \`$project_dir\` — $md_count file(s)" >> "$manifest"
    found=$((found + 1))
done

if [ "$found" -eq 0 ]; then
    echo "No project memory files found under ~/.claude/projects/*/memory/." >&2
    exit 1
fi

echo "Exported $found project(s) with memory files to: $out"
echo "See $manifest for what to do with them on the new machine."

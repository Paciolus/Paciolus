#!/bin/sh

# Paciolus Sprint Archiver
# Moves completed sprints from Active Phase in tasks/todo.md to tasks/archive/.
# Safe to run anytime — exits cleanly if nothing to archive.
#
# Usage: sh scripts/archive_sprints.sh
#        sh scripts/archive_sprints.sh --check   (exit 1 if threshold exceeded, no changes)

set -e

TODO="tasks/todo.md"
ARCHIVE_DIR="tasks/archive"
THRESHOLD=5

if [ ! -f "$TODO" ]; then
  echo "ERROR: $TODO not found"
  exit 1
fi

# ── Extract the Active Phase section ──────────────────────────────────
# Find the line number of "## Active Phase" and extract everything after it
# until the next "## " heading or end of file.
ACTIVE_START=$(grep -n '^## Active Phase' "$TODO" | head -1 | cut -d: -f1)

if [ -z "$ACTIVE_START" ]; then
  echo "ERROR: No '## Active Phase' section found in $TODO"
  exit 1
fi

TOTAL_LINES=$(wc -l < "$TODO" | tr -d ' ')

# Find next ## heading after Active Phase (if any)
NEXT_HEADING=$(tail -n +"$((ACTIVE_START + 1))" "$TODO" | grep -n '^## ' | head -1 | cut -d: -f1)

if [ -n "$NEXT_HEADING" ]; then
  ACTIVE_END=$((ACTIVE_START + NEXT_HEADING - 1))
else
  ACTIVE_END=$TOTAL_LINES
fi

# ── Count completed sprints ───────────────────────────────────────────
# A completed sprint heading ends with "— COMPLETE" (or has "**Status:** COMPLETE" on a following line)
COMPLETED_SPRINTS=$(sed -n "${ACTIVE_START},${ACTIVE_END}p" "$TODO" \
  | grep -cE '(— COMPLETE$|\*\*Status:\*\* COMPLETE)' 2>/dev/null || true)
COMPLETED_SPRINTS=$(echo "$COMPLETED_SPRINTS" | tr -d '[:space:]')
COMPLETED_SPRINTS=${COMPLETED_SPRINTS:-0}

echo "Active Phase: $COMPLETED_SPRINTS completed sprint(s) (threshold: $THRESHOLD)"

if [ "$COMPLETED_SPRINTS" -lt "$THRESHOLD" ]; then
  echo "Below threshold — nothing to archive."
  exit 0
fi

# ── Check-only mode ───────────────────────────────────────────────────
if [ "$1" = "--check" ]; then
  echo ""
  echo "ERROR: Archival threshold exceeded ($COMPLETED_SPRINTS >= $THRESHOLD)."
  echo "Run: sh scripts/archive_sprints.sh"
  exit 1
fi

# ── Identify sprint numbers to archive ────────────────────────────────
# Collect sprint numbers from completed sprint sections
SPRINT_NUMBERS=$(sed -n "${ACTIVE_START},${ACTIVE_END}p" "$TODO" \
  | grep -E '(— COMPLETE$|\*\*Status:\*\* COMPLETE)' \
  | grep -oE 'Sprint [0-9]+' \
  | grep -oE '[0-9]+' \
  | sort -n)

if [ -z "$SPRINT_NUMBERS" ]; then
  echo "No completed sprint numbers found."
  exit 0
fi

FIRST_SPRINT=$(echo "$SPRINT_NUMBERS" | head -1)
LAST_SPRINT=$(echo "$SPRINT_NUMBERS" | tail -1)
ARCHIVE_FILE="$ARCHIVE_DIR/sprints-${FIRST_SPRINT}-${LAST_SPRINT}-details.md"

echo "Archiving sprints $FIRST_SPRINT–$LAST_SPRINT to $ARCHIVE_FILE"

# ── Build the archive file ────────────────────────────────────────────
mkdir -p "$ARCHIVE_DIR"

{
  echo "# Sprints ${FIRST_SPRINT}–${LAST_SPRINT} Details"
  echo ""
  echo "> Archived from \`tasks/todo.md\` Active Phase on $(date +%Y-%m-%d)."
  echo ""
  echo "---"
  echo ""
} > "$ARCHIVE_FILE"

# Extract each completed sprint section and append to archive.
# A sprint section starts with "### Sprint NNN" and ends at the next "### " or "---" divider.
ACTIVE_CONTENT=$(sed -n "${ACTIVE_START},${ACTIVE_END}p" "$TODO")

# Use awk to extract completed sprint blocks
echo "$ACTIVE_CONTENT" | awk '
  /^### Sprint [0-9]+/ {
    in_sprint = 1
    block = $0 "\n"
    next
  }
  in_sprint && /^### |^---$/ {
    # Check if this block is COMPLETE
    if (block ~ /(— COMPLETE|\*\*Status:\*\* COMPLETE)/) {
      printf "%s\n---\n\n", block
    }
    if (/^### Sprint [0-9]+/) {
      block = $0 "\n"
    } else {
      in_sprint = 0
      block = ""
    }
    next
  }
  in_sprint {
    block = block $0 "\n"
  }
  END {
    if (in_sprint && block ~ /(— COMPLETE|\*\*Status:\*\* COMPLETE)/) {
      printf "%s\n---\n\n", block
    }
  }
' >> "$ARCHIVE_FILE"

echo "Archive written: $ARCHIVE_FILE"

# ── Remove completed sprint sections from todo.md ─────────────────────
# Build a new todo.md with completed sprint sections removed from Active Phase.
# We keep everything before Active Phase, the Active Phase header + archive notes,
# any non-complete sprint sections, and everything after Active Phase.

TMPFILE=$(mktemp)

# Part 1: Everything before and including the Active Phase header line
head -n "$ACTIVE_START" "$TODO" > "$TMPFILE"

# Part 2: Archive breadcrumb notes ("> Sprints..." lines) from Active Phase
sed -n "$((ACTIVE_START + 1)),${ACTIVE_END}p" "$TODO" | grep '^>' >> "$TMPFILE" || true

# Add the new archive note
echo "> Sprints ${FIRST_SPRINT}–${LAST_SPRINT} archived to \`$ARCHIVE_FILE\`." >> "$TMPFILE"
echo "" >> "$TMPFILE"

# Part 3: Non-complete sprint sections from Active Phase
echo "$ACTIVE_CONTENT" | awk '
  /^>/ { next }  # Skip archive breadcrumbs (already handled)
  /^## Active Phase/ { next }  # Skip the heading (already handled)
  /^$/ && !in_sprint { next }  # Skip blank lines between sections when not in a sprint

  /^### Sprint [0-9]+/ || /^### Pending/ {
    if (in_sprint && block !~ /\*\*Status:\*\* COMPLETE/) {
      printf "%s", block
    }
    in_sprint = 1
    block = $0 "\n"
    next
  }
  /^---$/ {
    if (in_sprint) {
      block = block $0 "\n\n"
      if (block !~ /\*\*Status:\*\* COMPLETE/) {
        printf "%s", block
      }
      in_sprint = 0
      block = ""
    }
    next
  }
  in_sprint {
    block = block $0 "\n"
  }
  END {
    if (in_sprint && block !~ /\*\*Status:\*\* COMPLETE/) {
      printf "%s", block
    }
  }
' >> "$TMPFILE"

# Part 4: Everything after Active Phase
if [ "$ACTIVE_END" -lt "$TOTAL_LINES" ]; then
  tail -n "+$((ACTIVE_END + 1))" "$TODO" >> "$TMPFILE"
fi

mv "$TMPFILE" "$TODO"

echo ""
echo "Updated $TODO — completed sprints removed from Active Phase."
echo "Archive breadcrumb added."
echo ""
echo "Next steps:"
echo "  1. Review $ARCHIVE_FILE"
echo "  2. git add $TODO $ARCHIVE_FILE"
echo "  3. Commit with: fix: archive sprints ${FIRST_SPRINT}–${LAST_SPRINT}"

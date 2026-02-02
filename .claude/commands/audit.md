# /audit — Run the Project Auditor

Run the independent project auditor. This performs a full workflow and code quality
audit against the defined principles framework and appends a dated entry to your
audit journal.

**Usage:** `/audit`

**What this does:**
1. Gathers live project evidence (file tree, git log, key files, test status)
2. Scores your project across 3 pillars (Workflow Orchestration, Task Management, Core Principles)
3. Appends a full dated report to `audit-journal.md`
4. Prints a summary dashboard to your terminal

**Frequency:** Run this periodically — after completing a major feature, after a sprint,
or whenever you want a workflow health check. It is not meant to run on every commit.

---

!bash
```
echo "=== PRE-COMPUTING EVIDENCE FOR AUDITOR ==="
echo ""
echo "--- FILE TREE (2 levels, excluding node_modules/.git/.env) ---"
find . -maxdepth 2 \
  -not -path './node_modules*' \
  -not -path './.git*' \
  -not -path './.env*' \
  | sort

echo ""
echo "--- CLAUDE.md ---"
if [ -f "CLAUDE.md" ]; then cat CLAUDE.md; else echo "[NOT FOUND]"; fi

echo ""
echo "--- tasks/todo.md ---"
if [ -f "tasks/todo.md" ]; then cat tasks/todo.md; else echo "[NOT FOUND]"; fi

echo ""
echo "--- tasks/lessons.md ---"
if [ -f "tasks/lessons.md" ]; then cat tasks/lessons.md; else echo "[NOT FOUND]"; fi

echo ""
echo "--- .claude/agents/ ---"
if [ -d ".claude/agents" ]; then ls -la .claude/agents/; else echo "[NOT FOUND]"; fi

echo ""
echo "--- .claude/commands/ ---"
if [ -d ".claude/commands" ]; then ls -la .claude/commands/; else echo "[NOT FOUND]"; fi

echo ""
echo "--- GIT LOG (last 20) ---"
git log --oneline -20 2>/dev/null || echo "[NOT A GIT REPO OR NO COMMITS]"

echo ""
echo "--- RECENT FILE CHANGES (last 5 changed files) ---"
git diff --name-only HEAD~5 HEAD 2>/dev/null || echo "[UNABLE TO DIFF]"

echo ""
echo "--- TEST COMMAND CHECK ---"
if [ -f "package.json" ]; then
  echo "package.json test script:"
  node -e "const p=require('./package.json'); console.log(p.scripts?.test || '[no test script]')" 2>/dev/null
fi
if [ -f "Makefile" ]; then
  echo "Makefile test target:"
  grep -A2 "^test:" Makefile 2>/dev/null || echo "[no test target in Makefile]"
fi

echo ""
echo "--- EXISTING AUDIT JOURNAL ---"
if [ -f "audit-journal.md" ]; then
  echo "[Journal exists — last 30 lines for trend reference:]"
  tail -30 audit-journal.md
else
  echo "[NOT FOUND — this will be the first audit entry]"
fi

echo ""
echo "=== EVIDENCE GATHERING COMPLETE — HANDING OFF TO AUDITOR ==="
```

Now invoke the project auditor subagent. It has all the evidence above in context.
Follow its instructions exactly: score every pillar, write the journal entry, print
the terminal dashboard.

Use the agent at: `.claude/agents/project-auditor.md

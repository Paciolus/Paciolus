# Paciolus Overnight Agent System

Automated nightly system that runs 5 specialized agents between 2:00–4:00 AM and
produces a single morning briefing report at `reports/nightly/YYYY-MM-DD.md`.

## Quick Start

1. Copy `.env.overnight.example` to `.env.overnight` and fill in `ANTHROPIC_API_KEY`
2. Run `setup_scheduler.ps1` from PowerShell (Admin) once:
   ```powershell
   powershell -ExecutionPolicy Bypass -File D:\Dev\Paciolus\setup_scheduler.ps1
   ```
3. To test immediately:
   ```powershell
   Start-ScheduledTask -TaskName "Paciolus-Overnight-Agent"
   ```
4. Morning report appears at: `reports/nightly/YYYY-MM-DD.md`

## Agent Schedule

| Time | Agent | Purpose | Est. Runtime |
|------|-------|---------|-------------|
| 2:00 AM | **QA Warden** | Run backend + frontend test suites, compare to baseline | ~6 min |
| 2:15 AM | **Report Auditor** | Meridian smoke tests, known bug status tracking | ~3 min |
| 2:45 AM | **Scout** | Find CPA pain points via Claude web search | ~5 min |
| 3:30 AM | **Sprint Shepherd** | Git history analysis, sprint progress tracking | ~10 sec |
| 3:45 AM | **Dependency Sentinel** | Outdated/vulnerable dependency detection | ~1 min |
| 4:00 AM | **Briefing Compiler** | Compile all results into morning report | ~30 sec |

## Running Agents Individually

Each agent can be run standalone for testing:

```bash
# From project root
D:\Dev\Paciolus\backend\venv\Scripts\python.exe scripts/overnight/agents/qa_warden.py
D:\Dev\Paciolus\backend\venv\Scripts\python.exe scripts/overnight/agents/report_auditor.py
D:\Dev\Paciolus\backend\venv\Scripts\python.exe scripts/overnight/agents/scout.py
D:\Dev\Paciolus\backend\venv\Scripts\python.exe scripts/overnight/agents/sprint_shepherd.py
D:\Dev\Paciolus\backend\venv\Scripts\python.exe scripts/overnight/agents/dependency_sentinel.py
D:\Dev\Paciolus\backend\venv\Scripts\python.exe scripts/overnight/briefing_compiler.py
```

## Dry Run

Test the full orchestrator without executing agents or making API calls:

```bash
D:\Dev\Paciolus\backend\venv\Scripts\python.exe scripts/overnight/orchestrator.py --dry-run
```

## Adding a New Agent

1. Create `scripts/overnight/agents/my_agent.py`
2. Implement a `run()` function that returns a dict with at minimum:
   ```python
   {
       "agent": "my_agent",
       "status": "green" | "yellow" | "red",
       "summary": "one sentence description of results"
   }
   ```
3. Include a `__main__` block: `if __name__ == "__main__": print(json.dumps(run(), indent=2))`
4. Save output to `reports/nightly/.my_agent_{TODAY}.json`
5. Add to `AGENT_SCHEDULE` in `scripts/overnight/orchestrator.py`
6. Add a `_format_my_agent_section()` in `scripts/overnight/briefing_compiler.py`
7. Add `"my_agent"` to the `AGENTS` list in `briefing_compiler.py`

## File Structure

```
scripts/overnight/
  __init__.py
  config.py              # Centralized paths, env vars, bug tracker
  orchestrator.py        # Entry point (called by Task Scheduler)
  briefing_compiler.py   # Reads agent JSONs, writes morning report
  agents/
    __init__.py
    qa_warden.py         # Test suite runner + baseline comparison
    report_auditor.py    # Meridian smoke tests + bug tracking
    scout.py             # CPA lead finder via Claude web search
    sprint_shepherd.py   # Git history + sprint progress
    dependency_sentinel.py  # Outdated/vulnerable dependencies

reports/nightly/
  YYYY-MM-DD.md          # Morning briefing report (the deliverable)
  .baseline.json         # Rolling baseline for comparisons
  .qa_warden_*.json      # Agent output files (dot-prefixed)
  .report_auditor_*.json
  .scout_*.json
  .sprint_shepherd_*.json
  .dependency_sentinel_*.json
  .run_log_*.txt         # Orchestrator execution log
```

## Troubleshooting

- **Check run logs:** `reports/nightly/.run_log_YYYY-MM-DD.txt`
- **Agent didn't run:** Its section in the morning report says "AGENT DID NOT RUN"
- **API key missing:** Scout and Briefing Compiler need `ANTHROPIC_API_KEY` in `.env.overnight`
- **Tests failing:** QA Warden captures all failures — check its JSON output for details
- **Task not triggering:** Verify in Task Scheduler that "Paciolus-Overnight-Agent" exists and is enabled

## Known Bugs Tracked by Report Auditor

| ID | Description |
|----|-------------|
| BUG-001 | Suggested procedures rotation bug — procedures repeat rather than rotate across reports |
| BUG-002 | Hardcoded risk tier labels — labels do not reflect dynamic risk scoring |
| BUG-003 | PDF cell overflow — long text overflows table cells in generated PDFs |
| BUG-004 | Orphaned ASC 250-10 references — appear in reports where not applicable |
| BUG-005 | PP&E ampersand escaping — & renders as &amp; in PDF output |
| BUG-006 | Identical data quality scores — multiple reports return same score regardless of input |
| BUG-007 | Empty drill-down stubs — drill-down sections render with no content |

## Environment Variables

| Variable | Required | Used By |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes | Scout, Briefing Compiler, Dependency Sentinel |
| `REDDIT_CLIENT_ID` | No | Scout (PRAW fallback) |
| `REDDIT_CLIENT_SECRET` | No | Scout (PRAW fallback) |
| `REDDIT_USER_AGENT` | No | Scout (PRAW fallback) |

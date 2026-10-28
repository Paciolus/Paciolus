"""Briefing Compiler — reads all agent JSON outputs and writes the morning report."""

import datetime
import io
import json
import subprocess
import sys
from pathlib import Path

# Force UTF-8 stdout on Windows to handle emoji in print()
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scripts.overnight.config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    KNOWN_BUGS,
    PREFLIGHT_PATH,
    REPORT_PATH,
    REPORTS_DIR,
    RUN_MANIFEST_PATH,
    TODAY,
)

AGENTS = [
    "qa_warden",
    "report_auditor",
    "scout",
    "sprint_shepherd",
    "dependency_sentinel",
    "coverage_sentinel",
]

STATUS_EMOJI = {
    "green": "\U0001f7e2", "yellow": "\U0001f7e1", "red": "\U0001f534",
    # Sprint 854: an agent that ran but checked nothing (0 tests) is neither a
    # pass nor a failure. A white circle, never green.
    "unverified": "⚪",
}
# Worst first. `unverified` outranks `yellow`: "nothing was checked" is a
# stronger reason to look than "something is slightly off".
_STATUS_RANK = ["red", "unverified", "yellow", "green"]


def _head_sha() -> str | None:
    """
    The repository's current HEAD, or None if git cannot be read.

    Sprint 810 (finding T-4). The brief published a headline verdict with no
    record of what it was a verdict *about*. `reports/nightly/2026-10-22.md`
    reported RED with 14 failures across the two audit-gate test files; re-run
    on the tree later the same day, those same files were 60 passed / 0 failed.
    The suite runs at 02:00 and the fixes landed during the day. The DEC report
    records the identical artifact for the prior day — **two consecutive days
    where the headline verdict was wrong by clock.**

    That is worse than a stale number. A RED that is routinely a timing artifact
    trains its reader to discount RED, which is how a real one gets missed.
    """
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parent.parent.parent,
        )
    except (subprocess.CalledProcessError, OSError):
        return None
    return completed.stdout.strip() or None


def _supersession_notice(tested_sha: str | None, current_sha: str | None) -> str:
    """
    One line stating whether this verdict still describes the tree.

    `_overall_status` already carries the three-outcome shape (green / yellow /
    red). This adds the fourth thing a reader needs: whether the verdict is
    still *about* anything.
    """
    if tested_sha is None:
        return (
            "> **Tested commit unknown.** This brief cannot say which tree it describes, "
            "so its verdict cannot be confirmed to still apply."
        )

    short = tested_sha[:8]
    if current_sha is None:
        return f"> **Tested commit:** `{short}` (current HEAD could not be read)."
    if current_sha == tested_sha:
        return f"> **Tested commit:** `{short}` — still HEAD, so this verdict describes the current tree."
    return (
        f"> **SUPERSEDED.** This brief tested `{short}`; HEAD is now `{current_sha[:8]}`. "
        f"Any failure below may already be fixed — re-run before acting on the verdict. "
        f"(Finding T-4: two consecutive briefs published a RED that was a timing artifact, "
        f"because the suite runs at 02:00 and fixes land during the day.)"
    )


def _load_agent_data(agent_name: str) -> dict | None:
    """Load an agent's JSON output for today."""
    path = REPORTS_DIR / f".{agent_name}_{TODAY}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError):
        return None


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _agent_run_check(
    agent_data: dict[str, dict | None],
    manifest: dict | None,
    sentinel_mtimes: dict[str, float | None],
) -> list[dict]:
    """Sprint 854: every agent that did not complete this run, and why.

    Only 43 of 109 dormant-period nights produced a qa_warden sentinel, and
    nobody noticed: a missing agent was one RED section among six, under a
    process that exited 0. This turns each one into a named line at the top
    of the brief. Three ways an agent can fail to have run:

    - **crashed** — the orchestrator recorded a non-zero exit, timeout or
      exception (even if a sentinel exists, it may be partial);
    - **did not run** — no sentinel for today at all;
    - **stale** — a sentinel exists but predates this run's start, so it is
      left over from an earlier run today, not this one.
    """
    problems: list[dict] = []
    run_agents = (manifest or {}).get("agents", {})
    run_started = None
    if manifest and manifest.get("started_at"):
        try:
            run_started = datetime.datetime.fromisoformat(manifest["started_at"]).timestamp()
        except ValueError:
            run_started = None

    for name in AGENTS:
        rec = run_agents.get(name)
        if rec and rec.get("outcome") not in ("ok", "dry_run", None):
            exit_part = f"exit {rec['exit_code']}" if rec.get("exit_code") is not None else rec["outcome"]
            detail = rec.get("detail") or ""
            problems.append({
                "agent": name, "problem": "crashed",
                "detail": f"{exit_part}" + (f": {detail}" if detail else ""),
            })
        elif agent_data.get(name) is None:
            why = "not started by the orchestrator" if manifest and rec is None else "no sentinel written"
            problems.append({"agent": name, "problem": "did not run", "detail": why})
        elif run_started is not None:
            mtime = sentinel_mtimes.get(name)
            if mtime is not None and mtime < run_started:
                problems.append({
                    "agent": name, "problem": "stale",
                    "detail": "sentinel predates this run — left over from an earlier run",
                })
    return problems


def _overall_status(
    agent_data: dict[str, dict | None],
    preflight: dict | None = None,
    run_problems: list[dict] | None = None,
) -> str:
    """Determine overall system status from agent statuses."""
    statuses = []
    for name, data in agent_data.items():
        if data is None:
            statuses.append("red")  # Missing agent = problem
        else:
            statuses.append(data.get("status", "yellow"))
    # Sprint 854: an environment that does not match the pins, or an agent
    # that did not complete, is RED regardless of what the sentinels say.
    if preflight and preflight.get("status") == "red":
        statuses.append("red")
    if run_problems:
        statuses.append("red")

    for status in _STATUS_RANK:
        if status in statuses:
            return status
    # An unknown status string must not be read as a pass.
    return "yellow" if statuses else "red"


def _tested_as_of(manifest: dict | None, agent_data: dict[str, dict | None]) -> tuple[str | None, str | None, str]:
    """(sha, timestamp, source) for the tree the suites ran against.

    Sprint 854. The 10-28 brief's `a9dfeb69` was HEAD at 04:00, when the brief
    was compiled; the suites ran at 02:00-03:00. Prefer the SHA the
    orchestrator recorded at run start, then the one QA Warden stamped as it
    began, and only then — saying so — HEAD at compile time.
    """
    if manifest and manifest.get("head_sha"):
        return manifest["head_sha"], manifest.get("started_at"), "orchestrator run start"
    for name in ("qa_warden", "coverage_sentinel", "report_auditor"):
        d = agent_data.get(name) or {}
        if d.get("tested_sha"):
            return d["tested_sha"], d.get("tested_at"), f"{name} start"
    return None, None, "not recorded"


def _hhmm(iso: str | None) -> str:
    if not iso:
        return "unknown time"
    try:
        return datetime.datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return iso


def _preflight_block(preflight: dict | None) -> str:
    if preflight is None:
        return (
            "> **Environment pre-flight: not recorded.** This run did not sync or verify the venv, "
            "so a RED below may be an environment fault rather than a code one."
        )
    if preflight.get("status") == "red":
        return (
            f"> **ENVIRONMENT PRE-FLIGHT FAILED.** {preflight.get('summary', '')} "
            f"Test results below ran in an environment that does not match `requirements.txt` — "
            f"fix the environment before reading them as code failures."
        )
    return f"> {preflight.get('summary', 'Environment pre-flight passed.')}"


def _run_check_block(problems: list[dict]) -> str:
    total = len(AGENTS)
    if not problems:
        return f"> **Did every agent run?** Yes — {total}/{total} completed this run."
    lines = [f"> **AGENTS THAT DID NOT COMPLETE: {len(problems)} of {total}.** Their sections below are not results."]
    for p in problems:
        lines.append(f"> - `{p['agent']}` — **{p['problem']}** ({p['detail']})")
    return "\n".join(lines)


def _generate_executive_summary(agent_data: dict[str, dict | None], overall: str) -> str:
    """Use Claude to generate a natural-language executive summary."""
    if not ANTHROPIC_API_KEY:
        # Fallback: build summary from agent summaries
        parts = []
        for name, data in agent_data.items():
            if data:
                parts.append(data.get("summary", f"{name}: no summary"))
            else:
                parts.append(f"{name}: did not run")
        return " ".join(parts)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        context = json.dumps(
            {k: (v if v else {"status": "DID_NOT_RUN"}) for k, v in agent_data.items()},
            indent=2, default=str,
        )

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": (
                    f"You are writing the executive summary for the Paciolus overnight "
                    f"agent report dated {TODAY}. Overall status: {overall}.\n\n"
                    f"Agent results:\n{context}\n\n"
                    f"Write a 3-5 sentence executive summary as if briefing a CPA founder "
                    f"starting their morning. Tone: direct, professional, no fluff. "
                    f"Mention the most important findings first. Plain text, no markdown."
                ),
            }],
        )
        for block in response.content:
            if hasattr(block, "text"):
                return block.text.strip()
    except Exception as e:
        print(f"  Warning: Claude summary generation failed: {e}")

    # Fallback
    parts = []
    for name, data in agent_data.items():
        if data:
            parts.append(data.get("summary", ""))
    return " ".join(parts)


def _format_qa_section(data: dict | None) -> str:
    """Format QA Warden section."""
    if not data:
        return (
            f"## \U0001f9ea QA Warden — \U0001f534 AGENT DID NOT RUN\n"
            f"\u26a0\ufe0f Agent did not produce output — check run log.\n"
        )

    e = STATUS_EMOJI.get(data.get("status", "red"), "\U0001f534")
    be = data.get("backend", {})
    fe = data.get("frontend", {})

    lines = [
        f"## \U0001f9ea QA Warden — {e} {data.get('status', 'unknown').upper()}",
        f"**Backend:** {be.get('passed', 0)} passed, {be.get('failed', 0)} failed ({be.get('duration_s', 0)}s)  ",
        (
            f"**Frontend:** \U0001f534 DID NOT RUN — {fe['did_not_run']}  "
            if fe.get("did_not_run") else
            f"**Frontend:** {fe.get('passed', 0)} passed, {fe.get('failed', 0)} failed ({fe.get('duration_s', 0)}s)  "
        ),
    ]
    if be.get("collection_error"):
        lines.append("**Backend collection FAILED** — the suite did not run; see the run log.  ")
    if data.get("tested_sha"):
        lines.append(f"**Tested:** `{data['tested_sha'][:8]}` at {_hhmm(data.get('tested_at'))}  ")

    new_failures = be.get("new_failures", [])
    if new_failures:
        lines.append(f"\n\u26a0\ufe0f **NEW FAILURES SINCE YESTERDAY:**")
        for f in new_failures:
            lines.append(f"- `{f}`")

    resolved = be.get("resolved", [])
    if resolved:
        lines.append(f"\n\u2705 **RESOLVED SINCE YESTERDAY:**")
        for r in resolved:
            lines.append(f"- `{r}`")

    return "\n".join(lines)


def _format_report_auditor_section(data: dict | None) -> str:
    """Format Report Auditor section."""
    if not data:
        return (
            f"## \U0001f4cb Report Auditor — \U0001f534 AGENT DID NOT RUN\n"
            f"\u26a0\ufe0f Agent did not produce output — check run log.\n"
        )

    e = STATUS_EMOJI.get(data.get("status", "red"), "\U0001f534")
    mt = data.get("meridian_tests", {})
    total = mt.get("passed", 0) + mt.get("failed", 0)

    lines = [
        f"## \U0001f4cb Report Auditor — {e} {data.get('status', 'unknown').upper()}",
        f"**Meridian Tests:** {mt.get('passed', 0)}/{total} passing  ",
        f"**Open Bugs:** {data.get('open_bug_count', '?')}/{len(KNOWN_BUGS)} confirmed open\n",
        "| Bug | Description | Status | Changed Today |",
        "|-----|-------------|--------|---------------|",
    ]

    bt = data.get("bug_tracker", {})
    for bug_id in sorted(bt.keys()):
        bug = bt[bug_id]
        changed = "yes" if bug.get("changed_today") else "no"
        lines.append(
            f"| {bug_id} | {bug.get('description', '')} | {bug.get('status', '?')} | {changed} |"
        )

    return "\n".join(lines)


def _format_scout_section(data: dict | None) -> str:
    """Format Scout section."""
    if not data:
        return (
            f"## \U0001f50d Scout — \U0001f534 AGENT DID NOT RUN\n"
            f"\u26a0\ufe0f Agent did not produce output — check run log.\n"
        )

    e = STATUS_EMOJI.get(data.get("status", "green"), "\U0001f7e2")

    lines = [
        f"## \U0001f50d Scout — {e} {data.get('status', 'unknown').upper()}",
        f"**Leads found:** {data.get('total_leads', 0)} across 5 search themes\n",
        "| # | Platform | Pain Point | Paciolus Feature | Urgency | Decision Maker |",
        "|---|----------|-----------|-----------------|---------|----------------|",
    ]

    leads = data.get("leads", [])[:10]
    for i, lead in enumerate(leads, 1):
        dm = "\u2705" if lead.get("is_decision_maker") else ""
        lines.append(
            f"| {i} | {lead.get('platform', '?')} | "
            f"{lead.get('pain_point', '?')[:60]} | "
            f"{lead.get('paciolus_solution', '?')[:40]} | "
            f"{lead.get('urgency_score', '?')} | {dm} |"
        )

    return "\n".join(lines)


def _format_sprint_section(data: dict | None) -> str:
    """Format Sprint Shepherd section."""
    if not data:
        return (
            f"## \U0001f3c3 Sprint Shepherd — \U0001f534 AGENT DID NOT RUN\n"
            f"\u26a0\ufe0f Agent did not produce output — check run log.\n"
        )

    e = STATUS_EMOJI.get(data.get("status", "green"), "\U0001f7e2")
    cl = data.get("sprint_checklist", {})

    lines = [
        f"## \U0001f3c3 Sprint Shepherd — {e} {data.get('status', 'unknown').upper()}",
        f"**Commits (24h):** {data.get('commits_last_24h', 0)} | **Commits (7d):** {data.get('commits_last_7d', 0)}  ",
    ]

    if cl.get("found"):
        lines.append(
            f"**Sprint progress:** {cl.get('completed', 0)}/{cl.get('total', 0)} "
            f"items complete ({cl.get('pct', 0)}%)  "
        )

    cats = data.get("work_categories_24h", {})
    if cats:
        cat_str = ", ".join(f"{k}: {v}" for k, v in cats.items())
        lines.append(f"**Work breakdown (24h):** {cat_str}  ")

    risk = data.get("risk_commits", [])
    if risk:
        lines.append(f"\n\u26a0\ufe0f **Risk signals:**")
        for r in risk:
            lines.append(f"- `{r['hash']}` {r['message']} (keyword: {r['keyword']})")

    open_items = data.get("open_items", [])
    if open_items:
        lines.append(f"\n\U0001f4cc **Open sprint items:**")
        for item in open_items:
            lines.append(f"- [ ] {item}")

    return "\n".join(lines)


def _format_dependency_section(data: dict | None) -> str:
    """Format Dependency Sentinel section."""
    if not data:
        return (
            f"## \U0001f4e6 Dependency Sentinel — \U0001f534 AGENT DID NOT RUN\n"
            f"\u26a0\ufe0f Agent did not produce output — check run log.\n"
        )

    e = STATUS_EMOJI.get(data.get("status", "green"), "\U0001f7e2")

    lines = [
        f"## \U0001f4e6 Dependency Sentinel — {e} {data.get('status', 'unknown').upper()}",
        f"**Backend outdated:** {len(data.get('backend_outdated', []))} packages | "
        f"**Frontend outdated:** {len(data.get('frontend_outdated', []))} packages  ",
    ]

    security = data.get("security_flagged", [])
    if security:
        lines.append(f"\n\U0001f512 **Security-relevant updates available:**")
        for p in security:
            lines.append(f"- **{p['package']}**: {p['current']} \u2192 {p['latest']} ({p['severity']})")

    # Deferred packages — shown for transparency but don't affect status
    deferred = data.get("deferred", [])
    if deferred:
        lines.append(f"\n**Deferred ({len(deferred)}):** monitored, not affecting status")
        for p in deferred:
            reason = p.get("deferral_reason", "")
            review = p.get("deferral_review_by", "")
            review_note = f" (review by {review})" if review else ""
            lines.append(
                f"- ~{p['package']}~ {p['current']} \u2192 {p['latest']} — {reason}{review_note}"
            )

    # Show ALL outdated packages (not just top 5) so nothing is silently hidden.
    # Notes are only generated for top-5 by the sentinel (API cost control).
    all_pkgs = data.get("backend_outdated", []) + data.get("frontend_outdated", [])
    # Exclude deferred packages from the main table (they're shown above)
    deferred_names = {p["package"] for p in deferred}
    actionable_pkgs = [p for p in all_pkgs if p["package"] not in deferred_names]
    note_map = {p["package"]: p.get("note", "") for p in data.get("top5_updates", [])}
    if actionable_pkgs:
        severity_order = {"major": 0, "minor": 1, "patch": 2}
        actionable_pkgs.sort(key=lambda p: severity_order.get(p.get("severity", ""), 3))
        lines.append(f"\n| Package | Current | Latest | Severity | Note |")
        lines.append(f"|---------|---------|--------|----------|------|")
        for p in actionable_pkgs:
            note = note_map.get(p["package"], "")[:60]
            lines.append(
                f"| {p['package']} | {p['current']} | {p['latest']} | {p['severity']} | {note} |"
            )

    return "\n".join(lines)


def _format_coverage_section(data: dict | None) -> str:
    """Format Coverage Sentinel section (Sprint 599)."""
    if not data:
        return (
            f"## \U0001f4ca Coverage Sentinel — \U0001f534 AGENT DID NOT RUN\n"
            f"\u26a0\ufe0f Agent did not produce output — check run log.\n"
        )

    if "error" in data and "percent_covered" not in data:
        e = STATUS_EMOJI.get("red", "\U0001f534")
        return (
            f"## \U0001f4ca Coverage Sentinel — {e} RED\n"
            f"\u26a0\ufe0f Coverage run failed: `{data.get('error', 'unknown')}`\n"
        )

    e = STATUS_EMOJI.get(data.get("status", "green"), "\U0001f7e2")
    pct = data.get("percent_covered", 0.0)
    covered = data.get("covered_lines", 0)
    total = data.get("num_statements", 0)
    missing = data.get("missing_lines", 0)
    mean_pct = data.get("rolling_mean_pct")
    delta = data.get("delta_pp")
    window = data.get("rolling_window_days", 7)

    lines = [
        f"## \U0001f4ca Coverage Sentinel — {e} {data.get('status', 'unknown').upper()}",
        f"**Backend line coverage:** {pct:.2f}% "
        f"({covered:,}/{total:,} statements, {missing:,} uncovered)  ",
    ]

    if mean_pct is not None and delta is not None:
        sign = "+" if delta >= 0 else ""
        arrow = "\u2193" if delta < 0 else "\u2191" if delta > 0 else "\u2192"
        lines.append(
            f"**{window}-day mean:** {mean_pct:.2f}%  |  "
            f"**Delta:** {arrow} {sign}{delta:.2f}pp  "
        )
    else:
        lines.append(f"**{window}-day mean:** _building baseline (need more runs)_  ")

    reasons = data.get("reasons", [])
    if reasons:
        lines.append("")
        lines.append("\u26a0\ufe0f **Flags:**")
        for r in reasons:
            lines.append(f"- {r}")

    top_uncovered = data.get("top_uncovered_files", [])
    if top_uncovered:
        lines.append("")
        lines.append("**Top uncovered files** (by missing statement count):")
        lines.append("")
        lines.append("| File | Coverage | Missing | Statements |")
        lines.append("|------|---------:|--------:|-----------:|")
        for f in top_uncovered[:10]:
            path = f.get("path", "?")
            fpct = f.get("percent_covered", 0.0)
            fmissing = f.get("missing_lines", 0)
            fstmts = f.get("num_statements", 0)
            lines.append(f"| `{path}` | {fpct:.1f}% | {fmissing:,} | {fstmts:,} |")

    return "\n".join(lines)


def run() -> dict:
    """Compile the morning briefing report."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load all agent data
    agent_data: dict[str, dict | None] = {}
    for name in AGENTS:
        agent_data[name] = _load_agent_data(name)

    # Sprint 854: the orchestrator's record of this run, and the env pre-flight.
    manifest = _load_json(RUN_MANIFEST_PATH)
    preflight = _load_json(PREFLIGHT_PATH)
    sentinel_mtimes = {}
    for name in AGENTS:
        p = REPORTS_DIR / f".{name}_{TODAY}.json"
        sentinel_mtimes[name] = p.stat().st_mtime if p.exists() else None
    run_problems = _agent_run_check(agent_data, manifest, sentinel_mtimes)

    agents_run = sum(1 for d in agent_data.values() if d is not None)
    overall = _overall_status(agent_data, preflight, run_problems)
    overall_emoji = STATUS_EMOJI.get(overall, "\U0001f534")

    # Executive summary. The pre-flight leads, so an environment fault is the
    # first thing said rather than being narrated as a test failure.
    exec_summary = _generate_executive_summary(
        {"env_preflight": preflight, **agent_data}, overall,
    )

    # Compute tomorrow's date
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    # Sprint 810 (T-4) + Sprint 854: record the commit this verdict is about —
    # as of when the suites ran, not when this brief was compiled — and state
    # plainly whether it still describes the tree.
    compiled_at = datetime.datetime.now()
    current_sha = _head_sha()
    tested_sha, tested_at, tested_source = _tested_as_of(manifest, agent_data)
    if tested_sha is None and current_sha is not None:
        tested_line = (
            f"`{current_sha}` — **HEAD at brief compile time ({compiled_at:%H:%M})**, not when the "
            f"suites ran: this run did not record the commit it tested, so the verdict may be stale."
        )
        supersession = _supersession_notice(None, current_sha)
    else:
        tested_line = f"`{tested_sha or 'unknown'}` as of {_hhmm(tested_at)} ({tested_source})"
        supersession = _supersession_notice(tested_sha, current_sha)

    # Build the report
    total_agents = len(AGENTS)
    report = f"""# \U0001f305 Paciolus Overnight Brief — {TODAY}
**Overall Status:** {overall_emoji} {overall.upper()}
**Report generated:** {compiled_at.strftime('%Y-%m-%d %H:%M')} | **Agents run:** {agents_run}/{total_agents}
**Tested commit:** {tested_line}

{supersession}

{_preflight_block(preflight)}

{_run_check_block(run_problems)}

{exec_summary}

---

{_format_qa_section(agent_data.get('qa_warden'))}

---

{_format_report_auditor_section(agent_data.get('report_auditor'))}

---

{_format_coverage_section(agent_data.get('coverage_sentinel'))}

---

{_format_scout_section(agent_data.get('scout'))}

---

{_format_sprint_section(agent_data.get('sprint_shepherd'))}

---

{_format_dependency_section(agent_data.get('dependency_sentinel'))}

---
*Next run: tomorrow at 2:00 AM | Output: reports/nightly/{tomorrow}.md*
---
"""

    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\u2705 Morning brief written to reports/nightly/{TODAY}.md")

    return {
        "agent": "briefing_compiler",
        "status": overall,
        # Sprint 810 (T-4): so a consumer of this payload — the report auditor
        # above all — can tell whether the verdict still describes the tree.
        "tested_sha": tested_sha,
        "tested_at": tested_at,
        "preflight_status": (preflight or {}).get("status"),
        "run_problems": run_problems,
        "agents_run": agents_run,
        "report_path": str(REPORT_PATH),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))

"""Briefing Compiler — reads all agent JSON outputs and writes the morning report."""

import datetime
import io
import json
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
    REPORTS_DIR,
    REPORT_PATH,
    TODAY,
)

AGENTS = ["qa_warden", "report_auditor", "scout", "sprint_shepherd", "dependency_sentinel"]

STATUS_EMOJI = {"green": "\U0001f7e2", "yellow": "\U0001f7e1", "red": "\U0001f534"}


def _load_agent_data(agent_name: str) -> dict | None:
    """Load an agent's JSON output for today."""
    path = REPORTS_DIR / f".{agent_name}_{TODAY}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError):
        return None


def _overall_status(agent_data: dict[str, dict | None]) -> str:
    """Determine overall system status from agent statuses."""
    statuses = []
    for name, data in agent_data.items():
        if data is None:
            statuses.append("red")  # Missing agent = problem
        else:
            statuses.append(data.get("status", "yellow"))

    if "red" in statuses:
        return "red"
    if "yellow" in statuses:
        return "yellow"
    return "green"


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
        f"**Frontend:** {fe.get('passed', 0)} passed, {fe.get('failed', 0)} failed ({fe.get('duration_s', 0)}s)  ",
    ]

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

    # Show ALL outdated packages (not just top 5) so nothing is silently hidden.
    # Notes are only generated for top-5 by the sentinel (API cost control).
    all_pkgs = data.get("backend_outdated", []) + data.get("frontend_outdated", [])
    note_map = {p["package"]: p.get("note", "") for p in data.get("top5_updates", [])}
    if all_pkgs:
        severity_order = {"major": 0, "minor": 1, "patch": 2}
        all_pkgs.sort(key=lambda p: severity_order.get(p.get("severity", ""), 3))
        lines.append(f"\n| Package | Current | Latest | Severity | Note |")
        lines.append(f"|---------|---------|--------|----------|------|")
        for p in all_pkgs:
            note = note_map.get(p["package"], "")[:60]
            lines.append(
                f"| {p['package']} | {p['current']} | {p['latest']} | {p['severity']} | {note} |"
            )

    return "\n".join(lines)


def run() -> dict:
    """Compile the morning briefing report."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load all agent data
    agent_data: dict[str, dict | None] = {}
    for name in AGENTS:
        agent_data[name] = _load_agent_data(name)

    agents_run = sum(1 for d in agent_data.values() if d is not None)
    overall = _overall_status(agent_data)
    overall_emoji = STATUS_EMOJI.get(overall, "\U0001f534")

    # Executive summary
    exec_summary = _generate_executive_summary(agent_data, overall)

    # Compute tomorrow's date
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    # Build the report
    report = f"""# \U0001f305 Paciolus Overnight Brief — {TODAY}
**Overall Status:** {overall_emoji} {overall.upper()}
**Report generated:** {datetime.datetime.now().strftime('%I:%M %p')} | **Agents run:** {agents_run}/5

{exec_summary}

---

{_format_qa_section(agent_data.get('qa_warden'))}

---

{_format_report_auditor_section(agent_data.get('report_auditor'))}

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
        "agents_run": agents_run,
        "report_path": str(REPORT_PATH),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))

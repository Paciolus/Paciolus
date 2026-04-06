"""Scout — finds CPAs publicly expressing pain points that Paciolus solves."""

import io
import json
import sys
import time
from pathlib import Path

# Force UTF-8 stdout on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from scripts.overnight.config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    REPORTS_DIR,
    TODAY,
    require_anthropic_key,
)

SEARCH_THEMES = [
    "CPA accountant complaining manual reconciliation Excel trial balance hours",
    "accountant audit trail documentation gap workpaper chaos r/taxpros OR r/accounting",
    "CPA frustrated journal entry testing manual sampling site:reddit.com",
    "small CPA firm audit software too expensive manual process 2025 2026",
    "accountant engagement letter workpaper chaos audit prep time r/taxpros",
]

SYSTEM_PROMPT = (
    "You are a market research analyst for Paciolus, an AI-powered financial audit SaaS "
    "platform for CPAs. Search the web for the given query and find real social media posts, "
    "forum threads, or public comments where CPAs, accountants, or auditors express genuine "
    "pain around the search topic. Return ONLY valid JSON — no markdown, no preamble — in "
    "this exact format:\n"
    '{\n'
    '  "leads": [\n'
    '    {\n'
    '      "platform": "Reddit|LinkedIn|Twitter|Forum|Other",\n'
    '      "url": "direct URL if available",\n'
    '      "username": "poster username or handle if public",\n'
    '      "pain_point": "one sentence describing what they are complaining about",\n'
    '      "paciolus_solution": "which Paciolus feature addresses this",\n'
    '      "urgency_score": 1,\n'
    '      "is_decision_maker": true,\n'
    '      "raw_quote": "brief paraphrase of what they said, under 30 words"\n'
    '    }\n'
    '  ],\n'
    '  "search_theme": "name of this theme"\n'
    '}\n'
    "Return up to 5 leads per theme. If no genuine leads found, return leads as empty array."
)


def _search_with_claude(query: str) -> list[dict]:
    """Run a single Claude web-search API call and return parsed leads."""
    import anthropic

    client = anthropic.Anthropic(api_key=require_anthropic_key())

    try:
        # Use Haiku for Scout — much higher rate limits on Tier 1
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
            messages=[{"role": "user", "content": query}],
        )

        # Extract text content from response
        text_content = ""
        for block in response.content:
            if hasattr(block, "text"):
                text_content += block.text

        if not text_content.strip():
            return []

        # Parse JSON from response — try multiple extraction strategies
        clean = text_content.strip()

        # Strategy 1: strip markdown code fences
        if "```" in clean:
            import re as _re
            m = _re.search(r"```(?:json)?\s*\n?(.*?)```", clean, _re.DOTALL)
            if m:
                clean = m.group(1).strip()

        # Strategy 2: find the first { ... } JSON object
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1 and end > start:
            clean = clean[start:end + 1]

        data = json.loads(clean)
        return data.get("leads", [])

    except (json.JSONDecodeError, KeyError) as e:
        print(f"  Warning: failed to parse Claude response for query: {e}")
        return []
    except Exception as e:
        print(f"  Warning: Claude API call failed: {e}")
        return []


def _search_with_praw() -> list[dict]:
    """Optional: search Reddit directly via PRAW if credentials are available."""
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        return []

    try:
        import praw
    except ImportError:
        print("  PRAW not installed — skipping Reddit direct search.")
        return []

    leads: list[dict] = []
    keywords = ["reconciliation", "audit trail", "journal entry", "workpaper", "engagement letter"]

    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )

        for sub_name in ["taxpros", "accounting"]:
            subreddit = reddit.subreddit(sub_name)
            for keyword in keywords:
                for post in subreddit.search(keyword, time_filter="week", limit=3):
                    leads.append({
                        "platform": "Reddit-PRAW",
                        "url": f"https://reddit.com{post.permalink}",
                        "username": str(post.author) if post.author else "unknown",
                        "pain_point": post.title[:120],
                        "paciolus_solution": "auto-detected",
                        "urgency_score": 3,
                        "is_decision_maker": False,
                        "raw_quote": (post.selftext[:100] + "...") if post.selftext else post.title[:100],
                    })
    except Exception as e:
        print(f"  PRAW search failed: {e}")

    return leads


def _deduplicate(leads: list[dict]) -> list[dict]:
    """Remove duplicate leads by URL."""
    seen_urls: set[str] = set()
    unique: list[dict] = []
    for lead in leads:
        url = lead.get("url", "")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        unique.append(lead)
    return unique


def run() -> dict:
    """Execute Scout and return structured results."""
    t0 = time.time()

    all_leads: list[dict] = []

    if not ANTHROPIC_API_KEY:
        print("WARNING: ANTHROPIC_API_KEY not set — Scout cannot run Claude searches.")
        print("Set it in .env.overnight or export it before running.")
    else:
        for i, theme in enumerate(SEARCH_THEMES, 1):
            print(f"  Searching theme {i}/5: {theme[:60]}...")
            leads = _search_with_claude(theme)
            all_leads.extend(leads)
            print(f"    Found {len(leads)} leads.")
            # Pause between API calls to respect rate limits
            # Web search calls use ~15-20k tokens; limit is 30k/min
            if i < len(SEARCH_THEMES):
                time.sleep(65)

    # PRAW fallback
    praw_leads = _search_with_praw()
    if praw_leads:
        print(f"  PRAW found {len(praw_leads)} additional leads.")
        all_leads.extend(praw_leads)

    # Deduplicate and sort
    all_leads = _deduplicate(all_leads)
    all_leads.sort(key=lambda x: x.get("urgency_score", 0), reverse=True)
    all_leads = all_leads[:20]  # Cap at 20

    # Determine top platform
    platforms: dict[str, int] = {}
    for lead in all_leads:
        p = lead.get("platform", "Unknown")
        platforms[p] = platforms.get(p, 0) + 1
    top_platform = max(platforms, key=platforms.get) if platforms else "none"

    top_urgency = ""
    if all_leads:
        top_lead = all_leads[0]
        top_urgency = top_lead.get("pain_point", "")[:80]

    result = {
        "agent": "scout",
        "status": "green",
        "total_leads": len(all_leads),
        "leads": all_leads,
        "summary": (
            f"Found {len(all_leads)} leads across 5 themes. "
            f"Top platform: {top_platform}. "
            f"Highest urgency: {top_urgency}"
        ),
    }

    out_path = REPORTS_DIR / f".scout_{TODAY}.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    elapsed = round(time.time() - t0, 1)
    print(f"Scout completed in {elapsed}s — {len(all_leads)} leads found.")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

"""Council 2026-11-25 L-1: the formats the website names are the formats the upload accepts.

The homepage and About page listed ODS, which is off by default (``FORMAT_ODS_ENABLED``),
and did not name Word, which is on. Format lists on marketing pages are now checked against
``upload_capabilities()`` — the same source the upload pickers use. The Terms are corrected
through counsel (Sprint 863) and are not scanned here.
"""

import re
from pathlib import Path

from routes.upload_capabilities import upload_capabilities
from shared.file_formats import FORMAT_PROFILES, FileFormat, is_format_enabled

REPO = Path(__file__).resolve().parents[2]

# Every marketing sentence that lists the accepted upload formats.
FORMAT_LIST_FILES = (
    "frontend/src/app/(marketing)/about/page.tsx",
    "frontend/src/components/marketing/ProcessTimeline.tsx",
)

# How each format is named in prose.
PROSE_NAME = {
    FileFormat.ODS: "ODS",
    FileFormat.DOCX: "Word",
}

COUNT_WORDS = {"ten": 10, "nine": 9, "eleven": 11, "twelve": 12}


def _text(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def test_disabled_formats_are_not_advertised():
    for fmt, name in PROSE_NAME.items():
        if FORMAT_PROFILES[fmt].parse_supported and is_format_enabled(fmt):
            continue
        for rel in FORMAT_LIST_FILES:
            assert not re.search(rf"\b{name}\b", _text(rel)), f"{rel} names {name}, which uploads refuse"


def test_enabled_formats_are_named():
    for fmt, name in PROSE_NAME.items():
        if not (FORMAT_PROFILES[fmt].parse_supported and is_format_enabled(fmt)):
            continue
        for rel in FORMAT_LIST_FILES:
            assert re.search(rf"\b{name}\b", _text(rel)), f"{rel} does not name {name}, which uploads accept"


def test_stated_format_count_matches_capabilities():
    enabled = len(upload_capabilities().formats)
    for rel in FORMAT_LIST_FILES:
        for match in re.finditer(r"\b(\d+|[Tt]en|[Nn]ine|[Ee]leven|[Tt]welve) (?:file )?formats\b", _text(rel)):
            word = match.group(1).lower()
            stated = int(word) if word.isdigit() else COUNT_WORDS[word]
            assert stated == enabled, f"{rel} says {stated} formats; uploads accept {enabled}"

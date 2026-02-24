"""
Report Standardization — Public API

Sprint 2: Re-exports from report_chrome.py and report_styles.py.
Import from here for the cleanest API:

    from shared.report_standardization import (
        ReportMetadata, build_cover_page, draw_page_footer, find_logo,
        FONT_TITLE, FONT_BODY, ClassicalColors,
    )
"""

from shared.report_chrome import (
    ReportMetadata,
    build_cover_page,
    draw_page_footer,
    draw_page_header,
    find_logo,
)
from shared.report_styles import (
    FONT_BODY,
    FONT_ITALIC,
    FONT_MONO,
    FONT_TITLE,
    MARGIN_BOTTOM,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    MARGIN_TOP,
    SIZE_BODY,
    SIZE_DISCLAIMER,
    SIZE_DISPLAY,
    SIZE_FOOTER,
    SIZE_SECTION,
    SIZE_SMALL,
    SIZE_TABLE,
    SIZE_TITLE,
    SPACE_BODY_AFTER,
    SPACE_COVER_AFTER_LOGO,
    SPACE_COVER_AFTER_RULE,
    SPACE_COVER_AFTER_TITLE,
    SPACE_FOOTER_Y,
    SPACE_SECTION_AFTER,
    SPACE_SECTION_BEFORE,
    ClassicalColors,
    ledger_table_style,
)

__all__ = [
    # report_chrome
    "ReportMetadata",
    "build_cover_page",
    "draw_page_footer",
    "draw_page_header",
    "find_logo",
    # report_styles — fonts
    "FONT_TITLE",
    "FONT_BODY",
    "FONT_ITALIC",
    "FONT_MONO",
    # report_styles — sizes
    "SIZE_DISPLAY",
    "SIZE_TITLE",
    "SIZE_SECTION",
    "SIZE_BODY",
    "SIZE_TABLE",
    "SIZE_FOOTER",
    "SIZE_DISCLAIMER",
    "SIZE_SMALL",
    # report_styles — spacing
    "SPACE_COVER_AFTER_LOGO",
    "SPACE_COVER_AFTER_TITLE",
    "SPACE_COVER_AFTER_RULE",
    "SPACE_SECTION_BEFORE",
    "SPACE_SECTION_AFTER",
    "SPACE_BODY_AFTER",
    "SPACE_FOOTER_Y",
    # report_styles — margins
    "MARGIN_LEFT",
    "MARGIN_RIGHT",
    "MARGIN_TOP",
    "MARGIN_BOTTOM",
    # report_styles — colors + helpers
    "ClassicalColors",
    "ledger_table_style",
]

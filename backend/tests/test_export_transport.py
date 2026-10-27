"""Sprint 817: build_streaming_response accepts exactly the formats its callers pass.

Every caller in ``export/pipeline.py`` passes a literal "pdf", "xlsx" or "csv";
the never-used "excel" alias (which would also have produced a ``.excel``
download name) was removed.
"""

import pytest

from export.transport import build_streaming_response


@pytest.mark.parametrize(
    "fmt,media_prefix",
    [
        ("pdf", "application/pdf"),
        ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("csv", "text/csv"),
    ],
)
def test_supported_formats(fmt, media_prefix):
    response = build_streaming_response(b"x", source_filename="tb.csv", filename_suffix="Diagnostic", fmt=fmt)
    assert response.media_type.startswith(media_prefix)
    assert f".{fmt}" in response.headers["content-disposition"]


@pytest.mark.parametrize("fmt", ["excel", "xls", "docx", ""])
def test_unsupported_format_raises(fmt):
    with pytest.raises(ValueError, match="Unsupported export format"):
        build_streaming_response(b"x", source_filename="tb.csv", filename_suffix="Diagnostic", fmt=fmt)

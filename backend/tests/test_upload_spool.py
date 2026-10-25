"""Sprint 840: uploads are not spooled to disk below the request-body cap."""

from starlette.datastructures import Headers
from starlette.formparsers import MultiPartParser


def test_spool_threshold_matches_the_body_cap():
    import main  # noqa: F401 — the setting is applied at app import
    from security_middleware import MAX_REQUEST_BODY_BYTES

    assert MultiPartParser.spool_max_size == MAX_REQUEST_BODY_BYTES


def test_a_5_mb_part_stays_in_memory():
    import asyncio

    import main  # noqa: F401

    boundary = "xyz"
    payload = b"a" * (5 * 1024 * 1024)
    body = (
        (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="tb.csv"\r\n'
            "Content-Type: text/csv\r\n\r\n"
        ).encode()
        + payload
        + f"\r\n--{boundary}--\r\n".encode()
    )

    async def stream():
        yield body

    parser = MultiPartParser(Headers({"content-type": f"multipart/form-data; boundary={boundary}"}), stream())
    form = asyncio.run(parser.parse())
    upload = form["file"]
    assert upload.file._rolled is False  # SpooledTemporaryFile never rolled over to disk
    assert upload.size == len(payload)

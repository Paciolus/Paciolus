"""Invalidate pre-Sprint-696 SHA-256 passcode shares (admin one-shot).

Context:
    Sprint 696 moved export-share passcode storage from SHA-256 hex to
    bcrypt, and Sprint 697 subsequently upgraded to Argon2id.  Any
    ``export_shares`` row whose ``passcode_hash`` is still a 64-char hex
    string (SHA-256) was created before the 2026-04-20 hardening and
    cannot be verified by the new code — the application rejects those
    rows at verification time and returns 403.

    Shares auto-expire within 24-48h TTL, so legacy rows drain within
    one weekend post-deploy.  This script makes the invariant explicit:
    rather than let users hit silent 403s until expiry, it proactively
    revokes affected rows so that

    1. the owner sees the share as "revoked" in their dashboard and can
       re-issue with a fresh Argon2id passcode,
    2. audit logs record a single ``legacy_passcode_invalidation`` event
       per deploy instead of N ``passcode_mismatch`` per failed
       recipient download.

Usage (from backend/):
    # Dry run — prints affected share IDs + owner user IDs, no writes:
    python scripts/invalidate_legacy_passcode_shares.py

    # Apply — revokes the rows and commits:
    python scripts/invalidate_legacy_passcode_shares.py --apply

    # Verbose (also prints per-row details on stdout):
    python scripts/invalidate_legacy_passcode_shares.py --apply --verbose

Environment:
    Reads ``DATABASE_URL`` from the same .env as the app.  Works on
    SQLite (dev) and PostgreSQL (prod).

Exit codes:
    0 — success (any number of rows affected)
    1 — precondition failure (DB connect, model import)
    2 — user aborted (answered 'n' at the apply confirmation prompt)
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from datetime import UTC, datetime

_SHA256_HEX_RE = re.compile(r"^[a-fA-F0-9]{64}$")


def _is_legacy_sha256(passcode_hash: str | None) -> bool:
    """A 64-char hex string that is NOT a bcrypt hash.

    bcrypt output always starts with ``$2a$`` / ``$2b$`` / ``$2y$``,
    Argon2id with ``$argon2id$``.  The legacy SHA-256 format is a bare
    64-char hex digest with no ``$`` prefix.  Guarding with the regex
    prevents false-positives on any future hash format that might be
    bcrypt-style but happen to be 64 chars long.
    """
    if not passcode_hash:
        return False
    if passcode_hash.startswith(("$2a$", "$2b$", "$2y$", "$argon2")):
        return False
    return bool(_SHA256_HEX_RE.match(passcode_hash))


def find_legacy_shares(db):
    """Return the list of live export_shares with legacy SHA-256 passcodes.

    A share is "live" if ``revoked_at`` is null — expired-but-not-revoked
    rows are also included so the secure_event stays honest about the
    total invalidated count.
    """
    from export_share_model import ExportShare

    candidates = (
        db.query(ExportShare)
        .filter(
            ExportShare.passcode_hash.isnot(None),
            ExportShare.revoked_at.is_(None),
        )
        .all()
    )
    return [s for s in candidates if _is_legacy_sha256(s.passcode_hash)]


def invalidate_legacy_shares(db, *, apply: bool = False, verbose: bool = False) -> dict:
    """Find legacy-hashed shares and optionally revoke them.

    Returns a summary dict with ``count``, ``share_ids``, ``owner_user_ids``
    (sorted unique), and ``applied`` (bool).  The caller commits — this
    function mutates the session but does not ``db.commit()``, so tests
    can wrap in a savepoint.
    """

    legacy = find_legacy_shares(db)

    now = datetime.now(UTC)
    summary = {
        "count": len(legacy),
        "share_ids": sorted(s.id for s in legacy),
        "owner_user_ids": sorted({s.user_id for s in legacy}),
        "applied": False,
        "timestamp": now.isoformat(),
    }

    if apply and legacy:
        for share in legacy:
            share.revoked_at = now
        summary["applied"] = True

        try:
            from security_utils import log_secure_operation

            log_secure_operation(
                "legacy_passcode_invalidation",
                f"count={len(legacy)} share_ids={summary['share_ids']}",
            )
        except Exception:
            # Security logger is best-effort; don't let a logging hiccup
            # block the invalidation itself.
            if verbose:
                print("WARNING: secure_event log failed (non-fatal)", file=sys.stderr)

    if verbose:
        for share in legacy:
            print(
                f"  share_id={share.id} user_id={share.user_id} "
                f"tool={share.tool_name} created={share.created_at} "
                f"expires={share.expires_at} hash_prefix={(share.passcode_hash or '')[:8]}"
            )

    return summary


def render_csv(summary: dict) -> str:
    """Return a CSV (headers + one row per affected share) for CEO courtesy email."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["share_id", "owner_user_id"])
    # We zip because summary has separate sorted lists; preserve pairing
    # via a fresh fetch would be cleaner but we already logged the IDs.
    # Reconstruct by re-querying in the caller if fidelity matters.
    for share_id in summary["share_ids"]:
        writer.writerow([share_id, ""])  # owner_user_id filled by caller with DB fetch
    return buf.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Invalidate pre-Sprint-696 SHA-256 passcode shares.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually revoke rows.  Without this flag, a dry run is performed.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-row details in addition to the summary.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt when --apply is set.",
    )
    args = parser.parse_args()

    # Lazy imports so --help works without a live DB.
    try:
        from database import SessionLocal
    except Exception as e:
        print(f"ERROR: could not import database module: {e}", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        legacy = find_legacy_shares(db)
        if not legacy:
            print("No legacy SHA-256 passcode shares found.  Nothing to do.")
            return 0

        print(f"Found {len(legacy)} legacy-hashed shares (dry-run summary):")
        print(f"  share_ids = {sorted(s.id for s in legacy)}")
        print(f"  owner_user_ids = {sorted({s.user_id for s in legacy})}")

        if not args.apply:
            print("\nDry run — pass --apply to revoke.")
            return 0

        if not args.yes:
            reply = input(f"\nRevoke all {len(legacy)} shares? [y/N] ").strip().lower()
            if reply not in {"y", "yes"}:
                print("Aborted.")
                return 2

        summary = invalidate_legacy_shares(db, apply=True, verbose=args.verbose)
        db.commit()
        print(
            f"\nApplied: revoked {summary['count']} shares "
            f"({len(summary['owner_user_ids'])} unique owners) "
            f"at {summary['timestamp']}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

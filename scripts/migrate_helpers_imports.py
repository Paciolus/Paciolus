#!/usr/bin/env python3
"""One-shot migration: rewrite ``from shared.helpers import X`` for re-exported X
to point at the owning module (Sprint 724).

The 2026-04-20 decomposition split helpers.py into shared.upload_pipeline,
shared.filenames, shared.background_email, shared.tool_run_recorder, but left a
re-export shim. This script sweeps all backend/.py files and migrates each
re-exported symbol to its owning module. Native helpers (try_parse_risk,
parse_json_list, is_authorized_for_client, etc.) stay in shared.helpers — see
the Sprint 724 todo.md entry for the deferred-items reconciliation.

Usage:
    python scripts/migrate_helpers_imports.py [--dry-run]

Idempotent: runs cleanly on already-migrated files (no-op).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"

# Symbol -> owning module for re-exported names.
REEXPORT_OWNER: dict[str, str] = {
    # shared.filenames
    "safe_download_filename": "shared.filenames",
    "sanitize_csv_value": "shared.filenames",
    "escape_like_wildcards": "shared.filenames",
    "hash_filename": "shared.filenames",
    "get_filename_display": "shared.filenames",
    # shared.upload_pipeline
    "_XLS_MAGIC": "shared.upload_pipeline",
    "_XLSX_MAGIC": "shared.upload_pipeline",
    "MAX_CELL_LENGTH": "shared.upload_pipeline",
    "MAX_COL_COUNT": "shared.upload_pipeline",
    "MAX_COMPRESSION_RATIO": "shared.upload_pipeline",
    "MAX_FILE_SIZE_BYTES": "shared.upload_pipeline",
    "MAX_FILE_SIZE_MB": "shared.upload_pipeline",
    "MAX_ROW_COUNT": "shared.upload_pipeline",
    "MAX_ZIP_ENTRIES": "shared.upload_pipeline",
    "MAX_ZIP_UNCOMPRESSED_BYTES": "shared.upload_pipeline",
    "_detect_delimiter": "shared.upload_pipeline",
    "_estimate_csv_row_count": "shared.upload_pipeline",
    "_estimate_xlsx_row_count": "shared.upload_pipeline",
    "_parse_csv": "shared.upload_pipeline",
    "_parse_docx": "shared.upload_pipeline",
    "_parse_excel": "shared.upload_pipeline",
    "_parse_iif": "shared.upload_pipeline",
    "_parse_ods": "shared.upload_pipeline",
    "_parse_ofx": "shared.upload_pipeline",
    "_parse_pdf": "shared.upload_pipeline",
    "_parse_tsv": "shared.upload_pipeline",
    "_parse_txt": "shared.upload_pipeline",
    "_scan_xlsx_xml_for_bombs": "shared.upload_pipeline",
    "_sniff_text_format": "shared.upload_pipeline",
    "_validate_and_convert_df": "shared.upload_pipeline",
    "_validate_xlsx_archive": "shared.upload_pipeline",
    "memory_cleanup": "shared.upload_pipeline",
    "parse_uploaded_file": "shared.upload_pipeline",
    "parse_uploaded_file_by_format": "shared.upload_pipeline",
    "validate_file_size": "shared.upload_pipeline",
    # shared.background_email
    "safe_background_email": "shared.background_email",
    # shared.tool_run_recorder
    "maybe_record_tool_run": "shared.tool_run_recorder",
    "_log_tool_activity": "shared.tool_run_recorder",
}

# Native symbols that stay in shared.helpers (per the deferred-items decision —
# moving 3 client-access helpers to a separate module isn't justified by the
# "prefer moving code, avoid new abstractions" guidance).
NATIVE_HELPERS: set[str] = {
    "try_parse_risk",
    "try_parse_risk_band",
    "parse_json_list",
    "parse_json_mapping",
    "is_authorized_for_client",
    "get_accessible_client",
    "require_client",
}

# Match both single-line and multi-line ``from shared.helpers import (...)`` blocks.
# Handles trailing comments and parenthesized lists.
IMPORT_RE = re.compile(
    r"""
    ^([ \t]*)                       # group 1: leading whitespace (preserve indent)
    from[ \t]+shared\.helpers       # the module name
    [ \t]+import[ \t]+
    (
        \(                          # parenthesized form (multi-line possible)
            (?P<paren>[^)]+)        # symbols inside the parens
        \)
        |                           # OR
        (?P<flat>[^\n#]+?)          # flat single-line list
    )
    [ \t]*(\#[^\n]*)?               # optional trailing comment
    $
    """,
    re.MULTILINE | re.VERBOSE,
)


def _split_symbols(import_clause: str) -> list[str]:
    """Split the symbols from an import clause, stripping commas/whitespace/'as' aliases.

    Aliasing (``foo as bar``) preserves the full ``foo as bar`` token so the rewrite
    keeps the alias intact.
    """
    return [s.strip() for s in import_clause.split(",") if s.strip()]


def _classify(symbols: list[str]) -> tuple[dict[str, list[str]], list[str], list[str]]:
    """Group symbols by owner. Returns (owner_to_symbols, native_keep, unknown).

    Aliased imports (``foo as bar``) are classified by the source name (``foo``).
    """
    owner_to_symbols: dict[str, list[str]] = {}
    native_keep: list[str] = []
    unknown: list[str] = []
    for sym_token in symbols:
        # ``foo as bar`` — classify on ``foo``, keep full token in output.
        source = sym_token.split(" as ")[0].strip()
        if source in REEXPORT_OWNER:
            owner = REEXPORT_OWNER[source]
            owner_to_symbols.setdefault(owner, []).append(sym_token)
        elif source in NATIVE_HELPERS:
            native_keep.append(sym_token)
        else:
            unknown.append(sym_token)
    return owner_to_symbols, native_keep, unknown


def _build_replacement(
    indent: str,
    owner_to_symbols: dict[str, list[str]],
    native_keep: list[str],
    unknown: list[str],
) -> str:
    """Build the replacement import block. Empty if everything was migrated to a single owner."""
    blocks: list[str] = []
    # Stable order: alphabetic by module.
    for owner in sorted(owner_to_symbols):
        symbols = sorted(owner_to_symbols[owner])
        if len(symbols) == 1:
            blocks.append(f"{indent}from {owner} import {symbols[0]}")
        else:
            joined = ",\n".join(f"{indent}    {s}" for s in symbols)
            blocks.append(f"{indent}from {owner} import (\n{joined},\n{indent})")
    # Native + unknown stay in shared.helpers.
    helpers_remaining = sorted(native_keep) + sorted(unknown)
    if helpers_remaining:
        if len(helpers_remaining) == 1:
            blocks.append(f"{indent}from shared.helpers import {helpers_remaining[0]}")
        else:
            joined = ",\n".join(f"{indent}    {s}" for s in helpers_remaining)
            blocks.append(f"{indent}from shared.helpers import (\n{joined},\n{indent})")
    return "\n".join(blocks)


def migrate_file(path: Path, dry_run: bool = False) -> tuple[int, list[str]]:
    """Apply migration to one file. Returns (n_imports_rewritten, unknown_symbols_seen)."""
    text = path.read_text(encoding="utf-8")
    rewrites = 0
    unknown_collected: list[str] = []

    def _replace(match: re.Match) -> str:
        nonlocal rewrites, unknown_collected
        indent = match.group(1)
        paren_block = match.group("paren")
        flat_block = match.group("flat")
        import_clause = paren_block if paren_block is not None else flat_block
        symbols = _split_symbols(import_clause.replace("\n", " "))
        if not symbols:
            return match.group(0)
        owner_to_symbols, native_keep, unknown = _classify(symbols)
        unknown_collected.extend(unknown)
        # Idempotent: if everything is already-native (no re-exports), skip rewrite.
        if not owner_to_symbols:
            return match.group(0)
        rewrites += 1
        return _build_replacement(indent, owner_to_symbols, native_keep, unknown)

    new_text = IMPORT_RE.sub(_replace, text)
    if rewrites and not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return rewrites, unknown_collected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing.")
    parser.add_argument(
        "--root",
        type=Path,
        default=BACKEND_ROOT,
        help=f"Root directory to scan (default: {BACKEND_ROOT})",
    )
    args = parser.parse_args(argv)

    if not args.root.exists():
        print(f"ERROR: root not found: {args.root}", file=sys.stderr)
        return 2

    files: list[Path] = []
    for p in args.root.rglob("*.py"):
        # Skip the helpers.py itself — it's the source of the re-exports.
        if p.resolve() == (args.root / "shared" / "helpers.py").resolve():
            continue
        if "__pycache__" in p.parts or ".venv" in p.parts:
            continue
        files.append(p)

    total_rewrites = 0
    files_touched = 0
    all_unknown: list[tuple[Path, str]] = []
    for path in sorted(files):
        rewrites, unknowns = migrate_file(path, dry_run=args.dry_run)
        if rewrites:
            files_touched += 1
            total_rewrites += rewrites
            print(f"  {'[dry-run] ' if args.dry_run else ''}{path.relative_to(REPO_ROOT)}: {rewrites} rewrite(s)")
        for u in unknowns:
            all_unknown.append((path, u))

    print()
    print(f"Files touched: {files_touched}")
    print(f"Imports rewritten: {total_rewrites}")
    if all_unknown:
        print()
        print(f"Unknown symbols (left in shared.helpers, may need manual review): {len(all_unknown)}")
        for path, sym in all_unknown:
            print(f"  {path.relative_to(REPO_ROOT)}: {sym}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

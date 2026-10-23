"""Rule 1: No Float for monetary columns.

Walks the AST of the configured model files and flags column declarations
typed ``Float`` inside a protected class, unless the column name is in the
float allowlist (ratio/percentage columns that legitimately use Float).

TWO DECLARATION FORMS, AND WHY BOTH MATTER
------------------------------------------
SQLAlchemy 1.x style::

    total_assets = Column(Float, nullable=True)

SQLAlchemy 2.0 style, which is what every model in this codebase now uses::

    total_assets: Mapped[float] = mapped_column(Float, nullable=True)

Until the 2026-10-22 review this checker recognised only ``Column(...)``.
The models had already migrated wholesale to ``mapped_column``, so the rule
matched **0 of 87** declarations inside its own four protected classes and
printed a confident pass over an empty scan. A ``Float`` monetary column
injected directly into ``DiagnosticSummary`` did not trip it.

Its unit tests passed throughout, because they were written against synthetic
``Column(Float, ...)`` sources — a syntax the repository does not contain.
The tests and the target were disjoint sets, and both were green.

THE COVERAGE SELF-CHECK IS THE PART THAT GENERALISES
----------------------------------------------------
Fixing the AST node name closes this instance. What closes the class is
:func:`count_column_declarations`: count the candidates independently, and
require the parser to account for all of them. The check asserts nothing
about what the declarations *contain* — only that none were invisible. A
parser that silently narrows produces no other signal, because the cases it
stops seeing simply stop being asserted.

**The oracle must not share the parser's blind spot.** An earlier draft of
this very function counted candidates with :func:`_call_factory_name` — the
same helper the parser uses — so removing ``mapped_column`` from
:data:`COLUMN_FACTORIES` would have dropped both counts to zero and the
coverage check would have passed on a scan of nothing. That is Sprint 786c's
defect reproduced inside the fix for it.

The independent oracle is the **SQLAlchemy 2.0 type annotation**: in this
codebase every mapped attribute is written ``name: Mapped[T] = <factory>(...)``,
and that annotation is a property of the ORM contract rather than of any
factory name. So candidates are counted from ``Mapped[...]`` annotations (plus
legacy bare ``Column`` assignments), and non-column mapped factories such as
``relationship`` are subtracted by an explicit exclusion list. The asymmetry is
deliberate: a new *column* factory produces a loud coverage failure, while a
new *non-column* factory produces a loud false positive. Both are visible.
Neither degrades to silence.

See ``tests/test_accounting_policy_guard.py::TestParserCoverage``.
"""

import ast
from pathlib import Path

from ..accounting_policy_guard import Violation

RULE = "no_float_monetary"

# Both column-declaration constructors. ``mapped_column`` is the 2.0 form and
# the only one this codebase actually uses; ``Column`` is kept for legacy
# models and for any module that has not migrated.
COLUMN_FACTORIES = frozenset({"Column", "mapped_column"})

# Monetary types that are acceptable. Present for the error message only —
# the rule flags Float, it does not require a specific replacement.
PREFERRED_MONETARY_TYPE = "Numeric(19, 2)"

# Mapped attributes that are NOT columns. Used only by the coverage oracle, to
# subtract relationships and friends from the ``Mapped[...]`` candidate count.
# Getting this list wrong produces a loud false positive, never a silent miss —
# which is the direction an exclusion list is allowed to fail in.
NON_COLUMN_MAPPED_FACTORIES = frozenset(
    {
        "relationship",
        "column_property",
        "composite",
        "deferred",
        "query_expression",
        "synonym",
        "association_proxy",
    }
)


def _call_factory_name(value: ast.expr | None) -> str | None:
    """Return the column-factory name if ``value`` is a column declaration.

    Handles both bare calls (``mapped_column(...)``) and attribute calls
    (``sa.Column(...)``), returning the final attribute name in the latter case.
    """
    if not isinstance(value, ast.Call):
        return None
    func = value.func
    if isinstance(func, ast.Name):
        name = func.id
    elif isinstance(func, ast.Attribute):
        name = func.attr
    else:
        return None
    return name if name in COLUMN_FACTORIES else None


def _mentions_float(node: ast.expr) -> bool:
    """Is this argument the SQLAlchemy ``Float`` type?

    Accepts ``Float``, ``Float()``, ``sa.Float``, and ``sa.Float(...)``.
    Deliberately narrow: it must be the *type* argument, not any identifier
    that happens to contain the word.
    """
    if isinstance(node, ast.Name):
        return node.id == "Float"
    if isinstance(node, ast.Attribute):
        return node.attr == "Float"
    if isinstance(node, ast.Call):
        return _mentions_float(node.func)
    return False


def _is_float_column(node: ast.Assign | ast.AnnAssign) -> tuple[str | None, bool]:
    """Check whether an assignment declares a Float column.

    Returns ``(column_name, is_float_column)``. ``column_name`` is returned
    even when the declaration is not a Float column, so callers can count
    candidates for the coverage self-check.
    """
    if isinstance(node, ast.AnnAssign):
        value, target = node.value, node.target
    else:
        value = node.value
        target = node.targets[0] if node.targets else None  # type: ignore[assignment]

    if target is None:
        return None, False

    if isinstance(target, ast.Name):
        col_name = target.id
    elif isinstance(target, ast.Attribute):
        col_name = target.attr
    else:
        return None, False

    if _call_factory_name(value) is None:
        return col_name, False

    assert isinstance(value, ast.Call)  # narrowed by _call_factory_name
    for arg in value.args:
        if _mentions_float(arg):
            return col_name, True
    for kw in value.keywords:
        if kw.arg in (None, "type_") and _mentions_float(kw.value):
            return col_name, True

    return col_name, False


def _is_mapped_annotation(node: ast.expr | None) -> bool:
    """Is this annotation ``Mapped[...]`` (optionally dotted, e.g. ``orm.Mapped``)?"""
    if node is None:
        return False
    if isinstance(node, ast.Subscript):
        base = node.value
        if isinstance(base, ast.Name):
            return base.id == "Mapped"
        if isinstance(base, ast.Attribute):
            return base.attr == "Mapped"
    return False


def _called_name(value: ast.expr | None) -> str | None:
    """Final callee name of a call expression, or None if not a call."""
    if not isinstance(value, ast.Call):
        return None
    func = value.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def count_column_declarations(tree: ast.Module, protected_classes: list[str]) -> tuple[int, int, list[str]]:
    """Coverage self-check: ``(candidates, seen_by_parser, unaccounted_names)``.

    ``candidates`` is counted by an oracle **independent of the parser's own
    factory list** — see the module docstring for why that independence is the
    whole point. A class-body statement is a candidate column declaration when
    either:

    * it is annotated ``Mapped[...]``, is assigned a call, and that call is not
      a known non-column mapped factory (``relationship`` and friends); or
    * it assigns a bare ``Column(...)`` call (the SQLAlchemy 1.x form, which
      carries no annotation).

    ``seen_by_parser`` counts the statements :func:`_is_float_column` actually
    inspected. Any gap means a declaration form is going unexamined and the
    rule is covering less than it claims.
    """
    candidates = 0
    seen = 0
    unaccounted: list[str] = []

    for node in ast.walk(tree):
        if not (isinstance(node, ast.ClassDef) and node.name in protected_classes):
            continue
        for item in node.body:
            if not isinstance(item, (ast.Assign, ast.AnnAssign)):
                continue

            called = _called_name(item.value)
            annotated_mapped = isinstance(item, ast.AnnAssign) and _is_mapped_annotation(item.annotation)

            is_candidate = False
            if annotated_mapped and called is not None and called not in NON_COLUMN_MAPPED_FACTORIES:
                is_candidate = True
            elif called == "Column":
                is_candidate = True

            if not is_candidate:
                continue
            candidates += 1

            if _call_factory_name(item.value) is not None:
                seen += 1
            else:
                target = item.target if isinstance(item, ast.AnnAssign) else item.targets[0]
                name = getattr(target, "id", getattr(target, "attr", "<unknown>"))
                unaccounted.append(f"{node.name}.{name} (line {item.lineno}, factory '{called}')")

    return candidates, seen, unaccounted


def check_monetary_float_ast(
    tree: ast.Module,
    file_path: str,
    protected_classes: list[str],
    float_allowlist: list[str],
) -> list[Violation]:
    """Check a single AST for Float columns in protected classes."""
    violations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name in protected_classes:
            for item in node.body:
                if isinstance(item, (ast.Assign, ast.AnnAssign)):
                    col_name, is_float = _is_float_column(item)
                    if is_float and col_name and col_name not in float_allowlist:
                        violations.append(
                            Violation(
                                rule=RULE,
                                file=file_path,
                                line=item.lineno,
                                message=(
                                    f"Column '{col_name}' in {node.name} uses Float. "
                                    f"Monetary columns must use {PREFERRED_MONETARY_TYPE}. "
                                    f"If '{col_name}' is a ratio, percentage or score rather than an "
                                    f"amount, add it to float_allowlist in guards/accounting_policy.toml."
                                ),
                                severity="error",
                            )
                        )

    return violations


def check_parser_coverage(
    tree: ast.Module,
    file_path: str,
    protected_classes: list[str],
) -> list[Violation]:
    """Fail if the parser could not account for every column declaration.

    This is a claim about the *parser*, not about the code under inspection.
    It is reported as a violation because a rule that has silently stopped
    scanning is strictly worse than one that fails loudly.
    """
    candidates, seen, unaccounted = count_column_declarations(tree, protected_classes)
    if candidates != seen:
        detail = "; ".join(unaccounted[:5]) or "(no detail)"
        return [
            Violation(
                rule=RULE,
                file=file_path,
                line=1,
                message=(
                    f"Parser coverage gap: {seen} of {candidates} column declarations in protected "
                    f"classes were inspected. Unaccounted: {detail}. Either add the declaration form "
                    f"to COLUMN_FACTORIES in guards/checkers/monetary_float.py, or — if it is not a "
                    f"column — add it to NON_COLUMN_MAPPED_FACTORIES. Do not suppress this: a rule "
                    f"that has stopped scanning still reports PASS."
                ),
                severity="error",
            )
        ]
    return []


def check_monetary_float(config: dict, backend_root: Path) -> list[Violation]:
    """Run no_float_monetary across configured files, with a coverage self-check.

    Reports a violation if a configured file is missing. A scan list that has
    stopped matching the tree is the same failure as a parser that has stopped
    matching the syntax: the rule keeps passing, on less.
    """
    violations = []
    files = config.get("files", [])
    protected_classes = config.get("protected_classes", [])
    float_allowlist = config.get("float_allowlist", [])

    if not files or not protected_classes:
        return [
            Violation(
                rule=RULE,
                file="guards/accounting_policy.toml",
                line=1,
                message="no_float_monetary is enabled but its files/protected_classes list is empty.",
                severity="error",
            )
        ]

    classes_found: set[str] = set()

    for filename in files:
        filepath = backend_root / filename
        if not filepath.exists():
            violations.append(
                Violation(
                    rule=RULE,
                    file=filename,
                    line=1,
                    message=(
                        f"Configured scan target '{filename}' does not exist. Update "
                        f"guards/accounting_policy.toml — a missing file silently shrinks this rule."
                    ),
                    severity="error",
                )
            )
            continue
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=filename)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in protected_classes:
                classes_found.add(node.name)
        violations.extend(check_parser_coverage(tree, filename, protected_classes))
        violations.extend(
            check_monetary_float_ast(
                tree,
                filename,
                protected_classes,
                float_allowlist,
            )
        )

    missing_classes = sorted(set(protected_classes) - classes_found)
    if missing_classes:
        violations.append(
            Violation(
                rule=RULE,
                file="guards/accounting_policy.toml",
                line=1,
                message=(
                    f"protected_classes names {missing_classes}, which were not found in any scanned "
                    f"file. A class that has moved or been renamed is no longer protected."
                ),
                severity="error",
            )
        )

    return violations

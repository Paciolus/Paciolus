"""
Saved testing settings -> engine config (Sprint 836).

The tool settings drawer and the Practice Settings page save JE / AP /
Payroll / Three-Way Match thresholds into ``User.settings``
(``PracticeSettings.je_testing_config`` etc.). Before Sprint 836 no route
read them: every run used the engine defaults while the customer believed
their thresholds were in force.

This module turns a saved dict into the engine's config dataclass. The rules
are deliberately conservative, because a threshold changes which entries are
flagged:

* Only fields the engine dataclass actually declares are applied.
* Every value is type-checked: booleans must be real booleans; numbers must be
  finite ints/floats (never a bool); whole-number fields must be whole; list
  fields must be non-empty lists of numbers.
* Numeric values must be non-negative, and fractions / hours / similarity
  ratios must sit inside their meaningful range.
* Anything that fails is NOT applied and is reported with a reason. A stale or
  malformed saved key never fails a run (no 400, no 500) and is never dropped
  silently.

Callers report ``applied`` (only values that differ from the engine default)
and ``ignored`` on the tool result as ``settings_applied`` /
``settings_ignored`` so the results page and memo can say exactly which
thresholds were not Paciolus defaults.
"""

from __future__ import annotations

import dataclasses
import json
import math
import typing
from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar

from practice_settings import PracticeSettings
from services.audit.ap_testing.analysis import APTestingConfig
from services.audit.je_testing.analysis import JETestingConfig
from services.audit.payroll_testing.analysis import PayrollTestingConfig
from three_way_match_engine import ThreeWayMatchConfig

T = TypeVar("T")

_MAX_LIST_ITEMS = 25

# Bounds shared by saved settings and the Three-Way Match per-run form fields
# (RPT-11 remediation, 2026-04-20). Defensive: rejects negative tolerances,
# >100% variance thresholds, or date windows measured in years.
TWM_CONFIG_BOUNDS: dict[str, tuple[float, float]] = {
    "amount_tolerance": (0.0, 10_000.0),  # up to $10K absolute
    "quantity_tolerance": (0.0, 10_000.0),  # up to 10K units
    "date_window_days": (0.0, 365.0),  # up to 1 year
    "fuzzy_vendor_threshold": (0.0, 1.0),
    "price_variance_threshold": (0.0, 1.0),  # 0-100%
    "fuzzy_composite_threshold": (0.0, 1.0),
}

_UNIT_INTERVAL = (0.0, 1.0)
_HOUR_OF_DAY = (0.0, 23.0)


@dataclass(frozen=True)
class SavedConfigSpec:
    """How one tool's saved settings map onto its engine config."""

    settings_attr: str  # PracticeSettings attribute holding the saved dict
    config_cls: type
    # Per-field (min, max). Fields not listed default to (0, +inf).
    bounds: dict[str, tuple[float, float]] = field(default_factory=dict)
    # Fields the engine declares but which are chosen per run, not saved.
    per_run_only: dict[str, str] = field(default_factory=dict)
    # Legacy saved key -> engine field (keys the frontend once saved under another name).
    aliases: dict[str, str] = field(default_factory=dict)
    # Field -> value an earlier settings form saved as a hidden default the
    # user never saw or chose. Not applied; reported instead.
    legacy_defaults: dict[str, Any] = field(default_factory=dict)
    # Fields that must be strictly greater than zero (the engine divides by
    # them, or zero makes the test meaningless). PR #229 review: a saved
    # single_user_volume_pct of 0 raised ZeroDivisionError and failed the run.
    positive: frozenset[str] = frozenset()


@dataclass
class SavedConfigOutcome(Generic[T]):
    """Result of applying saved settings to a base config."""

    config: T
    # Every saved value that was set on the config, keyed by engine field.
    overrides: dict[str, Any]
    # Only the overrides that differ from the engine's own default.
    applied: dict[str, Any]
    # Saved keys that were not applied: [{"key": ..., "reason": ...}].
    ignored: list[dict[str, str]]

    def result_fields(self) -> dict[str, Any]:
        """The transparency fields every wired tool result carries."""
        return {
            "settings_applied": dict(self.applied),
            "settings_ignored": [dict(i) for i in self.ignored],
        }


JE_SPEC = SavedConfigSpec(
    settings_attr="je_testing_config",
    config_cls=JETestingConfig,
    bounds={
        "single_user_volume_pct": _UNIT_INTERVAL,
        "suspicious_keyword_threshold": _UNIT_INTERVAL,
        "threshold_proximity_pct": _UNIT_INTERVAL,
        "month_end_outlier_min_gap": _UNIT_INTERVAL,
        "after_hours_start": _HOUR_OF_DAY,
        "after_hours_end": _HOUR_OF_DAY,
        "month_end_days": (1.0, 31.0),
    },
    per_run_only={
        "holiday_excluded_names": "The holiday calendar is set for each run, not from saved settings.",
        "holiday_additional_dates": "The holiday calendar is set for each run, not from saved settings.",
        "sampling_default_rate": "The sampling rate is chosen on each sampling run, not from saved settings.",
    },
    # Before Sprint 836 the settings form saved benford_min_entries=500 with
    # every JE save, though the field was never shown and the engine default
    # is 300 (Sprint 686). Applying it would quietly shrink Benford coverage.
    legacy_defaults={"benford_min_entries": 500},
    positive=frozenset({"single_user_volume_pct", "threshold_proximity_pct", "suspicious_keyword_threshold"}),
)

AP_SPEC = SavedConfigSpec(
    settings_attr="ap_testing_config",
    config_cls=APTestingConfig,
    bounds={
        "vendor_variation_threshold": _UNIT_INTERVAL,
        "threshold_proximity_pct": _UNIT_INTERVAL,
        "suspicious_keyword_threshold": _UNIT_INTERVAL,
    },
)

PAYROLL_SPEC = SavedConfigSpec(
    settings_attr="payroll_testing_config",
    config_cls=PayrollTestingConfig,
    bounds={
        "duplicate_name_similarity": _UNIT_INTERVAL,
        "address_similarity_threshold": _UNIT_INTERVAL,
    },
    # Before Sprint 836 the settings UI saved these toggles under names the
    # engine never declared; settings saved then are honoured under the engine name.
    aliases={
        "check_gap_enabled": "check_number_gap_enabled",
        "benford_enabled": "enable_benford",
        "ghost_enabled": "enable_ghost",
        "duplicate_bank_enabled": "enable_duplicates",
        "duplicate_tax_enabled": "enable_tax_id_duplicates",
    },
)

TWM_SPEC = SavedConfigSpec(
    settings_attr="three_way_match_config",
    config_cls=ThreeWayMatchConfig,
    bounds=dict(TWM_CONFIG_BOUNDS),
)


_SPEC_BY_MEMO_DOMAIN: dict[str, SavedConfigSpec] = {
    "journal_entry_testing": JE_SPEC,
    "ap_payment_testing": AP_SPEC,
    "payroll_testing": PAYROLL_SPEC,
    "three_way_match": TWM_SPEC,
}


def engine_defaults_for_domain(tool_domain: Optional[str]) -> dict[str, Any]:
    """Engine default values keyed by field, for the memo's comparison column."""
    spec = _SPEC_BY_MEMO_DOMAIN.get(tool_domain or "")
    if spec is None:
        return {}
    return {f.name: getattr(spec.config_cls(), f.name) for f in dataclasses.fields(spec.config_cls)}


def _fmt_bound(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else str(v)


def _check_number(value: Any, *, whole: bool, lo: float, hi: float) -> tuple[Optional[float | int], Optional[str]]:
    """Validate one numeric value. Returns (coerced, None) or (None, reason)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, f"must be a number, got {type(value).__name__}"
    if not math.isfinite(value):
        return None, "must be a finite number"
    if whole:
        if isinstance(value, float):
            if not value.is_integer():
                return None, "must be a whole number"
            value = int(value)
    else:
        value = float(value)
    if value < lo or value > hi:
        if math.isinf(hi):
            return None, f"must be at least {_fmt_bound(lo)}"
        return None, f"must be between {_fmt_bound(lo)} and {_fmt_bound(hi)}"
    return value, None


def _validate(value: Any, hint: Any, lo: float, hi: float) -> tuple[Any, Optional[str]]:
    """Validate ``value`` against the dataclass field type ``hint``."""
    if hint is bool:
        if not isinstance(value, bool):
            return None, f"must be true or false, got {type(value).__name__}"
        return value, None
    if hint is int:
        return _check_number(value, whole=True, lo=lo, hi=hi)
    if hint is float:
        return _check_number(value, whole=False, lo=lo, hi=hi)
    origin = typing.get_origin(hint)
    args = typing.get_args(hint)
    if origin is list and args and args[0] in (int, float):
        if not isinstance(value, list):
            return None, f"must be a list of numbers, got {type(value).__name__}"
        if not value:
            return None, "must list at least one value"
        if len(value) > _MAX_LIST_ITEMS:
            return None, f"must list at most {_MAX_LIST_ITEMS} values"
        out = []
        for item in value:
            coerced, reason = _check_number(item, whole=args[0] is int, lo=lo, hi=hi)
            if reason:
                return None, f"every value {reason}"
            out.append(coerced)
        return out, None
    return None, "cannot be set from saved settings"


def apply_saved_config(base: T, saved: Optional[dict[str, Any]], spec: SavedConfigSpec) -> SavedConfigOutcome[T]:
    """Layer ``saved`` onto ``base`` under ``spec``'s rules.

    ``base`` carries anything the caller already decided (e.g. the per-run
    JE holiday calendar); saved values are applied on top of it, so callers
    must apply per-run inputs AFTER this, or start from a base that holds
    fields saved settings cannot touch.
    """
    if not isinstance(base, spec.config_cls):
        raise TypeError(f"base must be a {spec.config_cls.__name__}")
    if not saved:
        return SavedConfigOutcome(config=base, overrides={}, applied={}, ignored=[])

    hints = typing.get_type_hints(spec.config_cls)
    field_names = {f.name for f in dataclasses.fields(spec.config_cls)}
    default = spec.config_cls()

    overrides: dict[str, Any] = {}
    ignored: list[dict[str, str]] = []

    # Canonical keys first, so a legacy alias never overrides the engine name.
    ordered = sorted(saved.items(), key=lambda kv: kv[0] in spec.aliases)
    for key, value in ordered:
        if not isinstance(key, str):
            continue
        name = spec.aliases.get(key, key)
        if name in spec.per_run_only:
            ignored.append({"key": key, "reason": spec.per_run_only[name]})
            continue
        if name not in field_names:
            ignored.append({"key": key, "reason": "Not a setting this tool recognises."})
            continue
        if name in overrides:
            ignored.append({"key": key, "reason": f"Superseded by the saved value for '{name}'."})
            continue
        if name in spec.legacy_defaults and value == spec.legacy_defaults[name] and type(value) is not bool:
            ignored.append(
                {
                    "key": key,
                    "reason": (
                        f"{_preview(value)} was saved automatically by an earlier version of the settings form, "
                        f"not chosen; the Paciolus default of {_preview(getattr(default, name))} applies."
                    ),
                }
            )
            continue
        lo, hi = spec.bounds.get(name, (0.0, math.inf))
        coerced, reason = _validate(value, hints.get(name), lo, hi)
        if reason is None and name in spec.positive and coerced == 0:
            reason = "must be greater than 0"
        if reason is not None:
            ignored.append({"key": key, "reason": f"Value {_preview(value)} {reason}."})
            continue
        overrides[name] = coerced

    config = dataclasses.replace(base, **overrides)  # type: ignore[type-var]
    applied = {k: v for k, v in overrides.items() if v != getattr(default, k)}
    return SavedConfigOutcome(config=config, overrides=overrides, applied=applied, ignored=ignored)


def effective_non_defaults(config: Any, spec: SavedConfigSpec) -> dict[str, Any]:
    """Every field of ``config`` that differs from the engine default, whatever set it.

    PR #229 review: for tools that also take per-run values (Three-Way Match),
    ``settings_applied`` must describe the configuration the run actually used,
    not only the saved overrides; otherwise a per-run tolerance went unreported
    and the memo called every threshold a default.
    """
    default = spec.config_cls()
    return {
        f.name: getattr(config, f.name)
        for f in dataclasses.fields(config)
        if f.name not in spec.per_run_only and getattr(config, f.name) != getattr(default, f.name)
    }


def _preview(value: Any) -> str:
    try:
        text = json.dumps(value)
    except (TypeError, ValueError):
        text = repr(value)
    return text if len(text) <= 40 else text[:37] + "..."


def load_saved_testing_config(user: Any, spec: SavedConfigSpec, base: Optional[T] = None) -> SavedConfigOutcome[T]:
    """Read ``user``'s saved settings for one tool and apply them to ``base``.

    ``base`` defaults to the engine's default config.
    """
    if base is None:
        base = spec.config_cls()
    raw = getattr(user, "settings", None) or "{}"
    settings = PracticeSettings.from_json(raw)
    saved = getattr(settings, spec.settings_attr, None)

    if saved is None and _raw_has_section(raw, spec.settings_attr):
        # PracticeSettings.from_json falls back to all-defaults when any part
        # of the stored blob is invalid; say so rather than drop the thresholds.
        return SavedConfigOutcome(
            config=base,
            overrides={},
            applied={},
            ignored=[
                {
                    "key": spec.settings_attr,
                    "reason": "Saved practice settings could not be read; Paciolus defaults were used.",
                }
            ],
        )
    if saved is not None and not isinstance(saved, dict):
        return SavedConfigOutcome(
            config=base,
            overrides={},
            applied={},
            ignored=[{"key": spec.settings_attr, "reason": "Saved settings are not a set of named values."}],
        )
    return apply_saved_config(base, saved, spec)


def _raw_has_section(raw: str, attr: str) -> bool:
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return False
    return isinstance(data, dict) and bool(data.get(attr))


def supersede_with_run_overrides(outcome: SavedConfigOutcome[T], run_fields: set[str]) -> None:
    """Record that per-run inputs replaced some saved values (per-run inputs win)."""
    for name in sorted(run_fields):
        if name in outcome.overrides:
            outcome.overrides.pop(name)
            # A saved value equal to the default changed nothing, so nothing to report.
            if outcome.applied.pop(name, None) is not None:
                outcome.ignored.append({"key": name, "reason": "Replaced by the value supplied for this run."})

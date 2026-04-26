"""Sprint 723 — coverage floor enforcement.

Tests ``scripts/check_coverage_floors.py``: TOML loading, path normalization,
floor breach detection, missing-file behavior, and the CLI exit codes. The
prevention story is that any future PR which drops coverage on a floored file
fails this check at PR time, not at the next nightly sentinel run.

Failure modes the tests cover:
  - floor literal violation
  - missing file in coverage report (default: fail; --missing-ok: warn)
  - malformed TOML
  - floor outside 0..100
  - mixed Windows/Linux path separators
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_coverage_floors import (  # noqa: E402  (path manipulation above)
    EXIT_FLOOR_BREACH,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    _normalize,
    check,
    load_coverage,
    load_floors,
    main,
)

# ---------------------------------------------------------------------------
# Path normalization
# ---------------------------------------------------------------------------


class TestNormalize:
    def test_backslash_to_forward_slash(self):
        assert _normalize("billing\\webhook_handler.py") == "billing/webhook_handler.py"

    def test_lowercase(self):
        assert _normalize("Routes/Auth.PY") == "routes/auth.py"

    def test_strips_dot_slash_prefix(self):
        assert _normalize("./excel_generator.py") == "excel_generator.py"

    def test_already_normalized(self):
        assert _normalize("excel_generator.py") == "excel_generator.py"


# ---------------------------------------------------------------------------
# TOML loader
# ---------------------------------------------------------------------------


class TestLoadFloors:
    def test_well_formed_toml(self, tmp_path: Path):
        toml = tmp_path / "floors.toml"
        toml.write_text(
            textwrap.dedent("""
                [floors]
                "excel_generator.py" = 44
                "billing/webhook_handler.py" = 58
            """).strip()
        )
        floors = load_floors(toml)
        assert floors == {
            "excel_generator.py": 44,
            "billing/webhook_handler.py": 58,
        }

    def test_path_keys_normalized(self, tmp_path: Path):
        toml = tmp_path / "floors.toml"
        toml.write_text('[floors]\n"Routes\\\\Auth.PY" = 80\n')
        floors = load_floors(toml)
        # Backslash + uppercase → normalized.
        assert "routes/auth.py" in floors
        assert floors["routes/auth.py"] == 80

    def test_empty_floors_section(self, tmp_path: Path):
        toml = tmp_path / "floors.toml"
        toml.write_text("[floors]\n")
        assert load_floors(toml) == {}

    def test_missing_floors_section(self, tmp_path: Path):
        toml = tmp_path / "floors.toml"
        toml.write_text("# no floors section\n")
        assert load_floors(toml) == {}

    def test_non_numeric_floor_rejected(self, tmp_path: Path):
        toml = tmp_path / "floors.toml"
        toml.write_text('[floors]\n"foo.py" = "high"\n')
        with pytest.raises(ValueError, match="must be a number"):
            load_floors(toml)

    def test_out_of_range_floor_rejected(self, tmp_path: Path):
        toml = tmp_path / "floors.toml"
        toml.write_text('[floors]\n"foo.py" = 105\n')
        with pytest.raises(ValueError, match="outside 0..100"):
            load_floors(toml)


# ---------------------------------------------------------------------------
# Coverage loader
# ---------------------------------------------------------------------------


class TestLoadCoverage:
    def test_well_formed_coverage_json(self, tmp_path: Path):
        cov = tmp_path / "coverage.json"
        cov.write_text(
            json.dumps(
                {
                    "files": {
                        "excel_generator.py": {"summary": {"percent_covered": 45.7}},
                        "billing\\webhook_handler.py": {"summary": {"percent_covered": 59.91}},
                    }
                }
            )
        )
        loaded = load_coverage(cov)
        # Backslash path normalized to forward.
        assert loaded["excel_generator.py"] == pytest.approx(45.7)
        assert loaded["billing/webhook_handler.py"] == pytest.approx(59.91)

    def test_missing_summary_skipped(self, tmp_path: Path):
        cov = tmp_path / "coverage.json"
        cov.write_text(json.dumps({"files": {"foo.py": {}}}))
        assert load_coverage(cov) == {}

    def test_missing_percent_covered_skipped(self, tmp_path: Path):
        cov = tmp_path / "coverage.json"
        cov.write_text(json.dumps({"files": {"foo.py": {"summary": {"missing": 10}}}}))
        assert load_coverage(cov) == {}


# ---------------------------------------------------------------------------
# Core check logic
# ---------------------------------------------------------------------------


class TestCheck:
    def test_all_above_floor(self):
        floors = {"foo.py": 50}
        coverage = {"foo.py": 60.0}
        failures, warnings = check(floors, coverage)
        assert failures == []
        assert warnings == []

    def test_breach_detected(self):
        floors = {"foo.py": 50}
        coverage = {"foo.py": 49.99}
        failures, warnings = check(floors, coverage)
        assert len(failures) == 1
        assert "foo.py" in failures[0]
        assert "49.99% below floor 50%" in failures[0]

    def test_at_floor_passes(self):
        # Equal is not a breach — only strict less-than fails.
        floors = {"foo.py": 50}
        coverage = {"foo.py": 50.0}
        failures, _ = check(floors, coverage)
        assert failures == []

    def test_missing_file_default_fails(self):
        floors = {"foo.py": 50}
        coverage = {}  # file absent from coverage report
        failures, warnings = check(floors, coverage, missing_ok=False)
        assert len(failures) == 1
        assert "not present in coverage report" in failures[0]
        assert warnings == []

    def test_missing_file_with_missing_ok_warns(self):
        floors = {"foo.py": 50}
        coverage = {}
        failures, warnings = check(floors, coverage, missing_ok=True)
        assert failures == []
        assert len(warnings) == 1
        assert "not present in coverage report" in warnings[0]

    def test_multiple_floors_some_breach(self):
        floors = {"a.py": 50, "b.py": 60, "c.py": 70}
        coverage = {"a.py": 50.0, "b.py": 55.0, "c.py": 71.0}
        failures, _ = check(floors, coverage)
        assert len(failures) == 1
        assert "b.py" in failures[0]


# ---------------------------------------------------------------------------
# CLI integration (main())
# ---------------------------------------------------------------------------


class TestMainCli:
    @staticmethod
    def _write(tmp_path: Path, floors_toml: str, coverage_json: dict) -> tuple[Path, Path]:
        floors_path = tmp_path / "floors.toml"
        floors_path.write_text(floors_toml)
        cov_path = tmp_path / "coverage.json"
        cov_path.write_text(json.dumps(coverage_json))
        return cov_path, floors_path

    def test_cli_passes_when_floors_met(self, tmp_path: Path):
        cov_path, floors_path = self._write(
            tmp_path,
            '[floors]\n"foo.py" = 50\n',
            {"files": {"foo.py": {"summary": {"percent_covered": 60.0}}}},
        )
        rc = main([str(cov_path), str(floors_path)])
        assert rc == EXIT_OK

    def test_cli_fails_on_breach(self, tmp_path: Path, capsys: pytest.CaptureFixture):
        cov_path, floors_path = self._write(
            tmp_path,
            '[floors]\n"foo.py" = 50\n',
            {"files": {"foo.py": {"summary": {"percent_covered": 40.0}}}},
        )
        rc = main([str(cov_path), str(floors_path)])
        assert rc == EXIT_FLOOR_BREACH
        captured = capsys.readouterr()
        assert "FAIL" in captured.out
        assert "below floor" in captured.err

    def test_cli_missing_coverage_file(self, tmp_path: Path, capsys: pytest.CaptureFixture):
        floors = tmp_path / "floors.toml"
        floors.write_text("[floors]\n")
        rc = main([str(tmp_path / "nonexistent.json"), str(floors)])
        assert rc == EXIT_USAGE_ERROR
        assert "coverage report not found" in capsys.readouterr().err

    def test_cli_missing_floors_file(self, tmp_path: Path, capsys: pytest.CaptureFixture):
        cov = tmp_path / "coverage.json"
        cov.write_text(json.dumps({"files": {}}))
        rc = main([str(cov), str(tmp_path / "nonexistent.toml")])
        assert rc == EXIT_USAGE_ERROR
        assert "floors file not found" in capsys.readouterr().err

    def test_cli_no_floors_configured_passes(self, tmp_path: Path, capsys: pytest.CaptureFixture):
        cov_path, floors_path = self._write(
            tmp_path,
            "[floors]\n",  # empty
            {"files": {"foo.py": {"summary": {"percent_covered": 40.0}}}},
        )
        rc = main([str(cov_path), str(floors_path)])
        assert rc == EXIT_OK
        assert "No floors configured" in capsys.readouterr().out

    def test_cli_missing_ok_flag(self, tmp_path: Path):
        cov_path, floors_path = self._write(
            tmp_path,
            '[floors]\n"renamed.py" = 50\n',
            {"files": {}},  # the floored file isn't in coverage
        )
        # Without --missing-ok, missing file is a failure.
        assert main([str(cov_path), str(floors_path)]) == EXIT_FLOOR_BREACH
        # With --missing-ok, it's just a warning and we exit 0.
        assert main([str(cov_path), str(floors_path), "--missing-ok"]) == EXIT_OK


# ---------------------------------------------------------------------------
# Sanity: the real shipped coverage_floors.toml parses cleanly.
# ---------------------------------------------------------------------------


class TestRepoFloorsParseCleanly:
    def test_repo_floors_load_without_error(self):
        floors_path = REPO_ROOT / "backend" / "coverage_floors.toml"
        floors = load_floors(floors_path)
        # Sanity: at least one floor configured (Sprint 723 ships 9).
        assert len(floors) >= 9
        # Every floor in 0..100.
        for path, pct in floors.items():
            assert 0 <= pct <= 100, f"{path} floor {pct} out of range"

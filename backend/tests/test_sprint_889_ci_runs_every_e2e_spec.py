"""Sprint 889 (CEO brief 14H, review TQ-16): CI runs every end-to-end spec, without secrets.

``frontend/e2e/trial-balance-mapping.spec.ts`` ran nowhere: the Playwright job named only
``smoke.spec.ts``, and skipped even that unless repository secrets were present (the repository has
none). The job now seeds a deterministic account into its own throwaway database and runs both.
"""

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
CI = REPO / ".github" / "workflows" / "ci.yml"


def _e2e_job() -> dict:
    return yaml.safe_load(CI.read_text(encoding="utf-8"))["jobs"]["e2e-smoke"]


def _playwright_command(job: dict) -> str:
    runs = [s.get("run", "") for s in job["steps"] if "playwright test" in s.get("run", "")]
    assert len(runs) == 1, runs
    return runs[0]


def test_every_spec_file_is_run():
    specs = sorted(p.relative_to(REPO / "frontend").as_posix() for p in (REPO / "frontend" / "e2e").glob("*.spec.ts"))
    assert "e2e/trial-balance-mapping.spec.ts" in specs and "e2e/smoke.spec.ts" in specs
    command = _playwright_command(_e2e_job())
    for spec in specs:
        assert spec in command, f"{spec} is not run by the e2e job"


def test_the_e2e_run_does_not_depend_on_secrets():
    job = _e2e_job()
    step = next(s for s in job["steps"] if "playwright test" in s.get("run", ""))
    assert "if" not in step, "the run step must not be skipped"
    assert "secrets." not in CI.read_text(encoding="utf-8").split("e2e-smoke:")[1].split("\n  # ──")[0]


def test_the_job_seeds_the_account_it_logs_in_with():
    job = _e2e_job()
    assert job["env"]["SMOKE_USER"] and job["env"]["SMOKE_PASS"]
    assert any("seed_e2e_user.py" in s.get("run", "") for s in job["steps"])
    assert (REPO / "scripts" / "seed_e2e_user.py").exists()

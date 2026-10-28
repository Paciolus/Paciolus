"""Sprint 852 (security review L2): ENV_MODE fails closed.

Every production guard in config.py is ``ENV_MODE == "production"``, so an
unrecognised value ("prod", "Production", a typo) used to silently run the
service with all of them off. config.py now accepts only an allow-list and
refuses to start on a Render host unless ENV_MODE is exactly "production".

Subprocess: config is evaluated at import time, and the SecretsManager
singleton caches env reads, so in-process monkeypatching cannot re-run it.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parent.parent

# The Render-run production values; mirrors _prod_env in
# test_security_hardening_2026_04_20.py so production mode loads cleanly.
_PROD_EXTRA = {
    "CORS_ORIGINS": "https://paciolus.com",
    "AUDIT_CHAIN_SECRET_KEY": "z" * 64,
    "REDIS_URL": "redis://localhost:6379/0",
    "DATABASE_URL": "postgresql://u:p@localhost:5432/x?sslmode=require",
    "DB_TLS_REQUIRED": "true",
    "STRIPE_SECRET_KEY": "placeholder-non-stripe-format",
    "STRIPE_PUBLISHABLE_KEY": "placeholder-non-stripe-format",
    "STRIPE_WEBHOOK_SECRET": "placeholder-non-whsec-format",
    "SENDGRID_API_KEY": "SG.test",
    "SEAT_ENFORCEMENT_MODE": "hard",
    "ENTITLEMENT_ENFORCEMENT": "hard",
}


def _import_config(env_mode: str, *, render: str | None = None, production: bool = False):
    env = {k: v for k, v in os.environ.items() if k not in ("ENV_MODE", "RENDER")}
    env.update(
        {
            "API_HOST": "127.0.0.1",
            "API_PORT": "8000",
            "CORS_ORIGINS": "http://localhost:3000",
            "JWT_SECRET_KEY": "x" * 64,
            "CSRF_SECRET_KEY": "y" * 64,
            "DATABASE_URL": "sqlite:///./env_mode_test.db",
            "DB_TLS_REQUIRED": "false",
            "ENV_MODE": env_mode,
            "PYTHONPATH": str(_BACKEND_ROOT),
        }
    )
    if production:
        env.update(_PROD_EXTRA)
    if render is not None:
        env["RENDER"] = render
    return subprocess.run(
        [sys.executable, "-c", "import config; print('ENV_MODE=' + config.ENV_MODE)"],
        cwd=_BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.mark.parametrize("env_mode", ["development", "test"])
def test_allowed_non_production_modes_load(env_mode):
    proc = _import_config(env_mode)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip().splitlines()[-1] == f"ENV_MODE={env_mode}"


def test_production_mode_loads():
    proc = _import_config("production", production=True)
    assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("env_mode", ["prod", "Production", "PRODUCTION", "staging", "dev", "productoin"])
def test_unknown_env_mode_refuses_to_start(env_mode):
    proc = _import_config(env_mode)
    assert proc.returncode != 0, f"config imported with ENV_MODE={env_mode!r}: {proc.stdout!r}"
    assert "ENV_MODE" in proc.stderr


@pytest.mark.parametrize("env_mode", ["development", "test"])
def test_render_host_requires_production(env_mode):
    proc = _import_config(env_mode, render="true")
    assert proc.returncode != 0, f"config imported on Render with ENV_MODE={env_mode!r}"
    assert "RENDER" in proc.stderr


def test_render_host_in_production_loads():
    proc = _import_config("production", render="true", production=True)
    assert proc.returncode == 0, proc.stderr

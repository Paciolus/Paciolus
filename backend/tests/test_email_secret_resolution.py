"""
Sprint 819 (item 9) — email settings resolve through the secrets chain.

config.py validates SENDGRID_API_KEY with ``secrets_manager.get_secret``
(environment → Docker secrets → cloud provider), but email_service read it
with ``os.getenv``. A key supplied only as a Docker secret therefore passed
the production startup check and then sent no email.
"""

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_sendgrid_key_supplied_only_as_a_docker_secret_reaches_email_service(monkeypatch, tmp_path):
    import email_service
    import secrets_manager

    (tmp_path / "sendgrid_api_key").write_text("SG.from-docker-secret\n")
    monkeypatch.delenv("SENDGRID_API_KEY", raising=False)
    monkeypatch.setattr(secrets_manager.SecretsManager, "DOCKER_SECRETS_PATH", tmp_path)
    monkeypatch.setattr(secrets_manager.get_secrets_manager(), "_cache", {})

    try:
        reloaded = importlib.reload(email_service)
        assert reloaded.SENDGRID_API_KEY == "SG.from-docker-secret"
    finally:
        monkeypatch.undo()
        secrets_manager.get_secrets_manager()._cache.clear()
        importlib.reload(email_service)

"""Secure credential management with multiple backend support (env, Docker, AWS/GCP/Azure)."""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache


class SecretsManager:
    """Secrets manager with priority chain: env vars > Docker secrets > cloud providers."""

    # Docker secrets mount path
    DOCKER_SECRETS_PATH = Path("/run/secrets")

    # Cloud provider environment keys
    CLOUD_PROVIDER_KEY = "SECRETS_PROVIDER"

    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._provider = os.getenv(self.CLOUD_PROVIDER_KEY, "env")

    def get_secret(
        self,
        key: str,
        default: Optional[str] = None,
        required: bool = False
    ) -> Optional[str]:
        """Retrieve a secret value with fallback chain. Raises ValueError if required and not found."""
        # Check cache first
        if key in self._cache:
            return self._cache[key]

        value = None

        # Priority 1: Environment variable
        value = os.getenv(key)

        # Priority 2: Docker secrets
        if value is None:
            value = self._read_docker_secret(key)

        # Priority 3: Cloud provider (if configured)
        if value is None and self._provider != "env":
            value = self._read_cloud_secret(key)

        # Priority 4: Default value
        if value is None:
            value = default

        # Handle required secrets
        if value is None and required:
            raise ValueError(
                f"Required secret '{key}' not found in any configured backend. "
                f"Provider: {self._provider}"
            )

        # Cache the value
        if value is not None:
            self._cache[key] = value

        return value

    def _read_docker_secret(self, key: str) -> Optional[str]:
        """Read secret from Docker secrets mount."""
        # Convert key to lowercase for Docker secret file naming convention
        secret_file = self.DOCKER_SECRETS_PATH / key.lower()

        if secret_file.exists():
            try:
                return secret_file.read_text().strip()
            except OSError:
                return None
        return None

    def _read_cloud_secret(self, key: str) -> Optional[str]:
        """Read secret from configured cloud provider (aws/gcp/azure)."""
        if self._provider == "aws":
            return self._read_aws_secret(key)
        elif self._provider == "gcp":
            return self._read_gcp_secret(key)
        elif self._provider == "azure":
            return self._read_azure_secret(key)
        return None

    def _read_aws_secret(self, key: str) -> Optional[str]:
        """Read from AWS Secrets Manager."""
        try:
            import boto3
            client = boto3.client("secretsmanager")
            response = client.get_secret_value(SecretId=key)
            return response.get("SecretString")
        except ImportError:
            print("[WARNING] boto3 not installed. AWS secrets unavailable.")
            return None
        except Exception as e:  # Cloud SDK exceptions are unpredictable
            print(f"[WARNING] AWS secret retrieval failed for {key}: {e}")
            return None

    def _read_gcp_secret(self, key: str) -> Optional[str]:
        """Read from Google Cloud Secret Manager."""
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv("GCP_PROJECT_ID")
            if not project_id:
                return None
            name = f"projects/{project_id}/secrets/{key}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except ImportError:
            print("[WARNING] google-cloud-secret-manager not installed.")
            return None
        except Exception as e:  # Cloud SDK exceptions are unpredictable
            print(f"[WARNING] GCP secret retrieval failed for {key}: {e}")
            return None

    def _read_azure_secret(self, key: str) -> Optional[str]:
        """Read from Azure Key Vault."""
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential
            vault_url = os.getenv("AZURE_VAULT_URL")
            if not vault_url:
                return None
            client = SecretClient(
                vault_url=vault_url,
                credential=DefaultAzureCredential()
            )
            return client.get_secret(key).value
        except ImportError:
            print("[WARNING] azure-keyvault-secrets not installed.")
            return None
        except Exception as e:  # Cloud SDK exceptions are unpredictable
            print(f"[WARNING] Azure secret retrieval failed for {key}: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        self._cache.clear()

    def get_provider(self) -> str:
        """Return the current secrets provider."""
        return self._provider


# Singleton instance
@lru_cache(maxsize=1)
def get_secrets_manager() -> SecretsManager:
    """Get the singleton SecretsManager instance."""
    return SecretsManager()


def get_secret(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """Convenience function to get a secret from the singleton manager."""
    return get_secrets_manager().get_secret(key, default, required)


def validate_production_secrets() -> bool:
    """Validate required production secrets at startup. Exits if critical secrets are missing."""
    env_mode = os.getenv("ENV_MODE", "development")

    if env_mode != "production":
        return True

    required_secrets = [
        "JWT_SECRET_KEY",
        "DATABASE_URL",
    ]

    missing = []
    sm = get_secrets_manager()

    for secret in required_secrets:
        if not sm.get_secret(secret):
            missing.append(secret)

    if missing:
        print("\n" + "=" * 60)
        print("PRODUCTION CONFIGURATION ERROR")
        print("=" * 60)
        print("\nThe following required secrets are not configured:")
        for s in missing:
            print(f"  - {s}")
        print("\nPlease configure these secrets before starting in production mode.")
        print("=" * 60 + "\n")
        sys.exit(1)

    # Validate JWT_SECRET_KEY strength
    jwt_key = sm.get_secret("JWT_SECRET_KEY")
    if jwt_key and len(jwt_key) < 32:
        print("\n" + "=" * 60)
        print("SECURITY WARNING")
        print("=" * 60)
        print("\nJWT_SECRET_KEY should be at least 32 characters for production.")
        print("Generate a secure key with: python -c \"import secrets; print(secrets.token_hex(32))\"")
        print("=" * 60 + "\n")
        sys.exit(1)

    return True

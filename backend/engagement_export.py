"""
Engagement ZIP Export — Sprint 101
Phase X: Engagement Layer

Generates a diagnostic package ZIP containing:
  - anomaly_summary.pdf — Anomaly summary report
  - workpaper_index.json — Workpaper index data
  - manifest.json — File list with SHA-256 hashes, timestamps, platform version

ZERO-STORAGE COMPLIANCE:
  - Does NOT include uploaded financial data
  - Does NOT include individual tool exports (user downloads separately)
  - Contains only metadata, narratives, and generated reports
"""

import json
import hashlib
from io import BytesIO
from datetime import datetime, UTC
from zipfile import ZipFile, ZIP_DEFLATED
from typing import Optional

from sqlalchemy.orm import Session

from models import Client
from engagement_model import Engagement
from anomaly_summary_generator import AnomalySummaryGenerator
from workpaper_index_generator import WorkpaperIndexGenerator


PLATFORM_VERSION = "0.90.0"


class EngagementExporter:
    """Generates a diagnostic package ZIP for an engagement."""

    def __init__(self, db: Session):
        self.db = db

    def _verify_engagement_access(
        self, user_id: int, engagement_id: int
    ) -> Optional[Engagement]:
        return (
            self.db.query(Engagement)
            .join(Client, Engagement.client_id == Client.id)
            .filter(
                Engagement.id == engagement_id,
                Client.user_id == user_id,
            )
            .first()
        )

    def generate_zip(self, user_id: int, engagement_id: int) -> tuple[bytes, str]:
        """
        Generate diagnostic package ZIP.

        Returns (zip_bytes, filename) tuple.
        """
        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        client = self.db.query(Client).filter(Client.id == engagement.client_id).first()
        client_name = client.name if client else f"Client_{engagement.client_id}"

        # Generate component files
        summary_gen = AnomalySummaryGenerator(self.db)
        anomaly_pdf = summary_gen.generate_pdf(user_id, engagement_id)

        index_gen = WorkpaperIndexGenerator(self.db)
        index_data = index_gen.generate(user_id, engagement_id)
        index_json = json.dumps(index_data, indent=2, default=str).encode('utf-8')

        # Build manifest
        generated_at = datetime.now(UTC).isoformat()
        files = {
            "anomaly_summary.pdf": anomaly_pdf,
            "workpaper_index.json": index_json,
        }

        manifest = {
            "platform": "Paciolus",
            "version": PLATFORM_VERSION,
            "generated_at": generated_at,
            "engagement_id": engagement_id,
            "client_name": client_name,
            "period_start": engagement.period_start.isoformat() if engagement.period_start else "",
            "period_end": engagement.period_end.isoformat() if engagement.period_end else "",
            "files": [],
        }

        for filename, content in files.items():
            sha256 = hashlib.sha256(content).hexdigest()
            manifest["files"].append({
                "filename": filename,
                "size_bytes": len(content),
                "sha256": sha256,
            })

        manifest_json = json.dumps(manifest, indent=2).encode('utf-8')

        # Build ZIP
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'w', ZIP_DEFLATED) as zf:
            for filename, content in files.items():
                zf.writestr(filename, content)
            zf.writestr("manifest.json", manifest_json)

        zip_bytes = zip_buffer.getvalue()

        # Build download filename
        safe_client = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in client_name)
        safe_client = safe_client.strip().replace(' ', '_')
        period_end_str = engagement.period_end.strftime("%Y%m%d") if engagement.period_end else "unknown"
        download_filename = f"{safe_client}_{period_end_str}_diagnostic_package.zip"

        return zip_bytes, download_filename

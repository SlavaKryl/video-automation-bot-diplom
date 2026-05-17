from __future__ import annotations

import logging
import xmlrpc.client
from dataclasses import dataclass
from typing import Any

from backend.config import ODOO_DB, ODOO_ENABLED, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME

logger = logging.getLogger(__name__)


@dataclass
class OdooVideoDraft:
    telegram_user_id: int
    transcription: str
    preview: str


class OdooClient:
    def __init__(self) -> None:
        self._enabled = ODOO_ENABLED
        self._url = ODOO_URL
        self._db = ODOO_DB
        self._username = ODOO_USERNAME
        self._password = ODOO_PASSWORD

    @property
    def is_ready(self) -> bool:
        return self._enabled and all([self._url, self._db, self._username, self._password])

    def _connect(self) -> tuple[int, xmlrpc.client.ServerProxy]:
        common = xmlrpc.client.ServerProxy(f"{self._url}/xmlrpc/2/common")
        uid = common.authenticate(self._db, self._username, self._password, {})

        if not uid:
            raise RuntimeError("Odoo authentication failed")

        models = xmlrpc.client.ServerProxy(f"{self._url}/xmlrpc/2/object")
        return uid, models

    def create_video_job(self, draft: OdooVideoDraft) -> int | None:
        if not self.is_ready:
            logger.info("Odoo integration is disabled or not configured")
            return None

        try:
            uid, models = self._connect()
            values: dict[str, Any] = {
                "name": f"Telegram video from user {draft.telegram_user_id}",
                "source": "telegram",
                "external_ref": str(draft.telegram_user_id),
                "transcription": draft.transcription,
                "content_preview": draft.preview,
                "state": "draft",
            }
            job_id = models.execute_kw(
                self._db,
                uid,
                self._password,
                "video.job",
                "create",
                [values],
            )
            logger.info("Created Odoo video.job id=%s", job_id)
            return int(job_id)
        except Exception:
            logger.exception("Failed to create video.job in Odoo")
            return None


odoo_client = OdooClient()

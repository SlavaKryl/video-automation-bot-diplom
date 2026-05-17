from __future__ import annotations

import logging
import socket
import xmlrpc.client
from dataclasses import dataclass
from typing import Any

from backend import config

logger = logging.getLogger(__name__)


@dataclass
class OdooVideoDraft:
    telegram_user_id: int
    transcription: str
    preview: str


class OdooClient:
    def __init__(self, timeout_seconds: int = 10) -> None:
        self._timeout_seconds = timeout_seconds

    @property
    def is_ready(self) -> bool:
        return config.ODOO_ENABLED and all(
            [config.ODOO_URL, config.ODOO_DB, config.ODOO_USERNAME, config.ODOO_PASSWORD]
        )

    def _build_proxy(self, endpoint: str) -> xmlrpc.client.ServerProxy:
        transport = xmlrpc.client.Transport()
        transport.timeout = self._timeout_seconds
        return xmlrpc.client.ServerProxy(endpoint, transport=transport, allow_none=True)

    def _connect(self) -> tuple[int, xmlrpc.client.ServerProxy]:
        common = self._build_proxy(f"{config.ODOO_URL}/xmlrpc/2/common")
        uid = common.authenticate(config.ODOO_DB, config.ODOO_USERNAME, config.ODOO_PASSWORD, {})
        if not uid:
            raise RuntimeError("Odoo authentication failed: check ODOO_DB/ODOO_USERNAME/ODOO_PASSWORD")

        models = self._build_proxy(f"{config.ODOO_URL}/xmlrpc/2/object")
        return uid, models

    def _ensure_model_exists(self, uid: int, models: xmlrpc.client.ServerProxy, model_name: str) -> None:
        model_ids = models.execute_kw(
            config.ODOO_DB,
            uid,
            config.ODOO_PASSWORD,
            "ir.model",
            "search",
            [[("model", "=", model_name)]],
            {"limit": 1},
        )
        if not model_ids:
            raise RuntimeError(
                f"Odoo model '{model_name}' not found. Install module 'video_automation' first."
            )

    def create_video_job(self, draft: OdooVideoDraft) -> int | None:
        if not self.is_ready:
            logger.info("Odoo integration is disabled or incomplete. Skip create video.job")
            return None

        try:
            uid, models = self._connect()
            self._ensure_model_exists(uid, models, "video.job")

            values: dict[str, Any] = {
                "name": f"Telegram video from user {draft.telegram_user_id}",
                "source": "telegram",
                "external_ref": str(draft.telegram_user_id),
                "transcription": draft.transcription,
                "content_preview": draft.preview,
                "state": "draft",
            }

            job_id = models.execute_kw(
                config.ODOO_DB,
                uid,
                config.ODOO_PASSWORD,
                "video.job",
                "create",
                [values],
            )
            logger.info("Created Odoo video.job id=%s", job_id)
            return int(job_id)
        except (socket.timeout, TimeoutError):
            logger.exception("Timeout while communicating with Odoo")
            return None
        except RuntimeError as err:
            logger.error("Odoo integration error: %s", err)
            return None
        except xmlrpc.client.Fault as fault:
            logger.error("Odoo XML-RPC fault %s: %s", fault.faultCode, fault.faultString)
            return None
        except Exception:
            logger.exception("Unexpected error while creating video.job in Odoo")
            return None


odoo_client = OdooClient()

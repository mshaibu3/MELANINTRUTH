from __future__ import annotations

from typing import Any

from app.api.phase3_app import ApiApplication
from app.backend.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.errors import structured_error


class Phase7ApiApplication(ApiApplication):
    """Release-candidate API behavior with expiring, idempotent upload tickets."""

    def upload_request(
        self,
        access_token: str,
        payload: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        try:
            ticket = self.services.images.request_upload(
                user.id,
                payload["content_type"],
                payload["size_bytes"],
                payload["checksum_sha256"],
            )
            return 201, {
                "upload_id": ticket.upload_id,
                "upload_url": ticket.upload_url,
                "checksum_sha256": ticket.checksum_sha256,
                "expires_at": ticket.expires_at.isoformat(),
                "idempotency_key": ticket.idempotency_key,
            }
        except AuthorizationError as exc:
            return 403, structured_error("CONSENT_REQUIRED", str(exc))
        except ValidationError as exc:
            return 422, structured_error("VALIDATION_ERROR", str(exc))

    def upload_complete(
        self,
        access_token: str,
        payload: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        try:
            image, created = self.services.images.complete_upload_ticket(
                user.id,
                upload_id=payload["upload_id"],
                idempotency_key=payload["idempotency_key"],
                content_type=payload["content_type"],
                size_bytes=payload["size_bytes"],
                checksum_sha256=payload["checksum_sha256"],
            )
            return (201 if created else 200), {
                "image_id": image.id,
                "status": image.status,
                "upload_id": payload["upload_id"],
                "idempotent_replay": not created,
            }
        except AuthorizationError as exc:
            return 403, structured_error("UPLOAD_KEY_INVALID", str(exc))
        except NotFoundError as exc:
            return 404, structured_error("UPLOAD_NOT_FOUND", str(exc))
        except ConflictError as exc:
            return 409, structured_error("UPLOAD_METADATA_CONFLICT", str(exc))
        except ValidationError as exc:
            message = str(exc)
            if "expired" in message.lower():
                return 410, structured_error("UPLOAD_EXPIRED", message)
            return 422, structured_error("VALIDATION_ERROR", message)

    def openapi_contract(self) -> dict[str, Any]:
        contract = super().openapi_contract()
        contract["info"]["version"] = "0.7.0"
        schemas = contract["components"]["schemas"]
        schemas["UploadTicketResponse"] = {
            "type": "object",
            "required": [
                "upload_id",
                "upload_url",
                "checksum_sha256",
                "expires_at",
                "idempotency_key",
            ],
            "properties": {
                "upload_id": {"type": "string"},
                "upload_url": {"type": "string", "format": "uri"},
                "checksum_sha256": {"type": "string"},
                "expires_at": {"type": "string", "format": "date-time"},
                "idempotency_key": {"type": "string"},
            },
        }
        schemas["UploadCompleteRequest"] = {
            "type": "object",
            "required": [
                "upload_id",
                "idempotency_key",
                "content_type",
                "size_bytes",
                "checksum_sha256",
            ],
        }
        return contract

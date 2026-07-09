from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .audit import AuditService
from .consent import ConsentService
from .entities import ConsentPurpose, ImageCapture, now
from .errors import AuthorizationError, NotFoundError, ValidationError
from .repository import InMemoryRepository

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/heic"}
MAX_IMAGE_BYTES = 10_485_760


@dataclass(frozen=True)
class UploadTicket:
    upload_url: str
    storage_ref: str
    checksum_sha256: str


class LocalStorageProvider:
    def signed_upload_url(self, tenant_id: str, checksum_sha256: str) -> UploadTicket:
        storage_ref = f"encrypted-local://tenant/{tenant_id}/image/{checksum_sha256}"
        signature = hashlib.sha256(storage_ref.encode()).hexdigest()[:24]
        return UploadTicket(upload_url=f"local-signed://upload/{signature}", storage_ref=storage_ref, checksum_sha256=checksum_sha256)


class ImageService:
    def __init__(self, repo: InMemoryRepository, audit: AuditService, consent: ConsentService, storage: LocalStorageProvider | None = None):
        self.repo = repo
        self.audit = audit
        self.consent = consent
        self.storage = storage or LocalStorageProvider()

    def request_upload(self, user_id: str, content_type: str, size_bytes: int, checksum_sha256: str) -> UploadTicket:
        self.consent.assert_granted(user_id, ConsentPurpose.IMAGE_PROCESSING)
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValidationError("unsupported image content type")
        if size_bytes > MAX_IMAGE_BYTES:
            raise ValidationError("image exceeds maximum file size")
        if len(checksum_sha256) != 64 or any(c not in "0123456789abcdef" for c in checksum_sha256.lower()):
            raise ValidationError("checksum_sha256 must be a lowercase SHA-256 hex digest")
        user = self.repo.users[user_id]
        ticket = self.storage.signed_upload_url(user.tenant_id, checksum_sha256.lower())
        self.audit.record("image.upload_requested", "image", None, user.id, user.tenant_id, {"content_type": content_type, "size_bytes": size_bytes})
        return ticket

    def complete_upload(self, user_id: str, ticket: UploadTicket, content_type: str, size_bytes: int) -> ImageCapture:
        self.consent.assert_granted(user_id, ConsentPurpose.IMAGE_PROCESSING)
        user = self.repo.users[user_id]
        image = ImageCapture(user_id=user.id, tenant_id=user.tenant_id, checksum_sha256=ticket.checksum_sha256, content_type=content_type, size_bytes=size_bytes, storage_ref=ticket.storage_ref)
        self.repo.images[image.id] = image
        self.audit.record("image.upload_completed", "image", image.id, user.id, user.tenant_id, {"content_type": content_type, "size_bytes": size_bytes})
        return image

    def public_metadata(self, user_id: str, image_id: str) -> dict[str, str | int]:
        image = self.repo.images.get(image_id)
        if not image or image.user_id != user_id or image.deleted_at:
            raise NotFoundError("image not found")
        self.audit.record("image.accessed", "image", image.id, user_id, image.tenant_id, {})
        return {"id": image.id, "content_type": image.content_type, "size_bytes": image.size_bytes, "status": image.status, "exif_policy": "strip_on_ingest"}

    def delete(self, user_id: str, image_id: str) -> None:
        image = self.repo.images.get(image_id)
        if not image or image.user_id != user_id:
            raise NotFoundError("image not found")
        image.deleted_at = now()
        image.status = "deleted"
        self.audit.record("image.deleted", "image", image.id, user_id, image.tenant_id, {})

    def assert_available(self, user_id: str, image_id: str) -> ImageCapture:
        image = self.repo.images.get(image_id)
        if not image or image.user_id != user_id or image.deleted_at:
            raise AuthorizationError("image is unavailable or not owned by user")
        return image

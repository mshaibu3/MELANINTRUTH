from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock

from .audit import AuditService
from .consent import ConsentService
from .entities import ConsentPurpose, ImageCapture, now
from .errors import AuthorizationError, ConflictError, NotFoundError, ValidationError
from .repository import InMemoryRepository

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/heic"}
MAX_IMAGE_BYTES = 10_485_760
UPLOAD_TICKET_TTL = timedelta(minutes=5)
COMPLETED_UPLOAD_REPLAY_TTL = timedelta(hours=1)


@dataclass(frozen=True)
class UploadTicket:
    upload_id: str
    upload_url: str
    storage_ref: str
    checksum_sha256: str
    content_type: str
    size_bytes: int
    user_id: str
    expires_at: datetime
    idempotency_key: str

    @property
    def expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at


@dataclass(frozen=True)
class CompletedUpload:
    image: ImageCapture
    user_id: str
    content_type: str
    size_bytes: int
    checksum_sha256: str
    idempotency_key_digest: str
    ticket_expires_at: datetime
    replay_expires_at: datetime


class LocalStorageProvider:
    def signed_upload_url(
        self,
        tenant_id: str,
        checksum_sha256: str,
        *,
        upload_id: str | None = None,
        content_type: str = "image/jpeg",
        size_bytes: int = 1,
        user_id: str = "legacy",
        expires_at: datetime | None = None,
        idempotency_key: str | None = None,
    ) -> UploadTicket:
        resolved_upload_id = upload_id or f"upl_{secrets.token_hex(12)}"
        resolved_expiry = expires_at or datetime.now(timezone.utc) + UPLOAD_TICKET_TTL
        resolved_key = idempotency_key or secrets.token_urlsafe(24)
        storage_ref = f"encrypted-local://tenant/{tenant_id}/image/{checksum_sha256}"
        signature_input = f"{storage_ref}:{resolved_upload_id}:{resolved_expiry.isoformat()}"
        signature = hashlib.sha256(signature_input.encode()).hexdigest()[:24]
        return UploadTicket(
            upload_id=resolved_upload_id,
            upload_url=f"local-signed://upload/{signature}",
            storage_ref=storage_ref,
            checksum_sha256=checksum_sha256,
            content_type=content_type,
            size_bytes=size_bytes,
            user_id=user_id,
            expires_at=resolved_expiry,
            idempotency_key=resolved_key,
        )


class ImageService:
    def __init__(
        self,
        repo: InMemoryRepository,
        audit: AuditService,
        consent: ConsentService,
        storage: LocalStorageProvider | None = None,
    ):
        self.repo = repo
        self.audit = audit
        self.consent = consent
        self.storage = storage or LocalStorageProvider()
        self._upload_tickets: dict[str, UploadTicket] = {}
        self._completed_uploads: dict[str, CompletedUpload] = {}
        self._upload_lock = RLock()

    @staticmethod
    def _idempotency_key_digest(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    def _cleanup_upload_state(
        self,
        current_time: datetime,
        *,
        preserve_upload_id: str | None = None,
    ) -> None:
        expired_tickets = [
            upload_id
            for upload_id, ticket in self._upload_tickets.items()
            if upload_id != preserve_upload_id and ticket.expires_at <= current_time
        ]
        for upload_id in expired_tickets:
            self._upload_tickets.pop(upload_id, None)

        expired_completions = [
            upload_id
            for upload_id, completion in self._completed_uploads.items()
            if completion.replay_expires_at <= current_time
            or completion.image.deleted_at is not None
        ]
        for upload_id in expired_completions:
            self._completed_uploads.pop(upload_id, None)

    def _validate_upload_metadata(
        self,
        content_type: str,
        size_bytes: int,
        checksum_sha256: str,
    ) -> str:
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValidationError("unsupported image content type")
        if size_bytes <= 0 or size_bytes > MAX_IMAGE_BYTES:
            raise ValidationError("image exceeds maximum file size")
        normalized_checksum = checksum_sha256.lower()
        if len(normalized_checksum) != 64 or any(
            character not in "0123456789abcdef" for character in normalized_checksum
        ):
            raise ValidationError("checksum_sha256 must be a lowercase SHA-256 hex digest")
        return normalized_checksum

    def request_upload(
        self,
        user_id: str,
        content_type: str,
        size_bytes: int,
        checksum_sha256: str,
    ) -> UploadTicket:
        self.consent.assert_granted(user_id, ConsentPurpose.IMAGE_PROCESSING)
        normalized_checksum = self._validate_upload_metadata(
            content_type,
            size_bytes,
            checksum_sha256,
        )
        user = self.repo.users[user_id]
        upload_id = f"upl_{secrets.token_hex(12)}"
        ticket = self.storage.signed_upload_url(
            user.tenant_id,
            normalized_checksum,
            upload_id=upload_id,
            content_type=content_type,
            size_bytes=size_bytes,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + UPLOAD_TICKET_TTL,
            idempotency_key=secrets.token_urlsafe(24),
        )
        with self._upload_lock:
            self._cleanup_upload_state(datetime.now(timezone.utc))
            self._upload_tickets[ticket.upload_id] = ticket
        self.audit.record(
            "image.upload_requested",
            "image",
            None,
            user.id,
            user.tenant_id,
            {"content_type": content_type, "size_bytes": size_bytes},
        )
        return ticket

    def complete_upload(
        self,
        user_id: str,
        ticket: UploadTicket,
        content_type: str,
        size_bytes: int,
    ) -> ImageCapture:
        """Legacy completion path retained for Phase 3-6 dependency-light tests."""
        self.consent.assert_granted(user_id, ConsentPurpose.IMAGE_PROCESSING)
        user = self.repo.users[user_id]
        image = ImageCapture(
            user_id=user.id,
            tenant_id=user.tenant_id,
            checksum_sha256=ticket.checksum_sha256,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_ref=ticket.storage_ref,
        )
        self.repo.images[image.id] = image
        self.audit.record(
            "image.upload_completed",
            "image",
            image.id,
            user.id,
            user.tenant_id,
            {"content_type": content_type, "size_bytes": size_bytes},
        )
        return image

    def complete_upload_ticket(
        self,
        user_id: str,
        *,
        upload_id: str,
        idempotency_key: str,
        content_type: str,
        size_bytes: int,
        checksum_sha256: str,
    ) -> tuple[ImageCapture, bool]:
        self.consent.assert_granted(user_id, ConsentPurpose.IMAGE_PROCESSING)
        normalized_checksum = self._validate_upload_metadata(
            content_type,
            size_bytes,
            checksum_sha256,
        )
        current_time = datetime.now(timezone.utc)
        supplied_key_digest = self._idempotency_key_digest(idempotency_key)

        with self._upload_lock:
            self._cleanup_upload_state(
                current_time,
                preserve_upload_id=upload_id,
            )
            completed = self._completed_uploads.get(upload_id)
            if completed is not None:
                if completed.user_id != user_id:
                    raise NotFoundError("upload ticket not found")
                if not secrets.compare_digest(
                    completed.idempotency_key_digest,
                    supplied_key_digest,
                ):
                    raise AuthorizationError("upload idempotency key is invalid")
                if (
                    completed.content_type != content_type
                    or completed.size_bytes != size_bytes
                    or completed.checksum_sha256 != normalized_checksum
                ):
                    raise ConflictError("upload completion metadata does not match the ticket")
                return completed.image, False

            ticket = self._upload_tickets.get(upload_id)
            if ticket is None or ticket.user_id != user_id:
                raise NotFoundError("upload ticket not found")
            if not secrets.compare_digest(ticket.idempotency_key, idempotency_key):
                raise AuthorizationError("upload idempotency key is invalid")
            if ticket.expired:
                self._upload_tickets.pop(upload_id, None)
                raise ValidationError("upload ticket expired")
            if (
                ticket.content_type != content_type
                or ticket.size_bytes != size_bytes
                or ticket.checksum_sha256 != normalized_checksum
            ):
                raise ConflictError("upload completion metadata does not match the ticket")

            image = self.complete_upload(user_id, ticket, content_type, size_bytes)
            self._completed_uploads[upload_id] = CompletedUpload(
                image=image,
                user_id=user_id,
                content_type=content_type,
                size_bytes=size_bytes,
                checksum_sha256=normalized_checksum,
                idempotency_key_digest=supplied_key_digest,
                ticket_expires_at=ticket.expires_at,
                replay_expires_at=current_time + COMPLETED_UPLOAD_REPLAY_TTL,
            )
            self._upload_tickets.pop(upload_id, None)
            return image, True

    def public_metadata(self, user_id: str, image_id: str) -> dict[str, str | int]:
        image = self.repo.images.get(image_id)
        if not image or image.user_id != user_id or image.deleted_at:
            raise NotFoundError("image not found")
        self.audit.record("image.accessed", "image", image.id, user_id, image.tenant_id, {})
        return {
            "id": image.id,
            "content_type": image.content_type,
            "size_bytes": image.size_bytes,
            "status": image.status,
            "exif_policy": "strip_on_ingest",
        }

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

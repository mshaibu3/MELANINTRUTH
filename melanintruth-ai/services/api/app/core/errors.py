from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ERROR_CODES = {
    "AUTH_REQUIRED",
    "FORBIDDEN",
    "VALIDATION_ERROR",
    "CONSENT_REQUIRED",
    "CONSENT_REVOKED",
    "IMAGE_NOT_FOUND",
    "IMAGE_QUALITY_TOO_LOW",
    "ANALYSIS_NOT_FOUND",
    "ANALYSIS_NOT_COMPLETED",
    "RENDER_REJECTED_BY_SAFETY_GATE",
    "TENANT_ACCESS_DENIED",
    "GOVERNANCE_APPROVAL_REQUIRED",
    "INTERNAL_ERROR",
}


@dataclass
class ApiError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict[str, Any] = field(default_factory=dict)

    def response(self) -> dict[str, Any]:
        return {"error": {"code": self.code, "message": self.message, "details": self.details}}


def structured_error(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or {}}}

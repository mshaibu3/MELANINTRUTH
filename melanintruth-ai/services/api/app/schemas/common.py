from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCIENTIFIC_LIMITATION = "This is an estimated visible skin appearance under standardised lighting assumptions, not an exact biological melanin measurement."

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:
    BaseModel = object  # type: ignore[assignment]

    def Field(default: Any = None, **_: Any) -> Any:  # type: ignore[override]
        return default


if BaseModel is object:
    @dataclass
    class ErrorDetail:
        code: str
        message: str
        details: dict[str, Any] = field(default_factory=dict)

    @dataclass
    class ErrorEnvelope:
        error: ErrorDetail

    @dataclass
    class ConfidenceMetadata:
        confidence_score: float
        uncertainty_score: float

else:
    class ErrorDetail(BaseModel):
        code: str = Field(..., examples=["CONSENT_REQUIRED"])
        message: str
        details: dict[str, Any] = Field(default_factory=dict)

    class ErrorEnvelope(BaseModel):
        error: ErrorDetail

    class ConfidenceMetadata(BaseModel):
        confidence_score: float = Field(ge=0, le=1)
        uncertainty_score: float = Field(ge=0, le=1)


@dataclass
class TokenContext:
    user_id: str
    tenant_id: str
    roles: list[str] = field(default_factory=list)

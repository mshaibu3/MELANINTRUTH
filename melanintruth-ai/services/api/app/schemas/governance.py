from __future__ import annotations

from app.schemas.common import BaseModel, Field

DEFAULT_PROHIBITED_USES = [
    "beautification_filter",
    "skin_whitening",
    "skin_lightening",
    "texture_smoothing",
    "identity_alteration",
]

if BaseModel is object:
    class ModelVersionRequest(dict):
        pass
else:
    class ModelVersionRequest(BaseModel):
        model_id: str
        version: str
        purpose: str
        status: str
        known_limitations: str = Field(min_length=10)
        supported_skin_tone_ranges: list[str] = Field(
            default_factory=lambda: ["melanin-rich", "deep brown", "brown", "dark skin"]
        )
        supported_lighting_conditions: list[str] = Field(
            default_factory=lambda: ["D65 daylight", "neutral studio", "indoor controlled"]
        )
        prohibited_uses: list[str] = Field(default_factory=lambda: DEFAULT_PROHIBITED_USES.copy())
        approved_by: str | None = None
        approval_date: str | None = None

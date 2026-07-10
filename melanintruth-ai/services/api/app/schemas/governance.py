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
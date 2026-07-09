from typing import Any
from app.schemas.common import BaseModel, Field, SCIENTIFIC_LIMITATION
if BaseModel is object:
    class AnalysisJobRequest(dict):
        pass
else:
    class AnalysisJobRequest(BaseModel):
        image_id: str
        cloud: bool = True
        sample_value: int | None = Field(default=None, ge=0, le=255)
        pixels: list[list[tuple[int, int, int]]] | None = None
    class AnalysisJobResponse(BaseModel):
        id: str
        status: str
        confidence_score: float
        uncertainty_score: float
        lighting_quality_score: float
        capture_quality_score: float
        limitation_warning: str = SCIENTIFIC_LIMITATION
        retake_recommendation: str | None
        result: dict[str, Any]

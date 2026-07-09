from typing import Any
from app.schemas.common import BaseModel, SCIENTIFIC_LIMITATION
if BaseModel is object:
    class RenderRequest(dict):
        pass
else:
    class RenderRequest(BaseModel):
        analysis_id: str
        confidence: float | None = None
        rendered: list[list[tuple[int, int, int]]] | None = None
        original: list[list[tuple[int, int, int]]] | None = None
    class RenderResponse(BaseModel):
        id: str
        render_status: str
        confidence_score: float
        uncertainty_score: float
        safety_gate_result: dict[str, Any]
        limitation_warning: str = SCIENTIFIC_LIMITATION
        public_render_available: bool

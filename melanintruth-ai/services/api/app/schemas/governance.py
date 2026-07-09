from app.schemas.common import BaseModel, Field
if BaseModel is object:
    class ModelVersionRequest(dict):
        pass
else:
    class ModelVersionRequest(BaseModel):
        model_id: str
        version: str
        purpose: str
        status: str
        known_limitations: str = Field(min_length=20)
        supported_skin_tone_ranges: list[str]
        supported_lighting_conditions: list[str]
        prohibited_uses: list[str]
        approved_by: str | None = None
        approval_date: bool | None = None

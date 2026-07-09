from app.schemas.common import BaseModel, Field
if BaseModel is object:
    class ConsentGrantRequest(dict):
        pass
else:
    class ConsentGrantRequest(BaseModel):
        purpose: str = Field(..., examples=["image_processing"])
        version: str = "2026-07"

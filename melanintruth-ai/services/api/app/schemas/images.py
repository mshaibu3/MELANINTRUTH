from app.schemas.common import BaseModel, Field
if BaseModel is object:
    class UploadRequest(dict):
        pass
else:
    class UploadRequest(BaseModel):
        content_type: str = Field(..., examples=["image/jpeg"])
        size_bytes: int = Field(gt=0, le=10_485_760)
        checksum_sha256: str = Field(..., min_length=64, max_length=64)

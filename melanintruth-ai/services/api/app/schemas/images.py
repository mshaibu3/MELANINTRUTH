from app.schemas.common import BaseModel, Field

if BaseModel is object:

    class UploadRequest(dict):
        pass

    class UploadCompleteRequest(dict):
        pass
else:

    class UploadRequest(BaseModel):
        content_type: str = Field(..., examples=["image/jpeg"])
        size_bytes: int = Field(gt=0, le=10_485_760)
        checksum_sha256: str = Field(..., min_length=64, max_length=64)

    class UploadCompleteRequest(UploadRequest):
        upload_id: str = Field(..., min_length=8, max_length=128)
        idempotency_key: str = Field(..., min_length=16, max_length=256)

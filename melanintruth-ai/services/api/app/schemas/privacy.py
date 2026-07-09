from app.schemas.common import BaseModel
if BaseModel is object:
    class PrivacyRequestResponse(dict):
        pass
else:
    class PrivacyRequestResponse(BaseModel):
        request_id: str
        status: str

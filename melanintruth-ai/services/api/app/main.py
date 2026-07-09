from __future__ import annotations

from app.api.phase3_app import ApiApplication
from app.api.router import create_fastapi_app
from app.services.container import repository_from_settings

api_application = ApiApplication(repository_from_settings())
app = create_fastapi_app(api_application)

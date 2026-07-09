from __future__ import annotations

from dataclasses import dataclass

from app.api.phase3_app import ApiApplication


@dataclass(frozen=True)
class RequestContext:
    ip: str = "context-not-captured"
    user_agent: str = "context-not-captured"


def get_api_application() -> ApiApplication:
    return ApiApplication()

from typing import Any, Callable

from app.api.phase3_app import ApiApplication
from app.core.errors import ApiError


def _payload(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    if isinstance(model, dict):
        return model
    return dict(model)


def build_openapi_contract(app: ApiApplication) -> dict[str, object]:
    return app.openapi_contract()


def create_fastapi_app(api: ApiApplication | None = None) -> Any:
    """Create the real FastAPI app when FastAPI is installed.

    The function is intentionally import-guarded so dependency-light tests still run in
    constrained environments while production installs use real FastAPI decorators.
    """
    try:
        from fastapi import Depends, FastAPI, HTTPException, Request
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse
        from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

        from app.core.config import settings
        from app.schemas.analysis import AnalysisJobRequest
        from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest
        from app.schemas.consent import ConsentGrantRequest
        from app.schemas.common import ErrorEnvelope
        from app.schemas.images import UploadRequest
        from app.schemas.renders import RenderRequest
    except ModuleNotFoundError:
        return api or ApiApplication()

    state = api or ApiApplication()
    app = FastAPI(title="MelaninTruth AI API", version="0.3.7")
    cors_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def secure_headers(request: Request, call_next: Callable[..., Any]) -> Any:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.exception_handler(ApiError)
    async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.response())

    @app.exception_handler(HTTPException)
    async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "AUTH_REQUIRED" if exc.status_code == 401 else "FORBIDDEN",
                    "message": str(exc.detail),
                    "details": {},
                }
            },
        )

    bearer_scheme = HTTPBearer(auto_error=False)

    def bearer(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> str:
        if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "AUTH_REQUIRED",
                        "message": "Bearer token required.",
                        "details": {},
                    }
                },
            )
        return credentials.credentials

    def unwrap(result: tuple[int, dict[str, Any]]) -> dict[str, Any]:
        status, body = result
        if status >= 400:
            raise HTTPException(status_code=status, detail=body)
        return body

    @app.get("/health", tags=["health"], responses={400: {"model": ErrorEnvelope}})
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/auth/register", tags=["auth"])
    def register(payload: RegisterRequest) -> dict[str, Any]:
        return unwrap(state.register(_payload(payload)))

    @app.post("/auth/login", tags=["auth"])
    def login(payload: LoginRequest) -> dict[str, Any]:
        return unwrap(state.login(_payload(payload)))

    @app.post("/auth/refresh", tags=["auth"])
    def refresh(payload: RefreshRequest) -> dict[str, Any]:
        return unwrap(state.refresh(_payload(payload)))

    @app.post("/auth/logout", tags=["auth"])
    def logout(payload: dict[str, str], token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.logout(token, payload["session_id"]))

    @app.get("/auth/sessions", tags=["auth"])
    def sessions(token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.sessions(token))

    @app.delete("/auth/sessions/{session_id}", tags=["auth"])
    def delete_session(session_id: str, token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.logout(token, session_id))

    @app.post("/auth/account-deletion-request", tags=["auth"])
    def account_deletion_request(token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.account_deletion_request(token))

    @app.get("/consent", tags=["consent"])
    def list_consent(token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.list_consent(token))

    @app.post("/consent", tags=["consent"])
    def grant_consent(payload: ConsentGrantRequest, token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.grant_consent(token, _payload(payload)))

    @app.patch("/consent/{consent_id}/revoke", tags=["consent"])
    def revoke_consent(consent_id: str, token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.revoke_consent(token, consent_id))

    @app.post("/images/upload-request", tags=["images"])
    def upload_request(payload: UploadRequest, token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.upload_request(token, _payload(payload)))

    @app.post("/images/upload-complete", tags=["images"])
    def upload_complete(payload: UploadRequest, token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.upload_complete(token, _payload(payload)))

    @app.get("/images/{image_id}", tags=["images"])
    def get_image(image_id: str, token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.get_image(token, image_id))

    @app.delete("/images/{image_id}", tags=["images"])
    def delete_image(image_id: str, token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.delete_image(token, image_id))

    @app.post("/analysis/jobs", tags=["analysis"])
    def create_analysis(payload: AnalysisJobRequest, token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.create_analysis(token, _payload(payload)))

    @app.get("/analysis/jobs", tags=["analysis"])
    def list_analysis(token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.list_analysis(token))

    @app.get("/analysis/jobs/{job_id}", tags=["analysis"])
    def get_analysis(job_id: str, token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.get_analysis(token, job_id))

    @app.post("/renders", tags=["renders"])
    def create_render(payload: RenderRequest, token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.create_render(token, _payload(payload)))

    @app.get("/renders", tags=["renders"])
    def list_renders(token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.list_renders(token))

    @app.get("/renders/{render_id}", tags=["renders"])
    def get_render(render_id: str, token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.get_render(token, render_id))

    @app.post("/privacy/export", tags=["privacy"])
    def privacy_export(token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.privacy_export(token))

    @app.get("/privacy/export/{request_id}", tags=["privacy"])
    def get_privacy_export(request_id: str, token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.get_privacy_export(token, request_id))

    @app.post("/privacy/delete", tags=["privacy"])
    def privacy_delete(token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.privacy_delete(token))

    @app.get("/governance/model-versions", tags=["governance"])
    def model_versions(token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.governance_model_list(token))

    @app.post("/governance/model-versions", tags=["governance"])
    def create_model_version(payload: dict[str, Any], token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.governance_model_create(token, payload))

    @app.get("/governance/bias-reports", tags=["governance"])
    def bias_reports(token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.bias_reports(token))

    @app.get("/governance/dataset-versions", tags=["governance"])
    def dataset_versions(token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.dataset_list(token))

    @app.post("/governance/dataset-versions", tags=["governance"])
    def create_dataset_version(payload: dict[str, Any], token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.dataset_create(token, payload))

    @app.post("/governance/incidents", tags=["governance"])
    def create_incident(payload: dict[str, Any], token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.incident_create(token, payload))

    @app.get("/governance/audit", tags=["governance"])
    def audit(token: str = Depends(bearer)) -> dict[str, Any]:
        return unwrap(state.audit(token))

    return app

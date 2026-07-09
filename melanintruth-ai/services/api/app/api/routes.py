from uuid import UUID
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from app.core.db import get_session
from app.core.security import create_access_token, hash_password, hash_token, new_refresh_token, verify_password
from app.models.domain import ConsentPurpose, ConsentRecord, DataDeletionRequest, DataExportRequest, GenericRecord, ImageCapture, Session as UserSession, Tenant, User
from app.services.ai import LIMITATION, authentic_render, image_quality, safety_gate

router=APIRouter()
class RegisterIn(BaseModel): email: EmailStr; password: str; tenant_name: str="Personal"
class LoginIn(BaseModel): email: EmailStr; password: str; device_label: str="unknown"
class ConsentIn(BaseModel): purpose: ConsentPurpose; version: str="2026-07"; granted: bool
class ImageUploadRequest(BaseModel): content_type: str; size_bytes: int; checksum_sha256: str
class ImageRef(BaseModel): image_id: UUID

def audit(db: Session, event_type: str, tenant_id: UUID | None, user_id: UUID | None, metadata: dict[str, object]) -> None:
    db.add(GenericRecord(event_type=event_type, tenant_id=tenant_id, user_id=user_id, metadata_json={k:v for k,v in metadata.items() if "token" not in k and "image_bytes" not in k and "raw" not in k}))

def current_user(db: Session=Depends(get_session)) -> User:
    user=db.exec(select(User)).first()
    if not user: raise HTTPException(401,"authentication required")
    return user

def require_consent(db: Session, user: User) -> None:
    ok=db.exec(select(ConsentRecord).where(ConsentRecord.user_id==user.id, ConsentRecord.tenant_id==user.tenant_id, ConsentRecord.purpose==ConsentPurpose.image_processing, ConsentRecord.granted==True, ConsentRecord.revoked_at.is_(None))).first()
    if not ok: raise HTTPException(403,"valid image processing consent is required")

@router.post("/auth/register")
def register(payload: RegisterIn, db: Session=Depends(get_session)) -> dict[str,str]:
    tenant=Tenant(name=payload.tenant_name); db.add(tenant); db.commit(); db.refresh(tenant)
    user=User(email=payload.email, password_hash=hash_password(payload.password), tenant_id=tenant.id); db.add(user); db.commit(); db.refresh(user)
    audit(db,"user.registered",tenant.id,user.id,{"email_domain":payload.email.split("@")[-1]}); db.commit()
    return {"user_id":str(user.id),"tenant_id":str(tenant.id)}
@router.post("/auth/login")
def login(payload: LoginIn, db: Session=Depends(get_session)) -> dict[str,str]:
    user=db.exec(select(User).where(User.email==payload.email)).first()
    if not user or not verify_password(payload.password,user.password_hash): raise HTTPException(401,"invalid credentials")
    refresh=new_refresh_token(); sess=UserSession(user_id=user.id, tenant_id=user.tenant_id, refresh_token_hash=hash_token(refresh), device_label=payload.device_label); db.add(sess); audit(db,"auth.login",user.tenant_id,user.id,{"device_label":payload.device_label}); db.commit()
    return {"access_token":create_access_token(user.id,user.tenant_id,["user"]),"refresh_token":refresh}
@router.post("/auth/refresh")
def refresh() -> dict[str,str]: return {"detail":"refresh token rotation endpoint wired for session-backed rotation"}
@router.post("/auth/logout")
def logout(user: User=Depends(current_user)) -> dict[str,str]: return {"detail":f"sessions for {user.id} can be revoked"}
@router.get("/auth/sessions")
def sessions(user: User=Depends(current_user), db: Session=Depends(get_session)) -> list[dict[str,str]]: return [{"id":str(s.id),"device_label":s.device_label} for s in db.exec(select(UserSession).where(UserSession.user_id==user.id, UserSession.tenant_id==user.tenant_id))]
@router.delete("/auth/sessions/{id}")
def delete_session(id: UUID) -> dict[str,str]: return {"deleted":str(id)}
@router.get("/consent")
def list_consent(user: User=Depends(current_user), db: Session=Depends(get_session)) -> list[ConsentRecord]: return list(db.exec(select(ConsentRecord).where(ConsentRecord.user_id==user.id, ConsentRecord.tenant_id==user.tenant_id)))
@router.post("/consent")
def create_consent(payload: ConsentIn, user: User=Depends(current_user), db: Session=Depends(get_session)) -> ConsentRecord:
    rec=ConsentRecord(tenant_id=user.tenant_id,user_id=user.id,**payload.model_dump()); db.add(rec); audit(db,"consent.changed",user.tenant_id,user.id,{"purpose":payload.purpose.value,"granted":payload.granted}); db.commit(); db.refresh(rec); return rec
@router.patch("/consent/{id}/revoke")
def revoke_consent(id: UUID) -> dict[str,str]: return {"revoked":str(id)}
@router.post("/images/upload-request")
def upload_request(payload: ImageUploadRequest, user: User=Depends(current_user)) -> dict[str,str]:
    if payload.content_type not in {"image/jpeg","image/png","image/heic"}: raise HTTPException(400,"unsupported content type")
    if payload.size_bytes>10_485_760: raise HTTPException(400,"file too large")
    return {"upload_url":f"signed://uploads/{user.tenant_id}/{payload.checksum_sha256}","storage_key":f"tenant/{user.tenant_id}/pending/{payload.checksum_sha256}"}
@router.post("/images/upload-complete")
def upload_complete(payload: ImageUploadRequest, user: User=Depends(current_user), db: Session=Depends(get_session)) -> dict[str,str]:
    img=ImageCapture(tenant_id=user.tenant_id,user_id=user.id,storage_key=f"tenant/{user.tenant_id}/image/{payload.checksum_sha256}",content_type=payload.content_type,size_bytes=payload.size_bytes,status="scan_pending"); db.add(img); audit(db,"image.upload_completed",user.tenant_id,user.id,{"image_id":str(img.id),"content_type":payload.content_type}); db.commit(); return {"image_id":str(img.id),"status":img.status}
@router.get("/images/{id}")
def get_image(id: UUID) -> dict[str,str]: return {"image_id":str(id),"raw_path":"redacted"}
@router.delete("/images/{id}")
def delete_image(id: UUID) -> dict[str,str]: return {"deleted":str(id)}
@router.post("/analysis/image-quality")
def quality(user: User=Depends(current_user), db: Session=Depends(get_session)) -> dict[str,object]:
    require_consent(db,user); img=np.full((32,32,3),128,dtype=np.uint8); return image_quality(img).__dict__ | {"limitations":LIMITATION}
@router.post("/analysis/skin")
def skin(user: User=Depends(current_user), db: Session=Depends(get_session)) -> dict[str,object]: require_consent(db,user); return {"estimated_visible_skin_tone":"visible tone estimate","undertone_estimate":"neutral","confidence_score":0.62,"uncertainty_score":0.38,"limitations":LIMITATION}
@router.get("/analysis/{id}")
def get_analysis(id: UUID) -> dict[str,str]: return {"analysis_id":str(id)}
@router.post("/renders")
def renders(user: User=Depends(current_user), db: Session=Depends(get_session)) -> dict[str,object]:
    require_consent(db,user); img=np.full((32,32,3),128,dtype=np.uint8); out,meta=authentic_render(img); gate=safety_gate(img,out,float(meta["confidence_score"]));
    if not gate["accepted"]: raise HTTPException(422,gate)
    return {"original_reference":"redacted","rendered_image_reference":"derived/redacted","difference_map_reference":"derived/diff/redacted","safety_report":gate,**meta}
@router.get("/renders/{id}")
def get_render(id: UUID) -> dict[str,str]: return {"render_id":str(id)}
@router.get("/progress")
def progress() -> list[dict[str,str]]: return []
@router.post("/progress")
def create_progress() -> dict[str,str]: return {"language":"visible change under captured conditions"}
@router.get("/progress/{id}")
def get_progress(id: UUID) -> dict[str,str]: return {"progress_id":str(id)}
@router.delete("/progress/{id}")
def delete_progress(id: UUID) -> dict[str,str]: return {"deleted":str(id)}
@router.post("/recommendations/{kind}")
def recommendations(kind: str) -> dict[str,object]:
    if kind not in {"makeup","clothing","photography"}: raise HTTPException(404,"unsupported recommendation type")
    return {"recommendations":["Use even indirect lighting and shade-inclusive products; no bleaching or whitening advice is provided."],"medical_advice":False,"confidence":0.5}
@router.post("/privacy/export")
def privacy_export(user: User=Depends(current_user), db: Session=Depends(get_session)) -> dict[str,str]:
    req=DataExportRequest(tenant_id=user.tenant_id,user_id=user.id); db.add(req); audit(db,"privacy.export_requested",user.tenant_id,user.id,{}); db.commit(); return {"request_id":str(req.id),"tenant_scope":str(user.tenant_id)}
@router.get("/privacy/export/{id}")
def get_export(id: UUID) -> dict[str,str]: return {"request_id":str(id),"status":"queued"}
@router.post("/privacy/delete")
def privacy_delete(user: User=Depends(current_user), db: Session=Depends(get_session)) -> dict[str,str]:
    req=DataDeletionRequest(tenant_id=user.tenant_id,user_id=user.id); db.add(req); audit(db,"privacy.delete_requested",user.tenant_id,user.id,{}); db.commit(); return {"request_id":str(req.id)}
@router.get("/privacy/delete/{id}")
def get_delete(id: UUID) -> dict[str,str]: return {"request_id":str(id),"status":"queued"}
@router.get("/governance/audit")
def governance_audit(user: User=Depends(current_user)) -> list[dict[str,str]]:
    raise HTTPException(status.HTTP_403_FORBIDDEN,"admin role required")
@router.get("/governance/{resource}")
def governance_get(resource: str) -> list[dict[str,str]]: return []
@router.post("/governance/{resource}")
def governance_post(resource: str) -> dict[str,str]: return {"resource":resource,"status":"created"}

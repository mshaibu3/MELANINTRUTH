from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from sqlmodel import JSON, Column, Field, SQLModel

class ConsentPurpose(str, Enum):
    image_processing="image_processing"; cloud_processing="cloud_processing"; local_processing="local_processing"; data_retention="data_retention"; model_improvement="model_improvement"; enterprise_sharing="enterprise_sharing"; marketing="marketing"; analytics="analytics"

class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: datetime | None = Field(default=None, index=True)

class Tenant(TimestampMixin, table=True):
    __tablename__="tenants"; id: UUID = Field(default_factory=uuid4, primary_key=True); name: str = Field(index=True)
class User(TimestampMixin, table=True):
    __tablename__="users"; id: UUID = Field(default_factory=uuid4, primary_key=True); tenant_id: UUID = Field(index=True); email: str = Field(unique=True, index=True); password_hash: str; is_verified: bool=False; mfa_enabled: bool=False
class Session(TimestampMixin, table=True):
    __tablename__="sessions"; id: UUID = Field(default_factory=uuid4, primary_key=True); tenant_id: UUID=Field(index=True); user_id: UUID=Field(index=True); refresh_token_hash: str; device_label: str; revoked_at: datetime|None=None
class Role(TimestampMixin, table=True):
    __tablename__="roles"; id: UUID=Field(default_factory=uuid4, primary_key=True); name: str=Field(index=True); tenant_id: UUID|None=Field(default=None,index=True)
class Permission(TimestampMixin, table=True):
    __tablename__="permissions"; id: UUID=Field(default_factory=uuid4, primary_key=True); name: str=Field(unique=True,index=True)
class UserRole(TimestampMixin, table=True):
    __tablename__="user_roles"; id: UUID=Field(default_factory=uuid4, primary_key=True); user_id: UUID=Field(index=True); role_id: UUID=Field(index=True); tenant_id: UUID=Field(index=True)
class ConsentRecord(TimestampMixin, table=True):
    __tablename__="consent_records"; id: UUID=Field(default_factory=uuid4, primary_key=True); tenant_id: UUID=Field(index=True); user_id: UUID=Field(index=True); purpose: ConsentPurpose=Field(index=True); version: str; granted: bool; revoked_at: datetime|None=None
class ImageCapture(TimestampMixin, table=True):
    __tablename__="image_captures"; id: UUID=Field(default_factory=uuid4, primary_key=True); tenant_id: UUID=Field(index=True); user_id: UUID=Field(index=True); storage_key: str; content_type: str; size_bytes: int; exif_policy: str="strip_on_ingest"; status: str="pending_scan"
class GenericRecord(TimestampMixin, table=True):
    __tablename__="audit_logs"; id: UUID=Field(default_factory=uuid4, primary_key=True); tenant_id: UUID|None=Field(default=None,index=True); user_id: UUID|None=Field(default=None,index=True); event_type: str=Field(index=True); metadata_json: dict[str, Any]=Field(default_factory=dict, sa_column=Column(JSON))
class DataExportRequest(TimestampMixin, table=True):
    __tablename__="data_export_requests"; id: UUID=Field(default_factory=uuid4, primary_key=True); tenant_id: UUID=Field(index=True); user_id: UUID=Field(index=True); status: str="queued"; export_ref: str|None=None
class DataDeletionRequest(TimestampMixin, table=True):
    __tablename__="data_deletion_requests"; id: UUID=Field(default_factory=uuid4, primary_key=True); tenant_id: UUID=Field(index=True); user_id: UUID=Field(index=True); status: str="queued"

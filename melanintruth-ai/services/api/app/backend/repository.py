from __future__ import annotations

from dataclasses import dataclass, field

from .entities import AnalysisJob, AuditEvent, ConsentRecord, Device, ImageCapture, ModelVersion, RenderJob, Session, User


@dataclass
class InMemoryRepository:
    users: dict[str, User] = field(default_factory=dict)
    users_by_email: dict[str, str] = field(default_factory=dict)
    devices: dict[str, Device] = field(default_factory=dict)
    sessions: dict[str, Session] = field(default_factory=dict)
    consent: dict[str, ConsentRecord] = field(default_factory=dict)
    images: dict[str, ImageCapture] = field(default_factory=dict)
    analysis_jobs: dict[str, AnalysisJob] = field(default_factory=dict)
    render_jobs: dict[str, RenderJob] = field(default_factory=dict)
    audit_events: list[AuditEvent] = field(default_factory=list)
    model_versions: dict[str, ModelVersion] = field(default_factory=dict)

    def reset(self) -> None:
        self.__dict__.update(InMemoryRepository().__dict__)

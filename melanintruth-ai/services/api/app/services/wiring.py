from __future__ import annotations

from dataclasses import dataclass

from app.backend.analysis import AnalysisService
from app.backend.audit import AuditService
from app.backend.auth import AuthService
from app.backend.consent import ConsentService
from app.backend.governance import GovernanceService
from app.backend.image_service import ImageService
from app.backend.privacy import PrivacyService
from app.backend.rendering import RenderService
from app.db.repositories.sqlite import SQLiteRepository


@dataclass
class ServiceContainer:
    repo: SQLiteRepository
    audit: AuditService
    auth: AuthService
    consent: ConsentService
    images: ImageService
    analysis: AnalysisService
    rendering: RenderService
    privacy: PrivacyService
    governance: GovernanceService


def build_container(repo: SQLiteRepository) -> ServiceContainer:
    audit = AuditService(repo)
    consent = ConsentService(repo, audit)
    images = ImageService(repo, audit, consent)
    return ServiceContainer(
        repo=repo,
        audit=audit,
        auth=AuthService(repo, audit),
        consent=consent,
        images=images,
        analysis=AnalysisService(repo, audit, consent, images),
        rendering=RenderService(repo, audit, consent),
        privacy=PrivacyService(repo, audit),
        governance=GovernanceService(repo, audit),
    )

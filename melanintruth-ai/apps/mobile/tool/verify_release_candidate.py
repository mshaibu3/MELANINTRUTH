from __future__ import annotations

import json
import plistlib
from pathlib import Path


MOBILE = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read(path: Path) -> str:
    require(path.is_file(), f"missing required file: {path.relative_to(REPO)}")
    return path.read_text(encoding="utf-8")


def verify_ios_privacy_manifest() -> None:
    manifest_path = MOBILE / "ios/Runner/PrivacyInfo.xcprivacy"
    require(manifest_path.is_file(), "iOS privacy manifest is missing")
    with manifest_path.open("rb") as handle:
        manifest = plistlib.load(handle)
    require(manifest.get("NSPrivacyTracking") is False, "iOS tracking must be disabled")
    collected = manifest.get("NSPrivacyCollectedDataTypes", [])
    photo_records = [
        item
        for item in collected
        if item.get("NSPrivacyCollectedDataType")
        == "NSPrivacyCollectedDataTypePhotosorVideos"
    ]
    require(photo_records, "photo/video collection must be declared")
    require(
        photo_records[0].get("NSPrivacyCollectedDataTypeTracking") is False,
        "photo/video data must not be used for tracking",
    )
    project = read(MOBILE / "ios/Runner.xcodeproj/project.pbxproj")
    require("PrivacyInfo.xcprivacy" in project, "privacy manifest is not referenced by Xcode")
    require(
        "PrivacyInfo.xcprivacy in Resources" in project,
        "privacy manifest is not copied into the iOS application bundle",
    )


def verify_google_data_safety() -> None:
    declaration = json.loads(read(REPO / "docs/mobile/google-play-data-safety.json"))
    require(
        declaration.get("application_id") == "com.hakilixlabs.melanintruth",
        "Google Play application ID is inconsistent",
    )
    require(
        declaration.get("data_shared_with_third_parties") is False,
        "third-party data sharing must remain disabled",
    )
    require(
        declaration.get("data_encrypted_in_transit") is True,
        "encrypted transport must be declared",
    )
    require(
        declaration.get("account_deletion_available") is True,
        "account deletion must be declared",
    )
    data_types = declaration.get("data_types", [])
    require(
        any(item.get("type") == "photos" and item.get("collected") for item in data_types),
        "photo collection must be declared",
    )


def verify_device_matrix() -> None:
    matrix = json.loads(read(REPO / "docs/mobile/phase7-device-test-matrix.json"))
    require(
        matrix.get("required_evidence_status") == "pending_external_execution",
        "device evidence must remain pending until external execution is recorded",
    )
    for platform in ("android", "ios"):
        profiles = matrix.get(platform, [])
        require(len(profiles) >= 2, f"{platform} requires modern and minimum profiles")
        scenarios = {
            scenario
            for profile in profiles
            for scenario in profile.get("required_scenarios", [])
        }
        for required in (
            "camera_permission_denied",
            "capture_cancelled",
            "consent_gating" if platform == "android" else "privacy_deletion",
        ):
            require(required in scenarios, f"{platform} matrix is missing {required}")
        require("privacy_deletion" in scenarios, f"{platform} matrix is missing privacy deletion")
    evidence = matrix.get("evidence_requirements", {}).get("per_scenario", [])
    for field in (
        "device_model",
        "os_version",
        "build_commit",
        "result",
        "evidence_uri",
    ):
        require(field in evidence, f"device evidence is missing {field}")


def verify_upload_contract() -> None:
    backend = read(REPO / "melanintruth-ai/services/api/app/api/phase7_app.py")
    service = read(REPO / "melanintruth-ai/services/api/app/backend/image_service.py")
    gateway = read(MOBILE / "lib/src/gateway.dart")
    schema = read(REPO / "melanintruth-ai/services/api/app/schemas/images.py")
    for token in ("upload_id", "expires_at", "idempotency_key"):
        require(token in backend, f"backend upload response is missing {token}")
        require(token in gateway, f"mobile upload flow is missing {token}")
    require("UPLOAD_EXPIRED" in backend, "expired upload tickets need a stable error code")
    require("complete_upload_ticket" in service, "idempotent completion service is missing")
    require("UploadCompleteRequest" in schema, "upload completion schema is missing")
    require(
        "Signed image uploads must use HTTPS" in gateway,
        "mobile signed uploads must enforce HTTPS",
    )


def verify_release_workflow() -> None:
    workflow = read(REPO / ".github/workflows/release-candidate.yml")
    require("workflow_dispatch:" in workflow, "signed builds must be explicitly dispatched")
    require("environment: mobile-release" in workflow, "signed jobs need a protected environment")
    require("release-candidate-policy" in workflow, "release policy job is missing")
    for secret in (
        "ANDROID_KEYSTORE_BASE64",
        "ANDROID_KEYSTORE_PASSWORD",
        "ANDROID_KEY_ALIAS",
        "ANDROID_KEY_PASSWORD",
        "IOS_CERTIFICATE_P12_BASE64",
        "IOS_CERTIFICATE_PASSWORD",
        "IOS_PROVISIONING_PROFILE_BASE64",
        "IOS_KEYCHAIN_PASSWORD",
        "APPLE_TEAM_ID",
    ):
        require(f"secrets.{secret}" in workflow, f"workflow is missing {secret}")
    require("permissions:\n  contents: read" in workflow, "workflow permissions must be read-only")
    require("timeout-minutes:" in workflow, "release jobs must be bounded")
    require("cancel-in-progress: true" in workflow, "release concurrency must cancel stale runs")


def verify_release_boundary() -> None:
    documentation = read(REPO / "docs/mobile/PHASE-7-RELEASE-CANDIDATE.md")
    require(
        "release_candidate_controls_ready" in documentation,
        "release status boundary is not documented",
    )
    lowered = documentation.lower()
    require(
        "not `store_ready` or `released`" in lowered,
        "store-release claims must remain blocked",
    )


def main() -> None:
    verify_ios_privacy_manifest()
    verify_google_data_safety()
    verify_device_matrix()
    verify_upload_contract()
    verify_release_workflow()
    verify_release_boundary()
    print("Phase 7 release-candidate policy verified.")


if __name__ == "__main__":
    main()

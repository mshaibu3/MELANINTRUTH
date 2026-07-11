from dataclasses import replace
from datetime import datetime, timedelta, timezone

from app.api.phase7_app import Phase7ApiApplication


def bootstrap_user(app: Phase7ApiApplication, email: str):
    assert app.register({"email": email, "password": "very-safe-password"})[0] == 201
    status, tokens = app.login(
        {
            "email": email,
            "password": "very-safe-password",
            "device_label": "phase7-test",
        }
    )
    assert status == 200
    assert app.grant_consent(
        tokens["access_token"], {"purpose": "image_processing"}
    )[0] == 201
    return tokens


def ticket_payload(checksum: str = "a" * 64):
    return {
        "content_type": "image/jpeg",
        "size_bytes": 128,
        "checksum_sha256": checksum,
    }


def completion_payload(ticket: dict, checksum: str = "a" * 64):
    return {
        **ticket_payload(checksum),
        "upload_id": ticket["upload_id"],
        "idempotency_key": ticket["idempotency_key"],
    }


def test_upload_ticket_contains_expiry_and_server_idempotency_key():
    app = Phase7ApiApplication()
    tokens = bootstrap_user(app, "ticket@example.com")

    status, ticket = app.upload_request(tokens["access_token"], ticket_payload())

    assert status == 201
    assert ticket["upload_id"].startswith("upl_")
    assert ticket["idempotency_key"]
    assert ticket["upload_url"].startswith("local-signed://")
    assert datetime.fromisoformat(ticket["expires_at"]) > datetime.now(timezone.utc)
    assert "storage_ref" not in ticket


def test_upload_completion_is_idempotent_and_rejects_metadata_drift():
    app = Phase7ApiApplication()
    tokens = bootstrap_user(app, "idempotent@example.com")
    _, ticket = app.upload_request(tokens["access_token"], ticket_payload())
    payload = completion_payload(ticket)

    first_status, first = app.upload_complete(tokens["access_token"], payload)
    replay_status, replay = app.upload_complete(tokens["access_token"], payload)

    assert first_status == 201
    assert replay_status == 200
    assert first["image_id"] == replay["image_id"]
    assert first["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True

    conflict_status, conflict = app.upload_complete(
        tokens["access_token"],
        {**payload, "size_bytes": 129},
    )
    assert conflict_status == 409
    assert conflict["error"]["code"] == "UPLOAD_METADATA_CONFLICT"


def test_expired_ticket_and_cross_user_key_are_rejected():
    app = Phase7ApiApplication()
    owner = bootstrap_user(app, "owner@example.com")
    other = bootstrap_user(app, "other-phase7@example.com")
    _, ticket = app.upload_request(owner["access_token"], ticket_payload("b" * 64))
    payload = completion_payload(ticket, "b" * 64)

    cross_status, cross = app.upload_complete(other["access_token"], payload)
    assert cross_status == 404
    assert cross["error"]["code"] == "UPLOAD_NOT_FOUND"

    stored = app.services.images._upload_tickets[ticket["upload_id"]]
    app.services.images._upload_tickets[ticket["upload_id"]] = replace(
        stored,
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    expired_status, expired = app.upload_complete(owner["access_token"], payload)
    assert expired_status == 410
    assert expired["error"]["code"] == "UPLOAD_EXPIRED"


def test_phase7_dependency_light_openapi_contract_documents_upload_schemas():
    contract = Phase7ApiApplication().openapi_contract()

    assert contract["info"]["version"] == "0.7.0"
    assert "UploadTicketResponse" in contract["components"]["schemas"]
    assert "UploadCompleteRequest" in contract["components"]["schemas"]

from __future__ import annotations

import time

from .conftest import make_test_wav_bytes


def test_profile_creation_endpoint(client):
    response = client.post(
        "/api/profiles",
        json={
            "display_name": "Studio Voice",
            "notes": "Primary narrator",
            "language_preference": "en",
            "tags": ["demo"],
            "avatar_color": "#7dd3fc",
            "synthesis_defaults": {
                "temperature": 0.75,
                "speed": 1.0,
                "length_penalty": 1.0,
                "repetition_penalty": 2.0,
                "top_k": 50,
                "top_p": 0.85,
                "enable_text_splitting": True,
            },
        },
    )

    assert response.status_code == 201
    assert response.json()["display_name"] == "Studio Voice"


def test_generation_validation_and_lifecycle(client):
    profile_response = client.post(
        "/api/profiles",
        json={
            "display_name": "Voice",
            "notes": "",
            "language_preference": "en",
            "tags": [],
            "avatar_color": "#7dd3fc",
            "synthesis_defaults": {
                "temperature": 0.75,
                "speed": 1.0,
                "length_penalty": 1.0,
                "repetition_penalty": 2.0,
                "top_k": 50,
                "top_p": 0.85,
                "enable_text_splitting": True,
            },
        },
    )
    profile_id = profile_response.json()["id"]

    empty_text = client.post(
        "/api/generations",
        json={"profile_id": profile_id, "input_text": "   ", "language": "en"},
    )
    assert empty_text.status_code == 400

    upload_response = client.post(
        f"/api/profiles/{profile_id}/clips/upload",
        files={"file": ("reference.wav", make_test_wav_bytes(), "audio/wav")},
    )
    assert upload_response.status_code == 201

    invalid_missing_profile = client.post(
        "/api/generations",
        json={"profile_id": "missing", "input_text": "Hello", "language": "en"},
    )
    assert invalid_missing_profile.status_code == 404

    generation_response = client.post(
        "/api/generations",
        json={"profile_id": profile_id, "input_text": "Hello local studio", "language": "en"},
    )
    assert generation_response.status_code == 202
    generation_id = generation_response.json()["id"]

    for _ in range(20):
        fetched = client.get(f"/api/generations/{generation_id}")
        payload = fetched.json()
        if payload["status"] == "completed":
            break
        time.sleep(0.1)

    assert payload["status"] == "completed"
    assert payload["output_url"].startswith("/api/files/generated/")


def test_invalid_audio_upload_rejected(client):
    profile_response = client.post(
        "/api/profiles",
        json={
            "display_name": "Voice",
            "notes": "",
            "language_preference": "en",
            "tags": [],
            "avatar_color": "#7dd3fc",
            "synthesis_defaults": {
                "temperature": 0.75,
                "speed": 1.0,
                "length_penalty": 1.0,
                "repetition_penalty": 2.0,
                "top_k": 50,
                "top_p": 0.85,
                "enable_text_splitting": True,
            },
        },
    )
    profile_id = profile_response.json()["id"]
    response = client.post(
        f"/api/profiles/{profile_id}/clips/upload",
        files={"file": ("bad.txt", b"not audio", "text/plain")},
    )
    assert response.status_code == 400


def test_clip_transcript_can_be_saved(client):
    profile_response = client.post(
        "/api/profiles",
        json={
            "display_name": "Voice",
            "notes": "",
            "language_preference": "en",
            "tags": [],
            "avatar_color": "#7dd3fc",
            "synthesis_defaults": {
                "temperature": 0.55,
                "speed": 1.0,
                "length_penalty": 1.0,
                "repetition_penalty": 2.2,
                "top_k": 40,
                "top_p": 0.75,
                "enable_text_splitting": True,
            },
        },
    )
    profile_id = profile_response.json()["id"]
    upload_response = client.post(
        f"/api/profiles/{profile_id}/clips/upload",
        files={"file": ("reference.wav", make_test_wav_bytes(), "audio/wav")},
    )
    clip_id = upload_response.json()["id"]

    transcript_response = client.patch(
        f"/api/profiles/{profile_id}/clips/{clip_id}",
        json={"reference_text": "This is the exact content of the reference clip."},
    )
    assert transcript_response.status_code == 200
    assert transcript_response.json()["reference_text"] == "This is the exact content of the reference clip."

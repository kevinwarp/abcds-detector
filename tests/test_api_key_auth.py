"""Tests for API key authentication: create, list, use, revoke, and evaluate."""

import io
import datetime
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Clear slowapi's in-memory counters before each test to prevent
    cross-test rate-limit bleed (the /api/evaluate_file endpoint is
    capped at 5/minute, which is easily exceeded across a test suite)."""
    from web_app import limiter
    storage = getattr(limiter, "_storage", None)
    if storage is not None:
        try:
            storage.reset()
        except Exception:
            pass
    yield


# ---------------------------------------------------------------------------
# Minimal fake evaluation result (same shape as web_app.format_results)
# ---------------------------------------------------------------------------

_FAKE_RESULT = {
    "brand_name": "TestBrand",
    "video_uri": "gs://test-bucket/test.mp4",
    "video_name": "test.mp4",
    "abcd": {
        "score": 75.0,
        "result": "Might Improve",
        "passed": 3,
        "total": 4,
        "features": [],
    },
    "persuasion": {"density": 50.0, "detected": 2, "total": 4, "features": []},
    "structure": {"features": []},
    "shorts": {"features": []},
    "scenes": [],
    "concept": {},
    "predictions": {"overall_score": 70},
    "reference_ads": [],
    "brand_intelligence": {},
    "video_metadata": {"duration_seconds": 5.0},
    "emotional_coherence": {"score": 85, "flagged_shifts": []},
    "audio_analysis": {},
    "action_plan": [],
    "feature_timeline": {
        "video_duration_s": 5.0,
        "scene_boundaries": [],
        "features": [],
    },
    "accessibility": {
        "score": 75.0,
        "passed": 3,
        "total": 4,
        "features": [],
        "speech_rate_wpm": 130,
        "speech_rate_flag": "ok",
    },
    "platform_fit": {},
    "benchmarks": {},
}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _register(client, email, password="Apipass1"):
    """Register a user and return the session cookie via the client."""
    resp = client.post("/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    return resp


def _create_key(client, name="test-key"):
    """Create an API key for the currently authenticated user. Returns the raw key."""
    resp = client.post(
        "/auth/api-keys",
        json={"name": name},
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _register_and_get_key(client, email, key_name="test-key"):
    """Register, create a key, return the raw secret string."""
    _register(client, email)
    return _create_key(client, key_name)["key"]


# ---------------------------------------------------------------------------
# API key creation
# ---------------------------------------------------------------------------

class TestApiKeyCreate:
    def test_create_success_returns_key(self, client):
        _register(client, "create@example.com")
        data = _create_key(client, "my-key")
        assert data["key"].startswith("acr_")
        assert len(data["key"]) == len("acr_") + 40  # 4-char prefix + 40 hex chars
        assert data["key_prefix"] == data["key"][: len("acr_") + 8]
        assert "id" in data
        assert "warning" in data

    def test_raw_key_not_in_list_response(self, client):
        """After creation the secret must not appear in list responses."""
        _register(client, "nosecret@example.com")
        _create_key(client, "hidden")
        resp = client.get("/auth/api-keys")
        for k in resp.json()["api_keys"]:
            assert "key" not in k

    def test_create_requires_name(self, client):
        _register(client, "noname@example.com")
        resp = client.post(
            "/auth/api-keys",
            json={},
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400
        assert "'name' is required" in resp.json()["detail"]

    def test_create_name_too_long(self, client):
        _register(client, "longname@example.com")
        resp = client.post(
            "/auth/api-keys",
            json={"name": "x" * 65},
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400

    def test_create_unauthenticated_rejected(self, client):
        client.cookies.clear()
        resp = client.post(
            "/auth/api-keys",
            json={"name": "key"},
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 401

    def test_each_key_is_unique(self, client):
        _register(client, "unique@example.com")
        key1 = _create_key(client, "k1")["key"]
        key2 = _create_key(client, "k2")["key"]
        assert key1 != key2


# ---------------------------------------------------------------------------
# API key listing
# ---------------------------------------------------------------------------

class TestApiKeyList:
    def test_list_empty_initially(self, client):
        _register(client, "empty@example.com")
        resp = client.get("/auth/api-keys")
        assert resp.status_code == 200
        assert resp.json()["api_keys"] == []

    def test_list_shows_created_key(self, client):
        _register_and_get_key(client, "listme@example.com", "my-script")
        resp = client.get("/auth/api-keys")
        keys = resp.json()["api_keys"]
        assert len(keys) == 1
        assert keys[0]["name"] == "my-script"
        assert keys[0]["is_active"] is True
        assert keys[0]["key_prefix"].startswith("acr_")

    def test_list_unauthenticated_rejected(self, client):
        client.cookies.clear()
        resp = client.get("/auth/api-keys")
        assert resp.status_code == 401

    def test_multiple_keys_all_listed(self, client):
        _register(client, "multi@example.com")
        _create_key(client, "key-a")
        _create_key(client, "key-b")
        keys = client.get("/auth/api-keys").json()["api_keys"]
        assert len(keys) == 2
        names = {k["name"] for k in keys}
        assert names == {"key-a", "key-b"}


# ---------------------------------------------------------------------------
# API key revocation
# ---------------------------------------------------------------------------

class TestApiKeyRevoke:
    def test_revoke_success(self, client):
        _register_and_get_key(client, "revoke@example.com")
        key_id = client.get("/auth/api-keys").json()["api_keys"][0]["id"]
        resp = client.delete(f"/auth/api-keys/{key_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "revoked"

    def test_revoked_key_shows_inactive_in_list(self, client):
        _register_and_get_key(client, "inactive@example.com")
        key_id = client.get("/auth/api-keys").json()["api_keys"][0]["id"]
        client.delete(f"/auth/api-keys/{key_id}")
        keys = client.get("/auth/api-keys").json()["api_keys"]
        assert keys[0]["is_active"] is False

    def test_revoke_nonexistent_returns_404(self, client):
        _register(client, "rev404@example.com")
        resp = client.delete("/auth/api-keys/does-not-exist")
        assert resp.status_code == 404

    def test_revoke_already_revoked_returns_already_revoked(self, client):
        _register_and_get_key(client, "double@example.com")
        key_id = client.get("/auth/api-keys").json()["api_keys"][0]["id"]
        client.delete(f"/auth/api-keys/{key_id}")
        resp = client.delete(f"/auth/api-keys/{key_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "already_revoked"

    def test_cannot_revoke_another_users_key(self, client):
        """User A cannot revoke user B's key (even if they know the key ID)."""
        _register_and_get_key(client, "owner@example.com")
        key_id = client.get("/auth/api-keys").json()["api_keys"][0]["id"]

        # Register as a different user
        client.cookies.clear()
        _register(client, "intruder@example.com")
        resp = client.delete(f"/auth/api-keys/{key_id}")
        assert resp.status_code == 404  # not found for this user


# ---------------------------------------------------------------------------
# Authentication via X-API-Key header
# ---------------------------------------------------------------------------

class TestApiKeyHeaderAuth:
    def test_valid_key_authenticates_me(self, client):
        """X-API-Key header must work for /auth/me without a session cookie."""
        raw_key = _register_and_get_key(client, "authme@example.com")
        client.cookies.clear()

        resp = client.get("/auth/me", headers={"X-API-Key": raw_key})
        assert resp.status_code == 200
        assert resp.json()["user"]["email"] == "authme@example.com"

    def test_invalid_key_returns_401(self, client):
        client.cookies.clear()
        resp = client.get("/auth/me", headers={"X-API-Key": "acr_notarealkey00000000"})
        assert resp.status_code == 401
        assert "Invalid or revoked" in resp.json()["detail"]

    def test_revoked_key_returns_401(self, client):
        raw_key = _register_and_get_key(client, "revokedauth@example.com")
        key_id = client.get("/auth/api-keys").json()["api_keys"][0]["id"]
        client.delete(f"/auth/api-keys/{key_id}")

        client.cookies.clear()
        resp = client.get("/auth/me", headers={"X-API-Key": raw_key})
        assert resp.status_code == 401

    def test_empty_api_key_falls_through_to_cookie_auth(self, client):
        """An empty X-API-Key must not crash — it should fall through to cookie check."""
        client.cookies.clear()
        resp = client.get("/auth/me", headers={"X-API-Key": ""})
        assert resp.status_code == 401  # no cookie either → 401

    def test_session_cookie_still_works_alongside_api_keys(self, client):
        """Cookie auth must keep working after API keys are added."""
        _register(client, "cookie@example.com")
        # client still has its session cookie — no X-API-Key header
        resp = client.get("/auth/me")
        assert resp.status_code == 200
        assert resp.json()["user"]["email"] == "cookie@example.com"

    def test_last_used_at_updated_on_use(self, client, db_engine):
        """Using an API key must update its last_used_at timestamp."""
        from sqlalchemy.orm import sessionmaker
        from db import ApiKey

        raw_key = _register_and_get_key(client, "lastseen@example.com")

        # Verify it starts as NULL
        Session = sessionmaker(bind=db_engine)
        with Session() as session:
            key_before = session.query(ApiKey).filter(
                ApiKey.key_hash is not None
            ).first()
            # last_used_at may or may not be None before first use

        client.cookies.clear()
        client.get("/auth/me", headers={"X-API-Key": raw_key})

        with Session() as session:
            key_after = session.query(ApiKey).order_by(
                ApiKey.created_at.desc()
            ).first()
            assert key_after.last_used_at is not None


# ---------------------------------------------------------------------------
# /api/evaluate_file end-to-end via API key (mocked pipeline)
# ---------------------------------------------------------------------------

class TestEvaluateFileWithApiKey:
    """Verify that /api/evaluate_file works when the caller authenticates
    with X-API-Key instead of a session cookie."""

    @staticmethod
    def _fake_mp4():
        return io.BytesIO(b"\x00\x00\x00\x18ftypmp42")  # plausible MP4 magic bytes

    @patch("web_app.notification_service.notify_evaluation_started", return_value=False)
    @patch("web_app._send_slack_notification")
    @patch("web_app._save_results_to_gcs")
    @patch("web_app.run_evaluation", return_value=_FAKE_RESULT.copy())
    @patch("web_app.upload_to_gcs", return_value="gs://test-bucket/test.mp4")
    @patch("web_app.credits_mod.deduct_credits", return_value=50)
    @patch("web_app.credits_mod.validate_upload", return_value=None)
    @patch("web_app.credits_mod.get_video_duration", return_value=5.0)
    @patch("web_app.credits_mod.release_job_slot")
    @patch("web_app.credits_mod.acquire_job_slot", return_value=True)
    def test_full_review_returned_as_json(
        self,
        mock_acquire, mock_release, mock_duration, mock_validate,
        mock_deduct, mock_upload, mock_run, mock_save, mock_slack, mock_notify,
        client,
    ):
        raw_key = _register_and_get_key(client, "evaluser@example.com")
        client.cookies.clear()

        resp = client.post(
            "/api/evaluate_file",
            files={"file": ("adspot.mp4", self._fake_mp4(), "video/mp4")},
            data={"use_abcd": "true", "use_shorts": "false", "use_ci": "true"},
            headers={"X-API-Key": raw_key},
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        # Top-level structure
        assert "report_id" in body
        assert "abcd" in body
        assert "persuasion" in body
        assert "scenes" in body
        assert body["brand_name"] == "TestBrand"
        # Scores present and numeric
        assert isinstance(body["abcd"]["score"], (int, float))
        assert isinstance(body["persuasion"]["density"], (int, float))
        # Pipeline was invoked
        mock_run.assert_called_once()
        mock_upload.assert_called_once()
        mock_deduct.assert_called_once()

    @patch("web_app.credits_mod.release_job_slot")
    @patch("web_app.credits_mod.acquire_job_slot", return_value=True)
    def test_unauthenticated_request_rejected(
        self, mock_acquire, mock_release, client
    ):
        client.cookies.clear()
        resp = client.post(
            "/api/evaluate_file",
            files={"file": ("video.mp4", self._fake_mp4(), "video/mp4")},
            data={"use_abcd": "true"},
        )
        assert resp.status_code == 401

    @patch("web_app.credits_mod.release_job_slot")
    @patch("web_app.credits_mod.acquire_job_slot", return_value=True)
    def test_non_mp4_file_rejected_with_415(
        self, mock_acquire, mock_release, client
    ):
        raw_key = _register_and_get_key(client, "wrongfmt@example.com")
        client.cookies.clear()

        resp = client.post(
            "/api/evaluate_file",
            files={"file": ("clip.mov", io.BytesIO(b"data"), "video/quicktime")},
            data={"use_abcd": "true"},
            headers={"X-API-Key": raw_key},
        )
        assert resp.status_code == 415
        assert ".mov" in resp.json()["message"]

    @patch("web_app.credits_mod.release_job_slot")
    @patch("web_app.credits_mod.acquire_job_slot", return_value=True)
    def test_revoked_key_cannot_evaluate(
        self, mock_acquire, mock_release, client
    ):
        raw_key = _register_and_get_key(client, "revokedeval@example.com")
        key_id = client.get("/auth/api-keys").json()["api_keys"][0]["id"]
        client.delete(f"/auth/api-keys/{key_id}")
        client.cookies.clear()

        resp = client.post(
            "/api/evaluate_file",
            files={"file": ("video.mp4", self._fake_mp4(), "video/mp4")},
            data={"use_abcd": "true"},
            headers={"X-API-Key": raw_key},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /api/evaluate_file — input validation (file vs url)
# ---------------------------------------------------------------------------

class TestEvaluateFileInputValidation:
    """Verify the new file/url mutual-exclusion rules."""

    @staticmethod
    def _fake_mp4():
        return io.BytesIO(b"\x00\x00\x00\x18ftypmp42")

    @patch("web_app.credits_mod.release_job_slot")
    @patch("web_app.credits_mod.acquire_job_slot", return_value=True)
    def test_neither_file_nor_url_returns_400(
        self, mock_acquire, mock_release, client
    ):
        raw_key = _register_and_get_key(client, "noinput@example.com")
        client.cookies.clear()
        resp = client.post(
            "/api/evaluate_file",
            data={"use_abcd": "true"},
            headers={"X-API-Key": raw_key},
        )
        assert resp.status_code == 400
        assert "missing_input" in resp.json()["error"]

    @patch("web_app.credits_mod.release_job_slot")
    @patch("web_app.credits_mod.acquire_job_slot", return_value=True)
    def test_both_file_and_url_returns_400(
        self, mock_acquire, mock_release, client
    ):
        raw_key = _register_and_get_key(client, "bothinput@example.com")
        client.cookies.clear()
        resp = client.post(
            "/api/evaluate_file",
            files={"file": ("video.mp4", self._fake_mp4(), "video/mp4")},
            data={"url": "https://www.youtube.com/watch?v=abc", "use_abcd": "true"},
            headers={"X-API-Key": raw_key},
        )
        assert resp.status_code == 400
        assert "ambiguous_input" in resp.json()["error"]


# ---------------------------------------------------------------------------
# /api/evaluate_file — YouTube URL mode
# ---------------------------------------------------------------------------

class TestEvaluateYouTubeUrl:
    """Verify that /api/evaluate_file accepts a YouTube URL and returns the
    full review JSON, with the same auth rules as the file upload path."""

    YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    YOUTU_BE_URL = "https://youtu.be/dQw4w9WgXcQ"

    @patch("web_app.notification_service.notify_evaluation_started", return_value=False)
    @patch("web_app._send_slack_notification")
    @patch("web_app._save_results_to_gcs")
    @patch("web_app.run_evaluation", return_value=_FAKE_RESULT.copy())
    @patch("web_app.credits_mod.deduct_credits", return_value=50)
    @patch("web_app.credits_mod.release_job_slot")
    @patch("web_app.credits_mod.acquire_job_slot", return_value=True)
    def test_youtube_url_returns_full_review(
        self,
        mock_acquire, mock_release, mock_deduct, mock_run,
        mock_save, mock_slack, mock_notify,
        client,
    ):
        raw_key = _register_and_get_key(client, "ytuser@example.com")
        client.cookies.clear()

        resp = client.post(
            "/api/evaluate_file",
            data={"url": self.YOUTUBE_URL, "use_abcd": "true", "use_ci": "true"},
            headers={"X-API-Key": raw_key},
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "report_id" in body
        assert "abcd" in body
        assert body["brand_name"] == "TestBrand"
        # run_evaluation must have been called with the YouTube URL
        call_args = mock_run.call_args
        assert self.YOUTUBE_URL in call_args[0]
        mock_deduct.assert_called_once()

    @patch("web_app.notification_service.notify_evaluation_started", return_value=False)
    @patch("web_app._send_slack_notification")
    @patch("web_app._save_results_to_gcs")
    @patch("web_app.run_evaluation", return_value=_FAKE_RESULT.copy())
    @patch("web_app.credits_mod.deduct_credits", return_value=50)
    @patch("web_app.credits_mod.release_job_slot")
    @patch("web_app.credits_mod.acquire_job_slot", return_value=True)
    def test_youtu_be_short_url_accepted(
        self,
        mock_acquire, mock_release, mock_deduct, mock_run,
        mock_save, mock_slack, mock_notify,
        client,
    ):
        raw_key = _register_and_get_key(client, "ytshort@example.com")
        client.cookies.clear()

        resp = client.post(
            "/api/evaluate_file",
            data={"url": self.YOUTU_BE_URL, "use_abcd": "true"},
            headers={"X-API-Key": raw_key},
        )
        assert resp.status_code == 200, resp.text

    @patch("web_app.credits_mod.release_job_slot")
    @patch("web_app.credits_mod.acquire_job_slot", return_value=True)
    def test_non_youtube_url_rejected_with_415(
        self, mock_acquire, mock_release, client
    ):
        raw_key = _register_and_get_key(client, "vimeouser@example.com")
        client.cookies.clear()

        resp = client.post(
            "/api/evaluate_file",
            data={"url": "https://vimeo.com/123456789", "use_abcd": "true"},
            headers={"X-API-Key": raw_key},
        )
        assert resp.status_code == 415
        assert "YouTube" in resp.json()["message"]

    @patch("web_app.credits_mod.release_job_slot")
    @patch("web_app.credits_mod.acquire_job_slot", return_value=True)
    def test_unauthenticated_url_request_rejected(
        self, mock_acquire, mock_release, client
    ):
        client.cookies.clear()
        resp = client.post(
            "/api/evaluate_file",
            data={"url": self.YOUTUBE_URL, "use_abcd": "true"},
        )
        assert resp.status_code == 401

    @patch("web_app.credits_mod.release_job_slot")
    @patch("web_app.credits_mod.acquire_job_slot", return_value=True)
    def test_url_mode_uses_youtube_provider(
        self, mock_acquire, mock_release, client
    ):
        """run_evaluation must be called with provider_type=YOUTUBE config."""
        _register_and_get_key(client, "ytprovider@example.com")

        captured = {}

        def _capture_config(video_uri, config, on_progress):
            captured["provider"] = config.creative_provider_type
            return _FAKE_RESULT.copy()

        with patch("web_app.run_evaluation", side_effect=_capture_config), \
             patch("web_app.credits_mod.deduct_credits", return_value=50), \
             patch("web_app._save_results_to_gcs"), \
             patch("web_app._send_slack_notification"):

            resp = client.post(
                "/api/evaluate_file",
                data={"url": self.YOUTUBE_URL},
            )

        assert resp.status_code == 200
        import models
        assert captured["provider"] == models.CreativeProviderType.YOUTUBE

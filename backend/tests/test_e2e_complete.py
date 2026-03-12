"""
Comprehensive E2E test suite for the AI Detection Platform.
Uses an in-memory SQLite DB and mocked Celery tasks.
"""
import io
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from tests.conftest import TestingSessionLocal, make_png_bytes


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _upload_image(client, token: str, filename: str = "test.png", data: bytes = None):
    """POST /detections/image and return the response."""
    if data is None:
        data = make_png_bytes()
    return client.post(
        "/detections/image",
        files={"file": (filename, io.BytesIO(data), "image/png")},
        headers=_auth_headers(token),
    )


# ────────────────────────────────────────────────────────────────────────────
# A) Auth: Registration + Login
# ────────────────────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_new_user(self, client):
        email = f"new_{uuid.uuid4().hex[:8]}@example.com"
        r = client.post("/auth/register", json={
            "email": email, "password": "StrongPass1!", "full_name": "Alice"
        })
        assert r.status_code in (200, 201), r.text
        data = r.json()
        assert "message" in data or "user" in data or "access_token" in data

    def test_register_duplicate_email(self, client, registered_user):
        r = client.post("/auth/register", json={
            "email": registered_user["email"],
            "password": "StrongPass1!",
            "full_name": "Dup User",
        })
        assert r.status_code in (400, 409, 422), r.text

    def test_login_valid_credentials(self, client, registered_user):
        r = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        assert r.status_code == 200, r.text
        assert "access_token" in r.json()

    def test_login_wrong_password(self, client, registered_user):
        r = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": "WrongPassword99!",
        })
        assert r.status_code in (400, 401), r.text

    def test_missing_auth_returns_401(self, client):
        r = client.get("/detections")
        assert r.status_code == 401


# ────────────────────────────────────────────────────────────────────────────
# B) File Upload + Detection (mocked Celery)
# ────────────────────────────────────────────────────────────────────────────

class TestDetectionUpload:
    @patch("app.celery_app.celery_app.send_task")
    def test_upload_image_returns_202(self, mock_send, client, registered_user):
        mock_send.return_value = MagicMock(id="fake-task-id")
        r = _upload_image(client, registered_user["token"])
        assert r.status_code in (200, 202), r.text
        data = r.json()
        assert "detection_id" in data
        assert "polling_url" in data

    def test_upload_without_auth_returns_401(self, client):
        r = client.post(
            "/detections/image",
            files={"file": ("test.png", io.BytesIO(make_png_bytes()), "image/png")},
        )
        assert r.status_code == 401

    def test_upload_invalid_file_type(self, client, registered_user):
        r = client.post(
            "/detections/image",
            files={"file": ("malware.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")},
            headers=_auth_headers(registered_user["token"]),
        )
        assert r.status_code == 400

    @patch("app.celery_app.celery_app.send_task")
    def test_duplicate_upload_returns_409(self, mock_send, client, registered_user):
        mock_send.return_value = MagicMock(id="fake-task-id")
        img = make_png_bytes(10, 10)
        # First upload
        r1 = client.post(
            "/detections/image",
            files={"file": ("dup.png", io.BytesIO(img), "image/png")},
            headers=_auth_headers(registered_user["token"]),
        )
        assert r1.status_code in (200, 202), r1.text
        # Second upload — same bytes → same hash
        r2 = client.post(
            "/detections/image",
            files={"file": ("dup.png", io.BytesIO(img), "image/png")},
            headers=_auth_headers(registered_user["token"]),
        )
        assert r2.status_code == 409, r2.text

    @patch("app.celery_app.celery_app.send_task")
    def test_get_detection_status(self, mock_send, client, registered_user):
        mock_send.return_value = MagicMock(id="fake-task-id")
        r = _upload_image(client, registered_user["token"], filename="status_test.png", data=make_png_bytes(12, 12))
        assert r.status_code in (200, 202)
        did = r.json()["detection_id"]

        r2 = client.get(f"/detections/{did}", headers=_auth_headers(registered_user["token"]))
        assert r2.status_code == 200
        assert r2.json()["detection_id"] == did
        assert "processing_status" in r2.json()

    @patch("app.celery_app.celery_app.send_task")
    def test_access_other_user_detection_returns_403(self, mock_send, client, registered_user):
        mock_send.return_value = MagicMock(id="fake-task-id")
        # Upload as user A
        r = _upload_image(client, registered_user["token"], data=make_png_bytes(14, 14))
        assert r.status_code in (200, 202)
        did = r.json()["detection_id"]

        # Create user B
        email_b = f"b_{uuid.uuid4().hex[:8]}@example.com"
        client.post("/auth/register", json={"email": email_b, "password": "Pass1234!", "full_name": "Bob"})
        db = TestingSessionLocal()
        from app.models.database import User
        user_b = db.query(User).filter(User.email == email_b).first()
        user_b.is_verified = True
        db.commit()
        db.close()
        r_login = client.post("/auth/login", json={"email": email_b, "password": "Pass1234!"})
        token_b = r_login.json()["access_token"]

        r3 = client.get(f"/detections/{did}", headers=_auth_headers(token_b))
        assert r3.status_code == 403

    def test_get_nonexistent_detection_returns_404(self, client, registered_user):
        r = client.get("/detections/999999", headers=_auth_headers(registered_user["token"]))
        assert r.status_code == 404

    @patch("app.celery_app.celery_app.send_task")
    def test_list_detections_paginated(self, mock_send, client, registered_user):
        mock_send.return_value = MagicMock(id="fake-task-id")
        r = client.get("/detections?skip=0&limit=5", headers=_auth_headers(registered_user["token"]))
        assert r.status_code == 200
        data = r.json()
        assert "detections" in data
        assert "total" in data


# ────────────────────────────────────────────────────────────────────────────
# C) Retry endpoint
# ────────────────────────────────────────────────────────────────────────────

class TestDetectionRetry:
    @patch("app.celery_app.celery_app.send_task")
    def test_retry_errored_detection(self, mock_send, client, registered_user):
        mock_send.return_value = MagicMock(id="retry-task-id")
        # Upload
        r = _upload_image(client, registered_user["token"], data=make_png_bytes(16, 16))
        did = r.json()["detection_id"]

        # Force status to 'error' in DB
        db = TestingSessionLocal()
        from app.models.database import Detection
        det = db.query(Detection).filter(Detection.id == did).first()
        det.processing_status = "error"
        det.error_message = "test error"
        db.commit()
        db.close()

        r2 = client.post(f"/detections/{did}/retry", headers=_auth_headers(registered_user["token"]))
        assert r2.status_code in (200, 202), r2.text
        assert r2.json()["status"] == "pending"

    @patch("app.celery_app.celery_app.send_task")
    def test_retry_completed_returns_409(self, mock_send, client, registered_user):
        mock_send.return_value = MagicMock(id="fake-id")
        r = _upload_image(client, registered_user["token"], data=make_png_bytes(18, 18))
        did = r.json()["detection_id"]

        # Force complete
        db = TestingSessionLocal()
        from app.models.database import Detection
        det = db.query(Detection).filter(Detection.id == did).first()
        det.processing_status = "completed"
        db.commit()
        db.close()

        r2 = client.post(f"/detections/{did}/retry", headers=_auth_headers(registered_user["token"]))
        assert r2.status_code == 409


# ────────────────────────────────────────────────────────────────────────────
# D) Batch Processing
# ────────────────────────────────────────────────────────────────────────────

class TestBatchProcessing:
    @patch("app.celery_app.celery_app.send_task")
    def test_create_batch(self, mock_send, client, registered_user):
        mock_send.return_value = MagicMock(id="batch-task-id")
        # Upload 3 images
        ids = []
        for i in range(3):
            r = _upload_image(client, registered_user["token"], data=make_png_bytes(20 + i, 20 + i))
            assert r.status_code in (200, 202), r.text
            ids.append(r.json()["detection_id"])

        r_batch = client.post(
            "/batches",
            json={"batch_name": "Test Batch", "detection_ids": ids},
            headers=_auth_headers(registered_user["token"]),
        )
        assert r_batch.status_code == 201, r_batch.text
        data = r_batch.json()
        assert data["files_count"] == 3
        assert "batch_id" in data

    @patch("app.celery_app.celery_app.send_task")
    def test_list_batches(self, mock_send, client, registered_user):
        mock_send.return_value = MagicMock(id="fake-id")
        r = client.get("/batches", headers=_auth_headers(registered_user["token"]))
        assert r.status_code == 200
        assert "batches" in r.json()

    @patch("app.celery_app.celery_app.send_task")
    def test_get_batch_status(self, mock_send, client, registered_user):
        mock_send.return_value = MagicMock(id="fake-id")
        # Upload + create batch
        r = _upload_image(client, registered_user["token"], data=make_png_bytes(30, 30))
        did = r.json()["detection_id"]
        r_batch = client.post(
            "/batches",
            json={"batch_name": "Status Batch", "detection_ids": [did]},
            headers=_auth_headers(registered_user["token"]),
        )
        bid = r_batch.json()["batch_id"]

        r_status = client.get(f"/batches/{bid}", headers=_auth_headers(registered_user["token"]))
        assert r_status.status_code == 200
        data = r_status.json()
        assert data["batch_id"] == bid
        assert "progress_percent" in data

    def test_get_nonexistent_batch_returns_404(self, client, registered_user):
        r = client.get("/batches/999999", headers=_auth_headers(registered_user["token"]))
        assert r.status_code == 404

    @patch("app.celery_app.celery_app.send_task")
    def test_batch_with_wrong_user_detection_returns_403(self, mock_send, client, registered_user):
        mock_send.return_value = MagicMock(id="fake-id")
        # Create a second user
        email_c = f"c_{uuid.uuid4().hex[:8]}@example.com"
        client.post("/auth/register", json={"email": email_c, "password": "Pass1234!", "full_name": "Carol"})
        db = TestingSessionLocal()
        from app.models.database import User
        uc = db.query(User).filter(User.email == email_c).first()
        uc.is_verified = True
        db.commit()
        db.close()
        r_c = client.post("/auth/login", json={"email": email_c, "password": "Pass1234!"})
        token_c = r_c.json()["access_token"]

        # Upload image as user C
        r_img = _upload_image(client, token_c, data=make_png_bytes(40, 40))
        did_c = r_img.json()["detection_id"]

        # Try to include it in a batch owned by registered_user
        r_batch = client.post(
            "/batches",
            json={"batch_name": "Cross-user Batch", "detection_ids": [did_c]},
            headers=_auth_headers(registered_user["token"]),
        )
        assert r_batch.status_code == 403


# ────────────────────────────────────────────────────────────────────────────
# E) Batch Export
# ────────────────────────────────────────────────────────────────────────────

class TestBatchExport:
    @patch("app.celery_app.celery_app.send_task")
    def test_export_batch_json(self, mock_send, client, registered_user):
        mock_send.return_value = MagicMock(id="fake-id")
        r = _upload_image(client, registered_user["token"], data=make_png_bytes(50, 50))
        did = r.json()["detection_id"]
        r_b = client.post(
            "/batches",
            json={"batch_name": "Export JSON", "detection_ids": [did]},
            headers=_auth_headers(registered_user["token"]),
        )
        bid = r_b.json()["batch_id"]

        r_exp = client.get(f"/batches/{bid}/export?fmt=json", headers=_auth_headers(registered_user["token"]))
        assert r_exp.status_code == 200
        data = r_exp.json()
        assert data["batch_id"] == bid
        assert "detections" in data
        assert "summary" in data

    @patch("app.celery_app.celery_app.send_task")
    def test_export_batch_csv(self, mock_send, client, registered_user):
        mock_send.return_value = MagicMock(id="fake-id")
        r = _upload_image(client, registered_user["token"], data=make_png_bytes(52, 52))
        did = r.json()["detection_id"]
        r_b = client.post(
            "/batches",
            json={"batch_name": "Export CSV", "detection_ids": [did]},
            headers=_auth_headers(registered_user["token"]),
        )
        bid = r_b.json()["batch_id"]

        r_exp = client.get(f"/batches/{bid}/export?fmt=csv", headers=_auth_headers(registered_user["token"]))
        assert r_exp.status_code == 200
        assert "text/csv" in r_exp.headers.get("content-type", "")

    def test_export_invalid_format(self, client, registered_user):
        r = client.get("/batches/1/export?fmt=xml", headers=_auth_headers(registered_user["token"]))
        assert r.status_code == 422  # query param validation


# ────────────────────────────────────────────────────────────────────────────
# F) API Key Management
# ────────────────────────────────────────────────────────────────────────────

class TestAPIKeys:
    def test_create_api_key(self, client, registered_user):
        r = client.post(
            "/api-keys",
            json={"name": "My Key"},
            headers=_auth_headers(registered_user["token"]),
        )
        assert r.status_code in (200, 201), r.text
        data = r.json()
        assert "key" in data or "api_key" in data

    def test_list_api_keys(self, client, registered_user):
        r = client.get("/api-keys", headers=_auth_headers(registered_user["token"]))
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))

    def test_revoke_api_key(self, client, registered_user):
        # Create
        r = client.post(
            "/api-keys",
            json={"name": "To Revoke"},
            headers=_auth_headers(registered_user["token"]),
        )
        assert r.status_code in (200, 201)

        # List keys to get the ID (creation response doesn't include id)
        r_list = client.get("/api-keys", headers=_auth_headers(registered_user["token"]))
        assert r_list.status_code == 200
        keys = r_list.json().get("keys", [])
        key_id = next((k["id"] for k in keys if k.get("name") == "To Revoke"), None)
        assert key_id is not None, "Created key not found in list"

        # Revoke
        r2 = client.delete(f"/api-keys/{key_id}", headers=_auth_headers(registered_user["token"]))
        assert r2.status_code in (200, 204)


# ────────────────────────────────────────────────────────────────────────────
# G) Quota Enforcement
# ────────────────────────────────────────────────────────────────────────────

class TestQuotaEnforcement:
    @patch("app.celery_app.celery_app.send_task")
    def test_quota_exceeded_returns_429(self, mock_send, client):
        mock_send.return_value = MagicMock(id="fake-id")
        # Create a user with 0 scans remaining
        email = f"quota_{uuid.uuid4().hex[:8]}@example.com"
        client.post("/auth/register", json={"email": email, "password": "Pass1234!", "full_name": "Quota Tester"})

        db = TestingSessionLocal()
        from app.models.database import User
        user = db.query(User).filter(User.email == email).first()
        user.is_verified = True
        user.subscription_tier = "free"
        db.commit()
        user_id = user.id
        db.close()

        r_login = client.post("/auth/login", json={"email": email, "password": "Pass1234!"})
        token = r_login.json()["access_token"]

        # Exhaust quota by setting scans_used = limit via UsageLog injection
        from app.services.usage_service import QUOTA_CONFIG
        from app.models.database import Detection as Det
        tier_limit = QUOTA_CONFIG.get("free", {}).get("scans_per_month", 5)
        now = datetime.utcnow()
        db = TestingSessionLocal()
        for i in range(tier_limit):
            db.add(Det(
                user_id=user_id,
                file_hash=f"quota_hash_{i}_{uuid.uuid4().hex}",
                file_type="image",
                processing_status="completed",
                created_at=now,
                uploaded_at=now,
            ))
        db.commit()
        db.close()

        r = client.post(
            "/detections/image",
            files={"file": ("over_quota.png", io.BytesIO(make_png_bytes()), "image/png")},
            headers=_auth_headers(token),
        )
        assert r.status_code == 429, r.text


# ────────────────────────────────────────────────────────────────────────────
# H) Error Handling
# ────────────────────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_upload_missing_file_field(self, client, registered_user):
        r = client.post(
            "/detections/image",
            data={},
            headers=_auth_headers(registered_user["token"]),
        )
        assert r.status_code == 422

    def test_health_endpoint(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_health_detailed_endpoint(self, client):
        r = client.get("/health/detailed")
        assert r.status_code == 200
        data = r.json()
        assert "database" in data or "status" in data


# ────────────────────────────────────────────────────────────────────────────
# I) Cache (DB-level unit tests)
# ────────────────────────────────────────────────────────────────────────────

class TestCacheService:
    def test_cache_miss_returns_none(self, db):
        from app.services.cache_service import cache_service
        result = cache_service.get_cached_result(db, "nonexistent_hash_abc123")
        assert result is None

    def test_cache_store_and_retrieve(self, db):
        from app.services.cache_service import cache_service
        h = "testhash_" + uuid.uuid4().hex
        payload = {"ai_probability": 0.75, "confidence_score": 0.9}
        cache_service.cache_result(db, h, "image", payload)
        result = cache_service.get_cached_result(db, h)
        assert result is not None
        assert result["ai_probability"] == 0.75

    def test_cache_hit_increments_counter(self, db):
        from app.services.cache_service import cache_service
        from app.models.database import DetectionCache
        h = "hit_counter_" + uuid.uuid4().hex
        cache_service.cache_result(db, h, "image", {"ai_probability": 0.5})
        cache_service.get_cached_result(db, h)
        cache_service.get_cached_result(db, h)
        entry = db.query(DetectionCache).filter(DetectionCache.file_hash == h).first()
        assert entry.hits == 2

    def test_clear_old_cache(self, db):
        from app.services.cache_service import cache_service
        from app.models.database import DetectionCache
        h = "old_entry_" + uuid.uuid4().hex
        cache_service.cache_result(db, h, "image", {"ai_probability": 0.3})
        # Force created_at into the distant past
        entry = db.query(DetectionCache).filter(DetectionCache.file_hash == h).first()
        from datetime import timedelta
        entry.created_at = datetime.utcnow() - timedelta(days=40)
        db.commit()
        deleted = cache_service.clear_old_cache(db, days=30)
        assert deleted >= 1


# ────────────────────────────────────────────────────────────────────────────
# J) Export Service unit tests
# ────────────────────────────────────────────────────────────────────────────

class TestExportService:
    def test_export_detection_as_json(self):
        from app.utils.export_service import export_service
        det = MagicMock()
        det.id = 1
        det.user_id = 10
        det.batch_id = None
        det.file_hash = "abc123"
        det.file_type = "image"
        det.original_filename = "test.png"
        det.file_size_bytes = 1024
        det.processing_status = "completed"
        det.ai_probability = 0.82
        det.confidence_score = 0.95
        det.detection_methods = "efficientnet_b4:0.82"
        det.result_json = {"artifacts_found": ["potential_deepfake"]}
        det.processing_time_ms = 500
        det.served_from_cache = False
        det.error_message = None
        det.uploaded_at = datetime.utcnow()
        det.completed_at = datetime.utcnow()

        result = export_service.export_detection_as_json(det)
        assert result["detection_id"] == 1
        assert result["ai_probability"] == 0.82
        assert "artifacts_found" in result

    def test_export_batch_as_csv(self):
        from app.utils.export_service import export_service
        batch = MagicMock()
        batch.id = 1
        batch.batch_name = "Test Batch"
        batch.status = "completed"
        batch.created_at = datetime.utcnow()
        batch.completed_at = datetime.utcnow()

        det = MagicMock()
        det.id = 1
        det.original_filename = "file.png"
        det.file_type = "image"
        det.uploaded_at = datetime.utcnow()
        det.ai_probability = 0.6
        det.confidence_score = 0.85
        det.processing_time_ms = 300
        det.processing_status = "completed"
        det.served_from_cache = False
        det.error_message = None

        csv_str = export_service.export_batch_as_csv(batch, [det])
        assert "detection_id" in csv_str
        assert "file.png" in csv_str

    def test_export_batch_as_json(self):
        from app.utils.export_service import export_service
        batch = MagicMock()
        batch.id = 5
        batch.batch_name = "JSON Export Batch"
        batch.status = "completed"
        batch.created_at = datetime.utcnow()
        batch.completed_at = datetime.utcnow()

        result = export_service.export_batch_as_json(batch, [])
        assert result["batch_id"] == 5
        assert "summary" in result
        assert result["detections"] == []

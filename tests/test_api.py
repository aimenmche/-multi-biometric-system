"""
Automated tests for the Multi-Biometric Identity Verification System.
Run with: python -m pytest tests/ -v
Requires the backend server to be running on port 8000.
"""

import requests
import json
import pytest

BASE_URL = "http://localhost:8000"

TEST_USER = {
    "username": "testuser_api",
    "email": "testapi@example.com",
    "password": "testpass123",
    "full_name": "Test API User",
    "role": "student",
}

ADMIN_CREDS = {
    "username": "admin",
    "password": "admin123",
}


class TestHealth:
    def test_health_check(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"


class TestRegistration:
    def setup_method(self):
        try:
            resp = requests.post(
                f"{BASE_URL}/api/register",
                json=TEST_USER,
            )
        except:
            pass

    def test_register_success(self):
        new_user = {
            "username": "new_test_user",
            "email": "new_test@example.com",
            "password": "password123",
            "full_name": "New Test User",
            "role": "student",
        }
        resp = requests.post(f"{BASE_URL}/api/register", json=new_user)
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "new_test_user"

    def test_register_duplicate(self):
        resp = requests.post(f"{BASE_URL}/api/register", json=TEST_USER)
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"]


class TestLogin:
    def test_login_success(self):
        resp = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": TEST_USER["username"], "password": TEST_USER["password"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["username"] == TEST_USER["username"]

    def test_login_wrong_password(self):
        resp = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": TEST_USER["username"], "password": "wrongpass"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent(self):
        resp = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": "nonexistent_user", "password": "password"},
        )
        assert resp.status_code == 401


class TestProfile:
    def setup_method(self):
        resp = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": TEST_USER["username"], "password": TEST_USER["password"]},
        )
        self.token = resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_get_profile(self):
        resp = requests.get(f"{BASE_URL}/api/profile", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == TEST_USER["username"]
        assert data["email"] == TEST_USER["email"]

    def test_profile_no_token(self):
        resp = requests.get(f"{BASE_URL}/api/profile")
        assert resp.status_code == 403


class TestAttendance:
    def setup_method(self):
        resp = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": TEST_USER["username"], "password": TEST_USER["password"]},
        )
        self.token = resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.user_id = resp.json()["user"]["id"]

    def test_record_attendance(self):
        resp = requests.post(
            f"{BASE_URL}/api/attendance/log",
            headers=self.headers,
            json={"user_id": self.user_id, "method": "web_manual", "status": "present"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "Attendance recorded" in data["message"]

    def test_my_attendance(self):
        resp = requests.get(
            f"{BASE_URL}/api/attendance/my?limit=10",
            headers=self.headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "records" in data


class TestAdmin:
    def setup_method(self):
        resp = requests.post(
            f"{BASE_URL}/api/login",
            json=ADMIN_CREDS,
        )
        self.token = resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_admin_list_users(self):
        resp = requests.get(f"{BASE_URL}/admin/users", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert data["total"] > 0

    def test_admin_attendance(self):
        resp = requests.get(f"{BASE_URL}/admin/attendance", headers=self.headers)
        assert resp.status_code == 200

    def test_admin_actions(self):
        resp = requests.get(f"{BASE_URL}/admin/actions", headers=self.headers)
        assert resp.status_code == 200


class TestBiometricFlow:
    def setup_method(self):
        resp = requests.post(
            f"{BASE_URL}/api/login",
            json=ADMIN_CREDS,
        )
        self.token = resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.admin_user_id = resp.json()["user"]["id"]

    def test_register_face_biometric_failure_no_face(self):
        resp = requests.post(
            f"{BASE_URL}/api/register-biometric",
            headers=self.headers,
            json={
                "user_id": self.admin_user_id,
                "biometric_type": "face",
                "template_data": "invalid_base64_data",
            },
        )
        assert resp.status_code in [400, 500]

    def test_register_fingerprint_simulation(self):
        resp = requests.post(
            f"{BASE_URL}/api/register-biometric",
            headers=self.headers,
            json={
                "user_id": self.admin_user_id,
                "biometric_type": "fingerprint",
                "template_data": "test_fingerprint_code_123",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["biometric_type"] == "fingerprint"

    def test_login_with_fingerprint(self):
        resp = requests.post(
            f"{BASE_URL}/api/login-fingerprint",
            json={
                "biometric_type": "fingerprint",
                "template_data": "test_fingerprint_code_123",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

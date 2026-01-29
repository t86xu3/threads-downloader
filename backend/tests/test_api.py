"""
API 端點測試
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """健康檢查端點測試"""

    def test_health_check(self, client: TestClient):
        """測試健康檢查端點"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "app" in data

    def test_root_endpoint(self, client: TestClient):
        """測試根端點"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data


class TestDownloadEndpoint:
    """下載端點測試"""

    def test_download_threads_url(self, client: TestClient, sample_urls: dict):
        """測試提交 Threads URL"""
        response = client.post(
            "/api/download",
            json={"url": sample_urls["threads"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "taskId" in data
        assert len(data["taskId"]) == 8

    def test_download_xiaohongshu_url(self, client: TestClient, sample_urls: dict):
        """測試提交小紅書 URL"""
        response = client.post(
            "/api/download",
            json={"url": sample_urls["xiaohongshu"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "taskId" in data

    def test_download_douyin_url(self, client: TestClient, sample_urls: dict):
        """測試提交抖音 URL"""
        response = client.post(
            "/api/download",
            json={"url": sample_urls["douyin"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "taskId" in data

    def test_download_with_platform(self, client: TestClient, sample_urls: dict):
        """測試指定平台提交"""
        response = client.post(
            "/api/download",
            json={"url": sample_urls["threads"], "platform": "threads"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "taskId" in data

    def test_download_invalid_url(self, client: TestClient, sample_urls: dict):
        """測試無效 URL"""
        response = client.post(
            "/api/download",
            json={"url": sample_urls["invalid"]},
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_download_empty_url(self, client: TestClient):
        """測試空 URL"""
        response = client.post(
            "/api/download",
            json={"url": ""},
        )
        assert response.status_code == 400

    def test_download_missing_url(self, client: TestClient):
        """測試缺少 URL"""
        response = client.post(
            "/api/download",
            json={},
        )
        assert response.status_code == 422  # Validation error


class TestStatusEndpoint:
    """狀態查詢端點測試"""

    def test_get_status_existing_task(self, client: TestClient, sample_urls: dict):
        """測試查詢存在的任務"""
        # 先建立任務
        create_response = client.post(
            "/api/download",
            json={"url": sample_urls["threads"]},
        )
        task_id = create_response.json()["taskId"]

        # 查詢狀態
        response = client.get(f"/api/status/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["taskId"] == task_id
        assert "status" in data
        assert "progress" in data

    def test_get_status_nonexistent_task(self, client: TestClient):
        """測試查詢不存在的任務"""
        response = client.get("/api/status/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestFileEndpoint:
    """檔案下載端點測試"""

    def test_get_nonexistent_file(self, client: TestClient):
        """測試下載不存在的檔案"""
        response = client.get("/api/files/nonexistent.mp4")
        assert response.status_code == 404

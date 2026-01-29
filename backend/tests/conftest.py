"""
Pytest 配置和共用 fixtures
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.queue import task_queue, TaskStatus


@pytest.fixture
def client():
    """同步測試客戶端"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """異步測試客戶端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def cleanup_queue():
    """每個測試後清理任務隊列"""
    yield
    # 清理所有任務
    task_queue._tasks.clear()


@pytest.fixture
def sample_urls():
    """測試用的範例 URL"""
    return {
        "threads": "https://www.threads.net/@user/post/ABC123",
        "xiaohongshu": "https://www.xiaohongshu.com/explore/abc123",
        "xiaohongshu_short": "https://xhslink.com/abc123",
        "douyin": "https://www.douyin.com/video/7123456789",
        "douyin_short": "https://v.douyin.com/abc123",
        "tiktok": "https://www.tiktok.com/@user/video/7123456789",
        "invalid": "https://www.youtube.com/watch?v=abc123",
    }

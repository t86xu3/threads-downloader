"""
任務隊列測試
"""

import pytest
from datetime import datetime, timedelta

from app.queue import TaskQueue, TaskStatus, Task


class TestTaskQueue:
    """任務隊列測試"""

    @pytest.fixture
    def queue(self):
        """建立新的任務隊列"""
        return TaskQueue()

    def test_create_task(self, queue: TaskQueue):
        """測試建立任務"""
        task = queue.create_task(
            url="https://threads.net/test",
            platform="threads",
        )
        assert task.id is not None
        assert len(task.id) == 8
        assert task.url == "https://threads.net/test"
        assert task.platform == "threads"
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0

    def test_get_task(self, queue: TaskQueue):
        """測試獲取任務"""
        created = queue.create_task("https://test.com", "threads")
        retrieved = queue.get_task(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_nonexistent_task(self, queue: TaskQueue):
        """測試獲取不存在的任務"""
        result = queue.get_task("nonexistent")
        assert result is None

    def test_update_task_status(self, queue: TaskQueue):
        """測試更新任務狀態"""
        task = queue.create_task("https://test.com", "threads")

        updated = queue.update_task(
            task.id,
            status=TaskStatus.PROCESSING,
        )
        assert updated.status == TaskStatus.PROCESSING

    def test_update_task_progress(self, queue: TaskQueue):
        """測試更新任務進度"""
        task = queue.create_task("https://test.com", "threads")

        updated = queue.update_task(task.id, progress=50)
        assert updated.progress == 50

    def test_update_task_download_url(self, queue: TaskQueue):
        """測試更新下載 URL"""
        task = queue.create_task("https://test.com", "threads")

        updated = queue.update_task(
            task.id,
            status=TaskStatus.COMPLETED,
            download_url="/api/files/test.mp4",
        )
        assert updated.status == TaskStatus.COMPLETED
        assert updated.download_url == "/api/files/test.mp4"

    def test_update_task_error(self, queue: TaskQueue):
        """測試更新任務錯誤"""
        task = queue.create_task("https://test.com", "threads")

        updated = queue.update_task(
            task.id,
            status=TaskStatus.FAILED,
            error="Download failed",
        )
        assert updated.status == TaskStatus.FAILED
        assert updated.error == "Download failed"

    def test_delete_task(self, queue: TaskQueue):
        """測試刪除任務"""
        task = queue.create_task("https://test.com", "threads")

        result = queue.delete_task(task.id)
        assert result is True
        assert queue.get_task(task.id) is None

    def test_delete_nonexistent_task(self, queue: TaskQueue):
        """測試刪除不存在的任務"""
        result = queue.delete_task("nonexistent")
        assert result is False

    def test_cleanup_old_tasks(self, queue: TaskQueue):
        """測試清理舊任務"""
        # 建立任務
        task = queue.create_task("https://test.com", "threads")

        # 模擬舊任務（修改建立時間）
        task.created_at = datetime.now() - timedelta(hours=2)

        # 清理 1 小時前的任務
        cleaned = queue.cleanup_old_tasks(max_age_seconds=3600)
        assert cleaned == 1
        assert queue.get_task(task.id) is None

    def test_cleanup_keeps_recent_tasks(self, queue: TaskQueue):
        """測試清理保留新任務"""
        task = queue.create_task("https://test.com", "threads")

        cleaned = queue.cleanup_old_tasks(max_age_seconds=3600)
        assert cleaned == 0
        assert queue.get_task(task.id) is not None

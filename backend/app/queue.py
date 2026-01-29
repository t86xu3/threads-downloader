"""
簡單的內存任務隊列
生產環境建議使用 Redis 或 Celery
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional
from datetime import datetime
import uuid


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    url: str
    platform: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    download_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class TaskQueue:
    def __init__(self):
        self._tasks: Dict[str, Task] = {}

    def create_task(self, url: str, platform: str) -> Task:
        task_id = str(uuid.uuid4())[:8]  # 短 ID
        task = Task(
            id=task_id,
            url=url,
            platform=platform,
        )
        self._tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[int] = None,
        download_url: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[Task]:
        task = self._tasks.get(task_id)
        if not task:
            return None

        if status is not None:
            task.status = status
        if progress is not None:
            task.progress = progress
        if download_url is not None:
            task.download_url = download_url
        if error is not None:
            task.error = error

        task.updated_at = datetime.now()
        return task

    def delete_task(self, task_id: str) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        """清理超過指定時間的任務"""
        now = datetime.now()
        to_delete = []
        for task_id, task in self._tasks.items():
            age = (now - task.created_at).total_seconds()
            if age > max_age_seconds:
                to_delete.append(task_id)

        for task_id in to_delete:
            del self._tasks[task_id]

        return len(to_delete)


# 全局任務隊列實例
task_queue = TaskQueue()

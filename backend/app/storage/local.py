"""
本地檔案存儲
用於開發和測試環境
"""

import os
import aiofiles
from pathlib import Path
from typing import Optional


class LocalStorage:
    def __init__(self, base_path: str = "/tmp/video-downloads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_file_path(self, filename: str) -> Path:
        return self.base_path / filename

    async def save_file(self, filename: str, content: bytes) -> str:
        """儲存檔案並返回本地路徑"""
        file_path = self.get_file_path(filename)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        return str(file_path)

    async def get_file(self, filename: str) -> Optional[bytes]:
        """讀取檔案內容"""
        file_path = self.get_file_path(filename)
        if not file_path.exists():
            return None
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def delete_file(self, filename: str) -> bool:
        """刪除檔案"""
        file_path = self.get_file_path(filename)
        if file_path.exists():
            os.remove(file_path)
            return True
        return False

    def file_exists(self, filename: str) -> bool:
        """檢查檔案是否存在"""
        return self.get_file_path(filename).exists()

    def get_download_url(self, filename: str) -> str:
        """獲取下載 URL（本地模式直接返回 API endpoint）"""
        return f"/api/files/{filename}"

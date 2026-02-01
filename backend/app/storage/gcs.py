"""
Google Cloud Storage 存儲
用於 GCP 生產環境
"""

import datetime
import asyncio
from functools import partial
from typing import Optional

from google.cloud import storage
from google.cloud.exceptions import NotFound


class GCSStorage:
    def __init__(
        self,
        bucket_name: str,
        project_id: Optional[str] = None,
    ):
        """
        初始化 GCS 存儲

        Args:
            bucket_name: GCS bucket 名稱
            project_id: GCP 專案 ID（可選，會自動從環境變數讀取）
        """
        self.bucket_name = bucket_name
        self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)

    async def upload_file(
        self,
        filename: str,
        content: bytes,
        content_type: str = "video/mp4",
    ) -> str:
        """上傳檔案到 GCS 並返回下載 URL"""
        loop = asyncio.get_event_loop()

        def _upload():
            blob = self.bucket.blob(filename)
            blob.upload_from_string(content, content_type=content_type)

        await loop.run_in_executor(None, _upload)

        return self.get_download_url(filename)

    async def upload_from_file(
        self,
        filename: str,
        file_path: str,
        content_type: str = "video/mp4",
    ) -> str:
        """從本地檔案上傳到 GCS 並返回下載 URL"""
        loop = asyncio.get_event_loop()

        def _upload():
            blob = self.bucket.blob(filename)
            blob.upload_from_filename(file_path, content_type=content_type)

        await loop.run_in_executor(None, _upload)

        return self.get_download_url(filename)

    async def delete_file(self, filename: str) -> bool:
        """從 GCS 刪除檔案"""
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                partial(self.bucket.blob(filename).delete),
            )
            return True
        except NotFound:
            return False
        except Exception:
            return False

    def get_download_url(self, filename: str) -> str:
        """
        獲取下載 URL（生成 24 小時有效的 signed URL）

        Note: 需要服務帳號有 storage.objects.get 權限
        """
        blob = self.bucket.blob(filename)
        url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(hours=24),
            method="GET",
        )
        return url

    async def file_exists(self, filename: str) -> bool:
        """檢查檔案是否存在"""
        loop = asyncio.get_event_loop()
        try:
            exists = await loop.run_in_executor(
                None,
                self.bucket.blob(filename).exists,
            )
            return exists
        except Exception:
            return False

    async def get_file(self, filename: str) -> Optional[bytes]:
        """下載檔案內容"""
        loop = asyncio.get_event_loop()
        try:
            blob = self.bucket.blob(filename)
            content = await loop.run_in_executor(
                None,
                blob.download_as_bytes,
            )
            return content
        except NotFound:
            return None
        except Exception:
            return None

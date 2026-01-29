"""
Cloudflare R2 存儲
用於生產環境
"""

import boto3
from botocore.config import Config
from typing import Optional
import asyncio
from functools import partial


class R2Storage:
    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        public_url: str = "",
    ):
        self.bucket_name = bucket_name
        self.public_url = public_url

        # R2 使用 S3 兼容 API
        self.client = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )

    async def upload_file(
        self,
        filename: str,
        content: bytes,
        content_type: str = "video/mp4",
    ) -> str:
        """上傳檔案到 R2 並返回公開 URL"""
        loop = asyncio.get_event_loop()

        await loop.run_in_executor(
            None,
            partial(
                self.client.put_object,
                Bucket=self.bucket_name,
                Key=filename,
                Body=content,
                ContentType=content_type,
            ),
        )

        return self.get_download_url(filename)

    async def delete_file(self, filename: str) -> bool:
        """從 R2 刪除檔案"""
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                partial(
                    self.client.delete_object,
                    Bucket=self.bucket_name,
                    Key=filename,
                ),
            )
            return True
        except Exception:
            return False

    def get_download_url(self, filename: str) -> str:
        """獲取公開下載 URL"""
        if self.public_url:
            return f"{self.public_url.rstrip('/')}/{filename}"
        # 如果沒有自定義域名，生成預簽名 URL
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": filename},
            ExpiresIn=86400,  # 24 小時
        )

    async def file_exists(self, filename: str) -> bool:
        """檢查檔案是否存在"""
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                partial(
                    self.client.head_object,
                    Bucket=self.bucket_name,
                    Key=filename,
                ),
            )
            return True
        except Exception:
            return False

"""
小紅書影片下載器
"""

import asyncio
import os
import re
from typing import Callable, Optional

from .base import BaseDownloader, DownloadResult


class XiaohongshuDownloader(BaseDownloader):
    platform_name = "xiaohongshu"

    def is_valid_url(self, url: str) -> bool:
        return "xiaohongshu.com" in url or "xhslink.com" in url

    async def download(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> DownloadResult:
        """下載小紅書影片"""

        self._update_progress(progress_callback, 10)

        # 如果是短連結，先解析真實 URL
        if "xhslink.com" in url:
            resolved_url = await self._resolve_short_url(url)
            if resolved_url:
                url = resolved_url

        self._update_progress(progress_callback, 20)

        # 嘗試使用 yt-dlp 下載
        result = await self._try_ytdlp(url, output_path, progress_callback)
        if result.success:
            return result

        self._update_progress(progress_callback, 40)

        # 嘗試解析頁面獲取影片 URL
        result = await self._try_parse_page(url, output_path, progress_callback)
        if result.success:
            return result

        return DownloadResult(
            success=False,
            error="無法下載此小紅書影片，可能是圖文筆記或連結無效",
        )

    async def _resolve_short_url(self, url: str) -> Optional[str]:
        """解析短連結獲取真實 URL"""
        try:
            command = [
                "curl",
                "-sI",
                "-L",
                "-o", "/dev/null",
                "-w", "%{url_effective}",
                url,
            ]

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30)
            resolved = stdout.decode().strip()

            if "xiaohongshu.com" in resolved:
                return resolved
            return None

        except Exception:
            return None

    async def _try_ytdlp(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]],
    ) -> DownloadResult:
        """使用 yt-dlp 下載"""
        try:
            command = [
                "yt-dlp",
                "-f", "best",
                "--merge-output-format", "mp4",
                "-o", output_path,
                "--no-warnings",
                "--extractor-args", "xiaohongshu:player_format=mp4",
                url,
            ]

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await asyncio.wait_for(process.communicate(), timeout=120)

            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                self._update_progress(progress_callback, 100)
                return DownloadResult(success=True, file_path=output_path)

            return DownloadResult(success=False)

        except Exception as e:
            return DownloadResult(success=False, error=str(e))

    async def _try_parse_page(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]],
    ) -> DownloadResult:
        """解析頁面獲取影片 URL"""
        try:
            # 獲取頁面內容
            command = [
                "curl",
                "-s",
                "-L",
                "-A", "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                url,
            ]

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30)
            page_content = stdout.decode()

            self._update_progress(progress_callback, 60)

            # 從頁面中提取影片 URL
            video_url = self._extract_video_url(page_content)

            if video_url:
                self._update_progress(progress_callback, 80)
                return await self._download_video(video_url, output_path, progress_callback)

            return DownloadResult(success=False, error="找不到影片連結")

        except Exception as e:
            return DownloadResult(success=False, error=str(e))

    def _extract_video_url(self, page_content: str) -> Optional[str]:
        """從頁面內容提取影片 URL"""
        patterns = [
            r'"url"\s*:\s*"(https?://[^"]+\.mp4[^"]*)"',
            r'"videoUrl"\s*:\s*"(https?://[^"]+)"',
            r'<video[^>]+src="(https?://[^"]+)"',
            r'"originVideoKey"\s*:\s*"([^"]+)"',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, page_content)
            for match in matches:
                # 處理轉義字符
                url = match.replace("\\u002F", "/")
                if url.startswith("http"):
                    return url

        return None

    async def _download_video(
        self,
        video_url: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]],
    ) -> DownloadResult:
        """下載影片"""
        try:
            command = [
                "curl",
                "-L",
                "-o", output_path,
                "-A", "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
                "-H", "Referer: https://www.xiaohongshu.com/",
                video_url,
            ]

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await asyncio.wait_for(process.communicate(), timeout=300)

            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                self._update_progress(progress_callback, 100)
                return DownloadResult(success=True, file_path=output_path)

            return DownloadResult(success=False, error="下載失敗")

        except Exception as e:
            return DownloadResult(success=False, error=str(e))

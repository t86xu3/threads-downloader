"""
抖音影片下載器
同時支援抖音和 TikTok
"""

import asyncio
import os
import re
from typing import Callable, Optional

from .base import BaseDownloader, DownloadResult


class DouyinDownloader(BaseDownloader):
    platform_name = "douyin"

    def is_valid_url(self, url: str) -> bool:
        return "douyin.com" in url or "tiktok.com" in url

    async def download(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> DownloadResult:
        """下載抖音/TikTok 影片"""

        self._update_progress(progress_callback, 10)

        # 如果是短連結，先解析
        if "v.douyin.com" in url or "vm.tiktok.com" in url:
            resolved_url = await self._resolve_short_url(url)
            if resolved_url:
                url = resolved_url

        self._update_progress(progress_callback, 20)

        # 優先使用 yt-dlp（對 TikTok 和抖音支援較好）
        result = await self._try_ytdlp(url, output_path, progress_callback)
        if result.success:
            return result

        self._update_progress(progress_callback, 40)

        # 備用方案：解析頁面
        result = await self._try_parse_page(url, output_path, progress_callback)
        if result.success:
            return result

        return DownloadResult(
            success=False,
            error="無法下載此影片，請確認連結是否正確",
        )

    async def _resolve_short_url(self, url: str) -> Optional[str]:
        """解析短連結"""
        try:
            command = [
                "curl",
                "-sI",
                "-L",
                "-o", "/dev/null",
                "-w", "%{url_effective}",
                "-A", "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
                url,
            ]

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30)
            resolved = stdout.decode().strip()

            if "douyin.com" in resolved or "tiktok.com" in resolved:
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
            # 抖音和 TikTok 需要特殊的 cookie 處理
            command = [
                "yt-dlp",
                "-f", "best[ext=mp4]/best",
                "--merge-output-format", "mp4",
                "-o", output_path,
                "--no-warnings",
                "--no-check-certificates",
                # 模擬手機 User-Agent
                "--user-agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                               "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                url,
            ]

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=120,
            )

            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                self._update_progress(progress_callback, 100)
                return DownloadResult(success=True, file_path=output_path)

            # 檢查錯誤訊息
            error_msg = stderr.decode() if stderr else ""
            if "login" in error_msg.lower() or "cookie" in error_msg.lower():
                return DownloadResult(
                    success=False,
                    error="此影片需要登入才能下載",
                )

            return DownloadResult(success=False)

        except asyncio.TimeoutError:
            return DownloadResult(success=False, error="下載超時")
        except Exception as e:
            return DownloadResult(success=False, error=str(e))

    async def _try_parse_page(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]],
    ) -> DownloadResult:
        """解析頁面獲取無浮水印影片 URL"""
        try:
            # 提取影片 ID
            video_id = self._extract_video_id(url)
            if not video_id:
                return DownloadResult(success=False, error="無法解析影片 ID")

            self._update_progress(progress_callback, 50)

            # 獲取影片資訊
            video_url = await self._get_video_url(video_id, url)

            if video_url:
                self._update_progress(progress_callback, 70)
                return await self._download_video(video_url, output_path, progress_callback)

            return DownloadResult(success=False, error="找不到影片連結")

        except Exception as e:
            return DownloadResult(success=False, error=str(e))

    def _extract_video_id(self, url: str) -> Optional[str]:
        """從 URL 提取影片 ID"""
        # 抖音格式: https://www.douyin.com/video/7xxxxx
        # TikTok 格式: https://www.tiktok.com/@user/video/7xxxxx

        patterns = [
            r"/video/(\d+)",
            r"vid=(\d+)",
            r"item_ids=(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    async def _get_video_url(self, video_id: str, original_url: str) -> Optional[str]:
        """獲取無浮水印影片 URL"""
        try:
            # 使用抖音 API 獲取影片資訊
            api_url = f"https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}"

            command = [
                "curl",
                "-s",
                "-A", "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
                api_url,
            ]

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30)
            response = stdout.decode()

            # 解析 JSON 獲取影片 URL
            import json
            data = json.loads(response)

            if data.get("item_list"):
                item = data["item_list"][0]
                # 獲取無浮水印地址
                video = item.get("video", {})

                # 嘗試不同的影片地址欄位
                play_addr = video.get("play_addr", {})
                url_list = play_addr.get("url_list", [])

                if url_list:
                    # 替換為無浮水印地址
                    video_url = url_list[0]
                    video_url = video_url.replace("playwm", "play")
                    return video_url

            return None

        except Exception:
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
                "-H", "Referer: https://www.douyin.com/",
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

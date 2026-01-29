"""
Threads 影片下載器
使用 Selenium 模擬瀏覽器繞過反爬蟲機制
"""

import asyncio
import os
import re
import subprocess
import tempfile
from typing import Callable, Optional

from .base import BaseDownloader, DownloadResult


class ThreadsDownloader(BaseDownloader):
    platform_name = "threads"

    def is_valid_url(self, url: str) -> bool:
        return "threads.net" in url

    async def download(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> DownloadResult:
        """下載 Threads 影片"""

        self._update_progress(progress_callback, 10)

        # 嘗試使用 yt-dlp 直接下載（最簡單的方式）
        result = await self._try_ytdlp(url, output_path, progress_callback)
        if result.success:
            return result

        self._update_progress(progress_callback, 30)

        # 如果 yt-dlp 失敗，嘗試使用 Selenium
        result = await self._try_selenium(url, output_path, progress_callback)
        if result.success:
            return result

        return DownloadResult(
            success=False,
            error="無法下載此影片，請確認連結是否正確",
        )

    async def _try_ytdlp(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]],
    ) -> DownloadResult:
        """嘗試使用 yt-dlp 下載"""
        try:
            command = [
                "yt-dlp",
                "-f", "best",
                "--merge-output-format", "mp4",
                "-o", output_path,
                "--no-warnings",
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

            if process.returncode == 0 and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                if file_size > 1000:  # 檔案大於 1KB
                    self._update_progress(progress_callback, 100)
                    return DownloadResult(success=True, file_path=output_path)

            return DownloadResult(success=False)

        except asyncio.TimeoutError:
            return DownloadResult(success=False, error="下載超時")
        except Exception as e:
            return DownloadResult(success=False, error=str(e))

    async def _try_selenium(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]],
    ) -> DownloadResult:
        """使用 Selenium 抓取影片 URL 後下載"""
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service

            self._update_progress(progress_callback, 40)

            # 設置 Chrome 選項
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # 嘗試不同的 Chrome 路徑
            chrome_paths = [
                "/usr/bin/chromium-browser",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium",
            ]
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_options.binary_location = path
                    break

            # 創建 driver
            loop = asyncio.get_event_loop()
            driver = await loop.run_in_executor(
                None,
                lambda: webdriver.Chrome(options=chrome_options),
            )

            self._update_progress(progress_callback, 50)

            try:
                # 載入頁面
                await loop.run_in_executor(None, lambda: driver.get(url))
                await asyncio.sleep(5)

                self._update_progress(progress_callback, 60)

                # 尋找影片元素
                video_url = await self._find_video_url(driver, loop)

                self._update_progress(progress_callback, 70)

                if video_url:
                    # 下載影片
                    result = await self._download_video_url(
                        video_url, output_path, progress_callback
                    )
                    return result

                # 如果找不到影片，嘗試從頁面源碼中提取
                page_source = driver.page_source
                video_url = self._extract_video_url_from_source(page_source)

                if video_url:
                    result = await self._download_video_url(
                        video_url, output_path, progress_callback
                    )
                    return result

                return DownloadResult(
                    success=False,
                    error="找不到影片連結",
                )

            finally:
                driver.quit()

        except Exception as e:
            return DownloadResult(success=False, error=f"Selenium 錯誤: {str(e)}")

    async def _find_video_url(self, driver, loop) -> Optional[str]:
        """從頁面中尋找影片 URL"""
        try:
            # 等待影片元素
            video_elements = await loop.run_in_executor(
                None,
                lambda: driver.find_elements(By.TAG_NAME, "video"),
            )

            for video in video_elements:
                src = video.get_attribute("src")
                if src and src.startswith("http"):
                    return src

            # 檢查 source 元素
            source_elements = await loop.run_in_executor(
                None,
                lambda: driver.find_elements(By.TAG_NAME, "source"),
            )

            for source in source_elements:
                src = source.get_attribute("src")
                if src and src.startswith("http"):
                    return src

            return None
        except Exception:
            return None

    def _extract_video_url_from_source(self, page_source: str) -> Optional[str]:
        """從頁面源碼中提取影片 URL"""
        patterns = [
            r'https?://[^"\s]+\.mp4[^"\s]*',
            r'https?://[^"\s]+\.mov[^"\s]*',
            r'https?://[^"\s]+\.webm[^"\s]*',
            r'https?://[^"\s]+instagram[^"\s]*\.fbcdn[^"\s]*',
            r'https?://[^"\s]+cdninstagram[^"\s]*',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, page_source)
            for match in matches:
                # 清理 URL
                match = match.split('"')[0].split("'")[0]
                if "video" in match.lower() or match.endswith((".mp4", ".mov", ".webm")):
                    return match

        return None

    async def _download_video_url(
        self,
        video_url: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]],
    ) -> DownloadResult:
        """下載指定的影片 URL"""
        self._update_progress(progress_callback, 80)

        try:
            # 使用 curl 下載
            command = [
                "curl",
                "-L",
                "-o", output_path,
                "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "-H", "Referer: https://www.threads.com/",
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

            return DownloadResult(success=False, error="下載的檔案無效")

        except asyncio.TimeoutError:
            return DownloadResult(success=False, error="下載超時")
        except Exception as e:
            return DownloadResult(success=False, error=str(e))

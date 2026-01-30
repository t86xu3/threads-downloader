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

from .base import BaseDownloader, DownloadResult, ParseResult, MediaItem
import json


class ThreadsDownloader(BaseDownloader):
    platform_name = "threads"

    def is_valid_url(self, url: str) -> bool:
        return "threads.net" in url or "threads.com" in url

    async def parse(self, url: str) -> ParseResult:
        """解析 Threads 貼文中的所有媒體"""
        try:
            # 使用 yt-dlp 獲取媒體資訊
            command = [
                "yt-dlp",
                "--dump-json",
                "--no-warnings",
                "--flat-playlist",
                url,
            ]

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=60,
            )

            if process.returncode != 0:
                # yt-dlp 失敗，嘗試使用 Selenium 解析
                return await self._parse_with_selenium(url)

            media_items = []
            # yt-dlp 可能輸出多行 JSON（playlist 的情況）
            for line in stdout.decode().strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    media_item = self._extract_media_item(data)
                    if media_item:
                        media_items.append(media_item)
                except json.JSONDecodeError:
                    continue

            if media_items:
                return ParseResult(success=True, media=media_items)

            # 如果沒找到，嘗試 Selenium
            return await self._parse_with_selenium(url)

        except asyncio.TimeoutError:
            return ParseResult(success=False, error="解析超時")
        except Exception as e:
            return ParseResult(success=False, error=str(e))

    def _extract_media_item(self, data: dict) -> Optional[MediaItem]:
        """從 yt-dlp JSON 中提取媒體項目"""
        # 獲取最佳格式的 URL
        url = data.get("url") or data.get("webpage_url")
        if not url:
            # 嘗試從 formats 中獲取
            formats = data.get("formats", [])
            if formats:
                # 選擇最佳品質
                best_format = max(formats, key=lambda f: f.get("height", 0) or 0)
                url = best_format.get("url")

        if not url:
            return None

        # 判斷類型
        media_type = "video"
        if data.get("ext") in ["jpg", "jpeg", "png", "webp", "gif"]:
            media_type = "image"

        # 格式化時長
        duration = None
        if data.get("duration"):
            secs = int(data["duration"])
            mins, secs = divmod(secs, 60)
            duration = f"{mins}:{secs:02d}"

        return MediaItem(
            type=media_type,
            url=url,
            thumbnail=data.get("thumbnail"),
            duration=duration,
            width=data.get("width"),
            height=data.get("height"),
        )

    def _create_chrome_driver(self):
        """建立 Chrome driver 並自動管理版本"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

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

        # 使用 webdriver-manager 自動管理 ChromeDriver
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    async def _parse_with_selenium(self, url: str) -> ParseResult:
        """使用 Selenium 解析頁面中的媒體"""
        try:
            from selenium.webdriver.common.by import By

            loop = asyncio.get_event_loop()
            driver = await loop.run_in_executor(
                None,
                self._create_chrome_driver,
            )

            try:
                await loop.run_in_executor(None, lambda: driver.get(url))
                await asyncio.sleep(5)

                media_items = []

                # 找所有影片
                video_elements = await loop.run_in_executor(
                    None,
                    lambda: driver.find_elements(By.TAG_NAME, "video"),
                )

                for video in video_elements:
                    src = video.get_attribute("src")
                    poster = video.get_attribute("poster")
                    if src and src.startswith("http"):
                        media_items.append(MediaItem(
                            type="video",
                            url=src,
                            thumbnail=poster,
                        ))

                # 找所有圖片（輪播貼文中的圖片）
                # Threads 的圖片通常在特定的容器中
                img_elements = await loop.run_in_executor(
                    None,
                    lambda: driver.find_elements(By.CSS_SELECTOR, "img[src*='cdninstagram'], img[src*='fbcdn']"),
                )

                for img in img_elements:
                    src = img.get_attribute("src")
                    if src and src.startswith("http") and "profile" not in src.lower():
                        # 過濾掉頭像等小圖
                        width = img.get_attribute("width")
                        if width and int(width) > 100:
                            media_items.append(MediaItem(
                                type="image",
                                url=src,
                                thumbnail=src,
                            ))

                # 從頁面源碼中尋找影片 URL
                if not media_items:
                    page_source = driver.page_source
                    video_url = self._extract_video_url_from_source(page_source)
                    if video_url:
                        media_items.append(MediaItem(
                            type="video",
                            url=video_url,
                        ))

                if media_items:
                    return ParseResult(success=True, media=media_items)

                return ParseResult(success=False, error="找不到媒體")

            finally:
                driver.quit()

        except Exception as e:
            return ParseResult(success=False, error=f"Selenium 解析錯誤: {str(e)}")

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
            from selenium.webdriver.common.by import By

            self._update_progress(progress_callback, 40)

            # 創建 driver（使用 webdriver-manager 自動管理版本）
            loop = asyncio.get_event_loop()
            driver = await loop.run_in_executor(
                None,
                self._create_chrome_driver,
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

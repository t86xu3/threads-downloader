"""
下載器基類
所有平台下載器都繼承此類
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional, Tuple
from dataclasses import dataclass


@dataclass
class DownloadResult:
    success: bool
    file_path: Optional[str] = None
    error: Optional[str] = None


class BaseDownloader(ABC):
    """下載器抽象基類"""

    platform_name: str = "unknown"

    @abstractmethod
    async def download(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> DownloadResult:
        """
        下載影片

        Args:
            url: 影片網址
            output_path: 輸出檔案路徑
            progress_callback: 進度回調函數，參數為 0-100 的進度值

        Returns:
            DownloadResult 包含成功狀態、檔案路徑或錯誤訊息
        """
        pass

    @abstractmethod
    def is_valid_url(self, url: str) -> bool:
        """檢查 URL 是否為此平台的有效連結"""
        pass

    def _update_progress(
        self,
        progress_callback: Optional[Callable[[int], None]],
        value: int,
    ):
        """安全地更新進度"""
        if progress_callback:
            progress_callback(min(100, max(0, value)))

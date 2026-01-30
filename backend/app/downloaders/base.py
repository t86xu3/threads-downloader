"""
下載器基類
所有平台下載器都繼承此類
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional, Tuple, List
from dataclasses import dataclass, field


@dataclass
class DownloadResult:
    success: bool
    file_path: Optional[str] = None
    error: Optional[str] = None


@dataclass
class MediaItem:
    """媒體項目（影片或圖片）"""
    type: str  # 'video' or 'image'
    url: str
    thumbnail: Optional[str] = None
    duration: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass
class ParseResult:
    """解析結果"""
    success: bool
    media: List[MediaItem] = field(default_factory=list)
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

    async def parse(self, url: str) -> ParseResult:
        """
        解析貼文中的所有媒體

        Args:
            url: 貼文網址

        Returns:
            ParseResult 包含成功狀態和媒體列表
        """
        # 預設實作：返回單一媒體（原始 URL）
        return ParseResult(
            success=True,
            media=[MediaItem(type="video", url=url)],
        )

    def _update_progress(
        self,
        progress_callback: Optional[Callable[[int], None]],
        value: int,
    ):
        """安全地更新進度"""
        if progress_callback:
            progress_callback(min(100, max(0, value)))

from .base import BaseDownloader
from .threads import ThreadsDownloader
from .xiaohongshu import XiaohongshuDownloader
from .douyin import DouyinDownloader
from typing import Optional


def get_downloader(url: str) -> Optional[BaseDownloader]:
    """根據 URL 自動選擇對應的下載器"""
    if "threads.net" in url:
        return ThreadsDownloader()
    elif "xiaohongshu.com" in url or "xhslink.com" in url:
        return XiaohongshuDownloader()
    elif "douyin.com" in url or "tiktok.com" in url:
        return DouyinDownloader()
    return None


def get_downloader_by_platform(platform: str) -> Optional[BaseDownloader]:
    """根據平台名稱選擇下載器"""
    downloaders = {
        "threads": ThreadsDownloader,
        "xiaohongshu": XiaohongshuDownloader,
        "douyin": DouyinDownloader,
    }
    downloader_class = downloaders.get(platform)
    return downloader_class() if downloader_class else None


__all__ = [
    "BaseDownloader",
    "ThreadsDownloader",
    "XiaohongshuDownloader",
    "DouyinDownloader",
    "get_downloader",
    "get_downloader_by_platform",
]

"""
下載器測試
"""

import pytest

from app.downloaders import (
    get_downloader,
    get_downloader_by_platform,
    ThreadsDownloader,
    XiaohongshuDownloader,
    DouyinDownloader,
)


class TestGetDownloader:
    """下載器選擇測試"""

    def test_get_threads_downloader(self):
        """測試獲取 Threads 下載器"""
        downloader = get_downloader("https://www.threads.net/@user/post/123")
        assert downloader is not None
        assert isinstance(downloader, ThreadsDownloader)

    def test_get_xiaohongshu_downloader(self):
        """測試獲取小紅書下載器"""
        downloader = get_downloader("https://www.xiaohongshu.com/explore/123")
        assert downloader is not None
        assert isinstance(downloader, XiaohongshuDownloader)

    def test_get_xiaohongshu_short_url(self):
        """測試小紅書短連結"""
        downloader = get_downloader("https://xhslink.com/abc123")
        assert downloader is not None
        assert isinstance(downloader, XiaohongshuDownloader)

    def test_get_douyin_downloader(self):
        """測試獲取抖音下載器"""
        downloader = get_downloader("https://www.douyin.com/video/123")
        assert downloader is not None
        assert isinstance(downloader, DouyinDownloader)

    def test_get_tiktok_downloader(self):
        """測試獲取 TikTok 下載器（使用抖音下載器）"""
        downloader = get_downloader("https://www.tiktok.com/@user/video/123")
        assert downloader is not None
        assert isinstance(downloader, DouyinDownloader)

    def test_get_invalid_downloader(self):
        """測試無效 URL 返回 None"""
        downloader = get_downloader("https://www.youtube.com/watch?v=123")
        assert downloader is None

    def test_get_downloader_by_platform(self):
        """測試按平台名稱獲取下載器"""
        threads = get_downloader_by_platform("threads")
        assert isinstance(threads, ThreadsDownloader)

        xiaohongshu = get_downloader_by_platform("xiaohongshu")
        assert isinstance(xiaohongshu, XiaohongshuDownloader)

        douyin = get_downloader_by_platform("douyin")
        assert isinstance(douyin, DouyinDownloader)

    def test_get_invalid_platform(self):
        """測試無效平台返回 None"""
        downloader = get_downloader_by_platform("youtube")
        assert downloader is None


class TestThreadsDownloader:
    """Threads 下載器測試"""

    @pytest.fixture
    def downloader(self):
        return ThreadsDownloader()

    def test_platform_name(self, downloader: ThreadsDownloader):
        """測試平台名稱"""
        assert downloader.platform_name == "threads"

    def test_is_valid_url_true(self, downloader: ThreadsDownloader):
        """測試有效 URL"""
        assert downloader.is_valid_url("https://www.threads.net/@user/post/123") is True
        assert downloader.is_valid_url("https://threads.net/t/ABC123") is True

    def test_is_valid_url_false(self, downloader: ThreadsDownloader):
        """測試無效 URL"""
        assert downloader.is_valid_url("https://www.instagram.com/p/123") is False
        assert downloader.is_valid_url("https://www.youtube.com/watch") is False


class TestXiaohongshuDownloader:
    """小紅書下載器測試"""

    @pytest.fixture
    def downloader(self):
        return XiaohongshuDownloader()

    def test_platform_name(self, downloader: XiaohongshuDownloader):
        """測試平台名稱"""
        assert downloader.platform_name == "xiaohongshu"

    def test_is_valid_url_full(self, downloader: XiaohongshuDownloader):
        """測試完整 URL"""
        assert downloader.is_valid_url("https://www.xiaohongshu.com/explore/123") is True

    def test_is_valid_url_short(self, downloader: XiaohongshuDownloader):
        """測試短連結"""
        assert downloader.is_valid_url("https://xhslink.com/abc123") is True

    def test_is_valid_url_false(self, downloader: XiaohongshuDownloader):
        """測試無效 URL"""
        assert downloader.is_valid_url("https://www.weibo.com/123") is False


class TestDouyinDownloader:
    """抖音下載器測試"""

    @pytest.fixture
    def downloader(self):
        return DouyinDownloader()

    def test_platform_name(self, downloader: DouyinDownloader):
        """測試平台名稱"""
        assert downloader.platform_name == "douyin"

    def test_is_valid_url_douyin(self, downloader: DouyinDownloader):
        """測試抖音 URL"""
        assert downloader.is_valid_url("https://www.douyin.com/video/123") is True
        assert downloader.is_valid_url("https://v.douyin.com/abc123") is True

    def test_is_valid_url_tiktok(self, downloader: DouyinDownloader):
        """測試 TikTok URL"""
        assert downloader.is_valid_url("https://www.tiktok.com/@user/video/123") is True
        assert downloader.is_valid_url("https://vm.tiktok.com/abc123") is True

    def test_is_valid_url_false(self, downloader: DouyinDownloader):
        """測試無效 URL"""
        assert downloader.is_valid_url("https://www.youtube.com/watch") is False

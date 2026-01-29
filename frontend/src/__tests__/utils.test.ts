/**
 * 工具函數測試
 */

// 從 page.tsx 提取的平台檢測邏輯
function detectPlatform(url: string): string | null {
  if (url.includes('threads.net')) return 'threads';
  if (url.includes('xiaohongshu.com') || url.includes('xhslink.com')) return 'xiaohongshu';
  if (url.includes('douyin.com') || url.includes('tiktok.com')) return 'douyin';
  return null;
}

describe('detectPlatform', () => {
  describe('Threads URLs', () => {
    it('should detect threads.net URL', () => {
      expect(detectPlatform('https://www.threads.net/@user/post/123')).toBe('threads');
    });

    it('should detect threads.net short URL', () => {
      expect(detectPlatform('https://threads.net/t/ABC123')).toBe('threads');
    });
  });

  describe('小紅書 URLs', () => {
    it('should detect xiaohongshu.com URL', () => {
      expect(detectPlatform('https://www.xiaohongshu.com/explore/123')).toBe('xiaohongshu');
    });

    it('should detect xhslink.com short URL', () => {
      expect(detectPlatform('https://xhslink.com/abc123')).toBe('xiaohongshu');
    });
  });

  describe('抖音/TikTok URLs', () => {
    it('should detect douyin.com URL', () => {
      expect(detectPlatform('https://www.douyin.com/video/123')).toBe('douyin');
    });

    it('should detect v.douyin.com short URL', () => {
      expect(detectPlatform('https://v.douyin.com/abc123')).toBe('douyin');
    });

    it('should detect tiktok.com URL', () => {
      expect(detectPlatform('https://www.tiktok.com/@user/video/123')).toBe('douyin');
    });

    it('should detect vm.tiktok.com short URL', () => {
      expect(detectPlatform('https://vm.tiktok.com/abc123')).toBe('douyin');
    });
  });

  describe('Invalid URLs', () => {
    it('should return null for YouTube URL', () => {
      expect(detectPlatform('https://www.youtube.com/watch?v=123')).toBeNull();
    });

    it('should return null for Instagram URL', () => {
      expect(detectPlatform('https://www.instagram.com/p/123')).toBeNull();
    });

    it('should return null for empty string', () => {
      expect(detectPlatform('')).toBeNull();
    });

    it('should return null for random URL', () => {
      expect(detectPlatform('https://example.com')).toBeNull();
    });
  });
});

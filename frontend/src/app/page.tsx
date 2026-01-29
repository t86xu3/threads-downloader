'use client';

import { useState, useCallback } from 'react';

type Status = 'idle' | 'loading' | 'processing' | 'completed' | 'error';

interface Platform {
  name: string;
  icon: string;
  color: string;
}

const PLATFORMS: Record<string, Platform> = {
  threads: { name: 'Threads', icon: '@', color: 'text-white' },
  xiaohongshu: { name: '小紅書', icon: '📕', color: 'text-red-500' },
  douyin: { name: '抖音', icon: '🎵', color: 'text-pink-500' },
};

function detectPlatform(url: string): string | null {
  if (url.includes('threads.net')) return 'threads';
  if (url.includes('xiaohongshu.com') || url.includes('xhslink.com')) return 'xiaohongshu';
  if (url.includes('douyin.com') || url.includes('tiktok.com')) return 'douyin';
  return null;
}

export default function Home() {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [progress, setProgress] = useState(0);
  const [downloadUrl, setDownloadUrl] = useState('');
  const [error, setError] = useState('');
  const [detectedPlatform, setDetectedPlatform] = useState<string | null>(null);

  const handleUrlChange = useCallback((value: string) => {
    setUrl(value);
    setDetectedPlatform(detectPlatform(value));
    if (error) setError('');
  }, [error]);

  const handleDownload = async () => {
    if (!url.trim()) return;

    const platform = detectPlatform(url);
    if (!platform) {
      setError('不支援的網址格式，請輸入 Threads、小紅書或抖音的影片網址');
      return;
    }

    setStatus('loading');
    setError('');
    setProgress(0);

    try {
      const res = await fetch('/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, platform }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || '提交失敗');
      }

      const { taskId } = await res.json();
      setStatus('processing');
      pollStatus(taskId);
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err.message : '提交失敗，請稍後再試');
    }
  };

  const pollStatus = async (taskId: string) => {
    const maxAttempts = 60; // 最多輪詢 2 分鐘
    let attempts = 0;

    const interval = setInterval(async () => {
      attempts++;

      if (attempts > maxAttempts) {
        clearInterval(interval);
        setStatus('error');
        setError('下載超時，請重試');
        return;
      }

      try {
        const res = await fetch(`/api/status/${taskId}`);
        const data = await res.json();

        setProgress(data.progress || 0);

        if (data.status === 'completed') {
          clearInterval(interval);
          setStatus('completed');
          setDownloadUrl(data.downloadUrl);
        } else if (data.status === 'failed') {
          clearInterval(interval);
          setStatus('error');
          setError(data.error || '下載失敗');
        }
      } catch {
        // 網路錯誤時繼續輪詢
      }
    }, 2000);
  };

  const reset = () => {
    setUrl('');
    setStatus('idle');
    setProgress(0);
    setDownloadUrl('');
    setError('');
    setDetectedPlatform(null);
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      handleUrlChange(text);
    } catch {
      // 剪貼簿存取失敗，忽略
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo 和標題 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            🎬 影片下載器
          </h1>
          <p className="text-gray-400 text-sm">
            貼上網址，一鍵下載
          </p>
        </div>

        {status === 'completed' ? (
          /* 完成狀態 */
          <div className="space-y-4">
            <div className="text-center py-6">
              <div className="text-5xl mb-4">✅</div>
              <p className="text-green-400 text-xl font-medium">下載完成！</p>
            </div>

            <a
              href={downloadUrl}
              download
              className="block w-full py-4 bg-green-600 hover:bg-green-700 text-white text-center rounded-2xl font-medium text-lg transition-colors btn-press"
            >
              💾 儲存影片
            </a>

            <button
              onClick={reset}
              className="w-full py-4 bg-gray-700 hover:bg-gray-600 text-white rounded-2xl font-medium transition-colors btn-press"
            >
              🔄 下載另一個
            </button>
          </div>
        ) : (
          /* 輸入/處理狀態 */
          <div className="space-y-4">
            {/* 輸入框 */}
            <div className="relative">
              <input
                type="url"
                value={url}
                onChange={(e) => handleUrlChange(e.target.value)}
                placeholder="貼上影片網址..."
                disabled={status !== 'idle'}
                className="w-full px-4 py-4 pr-16 rounded-2xl bg-gray-800 text-white placeholder-gray-500 border border-gray-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all disabled:opacity-50"
              />
              {status === 'idle' && !url && (
                <button
                  onClick={handlePaste}
                  className="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
                >
                  貼上
                </button>
              )}
            </div>

            {/* 平台識別顯示 */}
            {detectedPlatform && status === 'idle' && (
              <div className="flex items-center justify-center gap-2 text-sm">
                <span className={PLATFORMS[detectedPlatform].color}>
                  {PLATFORMS[detectedPlatform].icon}
                </span>
                <span className="text-gray-400">
                  偵測到 {PLATFORMS[detectedPlatform].name} 影片
                </span>
              </div>
            )}

            {/* 下載按鈕或進度顯示 */}
            {status === 'processing' ? (
              <div className="py-6 bg-gray-800 rounded-2xl border border-gray-700">
                <div className="text-center mb-4">
                  <span className="text-2xl progress-animate">⏳</span>
                  <p className="text-white mt-2">正在處理... {progress}%</p>
                </div>
                <div className="mx-6 h-3 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-300 rounded-full"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <p className="text-gray-500 text-xs text-center mt-3">
                  請勿關閉此頁面
                </p>
              </div>
            ) : (
              <button
                onClick={handleDownload}
                disabled={status === 'loading' || !url.trim()}
                className="w-full py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-2xl font-medium text-lg transition-all btn-press disabled:opacity-50"
              >
                {status === 'loading' ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                    提交中...
                  </span>
                ) : (
                  '📥 下載影片'
                )}
              </button>
            )}

            {/* 錯誤訊息 */}
            {error && (
              <div className="p-4 bg-red-900/30 border border-red-800 rounded-xl">
                <p className="text-red-400 text-center text-sm">{error}</p>
              </div>
            )}

            {/* 支援平台 */}
            <div className="flex items-center justify-center gap-4 text-sm text-gray-500 pt-2">
              <span>支援：</span>
              <span className="text-white">Threads</span>
              <span>•</span>
              <span className="text-red-400">小紅書</span>
              <span>•</span>
              <span className="text-pink-400">抖音</span>
            </div>
          </div>
        )}

        {/* 廣告位預留 */}
        <div className="mt-10 p-6 bg-gray-800/50 rounded-2xl border border-gray-700/50 text-center">
          <p className="text-gray-600 text-sm">廣告位</p>
        </div>

        {/* 頁腳 */}
        <footer className="mt-8 text-center text-gray-600 text-xs">
          <p>免費使用 • 無需註冊 • 隱私安全</p>
        </footer>
      </div>
    </main>
  );
}

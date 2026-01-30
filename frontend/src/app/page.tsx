'use client';

import { useState, useCallback } from 'react';
import AdSlot from '@/components/AdSlot';

type Status = 'idle' | 'loading' | 'parsing' | 'selecting' | 'downloading' | 'completed' | 'error';

interface Platform {
  name: string;
  icon: string;
  color: string;
}

interface MediaItem {
  id: string;
  type: 'video' | 'image';
  url: string;
  thumbnail?: string;
  duration?: string;
  selected: boolean;
  thumbnailFailed?: boolean;
}

const PLATFORMS: Record<string, Platform> = {
  threads: { name: 'Threads', icon: '@', color: 'text-white' },
  xiaohongshu: { name: '小紅書', icon: '📕', color: 'text-red-500' },
  douyin: { name: '抖音', icon: '🎵', color: 'text-pink-500' },
};

function detectPlatform(url: string): string | null {
  // 支援 threads.net 和 threads.com
  if (url.includes('threads.net') || url.includes('threads.com')) return 'threads';
  if (url.includes('xiaohongshu.com') || url.includes('xhslink.com')) return 'xiaohongshu';
  if (url.includes('douyin.com') || url.includes('tiktok.com')) return 'douyin';
  return null;
}

export default function Home() {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [progress, setProgress] = useState(0);
  const [downloadUrls, setDownloadUrls] = useState<string[]>([]);
  const [error, setError] = useState('');
  const [detectedPlatform, setDetectedPlatform] = useState<string | null>(null);
  const [mediaItems, setMediaItems] = useState<MediaItem[]>([]);
  const [currentDownloadIndex, setCurrentDownloadIndex] = useState(0);

  const handleUrlChange = useCallback((value: string) => {
    setUrl(value);
    setDetectedPlatform(detectPlatform(value));
    if (error) setError('');
  }, [error]);

  // 步驟 1: 解析貼文
  const handleParse = async () => {
    if (!url.trim()) return;

    const platform = detectPlatform(url);
    if (!platform) {
      setError('不支援的網址格式，請輸入 Threads、小紅書或抖音的影片網址');
      return;
    }

    setStatus('parsing');
    setError('');
    setMediaItems([]);

    try {
      const res = await fetch('/api/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, platform }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || '解析失敗');
      }

      const { media } = await res.json();

      if (!media || media.length === 0) {
        throw new Error('找不到可下載的媒體');
      }

      // 預設全選
      const items: MediaItem[] = media.map((m: any, index: number) => ({
        id: `media-${index}`,
        type: m.type || 'video',
        url: m.url,
        thumbnail: m.thumbnail,
        duration: m.duration,
        selected: true,
      }));

      setMediaItems(items);
      setStatus('selecting');
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err.message : '解析失敗，請稍後再試');
    }
  };

  // 切換選擇
  const toggleSelect = (id: string) => {
    setMediaItems(items =>
      items.map(item =>
        item.id === id ? { ...item, selected: !item.selected } : item
      )
    );
  };

  // 全選/取消全選
  const toggleSelectAll = () => {
    const allSelected = mediaItems.every(item => item.selected);
    setMediaItems(items =>
      items.map(item => ({ ...item, selected: !allSelected }))
    );
  };

  // 步驟 2: 下載選中的媒體
  const handleDownload = async () => {
    const selectedItems = mediaItems.filter(item => item.selected);
    if (selectedItems.length === 0) {
      setError('請至少選擇一個項目');
      return;
    }

    setStatus('downloading');
    setProgress(0);
    setDownloadUrls([]);
    setCurrentDownloadIndex(0);

    const urls: string[] = [];

    for (let i = 0; i < selectedItems.length; i++) {
      setCurrentDownloadIndex(i + 1);
      setProgress(Math.round((i / selectedItems.length) * 100));

      try {
        const res = await fetch('/api/download', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            url: selectedItems[i].url,
            platform: detectedPlatform,
            mediaType: selectedItems[i].type,
          }),
        });

        if (!res.ok) {
          console.error(`下載項目 ${i + 1} 失敗`);
          continue;
        }

        const { taskId } = await res.json();

        // 等待下載完成
        const downloadUrl = await waitForDownload(taskId);
        if (downloadUrl) {
          urls.push(downloadUrl);
        }
      } catch (err) {
        console.error(`下載項目 ${i + 1} 錯誤:`, err);
      }
    }

    setProgress(100);

    if (urls.length > 0) {
      setDownloadUrls(urls);
      setStatus('completed');
    } else {
      setStatus('error');
      setError('所有項目下載失敗');
    }
  };

  // 等待單個下載完成
  const waitForDownload = async (taskId: string): Promise<string | null> => {
    const maxAttempts = 60;

    for (let i = 0; i < maxAttempts; i++) {
      await new Promise(resolve => setTimeout(resolve, 2000));

      try {
        const res = await fetch(`/api/status/${taskId}`);
        const data = await res.json();

        if (data.status === 'completed') {
          return data.downloadUrl;
        } else if (data.status === 'failed') {
          return null;
        }
      } catch {
        // 繼續輪詢
      }
    }

    return null;
  };

  const reset = () => {
    setUrl('');
    setStatus('idle');
    setProgress(0);
    setDownloadUrls([]);
    setError('');
    setDetectedPlatform(null);
    setMediaItems([]);
    setCurrentDownloadIndex(0);
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      handleUrlChange(text);
    } catch {
      // 剪貼簿存取失敗
    }
  };

  const selectedCount = mediaItems.filter(item => item.selected).length;

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo 和標題 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            🎬 影片下載器
          </h1>
          <p className="text-gray-400 text-sm">
            貼上網址，選擇下載
          </p>
        </div>

        {status === 'completed' ? (
          /* 完成狀態 */
          <div className="space-y-4">
            <div className="text-center py-6">
              <div className="text-5xl mb-4">✅</div>
              <p className="text-green-400 text-xl font-medium">
                下載完成！({downloadUrls.length} 個檔案)
              </p>
            </div>

            {downloadUrls.map((downloadUrl, index) => (
              <a
                key={index}
                href={downloadUrl}
                download
                className="block w-full py-3 bg-green-600 hover:bg-green-700 text-white text-center rounded-xl font-medium transition-colors btn-press"
              >
                💾 儲存檔案 {downloadUrls.length > 1 ? `#${index + 1}` : ''}
              </a>
            ))}

            <button
              onClick={reset}
              className="w-full py-4 bg-gray-700 hover:bg-gray-600 text-white rounded-2xl font-medium transition-colors btn-press"
            >
              🔄 下載另一個
            </button>
          </div>
        ) : status === 'selecting' ? (
          /* 選擇媒體狀態 */
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-white font-medium">
                找到 {mediaItems.length} 個媒體
              </p>
              <button
                onClick={toggleSelectAll}
                className="text-sm text-blue-400 hover:text-blue-300"
              >
                {mediaItems.every(item => item.selected) ? '取消全選' : '全選'}
              </button>
            </div>

            {/* 媒體列表 */}
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {mediaItems.map((item, index) => (
                <div
                  key={item.id}
                  onClick={() => toggleSelect(item.id)}
                  className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all ${
                    item.selected
                      ? 'bg-blue-600/20 border border-blue-500'
                      : 'bg-gray-800 border border-gray-700 hover:border-gray-600'
                  }`}
                >
                  {/* 選擇框 */}
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      item.selected ? 'bg-blue-500' : 'bg-gray-700'
                    }`}
                  >
                    {item.selected && (
                      <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                  </div>

                  {/* 縮圖 */}
                  <div className="w-16 h-16 bg-gray-700 rounded-lg overflow-hidden flex-shrink-0 flex items-center justify-center text-2xl">
                    {item.thumbnail ? (
                      <img
                        src={item.thumbnail}
                        alt=""
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      item.type === 'video' ? '🎬' : '🖼️'
                    )}
                  </div>

                  {/* 資訊 */}
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium">
                      {item.type === 'video' ? '影片' : '圖片'} #{index + 1}
                    </p>
                    {item.duration && (
                      <p className="text-gray-400 text-sm">{item.duration}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* 下載按鈕 */}
            <button
              onClick={handleDownload}
              disabled={selectedCount === 0}
              className="w-full py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-2xl font-medium text-lg transition-all btn-press disabled:opacity-50"
            >
              📥 下載選中項目 ({selectedCount})
            </button>

            {/* 返回按鈕 */}
            <button
              onClick={reset}
              className="w-full py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-xl font-medium transition-colors"
            >
              ← 返回
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
                  偵測到 {PLATFORMS[detectedPlatform].name} 貼文
                </span>
              </div>
            )}

            {/* 解析/下載進度 */}
            {(status === 'parsing' || status === 'downloading') && (
              <div className="py-6 bg-gray-800 rounded-2xl border border-gray-700">
                <div className="text-center mb-4">
                  <span className="text-2xl progress-animate">⏳</span>
                  <p className="text-white mt-2">
                    {status === 'parsing' ? '正在解析貼文...' : `正在下載 ${currentDownloadIndex}/${mediaItems.filter(i => i.selected).length}...`}
                  </p>
                </div>
                {status === 'downloading' && (
                  <div className="mx-6 h-3 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-300 rounded-full"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                )}
                <p className="text-gray-500 text-xs text-center mt-3">
                  請勿關閉此頁面
                </p>
              </div>
            )}

            {/* 解析按鈕 */}
            {status === 'idle' && (
              <button
                onClick={handleParse}
                disabled={!url.trim()}
                className="w-full py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-2xl font-medium text-lg transition-all btn-press disabled:opacity-50"
              >
                🔍 解析貼文
              </button>
            )}

            {/* 錯誤訊息 */}
            {error && (
              <div className="p-4 bg-red-900/30 border border-red-800 rounded-xl">
                <p className="text-red-400 text-center text-sm">{error}</p>
                {status === 'error' && (
                  <button
                    onClick={reset}
                    className="w-full mt-3 py-2 text-sm text-red-400 hover:text-red-300"
                  >
                    重試
                  </button>
                )}
              </div>
            )}

            {/* 支援平台 */}
            {status === 'idle' && (
              <div className="flex items-center justify-center gap-4 text-sm text-gray-500 pt-2">
                <span>支援：</span>
                <span className="text-white">Threads</span>
                <span>•</span>
                <span className="text-red-400">小紅書</span>
                <span>•</span>
                <span className="text-pink-400">抖音</span>
              </div>
            )}
          </div>
        )}

        {/* 廣告位 */}
        <AdSlot slot="bottom-banner" className="mt-10" />

        {/* 頁腳 */}
        <footer className="mt-8 text-center text-gray-600 text-xs">
          <p>免費使用 • 無需註冊 • 隱私安全</p>
        </footer>
      </div>
    </main>
  );
}

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案簡介

一頁式多平台影片下載工具，支援 Threads、小紅書、抖音/TikTok。

## 開發命令

```bash
# 後端 (port 7988)
cd backend && source venv/bin/activate && uvicorn app.main:app --port 7988 --reload

# 前端 (port 3001)
cd frontend && npm run dev -- --port 3001

# 測試
./run-tests.sh          # 後端 + 前端單元測試
./run-tests.sh --e2e    # 包含 Playwright E2E

# 單獨執行測試
cd backend && pytest tests/ -v
cd backend && pytest tests/test_api.py::test_health -v  # 單一測試
cd frontend && npm test
cd frontend && npm run test:e2e
```

## 架構概覽

```
前端 (Next.js)                    後端 (FastAPI)
     │                                 │
     ├─ /api/parse ──────────────────→ /api/parse (解析媒體)
     ├─ /api/download ───────────────→ /api/download (建立任務)
     ├─ /api/status/[id] ────────────→ /api/status/{id} (查詢狀態)
     └─ /api/files/[filename] ───────→ /api/files/{filename} (取得檔案)
```

**下載流程**：
1. 前端呼叫 `/api/parse` 解析貼文中的媒體
2. 用戶選擇要下載的項目
3. 前端呼叫 `/api/download` 建立任務
4. 後端背景執行下載（yt-dlp 優先，Selenium 備用）
5. 前端輪詢 `/api/status/{id}` 直到完成
6. 用戶透過 `/api/files/{filename}` 下載檔案

**下載器架構** (`backend/app/downloaders/`)：
- `base.py`: 抽象基類，定義 `parse()` 和 `download()` 介面
- `threads.py`: Threads 下載器（yt-dlp + Selenium + webdriver-manager）
- `xiaohongshu.py`: 小紅書下載器
- `douyin.py`: 抖音/TikTok 下載器

## 部署資訊

### 舊版部署（Vercel + Render）

| 服務 | 平台 | URL |
|------|------|-----|
| 前端 | Vercel | https://threads-downloader-two.vercel.app |
| 後端 | Render | https://threads-downloader-1h19.onrender.com |
| Repo | GitHub | https://github.com/t86xu3/threads-downloader |

### 新版部署（Google Cloud）

| 服務 | 平台 | 說明 |
|------|------|------|
| 前端 | Firebase Hosting | 支援 Next.js SSR |
| 後端 | Cloud Run | min-instances=1 避免冷啟動 |
| 存儲 | Cloud Storage | 24 小時自動刪除 |

詳細部署步驟見 `docs/GCP_DEPLOYMENT.md`

### 環境變數

**前端：**
- `BACKEND_URL`: 後端 API 位址
- `NEXT_PUBLIC_ADSENSE_CLIENT_ID`: AdSense ID（可選）

**後端：**
- `STORAGE_PROVIDER`: 存儲後端（`local`、`r2`、`gcs`）
- `LOCAL_STORAGE_PATH`: 本地存儲路徑（local 模式）
- `GCS_BUCKET_NAME`: GCS bucket 名稱（gcs 模式）
- `GCS_PROJECT_ID`: GCP 專案 ID（可選，自動偵測）

## 開發規範

**Commit 風格**：繁體中文，格式 `類型: 描述`
- 範例：`功能: 新增抖音下載支援`、`修復: ChromeDriver 版本問題`

**命名規範**：
- 前端：camelCase（變數/函數），PascalCase（元件）
- 後端：snake_case（變數/函數），PascalCase（類別）

## 已知問題

- Render 免費版會休眠，首次請求約等 30-60 秒（GCP Cloud Run 已透過 min-instances=1 解決）
- 某些私人帳號的影片無法下載（需要登入 cookie）
- Chromium 版本需要匹配 ChromeDriver（使用 webdriver-manager 自動處理）

## 存儲架構

後端支援三種存儲模式，透過 `STORAGE_PROVIDER` 環境變數切換：

| 模式 | 用途 | 設定 |
|------|------|------|
| `local` | 開發測試 | `LOCAL_STORAGE_PATH` |
| `r2` | Cloudflare R2 | `R2_*` 系列變數 |
| `gcs` | Google Cloud Storage | `GCS_BUCKET_NAME` |

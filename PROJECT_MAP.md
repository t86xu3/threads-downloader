# PROJECT_MAP.md

## 專案概述
- 專案名稱：多平台影片下載器
- 專案目的：提供簡單的一頁式介面，讓用戶下載 Threads、小紅書、抖音影片

## 技術棧

| 類別 | 技術 | 版本 | 說明 |
|------|------|------|------|
| 前端框架 | Next.js | 14.2.5 | React 框架 |
| 樣式 | Tailwind CSS | 3.4.10 | 原子化 CSS |
| 語言 | TypeScript | 5.x | 型別安全 |
| 後端框架 | FastAPI | 0.128.0 | 高效能 Python API |
| 下載工具 | yt-dlp | 2025.12.8 | 通用影片下載 |
| 瀏覽器自動化 | Selenium | 4.40.0 | 繞過反爬蟲 |
| 後端測試 | pytest | 9.0.2 | Python 測試框架 |
| 前端測試 | Jest | 29.7.0 | JavaScript 測試框架 |
| E2E 測試 | Playwright | 1.41.0 | 端對端測試 |
| 部署（前端）| Vercel | - | 免費 Hobby 方案（舊） |
| 部署（後端）| Render | - | 免費 Web Service（舊） |
| 部署（前端）| Firebase Hosting | - | 支援 Next.js SSR（新） |
| 部署（後端）| Cloud Run | - | min-instances=1（新） |
| 存儲 | Google Cloud Storage | 2.14.0 | 影片暫存（24小時刪除） |

## 目錄結構

```
threads-downloader/
├── frontend/                    # Next.js 前端
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx        # 主頁面 UI
│   │   │   ├── layout.tsx      # 佈局
│   │   │   ├── globals.css     # 全域樣式
│   │   │   └── api/
│   │   │       ├── download/route.ts   # 提交下載 API
│   │   │       └── status/[id]/route.ts # 查詢狀態 API
│   │   └── __tests__/
│   │       └── utils.test.ts   # 工具函數測試
│   ├── e2e/
│   │   └── home.spec.ts        # 端對端測試
│   ├── package.json
│   ├── jest.config.js
│   ├── playwright.config.ts
│   ├── tailwind.config.ts
│   └── vercel.json
│
├── backend/                     # FastAPI 後端
│   ├── app/
│   │   ├── main.py             # API 入口
│   │   ├── config.py           # 設定管理
│   │   ├── queue.py            # 任務隊列
│   │   ├── storage/
│   │   │   ├── local.py        # 本地存儲
│   │   │   ├── r2.py           # Cloudflare R2
│   │   │   └── gcs.py          # Google Cloud Storage
│   │   └── downloaders/
│   │       ├── base.py         # 下載器基類
│   │       ├── threads.py      # Threads 下載器
│   │       ├── xiaohongshu.py  # 小紅書下載器
│   │       └── douyin.py       # 抖音下載器
│   ├── tests/
│   │   ├── conftest.py         # 測試配置
│   │   ├── test_api.py         # API 測試
│   │   ├── test_queue.py       # 隊列測試
│   │   └── test_downloaders.py # 下載器測試
│   ├── requirements.txt
│   ├── requirements-test.txt
│   ├── pytest.ini
│   ├── Dockerfile
│   ├── render.yaml
│   └── cloudbuild.yaml         # GCP Cloud Build 配置
│
├── docs/
│   └── GCP_DEPLOYMENT.md       # GCP 部署指南
│
├── firebase.json               # Firebase Hosting 配置
├── .firebaserc                 # Firebase 專案設定
├── download_threads.py          # 舊版腳本（備份）
├── run-tests.sh                 # 測試執行腳本
├── start-dev.sh                 # 開發啟動腳本
├── README.md
└── PROJECT_MAP.md
```

## 核心模組索引

| 模組/功能 | 檔案路徑 | 說明 |
|-----------|----------|------|
| 主頁面 UI | frontend/src/app/page.tsx | 一頁式響應式介面 |
| SEO 設定 | frontend/src/app/layout.tsx | Metadata、JSON-LD |
| Sitemap | frontend/src/app/sitemap.ts | 動態生成 sitemap.xml |
| Robots | frontend/src/app/robots.ts | 動態生成 robots.txt |
| OG Image | frontend/src/app/opengraph-image.tsx | 動態生成社群分享圖 |
| 廣告元件 | frontend/src/components/AdSlot.tsx | Google AdSense 整合 |
| 下載 API | frontend/src/app/api/download/route.ts | 前端代理 |
| 狀態 API | frontend/src/app/api/status/[id]/route.ts | 前端代理 |
| 後端入口 | backend/app/main.py | FastAPI 主程式 |
| 任務隊列 | backend/app/queue.py | 內存任務管理 |
| Threads 下載 | backend/app/downloaders/threads.py | Selenium + yt-dlp |
| 小紅書下載 | backend/app/downloaders/xiaohongshu.py | yt-dlp + 頁面解析 |
| 抖音下載 | backend/app/downloaders/douyin.py | yt-dlp + API |
| GCS 存儲 | backend/app/storage/gcs.py | Google Cloud Storage |
| 部署指南 | docs/GCP_DEPLOYMENT.md | GCP 部署步驟 |
| 後端測試 | backend/tests/ | pytest 測試套件 (42 tests) |
| 前端測試 | frontend/src/__tests__/ | Jest 測試 (12 tests) |
| E2E 測試 | frontend/e2e/ | Playwright 測試 (11 tests) |

## 開發進度

### 當前階段：v1.0 基礎功能 ✅

- [x] 建立 Next.js 前端專案結構
- [x] 實作一頁式 UI（響應式設計）
- [x] 建立 FastAPI 後端框架
- [x] 遷移 Threads 下載器到後端
- [x] 實作任務隊列
- [x] 前後端 API 串接
- [x] 實作小紅書下載器
- [x] 實作抖音下載器
- [x] URL 自動識別邏輯
- [x] 建立部署配置（Vercel + Render）
- [x] 本地測試
- [x] 自動化測試（65 tests 全部通過）

### v1.1 部署上線（Vercel + Render）✅

- [x] 部署前端到 Vercel
- [x] 部署後端到 Render

### v1.3 GCP 遷移（進行中）

#### 代碼準備 ✅
- [x] 新增 GCS 存儲模組 (gcs.py)
- [x] 新增 Cloud Build 配置 (cloudbuild.yaml)
- [x] 新增 Firebase Hosting 配置
- [x] 修改 main.py 支援多存儲後端
- [x] 建立部署指南文檔

#### 實際部署（待執行）
- [ ] 建立 GCP 專案、啟用 API
- [ ] 建立 Cloud Storage bucket
- [ ] 部署後端到 Cloud Run
- [ ] 部署前端到 Firebase Hosting
- [ ] 設定服務帳號權限
- [ ] 端對端線上測試

### v1.2 SEO 與廣告整合（進行中）

#### SEO 基礎建設 ✅
- [x] 加入 metadata（title, description, og:image）
- [x] 建立 sitemap.xml（動態生成）
- [x] 建立 robots.txt（動態生成）
- [x] 加入結構化數據（JSON-LD WebApplication）
- [x] 動態 OG Image 生成

#### 廣告整合 ✅
- [x] 預留廣告位元件（AdSlot）
- [x] Google AdSense 整合準備（環境變數配置）

#### 安全防護 ✅
- [x] Rate Limiting（slowapi）
  - /api/download: 10 次/分鐘
  - /api/parse: 20 次/分鐘

#### 內容頁面（SEO 長尾關鍵字）
- [ ] 教學頁面：如何下載 Threads 影片
- [ ] FAQ 頁面：常見問題
- [ ] 多語言支援（繁中、簡中、英文）

### 待優化項目

- [x] 雲端存儲整合（GCS / R2）
- [ ] 錯誤處理優化
- [ ] 下載進度更精確

## 關鍵檔案快速索引

- 進入點：frontend/src/app/page.tsx, backend/app/main.py
- 設定檔：frontend/next.config.mjs, backend/app/config.py
- 部署配置（舊）：frontend/vercel.json, backend/render.yaml
- 部署配置（GCP）：firebase.json, backend/cloudbuild.yaml, backend/Dockerfile
- 部署指南：docs/GCP_DEPLOYMENT.md
- 測試腳本：run-tests.sh
- 開發啟動：start-dev.sh

## 測試執行

```bash
# 執行所有測試（不含 E2E）
./run-tests.sh

# 包含端對端測試
./run-tests.sh --e2e

# 單獨執行
cd backend && source venv/bin/activate && pytest tests/ -v
cd frontend && npm test
cd frontend && npm run test:e2e
```

## 本地開發

```bash
# 後端 (port 7988)
cd backend && source venv/bin/activate && uvicorn app.main:app --port 7988

# 前端 (port 3001)
cd frontend && npm run dev -- --port 3001

# 訪問 http://localhost:3001
```

# 多平台影片下載器

一頁式影片下載工具，支援 Threads、小紅書、抖音。

## 功能特色

- **一頁式設計**：輸入網址，一鍵下載
- **Mobile First**：響應式設計，完美支援手機
- **自動識別平台**：從 URL 自動判斷來源
- **免費部署**：Vercel + Render 免費方案

## 支援平台

| 平台 | 網址格式 | 狀態 |
|------|----------|------|
| Threads | threads.net/... | ✅ |
| 小紅書 | xiaohongshu.com/..., xhslink.com/... | ✅ |
| 抖音 | douyin.com/..., v.douyin.com/... | ✅ |
| TikTok | tiktok.com/..., vm.tiktok.com/... | ✅ |

## 快速開始

### 本地開發

1. **啟動後端**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

2. **啟動前端**
```bash
cd frontend
npm install
npm run dev
```

3. 開啟 http://localhost:3000

### 使用 Docker（後端）

```bash
cd backend
docker build -t video-downloader-api .
docker run -p 8000:8000 video-downloader-api
```

## 部署

### 前端 (Vercel)

1. Fork 此倉庫
2. 在 Vercel 建立新專案，選擇 `frontend` 目錄
3. 設定環境變數 `BACKEND_URL`

### 後端 (Render)

1. 在 Render 建立新 Web Service
2. 選擇 Docker 部署
3. 指定 `backend` 目錄
4. 設定環境變數

## 目錄結構

```
threads-downloader/
├── frontend/                # Next.js 前端
│   ├── src/app/
│   │   ├── page.tsx        # 主頁面
│   │   └── api/            # API Routes
│   └── package.json
│
├── backend/                 # FastAPI 後端
│   ├── app/
│   │   ├── main.py         # API 入口
│   │   ├── queue.py        # 任務隊列
│   │   ├── downloaders/    # 下載器模組
│   │   └── storage/        # 存儲模組
│   ├── Dockerfile
│   └── requirements.txt
│
└── README.md
```

## API 文檔

### POST /api/download

建立下載任務。

**Request:**
```json
{
  "url": "https://threads.net/...",
  "platform": "threads"  // 可選，會自動識別
}
```

**Response:**
```json
{
  "taskId": "abc12345"
}
```

### GET /api/status/{taskId}

查詢任務狀態。

**Response:**
```json
{
  "taskId": "abc12345",
  "status": "completed",
  "progress": 100,
  "downloadUrl": "/api/files/abc12345.mp4"
}
```

## 技術棧

| 類別 | 技術 |
|------|------|
| 前端 | Next.js 14, Tailwind CSS, TypeScript |
| 後端 | FastAPI, Python 3.11 |
| 下載 | yt-dlp, Selenium, curl |
| 部署 | Vercel (前端), Render (後端) |

## License

MIT

# 多平台影片下載器 - 專案指令

## 專案簡介
一頁式影片下載工具，支援 Threads、小紅書、抖音/TikTok。

## 技術棧
- **前端**: Next.js 14 + Tailwind CSS + TypeScript
- **後端**: FastAPI + Python 3.13
- **下載**: yt-dlp + Selenium
- **測試**: pytest + Jest + Playwright

## 開發環境

### 端口配置
| 服務 | 端口 |
|------|------|
| 前端 | 3001 |
| 後端 | 7988 |

### 啟動命令
```bash
# 後端
cd backend && source venv/bin/activate && uvicorn app.main:app --port 7988

# 前端
cd frontend && npm run dev -- --port 3001
```

### 測試命令
```bash
# 全部測試
./run-tests.sh

# 包含 E2E
./run-tests.sh --e2e
```

## 當前工作
- v1.0 基礎功能已完成
- 自動化測試已建立（65 tests）
- 下一步：部署上線

## 開發規範

### Commit 風格
- 語言：繁體中文
- 格式：`類型: 描述`
- 範例：`功能: 新增抖音下載支援`

### 命名規範
- 前端：camelCase（變數/函數），PascalCase（元件）
- 後端：snake_case（變數/函數），PascalCase（類別）

## 已知問題
- 某些私人帳號的影片無法下載（需要登入 cookie）
- 抖音 API 可能因地區限制而失敗

## 重要路徑
- 主頁面：`frontend/src/app/page.tsx`
- 後端入口：`backend/app/main.py`
- 下載器：`backend/app/downloaders/`
- 測試：`backend/tests/`, `frontend/e2e/`

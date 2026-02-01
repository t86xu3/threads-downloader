# Google Cloud Platform 部署指南

本指南說明如何將 threads-downloader 部署到 Google Cloud Platform。

## 架構概覽

```
使用者
  │
  ▼
Firebase Hosting (前端 Next.js)
  │
  ▼
Cloud Run (後端 FastAPI)
  │ min-instances=1 (避免冷啟動)
  ▼
Cloud Storage (影片暫存，24小時自動刪除)
```

## 預估成本

| 服務 | 預估月費 |
|------|----------|
| Cloud Run (min-instances=1) | ~$30-40 |
| Firebase Hosting | ~$0-5 |
| Cloud Storage | ~$1-5 |
| **總計** | **~$35-50** |

---

## Phase 1: GCP 專案設定

### 1.1 建立專案

1. 前往 [Google Cloud Console](https://console.cloud.google.com)
2. 建立新專案，建議 ID：`threads-downloader-prod`

### 1.2 安裝並設定 gcloud CLI

```bash
# 登入
gcloud auth login

# 設定專案
gcloud config set project threads-downloader-prod
```

### 1.3 啟用必要 API

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com \
  artifactregistry.googleapis.com
```

### 1.4 建立 Cloud Storage Bucket

```bash
# 建立 bucket（選擇靠近目標用戶的區域）
gsutil mb -l us-central1 gs://threads-downloader-prod-videos

# 設定生命週期（24小時自動刪除）
cat > /tmp/lifecycle.json << 'EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 1}
      }
    ]
  }
}
EOF
gsutil lifecycle set /tmp/lifecycle.json gs://threads-downloader-prod-videos
```

---

## Phase 2: 部署後端到 Cloud Run

### 2.1 手動部署（首次）

```bash
cd backend

gcloud run deploy video-downloader-api \
  --source . \
  --region us-central1 \
  --min-instances 1 \
  --max-instances 10 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --allow-unauthenticated \
  --set-env-vars "STORAGE_PROVIDER=gcs,GCS_BUCKET_NAME=threads-downloader-prod-videos"
```

### 2.2 設定 Cloud Build（自動部署）

1. 前往 [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. 連接 GitHub 儲存庫
3. 建立 trigger：
   - 名稱：`deploy-backend`
   - 事件：Push to branch `main`
   - 配置檔案：`backend/cloudbuild.yaml`
   - 替換變數：`_GCS_BUCKET_NAME=threads-downloader-prod-videos`

### 2.3 驗證部署

```bash
# 取得服務 URL
gcloud run services describe video-downloader-api --region us-central1 --format 'value(status.url)'

# 測試健康檢查
curl https://video-downloader-api-xxx-uc.a.run.app/health
```

---

## Phase 3: 部署前端到 Firebase Hosting

### 3.1 安裝 Firebase CLI

```bash
npm install -g firebase-tools
firebase login
```

### 3.2 初始化 Firebase（首次）

```bash
# 在專案根目錄執行
firebase init hosting

# 選擇：
# - 使用現有專案：threads-downloader-prod
# - 公開目錄：frontend
# - 配置為 SPA：Yes
# - 設定 GitHub Actions：No（或 Yes 如果需要自動部署）
```

### 3.3 更新前端環境變數

建立 `frontend/.env.production`：

```env
BACKEND_URL=https://video-downloader-api-xxx-uc.a.run.app
```

### 3.4 部署前端

```bash
cd frontend
npm run build
firebase deploy --only hosting
```

---

## Phase 4: 服務帳號設定（用於 Signed URL）

Cloud Run 需要服務帳號來生成 GCS signed URL。

### 4.1 建立服務帳號

```bash
# 建立服務帳號
gcloud iam service-accounts create video-downloader-sa \
  --display-name="Video Downloader Service Account"

# 授予 Storage 權限
gcloud projects add-iam-policy-binding threads-downloader-prod \
  --member="serviceAccount:video-downloader-sa@threads-downloader-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# 授予 Service Account Token Creator 權限（用於 signed URL）
gcloud projects add-iam-policy-binding threads-downloader-prod \
  --member="serviceAccount:video-downloader-sa@threads-downloader-prod.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator"
```

### 4.2 更新 Cloud Run 使用此服務帳號

```bash
gcloud run services update video-downloader-api \
  --region us-central1 \
  --service-account video-downloader-sa@threads-downloader-prod.iam.gserviceaccount.com
```

---

## 驗證清單

- [ ] Cloud Run 服務正常運行：`curl $BACKEND_URL/health`
- [ ] 前端可以訪問：開啟 Firebase Hosting URL
- [ ] 完整下載流程測試：貼上 Threads 網址並下載
- [ ] 檢查 Cloud Storage 檔案：`gsutil ls gs://threads-downloader-prod-videos/`
- [ ] 確認檔案 24 小時後自動刪除

---

## 回滾策略

1. 保留 Vercel + Render 部署 1-2 週
2. 在 DNS 層面快速切換（如果使用自定義域名）
3. 確認 GCP 穩定後再關閉舊服務

---

## 常見問題

### Q: Signed URL 生成失敗？

確保服務帳號有以下權限：
- `roles/storage.objectAdmin`
- `roles/iam.serviceAccountTokenCreator`

### Q: Cloud Run 冷啟動還是很慢？

確認 `--min-instances 1` 設定生效：
```bash
gcloud run services describe video-downloader-api --region us-central1
```

### Q: 前端無法連接後端？

1. 確認 CORS 設定正確
2. 確認 `BACKEND_URL` 環境變數正確
3. 確認 Cloud Run 允許未認證請求

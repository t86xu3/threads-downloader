FROM python:3.11-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    chromium \
    curl \
    wget \
    ffmpeg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 設置 Chrome 環境變數
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage"

# 設置工作目錄
WORKDIR /app

# 複製依賴檔案
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 yt-dlp（確保是最新版）
RUN pip install --no-cache-dir --upgrade yt-dlp

# 複製應用程式
COPY . .

# 建立下載目錄
RUN mkdir -p /tmp/video-downloads

# 暴露端口（Cloud Run 使用 PORT 環境變數）
EXPOSE 8080

# 啟動命令（使用 shell 形式以支援環境變數）
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}

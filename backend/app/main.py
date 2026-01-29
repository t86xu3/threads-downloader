"""
Video Downloader API
FastAPI 主入口
"""

import os
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .config import get_settings
from .queue import task_queue, TaskStatus
from .downloaders import get_downloader, get_downloader_by_platform
from .storage.local import LocalStorage


# 應用設定
settings = get_settings()

# 本地存儲
storage = LocalStorage(settings.local_storage_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時
    Path(settings.local_storage_path).mkdir(parents=True, exist_ok=True)
    print(f"🚀 {settings.app_name} 啟動")
    print(f"📁 存儲路徑: {settings.local_storage_path}")

    yield

    # 關閉時
    print("👋 應用關閉")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境應限制來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class DownloadRequest(BaseModel):
    url: str
    platform: Optional[str] = None


class DownloadResponse(BaseModel):
    taskId: str


class StatusResponse(BaseModel):
    taskId: str
    status: str
    progress: int
    downloadUrl: Optional[str] = None
    error: Optional[str] = None


# API Endpoints
@app.post("/api/download", response_model=DownloadResponse)
async def create_download(req: DownloadRequest, background_tasks: BackgroundTasks):
    """建立下載任務"""
    url = req.url.strip()

    if not url:
        raise HTTPException(status_code=400, detail="請提供影片網址")

    # 自動識別平台或使用指定平台
    platform = req.platform
    if not platform:
        if "threads.net" in url:
            platform = "threads"
        elif "xiaohongshu.com" in url or "xhslink.com" in url:
            platform = "xiaohongshu"
        elif "douyin.com" in url or "tiktok.com" in url:
            platform = "douyin"
        else:
            raise HTTPException(
                status_code=400,
                detail="不支援的網址格式，請輸入 Threads、小紅書或抖音的影片網址",
            )

    # 檢查下載器是否存在
    downloader = get_downloader_by_platform(platform)
    if not downloader:
        raise HTTPException(status_code=400, detail=f"不支援的平台: {platform}")

    # 建立任務
    task = task_queue.create_task(url, platform)

    # 背景執行下載
    background_tasks.add_task(process_download, task.id)

    return DownloadResponse(taskId=task.id)


@app.get("/api/status/{task_id}", response_model=StatusResponse)
async def get_status(task_id: str):
    """查詢任務狀態"""
    task = task_queue.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任務不存在")

    return StatusResponse(
        taskId=task.id,
        status=task.status.value,
        progress=task.progress,
        downloadUrl=task.download_url,
        error=task.error,
    )


@app.get("/api/files/{filename}")
async def download_file(filename: str):
    """提供檔案下載"""
    file_path = storage.get_file_path(filename)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="video/mp4",
    )


@app.get("/health")
async def health():
    """健康檢查"""
    return {"status": "ok", "app": settings.app_name}


@app.get("/")
async def root():
    """根路徑"""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "endpoints": {
            "download": "POST /api/download",
            "status": "GET /api/status/{task_id}",
            "health": "GET /health",
        },
    }


# Background Task
async def process_download(task_id: str):
    """背景處理下載任務"""
    task = task_queue.get_task(task_id)
    if not task:
        return

    # 更新狀態為處理中
    task_queue.update_task(task_id, status=TaskStatus.PROCESSING)

    try:
        # 獲取下載器
        downloader = get_downloader_by_platform(task.platform)
        if not downloader:
            task_queue.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error="不支援的平台",
            )
            return

        # 準備輸出路徑
        output_filename = f"{task_id}.mp4"
        output_path = str(storage.get_file_path(output_filename))

        # 進度回調
        def progress_callback(progress: int):
            task_queue.update_task(task_id, progress=progress)

        # 執行下載
        result = await downloader.download(
            url=task.url,
            output_path=output_path,
            progress_callback=progress_callback,
        )

        if result.success:
            # 獲取下載 URL
            download_url = storage.get_download_url(output_filename)

            task_queue.update_task(
                task_id,
                status=TaskStatus.COMPLETED,
                progress=100,
                download_url=download_url,
            )
        else:
            task_queue.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error=result.error or "下載失敗",
            )

    except Exception as e:
        task_queue.update_task(
            task_id,
            status=TaskStatus.FAILED,
            error=f"處理錯誤: {str(e)}",
        )


# 定期清理任務（可選）
async def cleanup_task():
    """定期清理過期任務和檔案"""
    while True:
        await asyncio.sleep(3600)  # 每小時執行一次
        cleaned = task_queue.cleanup_old_tasks(max_age_seconds=86400)  # 清理 24 小時前的任務
        if cleaned > 0:
            print(f"🧹 清理了 {cleaned} 個過期任務")

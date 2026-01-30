"""
Video Downloader API
FastAPI 主入口
"""

import os
import asyncio
import base64
import aiohttp
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import get_settings
from .queue import task_queue, TaskStatus
from .downloaders import get_downloader, get_downloader_by_platform
from .storage.local import LocalStorage

# Rate Limiter 設定
limiter = Limiter(key_func=get_remote_address)


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

# Rate Limiter 註冊
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    mediaType: Optional[str] = None  # 'video' or 'image'


class DownloadResponse(BaseModel):
    taskId: str


class StatusResponse(BaseModel):
    taskId: str
    status: str
    progress: int
    downloadUrl: Optional[str] = None
    error: Optional[str] = None


class ParseRequest(BaseModel):
    url: str
    platform: Optional[str] = None


class MediaItemResponse(BaseModel):
    type: str
    url: str
    thumbnail: Optional[str] = None
    duration: Optional[str] = None


class ParseResponse(BaseModel):
    success: bool
    media: List[MediaItemResponse] = []
    error: Optional[str] = None


# API Endpoints
def is_direct_media_url(url: str) -> bool:
    """檢查是否為直接的媒體 CDN URL"""
    cdn_patterns = [
        "fbcdn.net",
        "cdninstagram.com",
        "instagram.f",
        ".mp4",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    ]
    return any(pattern in url.lower() for pattern in cdn_patterns)


@app.post("/api/download", response_model=DownloadResponse)
@limiter.limit("10/minute")  # 每個 IP 每分鐘最多 10 次下載
async def create_download(request: Request, req: DownloadRequest, background_tasks: BackgroundTasks):
    """建立下載任務"""
    url = req.url.strip()

    if not url:
        raise HTTPException(status_code=400, detail="請提供影片網址")

    # 檢查是否為直接的媒體 URL
    is_direct = is_direct_media_url(url)

    # 自動識別平台或使用指定平台
    platform = req.platform
    if not platform:
        # 支援 threads.net 和 threads.com
        if "threads.net" in url or "threads.com" in url:
            platform = "threads"
        elif "xiaohongshu.com" in url or "xhslink.com" in url:
            platform = "xiaohongshu"
        elif "douyin.com" in url or "tiktok.com" in url:
            platform = "douyin"
        elif is_direct:
            platform = "direct"  # 直接下載模式
        else:
            raise HTTPException(
                status_code=400,
                detail="不支援的網址格式，請輸入 Threads、小紅書或抖音的影片網址",
            )

    # 建立任務（包含媒體類型資訊）
    task = task_queue.create_task(url, platform)
    task.media_type = req.mediaType  # 儲存媒體類型

    # 背景執行下載
    background_tasks.add_task(process_download, task.id)

    return DownloadResponse(taskId=task.id)


@app.post("/api/parse", response_model=ParseResponse)
@limiter.limit("20/minute")  # 每個 IP 每分鐘最多 20 次解析
async def parse_post(request: Request, req: ParseRequest):
    """解析貼文中的所有媒體"""
    url = req.url.strip()

    if not url:
        raise HTTPException(status_code=400, detail="請提供網址")

    # 自動識別平台或使用指定平台
    platform = req.platform
    if not platform:
        # 支援 threads.net 和 threads.com
        if "threads.net" in url or "threads.com" in url:
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

    # 獲取下載器
    downloader = get_downloader_by_platform(platform)
    if not downloader:
        raise HTTPException(status_code=400, detail=f"不支援的平台: {platform}")

    # 解析媒體
    result = await downloader.parse(url)

    if not result.success:
        return ParseResponse(
            success=False,
            error=result.error or "解析失敗",
        )

    # 並行獲取所有縮圖
    async def fetch_single_thumbnail(session: aiohttp.ClientSession, item) -> MediaItemResponse:
        """獲取單個媒體項目的縮圖"""
        thumbnail_base64 = None

        # 先嘗試使用原始縮圖 URL
        if item.thumbnail:
            try:
                thumbnail_base64 = await fetch_thumbnail_as_base64(session, item.thumbnail)
            except Exception:
                pass

        # 如果是影片且沒有縮圖，用 ffmpeg 提取第一幀
        if not thumbnail_base64 and item.type == "video" and item.url:
            try:
                thumbnail_base64 = await extract_video_thumbnail(item.url)
            except Exception:
                pass

        return MediaItemResponse(
            type=item.type,
            url=item.url,
            thumbnail=thumbnail_base64,
            duration=item.duration,
        )

    # 並行執行所有縮圖獲取任務
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_single_thumbnail(session, item) for item in result.media]
        media_items = await asyncio.gather(*tasks)

    return ParseResponse(
        success=True,
        media=list(media_items),
    )


async def fetch_thumbnail_as_base64(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    """獲取縮圖並轉成 base64 data URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
        'Referer': 'https://www.threads.net/',
        'Accept': 'image/*,*/*;q=0.8',
    }
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                content = await resp.read()
                content_type = resp.headers.get('content-type', 'image/jpeg')
                b64 = base64.b64encode(content).decode('utf-8')
                return f"data:{content_type};base64,{b64}"
    except Exception:
        pass
    return None


async def extract_video_thumbnail(video_url: str) -> Optional[str]:
    """使用 ffmpeg 從影片提取第一幀作為縮圖"""
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name

        # 使用 ffmpeg 提取第一幀
        command = [
            'ffmpeg',
            '-i', video_url,
            '-ss', '0',
            '-vframes', '1',
            '-vf', 'scale=320:-1',
            '-y',
            '-headers', 'User-Agent: Mozilla/5.0\r\nReferer: https://www.threads.net/\r\n',
            tmp_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        await asyncio.wait_for(process.communicate(), timeout=15)

        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 100:
            with open(tmp_path, 'rb') as f:
                content = f.read()
            os.unlink(tmp_path)
            b64 = base64.b64encode(content).decode('utf-8')
            return f"data:image/jpeg;base64,{b64}"

        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    except Exception:
        pass
    return None


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

    # 根據副檔名判斷 media_type
    ext = filename.split(".")[-1].lower()
    media_types = {
        "mp4": "video/mp4",
        "mov": "video/quicktime",
        "webm": "video/webm",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
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
        # 直接下載模式（CDN URL）
        if task.platform == "direct":
            await process_direct_download(task_id, task)
            return

        # 獲取下載器
        downloader = get_downloader_by_platform(task.platform)
        if not downloader:
            task_queue.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error="不支援的平台",
            )
            return

        # 準備輸出路徑（根據媒體類型決定副檔名）
        ext = "jpg" if task.media_type == "image" else "mp4"
        output_filename = f"{task_id}.{ext}"
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


async def process_direct_download(task_id: str, task):
    """直接下載 CDN URL"""
    try:
        task_queue.update_task(task_id, progress=10)

        # 根據媒體類型決定副檔名
        ext = "jpg" if task.media_type == "image" else "mp4"
        output_filename = f"{task_id}.{ext}"
        output_path = str(storage.get_file_path(output_filename))

        task_queue.update_task(task_id, progress=30)

        # 使用 curl 下載
        command = [
            "curl",
            "-L",
            "-o", output_path,
            "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "-H", "Referer: https://www.threads.com/",
            "--max-time", "300",
            task.url,
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        task_queue.update_task(task_id, progress=50)

        await asyncio.wait_for(process.communicate(), timeout=300)

        task_queue.update_task(task_id, progress=90)

        # 檢查下載結果
        file_path = storage.get_file_path(output_filename)
        if file_path.exists() and file_path.stat().st_size > 1000:
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
                error="下載的檔案無效",
            )

    except asyncio.TimeoutError:
        task_queue.update_task(
            task_id,
            status=TaskStatus.FAILED,
            error="下載超時",
        )
    except Exception as e:
        task_queue.update_task(
            task_id,
            status=TaskStatus.FAILED,
            error=f"下載錯誤: {str(e)}",
        )


# 定期清理任務（可選）
async def cleanup_task():
    """定期清理過期任務和檔案"""
    while True:
        await asyncio.sleep(3600)  # 每小時執行一次
        cleaned = task_queue.cleanup_old_tasks(max_age_seconds=86400)  # 清理 24 小時前的任務
        if cleaned > 0:
            print(f"🧹 清理了 {cleaned} 個過期任務")

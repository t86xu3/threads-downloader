#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Threads 下載腳本 - 專為 n8n 設計
使用 Selenium 模擬瀏覽器來繞過反爬蟲機制
"""

import sys
import os
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def setup_chrome_driver():
    """設置 Chrome 瀏覽器驅動"""
    try:
        from selenium.webdriver.chrome.service import Service
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 無頭模式
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 在 Docker 容器中設置 Chrome 二進制檔案路徑
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        
        # 使用 Service 類指定 ChromeDriver 路徑
        service = Service("/usr/bin/chromedriver")
        
        # 嘗試創建驅動
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"❌ 無法創建 Chrome 驅動: {e}")
        return None

def download_threads_video(url, video_id, is_retry=False):
    """下載 Threads 影片"""
    print(f"🎯 開始下載 Threads 影片: {url}")
    print(f"🆔 影片 ID: {video_id}")
    
    if is_retry:
        print("🔄 重試模式：使用智能備用策略")
        return download_threads_with_backup_strategy(url, video_id)
    
    # 嘗試多次運行主要策略
    max_attempts = 3
    for attempt in range(max_attempts):
        print(f"🔄 主要策略嘗試 {attempt + 1}/{max_attempts}")
        
        driver = setup_chrome_driver()
        if not driver:
            print("❌ 無法創建瀏覽器驅動")
            continue
        
        try:
            print("🌐 正在加載頁面...")
            driver.get(url)
            
            # 等待頁面加載，增加等待時間
            print("⏳ 等待頁面完全加載...")
            time.sleep(10 + (attempt * 5))  # 每次重試增加等待時間
            
            print("📄 頁面標題:", driver.title)
            print("🔗 當前 URL:", driver.current_url)
            
            # 嘗試多種影片檢測策略
            video_found = False
            
            # 策略 1: 等待影片元素出現
            print("🔍 策略 1: 等待影片元素...")
            try:
                video_elements = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "video"))
                )
                
                print(f"🎥 找到 {len(video_elements)} 個影片元素")
                
                for i, video in enumerate(video_elements):
                    src = video.get_attribute('src')
                    print(f"  影片 {i+1}: {src}")
                    
                    if src and src.startswith('http'):
                        print(f"✅ 找到影片 URL: {src}")
                        
                        # 嘗試下載影片
                        success = download_video_with_ytdlp(src, video_id)
                        if success:
                            video_found = True
                            break
                
            except Exception as e:
                print(f"⚠️  策略 1 失敗: {e}")
            
            # 策略 2: 查找其他媒體元素
            if not video_found:
                print("🔍 策略 2: 查找其他媒體元素...")
                try:
                    # 查找 img 標籤
                    img_elements = driver.find_elements(By.TAG_NAME, "img")
                    print(f"🖼️  找到 {len(img_elements)} 個圖片元素")
                    
                    for i, img in enumerate(img_elements):
                        src = img.get_attribute('src')
                        if src and ('video' in src.lower() or 'media' in src.lower()):
                            print(f"✅ 找到可能的媒體 URL: {src}")
                            
                            # 嘗試下載
                            success = download_video_with_ytdlp(src, video_id)
                            if success:
                                video_found = True
                                break
                                
                except Exception as e:
                    print(f"⚠️  策略 2 失敗: {e}")
            
            # 策略 3: 查找 source 標籤
            if not video_found:
                print("🔍 策略 3: 查找 source 標籤...")
                try:
                    source_elements = driver.find_elements(By.TAG_NAME, "source")
                    print(f"📹 找到 {len(source_elements)} 個 source 元素")
                    
                    for i, source in enumerate(source_elements):
                        src = source.get_attribute('src')
                        if src and src.startswith('http'):
                            print(f"✅ 找到 source URL: {src}")
                            
                            # 嘗試下載
                            success = download_video_with_ytdlp(src, video_id)
                            if success:
                                video_found = True
                                break
                                
                except Exception as e:
                    print(f"⚠️  策略 3 失敗: {e}")
            
            # 策略 4: 查找 iframe 中的影片
            if not video_found:
                print("🔍 策略 4: 查找 iframe 中的影片...")
                try:
                    iframe_elements = driver.find_elements(By.TAG_NAME, "iframe")
                    print(f"🖼️  找到 {len(iframe_elements)} 個 iframe 元素")
                    
                    for i, iframe in enumerate(iframe_elements):
                        try:
                            driver.switch_to.frame(iframe)
                            
                            # 在 iframe 中查找影片
                            iframe_videos = driver.find_elements(By.TAG_NAME, "video")
                            if iframe_videos:
                                print(f"✅ 在 iframe {i+1} 中找到 {len(iframe_videos)} 個影片")
                                for video in iframe_videos:
                                    src = video.get_attribute('src')
                                    if src and src.startswith('http'):
                                        print(f"✅ 找到 iframe 影片 URL: {src}")
                                        success = download_video_with_ytdlp(src, video_id)
                                        if success:
                                            video_found = True
                                            break
                            
                            driver.switch_to.default_content()
                            if video_found:
                                break
                                
                        except Exception as e:
                            print(f"⚠️  處理 iframe {i+1} 時出錯: {e}")
                            driver.switch_to.default_content()
                            continue
                            
                except Exception as e:
                    print(f"⚠️  策略 4 失敗: {e}")
            
            # 策略 5: 分析頁面源碼，尋找隱藏的影片 URL
            if not video_found:
                print("🔍 策略 5: 分析頁面源碼...")
                try:
                    page_source = driver.page_source
                    
                    # 查找可能的影片 URL 模式
                    import re
                    video_patterns = [
                        r'https?://[^"\s]+\.mp4[^"\s]*',
                        r'https?://[^"\s]+\.mov[^"\s]*',
                        r'https?://[^"\s]+\.webm[^"\s]*',
                        r'https?://[^"\s]+video[^"\s]*',
                        r'https?://[^"\s]+media[^"\s]*',
                        r'https?://[^"\s]+instagram[^"\s]*\.fbcdn[^"\s]*',
                        r'https?://[^"\s]+cdninstagram[^"\s]*'
                    ]
                    
                    for pattern in video_patterns:
                        matches = re.findall(pattern, page_source)
                        if matches:
                            print(f"🔍 找到匹配的 URL 模式: {pattern}")
                            for match in matches:
                                print(f"  匹配: {match}")
                                
                                # 嘗試下載
                                success = download_video_with_ytdlp(match, video_id)
                                if success:
                                    video_found = True
                                    break
                            if video_found:
                                break
                                
                except Exception as e:
                    print(f"⚠️  策略 5 失敗: {e}")
            
            if video_found:
                print("🎉 成功找到並下載影片！")
                driver.quit()
                return True
            else:
                print(f"❌ 嘗試 {attempt + 1} 未找到可下載的影片")
                if attempt < max_attempts - 1:
                    print("🔄 等待後重試...")
                    time.sleep(5)
                driver.quit()
                continue
                
        except Exception as e:
            print(f"❌ 嘗試 {attempt + 1} 出錯: {e}")
            if driver:
                driver.quit()
            if attempt < max_attempts - 1:
                print("🔄 等待後重試...")
                time.sleep(5)
            continue
    
    print("❌ 所有主要策略嘗試都失敗了")
    return False

def download_threads_with_backup_strategy(url, video_id):
    """使用備用策略下載 Threads 影片"""
    print("🔄 嘗試備用策略...")
    
    # 策略 1: 嘗試不同的 URL 格式
    url_variations = [
        url.replace('/media?xmt=', ''),  # 移除 xmt 參數
        url.replace('/media', ''),       # 移除 /media 路徑
        url.split('?')[0],               # 移除所有查詢參數
    ]
    
    for i, test_url in enumerate(url_variations):
        print(f"🔄 策略 {i+1}: 嘗試 URL 格式 {test_url}")
        
        # 嘗試使用 yt-dlp 下載
        success = download_video_with_ytdlp(test_url, video_id)
        if success:
            return True
    
    # 策略 2: 使用 curl 獲取頁面內容，然後分析
    print("🔄 策略 4: 使用 curl 分析頁面")
    try:
        import subprocess
        
        # 使用 curl 獲取頁面內容
        curl_command = f'curl -s -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" -H "Accept: */*" -H "Referer: https://www.threads.com/" -H "Origin: https://www.threads.com" "{url}"'
        
        result = subprocess.run(
            curl_command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout:
            print("✅ 成功獲取頁面內容")
            
            # 分析頁面內容，尋找影片 URL
            import re
            video_patterns = [
                r'https?://[^"\s]+\.mp4[^"\s]*',
                r'https?://[^"\s]+\.mov[^"\s]*',
                r'https?://[^"\s]+\.webm[^"\s]*',
                r'https?://[^"\s]+video[^"\s]*',
                r'https?://[^"\s]+media[^"\s]*'
            ]
            
            for pattern in video_patterns:
                matches = re.findall(pattern, result.stdout)
                if matches:
                    print(f"🔍 找到匹配的 URL 模式: {pattern}")
                    for match in matches:
                        print(f"  匹配: {match}")
                        
                        # 嘗試下載
                        success = download_video_with_ytdlp(match, video_id)
                        if success:
                            return True
        else:
            print(f"❌ curl 失敗: {result.stderr}")
            
    except Exception as e:
        print(f"❌ curl 策略出錯: {e}")
    
    # 策略 3: 最後嘗試使用 Python 腳本再次運行（無頭模式）
    print("🔄 策略 5: 最後嘗試無頭模式")
    try:
        driver = setup_chrome_driver()
        if driver:
            driver.get(url)
            time.sleep(3)
            
            # 快速檢查頁面
            page_source = driver.page_source
            
            # 查找影片 URL
            import re
            video_patterns = [
                r'https?://[^"\s]+\.mp4[^"\s]*',
                r'https?://[^"\s]+\.mov[^"\s]*',
                r'https?://[^"\s]+\.webm[^"\s]*',
            ]
            
            for pattern in video_patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    for match in matches:
                        success = download_video_with_ytdlp(match, video_id)
                        if success:
                            driver.quit()
                            return True
            
            driver.quit()
    except Exception as e:
        print(f"❌ 無頭模式出錯: {e}")
    
    print("❌ 所有備用策略都失敗了")
    return False

def download_video_with_ytdlp(url, video_id):
    """使用 yt-dlp 下載影片"""
    print(f"📥 嘗試下載: {url}")
    
    # 使用容器內的影片目錄
    output_file = f"/data/video/{video_id}.mp4"
    
    # 根據 URL 類型選擇不同的下載策略
    if 'instagram.fkhh6-1.fna.fbcdn.net' in url:
        # Instagram CDN URL，使用 curl 直接下載
        print("🔄 檢測到 Instagram CDN URL，使用 curl 直接下載")
        return download_with_curl(url, video_id, output_file)
    else:
        # 通用下載指令
        command = f'yt-dlp -f "best" --merge-output-format mp4 -o "{output_file}" "{url}"'
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=120
            )
            
            if result.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"✅ 下載成功: {output_file}")
                print(f"📁 檔案大小: {os.path.getsize(output_file)} bytes")
                return True
            else:
                print(f"❌ 下載失敗: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 下載出錯: {e}")
            return False

def download_with_curl(url, video_id, output_file):
    """使用 curl 下載影片"""
    print(f"🔄 使用 curl 下載: {url}")
    
    # 嘗試多種 curl 策略
    curl_strategies = [
        # 策略 1: 基本標頭，允許重定向（簡化版本）
        f'curl -s -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" -H "Referer:https://www.threads.com/" -H "Origin:https://www.threads.com" -H "Accept:*/*" -o "{output_file}" "{url}"',
        
        # 策略 2: 更完整的標頭（簡化版本）
        f'curl -s -L -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" -H "Referer:https://www.threads.com/" -H "Origin:https://www.threads.com" -H "Accept:video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5" -H "Accept-Language:en-US,en;q=0.9" -o "{output_file}" "{url}"',
        
        # 策略 3: 使用 wget 作為備用
        f'wget --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" --header="Referer: https://www.threads.com" --header="Origin: https://www.threads.com" -O "{output_file}" "{url}"',
        
        # 策略 4: 使用 Python urllib（內建庫）
        f'python3 -c "import urllib.request; import urllib.parse; opener = urllib.request.build_opener(); opener.addheaders = [(\'User-Agent\', \'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\'), (\'Referer\', \'https://www.threads.com/\'), (\'Origin\', \'https://www.threads.com\')]; urllib.request.install_opener(opener); urllib.request.urlretrieve(\'{url}\', \'{output_file}\')"'
    ]
    
    for i, strategy in enumerate(curl_strategies):
        print(f"🔄 嘗試策略 {i+1}...")
        
        try:
            if 'python3' in strategy:
                # Python 策略
                result = subprocess.run(
                    strategy, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=300
                )
            else:
                # curl/wget 策略
                result = subprocess.run(
                    strategy, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=300
                )
            
            if result.returncode == 0 and os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"✅ 策略 {i+1} 下載成功: {file_size} bytes")
                
                # 檢查檔案是否為有效的影片檔案
                if file_size > 10000:  # 至少 10KB
                    return True
                elif file_size > 100:  # 檢查檔案內容
                    try:
                        with open(output_file, 'rb') as f:
                            header = f.read(12)
                            # 檢查是否為 MP4 檔案頭
                            if header.startswith(b'ftyp'):
                                print(f"✅ 策略 {i+1} 檢測到有效的 MP4 檔案頭")
                                return True
                            else:
                                print(f"⚠️  策略 {i+1} 檔案頭不是 MP4 格式")
                                os.remove(output_file)
                                continue
                    except Exception as e:
                        print(f"⚠️  策略 {i+1} 檢查檔案頭時出錯: {e}")
                        os.remove(output_file)
                        continue
                else:
                    print(f"⚠️  策略 {i+1} 檔案太小: {file_size} bytes")
                    os.remove(output_file)
                    continue
            else:
                print(f"❌ 策略 {i+1} 失敗: {result.stderr}")
                if result.stdout:
                    print(f"  輸出: {result.stdout[:200]}...")
                
        except Exception as e:
            print(f"❌ 策略 {i+1} 出錯: {e}")
            continue
    
    print("❌ 所有 curl 策略都失敗了")
    return False

def main():
    """主函數"""
    if len(sys.argv) < 3:
        print("❌ 使用方法: python3 download_threads.py <URL> <VIDEO_ID> [--retry]")
        sys.exit(1)
    
    url = sys.argv[1]
    video_id = sys.argv[2]
    is_retry = len(sys.argv) > 3 and sys.argv[3] == "--retry"
    
    print("🚀 Threads 下載腳本啟動")
    print("=" * 60)
    print(f"🎯 URL: {url}")
    print(f"🆔 影片 ID: {video_id}")
    if is_retry:
        print("🔄 重試模式：使用備用策略")
    print("=" * 60)
    
    # 開始下載
    success = download_threads_video(url, video_id, is_retry)
    
    if success:
        print("\n🎉 下載成功！")
        sys.exit(0)
    else:
        print("\n❌ 下載失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()

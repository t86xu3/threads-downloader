#!/bin/bash
# 本地開發啟動腳本

echo "🚀 啟動多平台影片下載器開發環境"
echo "================================"

# 檢查 Python 虛擬環境
if [ ! -d "backend/venv" ]; then
    echo "📦 建立 Python 虛擬環境..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo "✅ Python 虛擬環境已存在"
fi

# 檢查 Node modules
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 安裝前端依賴..."
    cd frontend
    npm install
    cd ..
else
    echo "✅ 前端依賴已安裝"
fi

echo ""
echo "================================"
echo "啟動服務（請在兩個終端分別執行）："
echo ""
echo "📡 後端："
echo "   cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000"
echo ""
echo "🎨 前端："
echo "   cd frontend && npm run dev"
echo ""
echo "================================"
echo "開啟 http://localhost:3000 使用應用"

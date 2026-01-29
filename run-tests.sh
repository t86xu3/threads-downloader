#!/bin/bash
# 自動化測試執行腳本

set -e

echo "=========================================="
echo "  多平台影片下載器 - 自動化測試"
echo "=========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 計數器
TOTAL_PASSED=0
TOTAL_FAILED=0

cd "$(dirname "$0")"

# 1. 後端測試
echo -e "${YELLOW}[1/3] 執行後端測試 (pytest)${NC}"
echo "----------------------------------------"
cd backend
source venv/bin/activate
if python -m pytest tests/ -v --tb=short; then
    echo -e "${GREEN}✅ 後端測試通過${NC}"
    TOTAL_PASSED=$((TOTAL_PASSED + 1))
else
    echo -e "${RED}❌ 後端測試失敗${NC}"
    TOTAL_FAILED=$((TOTAL_FAILED + 1))
fi
cd ..
echo ""

# 2. 前端單元測試
echo -e "${YELLOW}[2/3] 執行前端單元測試 (Jest)${NC}"
echo "----------------------------------------"
cd frontend
if npm test; then
    echo -e "${GREEN}✅ 前端單元測試通過${NC}"
    TOTAL_PASSED=$((TOTAL_PASSED + 1))
else
    echo -e "${RED}❌ 前端單元測試失敗${NC}"
    TOTAL_FAILED=$((TOTAL_FAILED + 1))
fi
cd ..
echo ""

# 3. 端對端測試 (可選)
if [ "$1" == "--e2e" ]; then
    echo -e "${YELLOW}[3/3] 執行端對端測試 (Playwright)${NC}"
    echo "----------------------------------------"

    # 啟動後端
    cd backend
    source venv/bin/activate
    uvicorn app.main:app --port 7988 &
    BACKEND_PID=$!
    cd ..

    # 啟動前端
    cd frontend
    npm run dev -- --port 3001 &
    FRONTEND_PID=$!

    # 等待服務啟動
    echo "等待服務啟動..."
    sleep 10

    # 執行 E2E 測試
    if npx playwright test --project=chromium; then
        echo -e "${GREEN}✅ 端對端測試通過${NC}"
        TOTAL_PASSED=$((TOTAL_PASSED + 1))
    else
        echo -e "${RED}❌ 端對端測試失敗${NC}"
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi

    # 清理
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    cd ..
else
    echo -e "${YELLOW}[3/3] 跳過端對端測試 (加 --e2e 參數執行)${NC}"
fi

echo ""
echo "=========================================="
echo "  測試結果摘要"
echo "=========================================="
echo -e "通過: ${GREEN}${TOTAL_PASSED}${NC}"
echo -e "失敗: ${RED}${TOTAL_FAILED}${NC}"
echo ""

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有測試通過！${NC}"
    exit 0
else
    echo -e "${RED}❌ 有測試失敗${NC}"
    exit 1
fi

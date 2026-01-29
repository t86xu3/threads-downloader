import { test, expect } from '@playwright/test';

test.describe('首頁功能測試', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('應顯示標題和輸入框', async ({ page }) => {
    // 檢查標題
    await expect(page.locator('h1')).toContainText('影片下載器');

    // 檢查輸入框
    const input = page.locator('input[type="url"]');
    await expect(input).toBeVisible();
    await expect(input).toHaveAttribute('placeholder', '貼上影片網址...');

    // 檢查下載按鈕
    const button = page.locator('button:has-text("下載影片")');
    await expect(button).toBeVisible();
  });

  test('應顯示支援的平台', async ({ page }) => {
    await expect(page.locator('text=Threads')).toBeVisible();
    await expect(page.locator('text=小紅書')).toBeVisible();
    await expect(page.locator('text=抖音')).toBeVisible();
  });

  test('空輸入時下載按鈕應該被禁用', async ({ page }) => {
    const button = page.locator('button:has-text("下載影片")');
    await expect(button).toBeDisabled();
  });

  test('輸入 URL 後下載按鈕應該啟用', async ({ page }) => {
    const input = page.locator('input[type="url"]');
    await input.fill('https://www.threads.net/@user/post/123');

    const button = page.locator('button:has-text("下載影片")');
    await expect(button).toBeEnabled();
  });

  test('應該自動識別 Threads URL', async ({ page }) => {
    const input = page.locator('input[type="url"]');
    await input.fill('https://www.threads.net/@user/post/123');

    await expect(page.locator('text=偵測到 Threads 影片')).toBeVisible();
  });

  test('應該自動識別小紅書 URL', async ({ page }) => {
    const input = page.locator('input[type="url"]');
    await input.fill('https://www.xiaohongshu.com/explore/123');

    await expect(page.locator('text=偵測到 小紅書 影片')).toBeVisible();
  });

  test('應該自動識別抖音 URL', async ({ page }) => {
    const input = page.locator('input[type="url"]');
    await input.fill('https://www.douyin.com/video/123');

    await expect(page.locator('text=偵測到 抖音 影片')).toBeVisible();
  });
});

test.describe('錯誤處理測試', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('無效 URL 應顯示錯誤訊息', async ({ page }) => {
    const input = page.locator('input[type="url"]');
    await input.fill('https://www.youtube.com/watch?v=123');

    const button = page.locator('button:has-text("下載影片")');
    await button.click();

    // 應該顯示錯誤訊息
    await expect(page.locator('text=不支援')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('響應式設計測試', () => {
  test('行動版應正確顯示', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // 檢查主要元素是否可見
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('input[type="url"]')).toBeVisible();
    await expect(page.locator('button:has-text("下載影片")')).toBeVisible();
  });

  test('桌面版應正確顯示', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');

    // 檢查主要元素是否可見
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('input[type="url"]')).toBeVisible();
    await expect(page.locator('button:has-text("下載影片")')).toBeVisible();
  });
});

test.describe('API 整合測試', () => {
  test('提交下載應顯示處理中狀態', async ({ page }) => {
    await page.goto('/');

    const input = page.locator('input[type="url"]');
    await input.fill('https://www.threads.net/@user/post/123');

    const button = page.locator('button:has-text("下載影片")');
    await button.click();

    // 應該顯示提交中或處理中狀態
    await expect(
      page.locator('text=提交中').or(page.locator('text=正在處理'))
    ).toBeVisible({ timeout: 10000 });
  });
});

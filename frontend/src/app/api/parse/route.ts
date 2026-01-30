import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:7988';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { url, platform } = body;

    if (!url) {
      return NextResponse.json(
        { error: '請提供網址' },
        { status: 400 }
      );
    }

    // 轉發到後端
    const response = await fetch(`${BACKEND_URL}/api/parse`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url, platform }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || '解析失敗' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Parse API error:', error);
    return NextResponse.json(
      { error: '服務暫時不可用，請稍後再試' },
      { status: 503 }
    );
  }
}

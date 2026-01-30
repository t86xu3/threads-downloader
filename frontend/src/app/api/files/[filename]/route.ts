import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:7988';

export async function GET(
  request: NextRequest,
  { params }: { params: { filename: string } }
) {
  try {
    const filename = params.filename;

    // 轉發到後端獲取檔案
    const response = await fetch(`${BACKEND_URL}/api/files/${filename}`, {
      method: 'GET',
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: '檔案不存在' },
        { status: response.status }
      );
    }

    const contentType = response.headers.get('content-type') || 'application/octet-stream';
    const buffer = await response.arrayBuffer();

    return new NextResponse(buffer, {
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': `attachment; filename="${filename}"`,
        'Cache-Control': 'public, max-age=3600',
      },
    });
  } catch (error) {
    console.error('Files API error:', error);
    return NextResponse.json(
      { error: '服務暫時不可用' },
      { status: 503 }
    );
  }
}

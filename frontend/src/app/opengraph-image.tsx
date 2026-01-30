import { ImageResponse } from "next/og";

export const runtime = "edge";

export const alt = "Threads 影片下載器";
export const size = {
  width: 1200,
  height: 630,
};
export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#1a1a2e",
          backgroundImage:
            "linear-gradient(to bottom right, #1a1a2e, #16213e)",
        }}
      >
        {/* Icon */}
        <div
          style={{
            fontSize: 120,
            marginBottom: 20,
          }}
        >
          🎬
        </div>

        {/* Title */}
        <div
          style={{
            fontSize: 60,
            fontWeight: "bold",
            color: "white",
            marginBottom: 20,
            textAlign: "center",
          }}
        >
          影片下載器
        </div>

        {/* Subtitle */}
        <div
          style={{
            fontSize: 32,
            color: "#9ca3af",
            textAlign: "center",
          }}
        >
          免費下載 Threads・小紅書・抖音 影片
        </div>

        {/* Features */}
        <div
          style={{
            display: "flex",
            gap: 40,
            marginTop: 40,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              color: "#60a5fa",
              fontSize: 24,
            }}
          >
            ✓ 免費使用
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              color: "#60a5fa",
              fontSize: 24,
            }}
          >
            ✓ 無需安裝
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              color: "#60a5fa",
              fontSize: 24,
            }}
          >
            ✓ 支援手機
          </div>
        </div>
      </div>
    ),
    {
      ...size,
    }
  );
}

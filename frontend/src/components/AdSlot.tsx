"use client";

import { useEffect, useRef } from "react";

interface AdSlotProps {
  slot: string; // AdSense 廣告單元 ID
  format?: "auto" | "rectangle" | "horizontal" | "vertical";
  responsive?: boolean;
  className?: string;
}

declare global {
  interface Window {
    adsbygoogle: unknown[];
  }
}

export default function AdSlot({
  slot,
  format = "auto",
  responsive = true,
  className = "",
}: AdSlotProps) {
  const adRef = useRef<HTMLDivElement>(null);
  const isAdLoaded = useRef(false);

  useEffect(() => {
    // 只在客戶端執行，且只載入一次
    if (typeof window === "undefined" || isAdLoaded.current) return;

    try {
      // 如果 AdSense 腳本已載入，推送廣告
      if (window.adsbygoogle) {
        window.adsbygoogle.push({});
        isAdLoaded.current = true;
      }
    } catch (err) {
      console.error("AdSense error:", err);
    }
  }, []);

  // 開發環境顯示佔位符
  if (process.env.NODE_ENV === "development") {
    return (
      <div
        className={`bg-gray-800/50 border border-gray-700/50 rounded-2xl p-6 text-center ${className}`}
      >
        <p className="text-gray-500 text-sm">廣告位 ({slot || "預覽"})</p>
      </div>
    );
  }

  return (
    <div ref={adRef} className={className}>
      <ins
        className="adsbygoogle"
        style={{ display: "block" }}
        data-ad-client={process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID}
        data-ad-slot={slot}
        data-ad-format={format}
        data-full-width-responsive={responsive ? "true" : "false"}
      />
    </div>
  );
}

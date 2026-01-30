import type { Metadata, Viewport } from "next";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://threads-downloader.vercel.app";

export const metadata: Metadata = {
  title: {
    default: "Threads 影片下載器 - 免費下載 Threads、小紅書、抖音影片",
    template: "%s | Threads 影片下載器",
  },
  description:
    "免費線上 Threads 影片下載工具，支援下載 Threads、小紅書、抖音影片和圖片。無需安裝，貼上網址即可下載，支援手機與電腦。",
  keywords: [
    "Threads 下載",
    "Threads 影片下載",
    "Threads 下載器",
    "threads video download",
    "小紅書下載",
    "小紅書影片下載",
    "抖音下載",
    "抖音影片下載",
    "TikTok 下載",
    "社群媒體下載器",
  ],
  authors: [{ name: "Threads Downloader" }],
  creator: "Threads Downloader",
  metadataBase: new URL(siteUrl),
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    locale: "zh_TW",
    url: siteUrl,
    siteName: "Threads 影片下載器",
    title: "Threads 影片下載器 - 免費下載 Threads、小紅書、抖音影片",
    description:
      "免費線上影片下載工具，支援 Threads、小紅書、抖音。貼上網址即可下載，無需安裝。",
    images: ["/opengraph-image"],
  },
  twitter: {
    card: "summary_large_image",
    title: "Threads 影片下載器 - 免費下載影片",
    description: "免費線上影片下載工具，支援 Threads、小紅書、抖音",
    images: ["/opengraph-image"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  verification: {
    // google: "your-google-verification-code",  // 之後加入 Google Search Console 驗證碼
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#1a1a2e",
};

// JSON-LD 結構化數據
const jsonLd = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  name: "Threads 影片下載器",
  description:
    "免費線上 Threads 影片下載工具，支援下載 Threads、小紅書、抖音影片和圖片",
  url: siteUrl,
  applicationCategory: "MultimediaApplication",
  operatingSystem: "Any",
  offers: {
    "@type": "Offer",
    price: "0",
    priceCurrency: "TWD",
  },
  featureList: [
    "下載 Threads 影片和圖片",
    "下載小紅書影片",
    "下載抖音/TikTok 影片",
    "支援批量選擇下載",
    "免費使用",
    "無需安裝",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-TW">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        {/* Google AdSense - 申請通過後取消註解並填入 client ID */}
        {process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID && (
          <script
            async
            src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID}`}
            crossOrigin="anonymous"
          />
        )}
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}

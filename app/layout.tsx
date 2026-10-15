import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "香迹 · 香方复原实验室",
  description: "查阅古代香方，补全残缺配料，保存复原记录。",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}

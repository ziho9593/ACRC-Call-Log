import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "ACRC-Call-Log",
  description: "사내 통화 녹취 분석 PoC"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}


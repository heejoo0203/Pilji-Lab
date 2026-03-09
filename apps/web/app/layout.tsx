import type { Metadata } from "next";
import { Manrope, Noto_Sans_KR } from "next/font/google";
import "./globals.css";
import "./brand-refresh.css";
import { AuthProvider } from "@/app/components/auth-provider";
import { AuthModal } from "@/app/components/auth-modal";

const bodyFont = Noto_Sans_KR({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "700", "800"],
  display: "swap",
});

const displayFont = Manrope({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["600", "700", "800"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "필지랩",
  description: "필지 경계 기반 개별공시지가 조회·구역 분석 플랫폼",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className={`${bodyFont.variable} ${displayFont.variable}`}>
        <AuthProvider>
          {children}
          <AuthModal />
        </AuthProvider>
      </body>
    </html>
  );
}

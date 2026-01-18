import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { FinancialProvider } from '@/context/FinancialContext';
import { ChatProvider } from '@/context/ChatContext';

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "MindMoney",
  description: "AI Financial Architect",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-slate-50`}>
        <FinancialProvider>
          <ChatProvider>
            {children}
          </ChatProvider>
        </FinancialProvider>
      </body>
    </html>
  );
}
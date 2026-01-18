import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { FinancialProvider } from '@/context/FinancialContext';
import { ChatProvider } from '@/context/ChatContext';
import { AuthProvider } from '@/contexts/AuthContext';

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
      <body className={`${inter.className} bg-[var(--background)] text-[var(--text-primary)] antialiased`}>
        <AuthProvider>
          <FinancialProvider>
            <ChatProvider>
              {children}
            </ChatProvider>
          </FinancialProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css"; // <--- CRITICAL: This restores Tailwind!
import { FinancialProvider } from '@/context/FinancialContext';

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
      <body className={inter.className}>
        <FinancialProvider>
          {children}
        </FinancialProvider>
      </body>
    </html>
  );
}
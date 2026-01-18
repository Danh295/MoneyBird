import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { FinancialProvider } from '@/context/FinancialContext';
import { ChatProvider } from '@/context/ChatContext'; // <--- NEW IMPORT
import Link from "next/link";
import { MessageSquare, LayoutDashboard } from "lucide-react";

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
          <ChatProvider> {/* <--- WRAP APP IN CHAT PROVIDER */}
            
            {/* GLOBAL NAVIGATION BAR */}
            <nav className="fixed top-4 left-1/2 -translate-x-1/2 z-50 bg-slate-900/90 backdrop-blur-md text-white px-6 py-3 rounded-full shadow-2xl flex items-center gap-8 border border-slate-700/50 transition-all hover:scale-105">
              <Link href="/" className="flex items-center gap-2 hover:text-teal-400 transition-colors">
                <MessageSquare size={18} />
                <span className="text-sm font-medium">Assistant</span>
              </Link>
              <div className="w-px h-4 bg-slate-700"></div>
              <Link href="/dashboard" className="flex items-center gap-2 hover:text-teal-400 transition-colors">
                <LayoutDashboard size={18} />
                <span className="text-sm font-medium">Dashboard</span>
              </Link>
            </nav>

            {/* Main Content Area */}
            <div className="pt-0 min-h-screen">
              {children}
            </div>

          </ChatProvider>
        </FinancialProvider>
      </body>
    </html>
  );
}
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ReactNode } from "react";
import Navbar from "./components/Navbar";
import FloatingChatButton from "./components/FloatingChatButton";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "evoToDo - Evolve Your Productivity",
  description: "A secure, beautiful, and intuitive todo application to help you manage your daily tasks efficiently.",
  keywords: ["todo", "productivity", "task manager", "evoToDo"],
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} custom-scrollbar`}>
        <div className="min-h-screen bg-background">
          <Navbar />
          {children}
          <FloatingChatButton />
        </div>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '16px',
              boxShadow: '0 10px 40px rgba(0, 0, 0, 0.1)',
            },
          }}
        />
      </body>
    </html>
  );
}

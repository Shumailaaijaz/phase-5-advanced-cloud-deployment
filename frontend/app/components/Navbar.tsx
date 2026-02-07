"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { LogOut, Sparkles } from "lucide-react";

export default function Navbar() {
  const router = useRouter();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  const checkAuth = () => {
    const token = localStorage.getItem("token");
    setIsLoggedIn(!!token);
  };

  useEffect(() => {
    checkAuth();
    window.addEventListener("storage", checkAuth);
    const interval = setInterval(checkAuth, 1000);

    // Scroll effect for navbar
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener("scroll", handleScroll);

    return () => {
      window.removeEventListener("storage", checkAuth);
      window.removeEventListener("scroll", handleScroll);
      clearInterval(interval);
    };
  }, []);

  const handleLogout = () => {
    localStorage.clear();
    setIsLoggedIn(false);
    router.push("/login");
    router.refresh();
  };

  return (
    <nav className={`fixed top-0 left-0 right-0 h-18 z-50 transition-all duration-300 ${
      scrolled
        ? "bg-white/95 backdrop-blur-md shadow-lg border-b border-gray-100"
        : "bg-white/80 backdrop-blur-sm"
    }`}>
      <div className="container mx-auto px-4 max-w-6xl flex items-center justify-between h-full py-2">
        <Link href="/" className="flex items-center group">
          {/* Enhanced Logo with visibility improvements */}
          <div className="relative flex items-center">
            <div className="relative w-[180px] h-[50px] drop-shadow-lg group-hover:drop-shadow-xl transition-all duration-300">
              <Image
                src="/logoh2p2.jpeg"
                alt="evoToDo Logo"
                fill
                className="object-contain rounded-lg brightness-105 contrast-105"
                priority
              />
            </div>
            {/* Glow effect on hover */}
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/0 via-indigo-500/10 to-green-500/0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 blur-xl" />
          </div>
        </Link>

        <div className="flex items-center gap-3">
          {isLoggedIn ? (
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 bg-gradient-to-r from-red-50 to-pink-50 text-red-600 px-5 py-2.5 rounded-2xl font-semibold hover:from-red-100 hover:to-pink-100 transition-all duration-300 border border-red-100 shadow-sm hover:shadow-md active:scale-95"
            >
              <LogOut size={18} /> Logout
            </button>
          ) : (
            <Link
              href="/login"
              className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-2.5 rounded-2xl font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all duration-300 shadow-lg shadow-indigo-200 hover:shadow-xl hover:shadow-indigo-300 active:scale-95"
            >
              <Sparkles size={16} /> Get Started
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
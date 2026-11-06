"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { LogIn, LogOut, LayoutDashboard, Crown, Volume2, ShieldCheck } from "lucide-react";

export default function Navbar() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/auth/me")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.authenticated) {
          setUser(data.user);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    window.location.href = "/";
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0B0D13]/80 backdrop-blur-md border-b border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo & Name */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative w-10 h-10 rounded-xl overflow-hidden ring-2 ring-discord-blurple/30 group-hover:ring-discord-blurple transition">
            <Image
              src="/logo.jpg"
              alt="Dissound Logo"
              width={40}
              height={40}
              className="object-cover"
              priority
            />
          </div>
          <div className="flex flex-col">
            <span className="font-extrabold tracking-tight text-lg text-white group-hover:text-discord-blurple transition flex items-center gap-1.5">
              DISSOUND
              <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-discord-blurple/20 text-discord-blurple border border-discord-blurple/30">
                Bot & Web
              </span>
            </span>
          </div>
        </Link>

        {/* Navigation Links */}
        <div className="hidden md:flex items-center gap-6 text-sm font-medium text-gray-300">
          <Link href="/#sounds" className="hover:text-white transition flex items-center gap-1.5">
            <Volume2 className="w-4 h-4 text-discord-blurple" />
            Sound Catalog
          </Link>
          <Link href="/dashboard" className="hover:text-white transition flex items-center gap-1.5">
            <LayoutDashboard className="w-4 h-4 text-cyan-400" />
            Web Dashboard
          </Link>
          <Link href="/pricing" className="hover:text-white transition flex items-center gap-1.5 text-amber-300">
            <Crown className="w-4 h-4 text-amber-400" />
            Dissound Pro (Paywall)
          </Link>
        </div>

        {/* Auth / Profile Area */}
        <div className="flex items-center gap-3">
          {loading ? (
            <div className="w-8 h-8 rounded-full bg-white/5 animate-pulse" />
          ) : user ? (
            <div className="flex items-center gap-3">
              <Link
                href="/dashboard"
                className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition"
              >
                {user.avatar ? (
                  <img src={user.avatar} alt={user.username} className="w-7 h-7 rounded-full" />
                ) : (
                  <div className="w-7 h-7 rounded-full bg-discord-blurple flex items-center justify-center font-bold text-xs">
                    {user.username.slice(0, 2).toUpperCase()}
                  </div>
                )}
                <div className="text-left hidden sm:block">
                  <div className="text-xs font-semibold text-white flex items-center gap-1">
                    {user.username}
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  </div>
                  <div className="text-[10px] text-gray-400">OTP Verified</div>
                </div>
              </Link>
              <button
                onClick={handleLogout}
                title="Log Out"
                className="p-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <a
                href="/api/auth/discord?demo=true"
                className="hidden sm:inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-white px-2.5 py-1.5 rounded-lg border border-white/10 hover:border-white/20 transition"
                title="Log in instantly using Demo Mode without configuring Discord Portal"
              >
                ⚡ Quick Demo Login
              </a>
              <a
                href="/api/auth/discord"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-discord-blurple hover:bg-discord-blurple/90 text-white font-semibold text-sm shadow-lg shadow-discord-blurple/25 transition active:scale-95"
              >
                <LogIn className="w-4 h-4" />
                Login with Discord
              </a>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}

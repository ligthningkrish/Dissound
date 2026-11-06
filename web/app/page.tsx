"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Volume2,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Zap,
  Sliders,
  Crown,
  Play,
  Pause,
  UploadCloud,
  CheckCircle2,
  Lock,
} from "lucide-react";
import SoundCard from "@/components/SoundCard";
import PaywallModal from "@/components/PaywallModal";
import { SoundItem } from "@/app/api/sounds/route";

export default function HomePage() {
  const [sounds, setSounds] = useState<SoundItem[]>([]);
  const [activeCategory, setActiveCategory] = useState("All");
  const [categories, setCategories] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [paywallOpen, setPaywallOpen] = useState(false);
  const [selectedProFeature, setSelectedProFeature] = useState({ name: "", desc: "" });

  useEffect(() => {
    fetch("/api/sounds")
      .then((r) => r.json())
      .then((data) => {
        setSounds(data.sounds || []);
        setCategories(data.categories || []);
      })
      .catch(() => {});
  }, []);

  const openPaywall = (name: string, desc: string) => {
    setSelectedProFeature({ name, desc });
    setPaywallOpen(true);
  };

  const filteredSounds = sounds.filter((s) => {
    const matchesCat = activeCategory === "All" || s.category.toLowerCase() === activeCategory.toLowerCase();
    const matchesSearch =
      !searchQuery ||
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCat && matchesSearch;
  });

  return (
    <div className="min-h-screen">
      {/* HERO SECTION */}
      <section className="relative pt-12 pb-20 md:pt-20 md:pb-32 overflow-hidden">
        {/* Glow Effects */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-discord-blurple/15 rounded-full blur-[140px] pointer-events-none" />
        <div className="absolute top-1/3 right-10 w-[350px] h-[350px] bg-purple-600/15 rounded-full blur-[120px] pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          {/* Top Pill */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-semibold text-gray-300 mb-8 backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Discord Soundboard Bot + Web Dashboard</span>
            <span className="text-gray-500">•</span>
            <span className="text-discord-blurple font-bold">OAuth + Mail OTP</span>
          </div>

          {/* Logo & Headline */}
          <div className="flex flex-col items-center">
            <div className="relative w-28 h-28 sm:w-36 sm:h-36 mb-6 rounded-3xl overflow-hidden ring-4 ring-discord-blurple/30 shadow-2xl shadow-discord-blurple/30 hover:scale-105 transition-transform duration-300">
              <Image src="/logo.jpg" alt="Dissound Logo" fill className="object-cover" priority />
            </div>

            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black text-white tracking-tight max-w-4xl leading-[1.1]">
              Level Up Your Discord <br />
              <span className="bg-gradient-to-r from-discord-blurple via-purple-400 to-cyan-400 bg-clip-text text-transparent">
                Soundboard Instantly
              </span>
            </h1>

            <p className="mt-6 text-lg sm:text-xl text-gray-400 max-w-2xl leading-relaxed">
              No more searching sketchy sites, downloading files, or wrestling with audio converters.
              Search, preview, and upload meme sounds directly into your server soundboard.
            </p>
          </div>

          {/* Action CTAs */}
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="/api/auth/discord"
              className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-discord-blurple hover:bg-discord-blurple/90 text-white font-bold text-base shadow-xl shadow-discord-blurple/30 flex items-center justify-center gap-3 transition active:scale-95"
            >
              <span>Login via Discord (with Mail OTP)</span>
              <ArrowRight className="w-5 h-5" />
            </a>
            <a
              href="/api/auth/discord?demo=true"
              className="w-full sm:w-auto px-6 py-4 rounded-2xl bg-white/5 hover:bg-white/10 text-gray-200 font-semibold text-base border border-white/10 transition flex items-center justify-center gap-2"
            >
              <Zap className="w-5 h-5 text-amber-400" />
              <span>Instant Demo Login</span>
            </a>
          </div>

          <div className="mt-6 flex items-center justify-center gap-6 text-xs text-gray-500">
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Two-Factor Mail OTP Verification</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Sliders className="w-4 h-4 text-discord-blurple" />
              <span>Auto-Trims to &le; 5.2s</span>
            </div>
          </div>
        </div>
      </section>

      {/* INTERACTIVE SOUND CATALOG SAMPLER */}
      <section id="sounds" className="py-16 bg-[#0E1118]/80 border-t border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-4 mb-8">
            <div>
              <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-discord-blurple mb-2">
                <Volume2 className="w-4 h-4" />
                Live Soundboard Sampler
              </div>
              <h2 className="text-3xl font-extrabold text-white">Click Any Sound to Listen</h2>
              <p className="text-sm text-gray-400 mt-1">
                Listen in your browser, or install directly into your server soundboard.
              </p>
            </div>

            {/* Search Input */}
            <div className="w-full md:w-72">
              <input
                type="text"
                placeholder="Search meme sounds..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 text-sm focus:border-discord-blurple focus:outline-none transition"
              />
            </div>
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-4 mb-6 text-sm no-scrollbar">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`px-4 py-1.5 rounded-xl whitespace-nowrap font-medium text-xs transition ${
                  activeCategory === cat
                    ? "bg-discord-blurple text-white shadow-md shadow-discord-blurple/30 font-semibold"
                    : "bg-white/5 text-gray-400 hover:text-white hover:bg-white/10"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Sound Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredSounds.map((sound) => (
              <SoundCard key={sound.id} sound={sound} onOpenPaywall={openPaywall} />
            ))}
          </div>
        </div>
      </section>

      {/* THREE PILLAR FEATURES */}
      <section className="py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Built for Discord Communities & Creators
          </h2>
          <p className="mt-4 text-base text-gray-400">
            Everything you need to discover, sanitize, and manage sound effects across all your servers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Card 1 */}
          <div className="rounded-3xl bg-[#141721] border border-white/5 p-8 flex flex-col justify-between hover:border-discord-blurple/30 transition shadow-xl">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-discord-blurple/20 text-discord-blurple flex items-center justify-center mb-6">
                <Sliders className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">Automatic Audio Processing</h3>
              <p className="text-sm text-gray-400 leading-relaxed">
                Discord enforces strict limits: max 5.2 seconds, under 512 KB, and MP3/OGG format. Dissound automatically trims, normalizes loudness, and optimizes every file.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-white/5 text-xs text-discord-blurple font-semibold">
              &le; 5.2s • &le; 512 KB • Loudnorm Filter
            </div>
          </div>

          {/* Card 2 */}
          <div className="rounded-3xl bg-[#141721] border border-white/5 p-8 flex flex-col justify-between hover:border-emerald-500/30 transition shadow-xl">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center mb-6">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">Two-Factor Mail OTP Verification</h3>
              <p className="text-sm text-gray-400 leading-relaxed">
                Security made simple. Users authenticate with Discord OAuth, then receive a single-use 6-digit verification code to their registered Discord email to guard administrative soundboard permissions.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-white/5 text-xs text-emerald-400 font-semibold">
              Zero Unauthorized Uploads • High Security
            </div>
          </div>

          {/* Card 3 */}
          <div className="rounded-3xl bg-[#141721] border border-white/5 p-8 flex flex-col justify-between hover:border-amber-500/30 transition shadow-xl">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-amber-500/20 text-amber-400 flex items-center justify-center mb-6">
                <Crown className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">Paywalled Pro Tier Capabilities</h3>
              <p className="text-sm text-gray-400 leading-relaxed">
                Unlock AI Text-to-Sound effect generation, live Voice Channel Web Remote control, Multi-Server Soundboard Auto-Sync, and AI Vocal Stem isolation.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-white/5 text-xs text-amber-400 font-semibold">
              <Link href="/pricing" className="hover:underline flex items-center gap-1">
                Explore Pro Pricing <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Paywall Modal */}
      <PaywallModal
        isOpen={paywallOpen}
        onClose={() => setPaywallOpen(false)}
        featureName={selectedProFeature.name}
        featureDescription={selectedProFeature.desc}
      />
    </div>
  );
}

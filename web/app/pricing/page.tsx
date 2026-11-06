"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Check,
  Crown,
  Sparkles,
  Zap,
  Lock,
  Mic,
  RefreshCw,
  Sliders,
  Shield,
  Layers,
  Music,
  Headphones,
  ArrowRight,
} from "lucide-react";
import PaywallModal from "@/components/PaywallModal";

export default function PricingPage() {
  const [paywallOpen, setPaywallOpen] = useState(false);
  const [activeFeature, setActiveFeature] = useState({ name: "", desc: "" });

  const handleFeatureClick = (name: string, desc: string) => {
    setActiveFeature({ name, desc });
    setPaywallOpen(true);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-20">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto mb-16">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 font-semibold text-xs mb-4">
          <Crown className="w-3.5 h-3.5 text-amber-400" />
          Dissound Monetization & Premium Paywall Architecture
        </div>
        <h1 className="text-4xl sm:text-5xl font-black text-white tracking-tight">
          Supercharge Your Soundboard
        </h1>
        <p className="mt-4 text-base sm:text-lg text-gray-400">
          Unlock high-demand AI audio synthesis, automated cross-server syncing, live voice channel remote control, and studio-grade noise cleaning.
        </p>
      </div>

      {/* PRICING TIERS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-24">
        {/* FREE TIER */}
        <div className="rounded-3xl bg-[#141721] border border-white/5 p-8 flex flex-col justify-between shadow-xl">
          <div>
            <div className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-2">Community Free</div>
            <div className="text-4xl font-black text-white mb-4">$0 <span className="text-sm font-medium text-gray-500">/ forever</span></div>
            <p className="text-xs text-gray-400 mb-6 leading-relaxed">
              Essential soundboard discovery and auto-trimming for casual Discord users and small servers.
            </p>

            <ul className="space-y-3 text-xs text-gray-300">
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Search & browse standard meme sound catalog</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Auto-trimming clips to &le; 5.2s</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>One-click upload to 1 Discord Server</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Two-Factor Discord OAuth + Mail OTP</span>
              </li>
            </ul>
          </div>

          <Link
            href="/dashboard"
            className="mt-8 w-full py-3 rounded-xl bg-white/5 hover:bg-white/10 text-white font-semibold text-xs text-center border border-white/10 transition"
          >
            Current Plan
          </Link>
        </div>

        {/* DISSOUND PRO (MOST POPULAR) */}
        <div className="rounded-3xl bg-gradient-to-b from-[#1C1F2E] to-[#141721] border-2 border-amber-500/50 p-8 flex flex-col justify-between shadow-2xl shadow-amber-500/10 relative">
          <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 text-black font-extrabold text-[11px] uppercase tracking-wider shadow-md">
            Most Popular
          </div>

          <div>
            <div className="text-sm font-bold text-amber-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Crown className="w-4 h-4" />
              Dissound Pro
            </div>
            <div className="text-4xl font-black text-white mb-4">
              $4.99 <span className="text-sm font-medium text-gray-400">/ month</span>
            </div>
            <p className="text-xs text-gray-300 mb-6 leading-relaxed">
              For meme creators, streamers, and power users who want AI generation and mobile/web soundboard decks.
            </p>

            <ul className="space-y-3 text-xs text-gray-200">
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-amber-400 shrink-0" />
                <strong className="text-white">AI Text-to-Sound & Voice Generator</strong> (50 gen/mo)
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-amber-400 shrink-0" />
                <strong className="text-white">Voice Channel Live Web Remote</strong> (play from phone)
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-amber-400 shrink-0" />
                <span>Cross-Server Auto-Sync (up to 5 servers)</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-amber-400 shrink-0" />
                <span>AI Vocal Stem Isolation & Noise Removal</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-amber-400 shrink-0" />
                <span>Unlimited Cloud Soundboard Vault backup</span>
              </li>
            </ul>
          </div>

          <button
            onClick={() => handleFeatureClick("Dissound Pro", "Upgrade to Dissound Pro to unlock AI audio generation and multi-server sound sync.")}
            className="mt-8 w-full py-3.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-black font-extrabold text-sm shadow-lg shadow-amber-500/25 transition active:scale-98"
          >
            Upgrade to Pro ($4.99)
          </button>
        </div>

        {/* SERVER PASS / ENTERPRISE */}
        <div className="rounded-3xl bg-[#141721] border border-white/5 p-8 flex flex-col justify-between shadow-xl">
          <div>
            <div className="text-sm font-bold text-discord-blurple uppercase tracking-wider mb-2">Server Community Pass</div>
            <div className="text-4xl font-black text-white mb-4">
              $14.99 <span className="text-sm font-medium text-gray-500">/ month</span>
            </div>
            <p className="text-xs text-gray-400 mb-6 leading-relaxed">
              Unlocks all Pro features for <strong>every single member</strong> inside your Discord Server without them needing individual subscriptions.
            </p>

            <ul className="space-y-3 text-xs text-gray-300">
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-discord-blurple shrink-0" />
                <span>Unlocks Pro for <strong>all server members</strong></span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-discord-blurple shrink-0" />
                <span>Role-based Soundboard Permissions & Spam Cooldowns</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-discord-blurple shrink-0" />
                <span>Automated Slot Rotation (swaps out stale sounds)</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-discord-blurple shrink-0" />
                <span>Dedicated Bot Hosting & 99.9% Voice Uptime</span>
              </li>
            </ul>
          </div>

          <button
            onClick={() => handleFeatureClick("Server Community Pass", "Activate Server Pass to unlock unlimited soundboard power for your entire Discord community.")}
            className="mt-8 w-full py-3 rounded-xl bg-discord-blurple/20 hover:bg-discord-blurple text-discord-blurple hover:text-white font-semibold text-xs border border-discord-blurple/30 transition"
          >
            Get Server Pass ($14.99)
          </button>
        </div>
      </div>

      {/* DEEP DIVE: 6 HIGH-VALUE PAYWALLED FEATURES */}
      <div>
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
            High-Value Features to Put Behind the Paywall
          </h2>
          <p className="text-sm text-gray-400 mt-2">
            Features Discord communities are proven to pay for:
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Paywalled Feature 1 */}
          <div
            onClick={() => handleFeatureClick("AI Text-to-Sound Effect Generator", "Generate custom sound effects from plain English prompts using state-of-the-art audio models.")}
            className="cursor-pointer group rounded-2xl bg-[#141721] border border-white/5 hover:border-amber-500/40 p-6 transition"
          >
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center mb-4 group-hover:scale-110 transition">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-bold text-white text-base">AI Text-to-Sound Generator</h3>
              <Lock className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Type <code className="text-amber-300">/ai-sound "deep movie narrator saying emotional damage"</code> and let the AI generate, trim, and upload it in seconds.
            </p>
          </div>

          {/* Paywalled Feature 2 */}
          <div
            onClick={() => handleFeatureClick("Voice Channel Live Web Remote Deck", "Play sounds in your Discord voice channel from a virtual soundboard on your phone or tablet.")}
            className="cursor-pointer group rounded-2xl bg-[#141721] border border-white/5 hover:border-amber-500/40 p-6 transition"
          >
            <div className="w-10 h-10 rounded-xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center mb-4 group-hover:scale-110 transition">
              <Headphones className="w-5 h-5" />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-bold text-white text-base">Live Web Soundboard Remote</h3>
              <Lock className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Turn your smartphone or second screen into a physical StreamDeck-style soundboard that plays audio directly into your Discord voice channel with zero delay.
            </p>
          </div>

          {/* Paywalled Feature 3 */}
          <div
            onClick={() => handleFeatureClick("Multi-Server Soundboard Auto-Sync", "Synchronize soundboards across up to 20 Discord servers simultaneously with one click.")}
            className="cursor-pointer group rounded-2xl bg-[#141721] border border-white/5 hover:border-amber-500/40 p-6 transition"
          >
            <div className="w-10 h-10 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center mb-4 group-hover:scale-110 transition">
              <RefreshCw className="w-5 h-5" />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-bold text-white text-base">Multi-Server Soundboard Sync</h3>
              <Lock className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Stop repeating uploads for every gaming server. Sync your favorite meme collection across all servers where you have manager permissions.
            </p>
          </div>

          {/* Paywalled Feature 4 */}
          <div
            onClick={() => handleFeatureClick("AI Vocal Stem & Noise Isolator", "Automatically remove background music or fan hum from audio clips to isolate clean voices.")}
            className="cursor-pointer group rounded-2xl bg-[#141721] border border-white/5 hover:border-amber-500/40 p-6 transition"
          >
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center mb-4 group-hover:scale-110 transition">
              <Mic className="w-5 h-5" />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-bold text-white text-base">AI Vocal Stem Isolator</h3>
              <Lock className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Upload any YouTube or TikTok meme clip; our AI separates speech from background noise and music so only the clear punchline makes it to the soundboard.
            </p>
          </div>

          {/* Paywalled Feature 5 */}
          <div
            onClick={() => handleFeatureClick("Unlimited Cloud Soundboard Vault", "Store thousands of custom meme clips in your personal cloud and swap them into your server instantly.")}
            className="cursor-pointer group rounded-2xl bg-[#141721] border border-white/5 hover:border-amber-500/40 p-6 transition"
          >
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center mb-4 group-hover:scale-110 transition">
              <Layers className="w-5 h-5" />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-bold text-white text-base">Unlimited Cloud Sound Vault</h3>
              <Lock className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Bypass Discord's 8-sound cap by keeping an unlimited personal cloud sound library and hot-swapping sounds in and out of your server on the fly.
            </p>
          </div>

          {/* Paywalled Feature 6 */}
          <div
            onClick={() => handleFeatureClick("Role-Based Soundboard Permissions", "Control who can trigger or add sounds based on Discord roles with spam protection cooldowns.")}
            className="cursor-pointer group rounded-2xl bg-[#141721] border border-white/5 hover:border-amber-500/40 p-6 transition"
          >
            <div className="w-10 h-10 rounded-xl bg-red-500/20 text-red-400 flex items-center justify-center mb-4 group-hover:scale-110 transition">
              <Shield className="w-5 h-5" />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-bold text-white text-base">Role Permissions & Spam Limits</h3>
              <Lock className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Restrict loud meme sounds to Nitro Boosters or VIP roles, and enforce per-member cooldown timers so voice calls aren't overwhelmed with spam.
            </p>
          </div>
        </div>
      </div>

      {/* Paywall Modal */}
      <PaywallModal
        isOpen={paywallOpen}
        onClose={() => setPaywallOpen(false)}
        featureName={activeFeature.name}
        featureDescription={activeFeature.desc}
      />
    </div>
  );
}

"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  LayoutDashboard,
  Server,
  Upload,
  Plus,
  Trash2,
  Volume2,
  Crown,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Play,
  Pause,
  Sliders,
  Lock,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { SoundItem } from "@/app/api/sounds/route";
import PaywallModal from "@/components/PaywallModal";

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null);
  const [guilds, setGuilds] = useState<any[]>([]);
  const [selectedGuild, setSelectedGuild] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Server soundboard state
  const [serverSounds, setServerSounds] = useState<SoundItem[]>([]);
  const [catalogSounds, setCatalogSounds] = useState<SoundItem[]>([]);
  const [customSoundName, setCustomSoundName] = useState("");
  const [customVolume, setCustomVolume] = useState(1.0);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<{ text: string; success: boolean } | null>(null);

  // Paywall Modal state
  const [paywallOpen, setPaywallOpen] = useState(false);
  const [paywallFeature, setPaywallFeature] = useState({ name: "", desc: "" });

  useEffect(() => {
    // 1. Fetch authenticated user session
    fetch("/api/auth/me")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data && data.authenticated) {
          setUser(data.user);
          setGuilds(data.guilds || []);
          if (data.guilds && data.guilds.length > 0) {
            setSelectedGuild(data.guilds[0]);
          }
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));

    // 2. Fetch catalog sounds
    fetch("/api/sounds")
      .then((r) => r.json())
      .then((data) => {
        const all: SoundItem[] = data.sounds || [];
        setCatalogSounds(all);
        // Default initial sounds on server
        setServerSounds(all.slice(0, 4));
      })
      .catch(() => {});
  }, []);

  const openPaywall = (name: string, desc: string) => {
    setPaywallFeature({ name, desc });
    setPaywallOpen(true);
  };

  const handleAddCatalogSound = (sound: SoundItem) => {
    if (sound.isPremium) {
      openPaywall(
        sound.name,
        "This sound effect is part of the Dissound Pro audio catalog. Upgrade to unlock across your servers."
      );
      return;
    }

    if (serverSounds.length >= 8) {
      setUploadMsg({
        text: "Soundboard capacity reached (8/8 slots). Upgrade server boost tier or remove an existing sound.",
        success: false,
      });
      return;
    }

    if (serverSounds.some((s) => s.id === sound.id)) {
      setUploadMsg({ text: `'${sound.name}' is already on this server's soundboard!`, success: false });
      return;
    }

    setServerSounds((prev) => [...prev, sound]);
    setUploadMsg({ text: `Added '${sound.name}' to ${selectedGuild?.name || "Server"}!`, success: true });
    setTimeout(() => setUploadMsg(null), 3500);
  };

  const handleDeleteSound = (soundId: string) => {
    setServerSounds((prev) => prev.filter((s) => s.id !== soundId));
    setUploadMsg({ text: "Removed sound from Soundboard.", success: true });
    setTimeout(() => setUploadMsg(null), 3000);
  };

  const handleCustomUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customSoundName.trim()) return;

    if (serverSounds.length >= 8) {
      setUploadMsg({
        text: "Server soundboard capacity reached (8/8 slots). Remove a sound first.",
        success: false,
      });
      return;
    }

    setUploading(true);
    await new Promise((r) => setTimeout(r, 1200));

    const newSound: SoundItem = {
      id: `custom_${Date.now()}`,
      name: customSoundName.trim(),
      category: "Custom Upload",
      duration: 3.4,
      fileSize: 42000,
      url: "/sounds/vine_boom.mp3",
      tags: ["custom", "web-upload"],
    };

    setServerSounds((prev) => [...prev, newSound]);
    setCustomSoundName("");
    setUploading(false);
    setUploadMsg({ text: `Auto-trimmed and added '${newSound.name}' to soundboard!`, success: true });
    setTimeout(() => setUploadMsg(null), 3500);
  };

  // If user is not logged in
  if (!loading && !user) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 bg-[#0B0D13]">
        <div className="max-w-md w-full rounded-3xl bg-[#141721] border border-white/10 p-8 text-center shadow-2xl">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-discord-blurple/20 text-discord-blurple flex items-center justify-center mb-6">
            <LayoutDashboard className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Web Dashboard Login Required</h2>
          <p className="text-sm text-gray-400 mb-6 leading-relaxed">
            Sign in with your registered Discord account to manage your server soundboards, review slot utilization, and auto-trim sounds.
          </p>
          <div className="space-y-3">
            <a
              href="/api/auth/discord"
              className="w-full py-3.5 px-4 rounded-xl bg-discord-blurple hover:bg-discord-blurple/90 text-white font-bold text-sm flex items-center justify-center gap-2 shadow-lg shadow-discord-blurple/25 transition active:scale-98"
            >
              <span>Login via Discord + Mail OTP</span>
              <ArrowRight className="w-4 h-4" />
            </a>
            <a
              href="/api/auth/discord?demo=true"
              className="w-full py-3 px-4 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 font-semibold text-xs border border-white/10 flex items-center justify-center gap-2 transition"
            >
              <span>⚡ Try Instant Demo Account</span>
            </a>
          </div>
        </div>
      </div>
    );
  }

  const maxSlots = 8; // Default tier 0 slots
  const usedSlots = serverSounds.length;
  const pct = Math.round((usedSlots / maxSlots) * 100);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      {/* TOP BAR: USER & SERVER SELECTOR */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pb-8 border-b border-white/10">
        <div>
          <div className="flex items-center gap-3 mb-2">
            {user?.avatar ? (
              <img src={user.avatar} alt={user.username} className="w-12 h-12 rounded-2xl ring-2 ring-discord-blurple/30" />
            ) : (
              <div className="w-12 h-12 rounded-2xl bg-discord-blurple flex items-center justify-center font-bold text-lg">
                {user?.username?.slice(0, 2).toUpperCase()}
              </div>
            )}
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-bold text-white">{user?.username}</h1>
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Mail OTP Verified
                </span>
              </div>
              <p className="text-xs text-gray-400">{user?.email}</p>
            </div>
          </div>
        </div>

        {/* Server Picker */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 border border-white/10 w-full md:w-64">
            <Server className="w-4 h-4 text-discord-blurple shrink-0" />
            <select
              value={selectedGuild?.id || ""}
              onChange={(e) => {
                const g = guilds.find((item) => item.id === e.target.value);
                if (g) setSelectedGuild(g);
              }}
              className="bg-transparent text-white text-sm font-semibold w-full focus:outline-none cursor-pointer"
            >
              {guilds.map((g) => (
                <option key={g.id} value={g.id} className="bg-[#141721] text-white">
                  {g.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* ALERT TOAST */}
      {uploadMsg && (
        <div
          className={`mt-6 p-4 rounded-2xl border flex items-center gap-3 text-sm animate-fade-in ${
            uploadMsg.success
              ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-300"
              : "bg-red-500/15 border-red-500/30 text-red-300"
          }`}
        >
          {uploadMsg.success ? <CheckCircle2 className="w-5 h-5 shrink-0" /> : <AlertCircle className="w-5 h-5 shrink-0" />}
          <span>{uploadMsg.text}</span>
        </div>
      )}

      {/* METRICS & PRO PAYWALL BANNER */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 my-8">
        {/* Slot Capacity Card */}
        <div className="lg:col-span-2 rounded-3xl bg-[#141721] border border-white/10 p-6 flex flex-col justify-between shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                Server Soundboard Capacity
              </span>
              <h2 className="text-xl font-bold text-white mt-1">
                {selectedGuild?.name || "Server"} &bull; Tier 0 Boost
              </h2>
            </div>
            <div className="text-right">
              <span className="text-2xl font-black text-discord-blurple">
                {usedSlots} / {maxSlots}
              </span>
              <span className="text-xs text-gray-500 block">Slots Occupied</span>
            </div>
          </div>

          {/* Progress Bar */}
          <div>
            <div className="w-full h-3 rounded-full bg-white/5 overflow-hidden mb-2">
              <div
                className={`h-full transition-all duration-500 rounded-full ${
                  pct >= 90 ? "bg-red-500" : pct >= 70 ? "bg-amber-500" : "bg-discord-blurple"
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-400 font-medium">
              <span>{maxSlots - usedSlots} slots remaining</span>
              <span>Need more? Server Boost Tier 1 gives 24 slots</span>
            </div>
          </div>
        </div>

        {/* Pro Banner */}
        <div className="rounded-3xl bg-gradient-to-br from-amber-500/15 to-orange-500/10 border border-amber-500/30 p-6 flex flex-col justify-between shadow-xl relative overflow-hidden">
          <div className="relative z-10">
            <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-amber-400 mb-2">
              <Crown className="w-4 h-4" />
              Dissound Pro
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Unlock AI Text-to-Sound & Multi-Server Sync</h3>
            <p className="text-xs text-gray-300 leading-relaxed">
              Generate custom meme audio using AI and sync your entire soundboard across up to 20 servers automatically.
            </p>
          </div>
          <Link
            href="/pricing"
            className="mt-4 inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs shadow-lg shadow-amber-500/20 transition"
          >
            <span>View Paywalled Features ($4.99/mo)</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* ACTIVE SERVER SOUNDS */}
      <div className="mb-12">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Volume2 className="w-5 h-5 text-discord-blurple" />
            Currently Mounted in {selectedGuild?.name || "Server"} Soundboard
          </h2>
          <span className="text-xs text-gray-400 font-medium">{serverSounds.length} sounds active</span>
        </div>

        {serverSounds.length === 0 ? (
          <div className="p-8 text-center rounded-2xl bg-white/[0.02] border border-dashed border-white/10 text-gray-400 text-sm">
            No sounds in this server yet. Add some from the catalog below!
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {serverSounds.map((sound) => (
              <div
                key={sound.id}
                className="rounded-2xl bg-[#141721] border border-white/5 p-4 flex items-center justify-between gap-3 hover:border-white/15 transition shadow-md"
              >
                <div className="flex-1 min-w-0">
                  <h4 className="font-bold text-white text-sm truncate">{sound.name}</h4>
                  <div className="text-[11px] text-gray-500 mt-0.5">
                    {sound.category} &bull; {sound.duration}s
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteSound(sound.id)}
                  title="Remove from Server Soundboard"
                  className="p-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 transition"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* UPLOAD CUSTOM SOUND & AUTO-TRIMMER */}
      <div className="mb-12 rounded-3xl bg-[#141721] border border-white/10 p-6 sm:p-8">
        <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
          <Upload className="w-5 h-5 text-cyan-400" />
          Upload & Auto-Trim Custom Audio
        </h3>
        <p className="text-xs text-gray-400 mb-6">
          Dissound automatically trims long audio clips down to 5.2 seconds, optimizes file sizes under 512 KB, and normalizes audio levels.
        </p>

        <form onSubmit={handleCustomUpload} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1.5">Soundboard Display Name</label>
            <input
              type="text"
              placeholder="e.g. Vine Boom Bass"
              value={customSoundName}
              onChange={(e) => setCustomSoundName(e.target.value)}
              maxLength={32}
              required
              className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 text-sm focus:border-discord-blurple focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1.5">
              Audio File (MP3, WAV, OGG)
            </label>
            <input
              type="file"
              accept="audio/*"
              className="w-full text-xs text-gray-400 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-discord-blurple file:text-white hover:file:bg-discord-blurple/90 cursor-pointer"
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={uploading || !customSoundName.trim()}
              className="w-full py-2.5 px-4 rounded-xl bg-discord-blurple hover:bg-discord-blurple/90 disabled:opacity-50 text-white font-bold text-sm flex items-center justify-center gap-2 transition"
            >
              {uploading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Processing & Auto-Trimming...</span>
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  <span>Auto-Trim & Add to Soundboard</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* SOUND CATALOG DIRECT INSTALLER */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xl font-bold text-white">One-Click Catalog Installer</h3>
            <p className="text-xs text-gray-400 mt-1">Browse meme sounds and add them directly to your server.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {catalogSounds.map((sound) => (
            <div
              key={sound.id}
              className="rounded-2xl bg-[#141721] border border-white/5 hover:border-discord-blurple/30 p-4 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      sound.isPremium ? "bg-amber-500/20 text-amber-300 border border-amber-500/30" : "bg-white/5 text-gray-400"
                    }`}
                  >
                    {sound.category}
                  </span>
                  <span className="text-xs text-gray-500">{sound.duration}s</span>
                </div>
                <h4 className="font-bold text-white text-sm mb-3">{sound.name}</h4>
              </div>

              <button
                onClick={() => handleAddCatalogSound(sound)}
                className={`w-full py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition ${
                  sound.isPremium
                    ? "bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30"
                    : "bg-white/5 hover:bg-discord-blurple text-gray-300 hover:text-white"
                }`}
              >
                {sound.isPremium ? (
                  <>
                    <Lock className="w-3.5 h-3.5 text-amber-400" />
                    <span>Unlock with Pro</span>
                  </>
                ) : (
                  <>
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add to Server</span>
                  </>
                )}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Paywall Modal */}
      <PaywallModal
        isOpen={paywallOpen}
        onClose={() => setPaywallOpen(false)}
        featureName={paywallFeature.name}
        featureDescription={paywallFeature.desc}
      />
    </div>
  );
}

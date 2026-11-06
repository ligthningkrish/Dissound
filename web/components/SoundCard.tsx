"use client";

import React, { useState, useRef } from "react";
import { Play, Pause, Plus, Lock, Volume2, CheckCircle2, Loader2 } from "lucide-react";
import { SoundItem } from "@/app/api/sounds/route";

interface SoundCardProps {
  sound: SoundItem;
  onOpenPaywall?: (name: string, desc: string) => void;
  selectedGuildId?: string;
}

export default function SoundCard({ sound, onOpenPaywall, selectedGuildId }: SoundCardProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const togglePlay = () => {
    if (sound.isPremium) {
      onOpenPaywall?.(
        sound.name,
        "This HD / AI-synthesized audio asset is part of the Dissound Pro library. Upgrade to play and sync."
      );
      return;
    }

    if (!audioRef.current) {
      audioRef.current = new Audio(sound.url);
      audioRef.current.onended = () => setIsPlaying(false);
      audioRef.current.onerror = () => setIsPlaying(false);
    }

    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.currentTime = 0;
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleAddToSoundboard = async () => {
    if (sound.isPremium) {
      onOpenPaywall?.(
        sound.name,
        "Adding Pro-tier sounds directly to your server soundboard requires a Dissound Pro or Server Pass."
      );
      return;
    }

    setAdding(true);
    // Simulate upload to guild soundboard via API
    await new Promise((r) => setTimeout(r, 1200));
    setAdding(false);
    setAdded(true);
    setTimeout(() => setAdded(false), 3000);
  };

  return (
    <div className="relative group rounded-2xl bg-[#141721] border border-white/5 hover:border-discord-blurple/40 p-4 transition-all duration-300 shadow-lg hover:shadow-discord-blurple/10 flex flex-col justify-between">
      {/* Top Details */}
      <div>
        <div className="flex items-start justify-between gap-3 mb-3">
          {/* Play/Pause Button */}
          <button
            onClick={togglePlay}
            className={`w-12 h-12 rounded-xl flex items-center justify-center transition shrink-0 ${
              sound.isPremium
                ? "bg-amber-500/20 text-amber-400 group-hover:bg-amber-500 group-hover:text-black"
                : isPlaying
                ? "bg-discord-blurple text-white shadow-lg shadow-discord-blurple/40 animate-pulse"
                : "bg-white/5 hover:bg-discord-blurple text-gray-300 hover:text-white"
            }`}
          >
            {sound.isPremium ? (
              <Lock className="w-5 h-5" />
            ) : isPlaying ? (
              <Pause className="w-5 h-5" />
            ) : (
              <Play className="w-5 h-5 ml-0.5" />
            )}
          </button>

          {/* Sound Name & Category */}
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-white text-base truncate group-hover:text-discord-blurple transition">
              {sound.name}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <span
                className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                  sound.isPremium
                    ? "bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold"
                    : "bg-white/5 text-gray-400"
                }`}
              >
                {sound.category}
              </span>
              <span className="text-xs text-gray-500">⏱️ {sound.duration}s</span>
            </div>
          </div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {sound.tags.slice(0, 3).map((tag) => (
            <span key={tag} className="text-[10px] text-gray-400 bg-white/[0.03] px-2 py-0.5 rounded">
              #{tag}
            </span>
          ))}
        </div>
      </div>

      {/* Bottom Action */}
      <div className="pt-3 border-t border-white/5 flex items-center justify-between">
        <span className="text-xs text-gray-500">{(sound.fileSize / 1024).toFixed(0)} KB</span>
        <button
          onClick={handleAddToSoundboard}
          disabled={adding || added}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition active:scale-95 ${
            added
              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
              : sound.isPremium
              ? "bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30"
              : "bg-discord-blurple/15 hover:bg-discord-blurple text-discord-blurple hover:text-white border border-discord-blurple/30"
          }`}
        >
          {adding ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Uploading...</span>
            </>
          ) : added ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Added to Server!</span>
            </>
          ) : sound.isPremium ? (
            <>
              <Lock className="w-3 h-3 text-amber-400" />
              <span>Unlock (Pro)</span>
            </>
          ) : (
            <>
              <Plus className="w-3.5 h-3.5" />
              <span>Add to Soundboard</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}

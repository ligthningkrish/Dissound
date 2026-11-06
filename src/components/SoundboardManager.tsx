import React from 'react';
import { ServerData, SoundboardSound } from '../types';
import {
  Volume2,
  Trash2,
  Plus,
  Sparkles,
  Zap,
  Info,
  Radio,
  Sliders,
} from 'lucide-react';

interface SoundboardManagerProps {
  server: ServerData;
  activeSoundId: string | null;
  isPlaying: boolean;
  onPlaySound: (sound: { sound_id: string; sound_name: string; file_path: string; volume?: number }) => void;
  onDeleteSound: (soundboardSoundId: string, name: string) => void;
  onOpenCatalog: () => void;
  onOpenUpload: () => void;
}

export const SoundboardManager: React.FC<SoundboardManagerProps> = ({
  server,
  activeSoundId,
  isPlaying,
  onPlaySound,
  onDeleteSound,
  onOpenCatalog,
  onOpenUpload,
}) => {
  const maxSlots = server.sound_limit;
  const usedSlots = server.sounds.length;
  const availableSlots = Math.max(0, maxSlots - usedSlots);
  const percentUsed = Math.min(100, Math.round((usedSlots / maxSlots) * 100));

  // Key shortcuts 1-9
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if typing in an input
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) {
        return;
      }
      const num = parseInt(e.key, 10);
      if (!isNaN(num) && num >= 1 && num <= 9 && num <= server.sounds.length) {
        const targetSound = server.sounds[num - 1];
        if (targetSound) {
          onPlaySound({
            sound_id: targetSound.sound_id,
            sound_name: targetSound.name,
            file_path: targetSound.file_path,
            volume: targetSound.volume,
          });
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [server.sounds, onPlaySound]);

  const getCapacityColor = () => {
    if (percentUsed >= 100) return 'from-rose-500 to-red-600';
    if (percentUsed >= 75) return 'from-amber-500 to-orange-500';
    return 'from-indigo-500 via-purple-500 to-cyan-400';
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Hero with Capacity Gauge */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#16181f] via-[#12141a] to-[#0e1015] border border-white/10 p-6 sm:p-8 shadow-2xl">
        {/* Ambient glow */}
        <div className="absolute -top-24 -right-24 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          <div className="lg:col-span-7 space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-2xl">{server.icon}</span>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                {server.name}
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center gap-1">
                <Zap className="w-3 h-3 fill-purple-400 text-purple-400" />
                Boost Tier {server.premium_tier}
              </span>
            </div>

            <p className="text-sm text-zinc-400 max-w-xl">
              Play, trigger, and manage soundboard expressions directly integrated with Discord's official Soundboard API. Press numbers <code className="text-cyan-300 font-mono bg-cyan-950/50 px-1.5 py-0.5 rounded border border-cyan-800/40">1-9</code> on your keyboard for instant meme drops!
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                onClick={onOpenCatalog}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-all shadow-lg shadow-indigo-600/30 active:scale-95"
              >
                <Plus className="w-4 h-4" />
                Add Sound from Catalog
              </button>
              <button
                onClick={onOpenUpload}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-zinc-200 hover:text-white font-semibold text-xs border border-white/10 transition-all active:scale-95"
              >
                <Sparkles className="w-4 h-4 text-cyan-400" />
                Upload Custom Audio
              </button>
            </div>
          </div>

          {/* Capacity Meter */}
          <div className="lg:col-span-5 bg-[#0e1015]/80 rounded-2xl p-5 border border-white/10 backdrop-blur-md">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-indigo-400 animate-pulse" />
                <span className="text-xs font-bold uppercase tracking-wider text-zinc-300">
                  Soundboard Capacity
                </span>
              </div>
              <span className="text-xs font-mono font-bold text-white">
                {usedSlots} / {maxSlots} Slots
              </span>
            </div>

            {/* Visual Bar */}
            <div className="w-full h-3 rounded-full bg-zinc-800/80 overflow-hidden p-0.5 border border-white/5">
              <div
                className={`h-full rounded-full bg-gradient-to-r ${getCapacityColor()} transition-all duration-500`}
                style={{ width: `${percentUsed}%` }}
              />
            </div>

            <div className="flex items-center justify-between text-[11px] text-zinc-400 mt-3 pt-2 border-t border-white/5">
              <div>
                <span className="font-semibold text-white">{availableSlots}</span> available
              </div>
              <div className="flex items-center gap-1.5 text-zinc-400">
                <Info className="w-3.5 h-3.5 text-zinc-500" />
                <span>
                  Tier {server.premium_tier} Max: {maxSlots}
                </span>
              </div>
            </div>

            {percentUsed >= 100 && (
              <div className="mt-3 p-2 rounded-xl bg-red-500/10 border border-red-500/30 text-[11px] text-red-300 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                Soundboard is at max capacity! Delete sounds or boost server to expand.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Soundboard Pads Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Volume2 className="w-5 h-5 text-indigo-400" />
              Active Server Soundboard Sounds ({server.sounds.length})
            </h2>
            <p className="text-xs text-zinc-400">
              Click any sound pad to trigger playback. Each sound is volume-normalized for Discord voice chats.
            </p>
          </div>
        </div>

        {server.sounds.length === 0 ? (
          <div className="text-center py-16 px-4 rounded-3xl bg-[#14161d] border border-dashed border-white/10">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-indigo-500/10 flex items-center justify-center text-3xl mb-4">
              🔇
            </div>
            <h3 className="text-base font-bold text-white mb-1">
              No sounds on this server yet
            </h3>
            <p className="text-xs text-zinc-400 max-w-md mx-auto mb-5">
              Your server soundboard is currently empty. Browse our meme sound catalog or upload your custom MP3 to get started!
            </p>
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={onOpenCatalog}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-all shadow-md"
              >
                Browse Catalog
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-4 xl:grid-cols-6 gap-3 sm:gap-4">
            {server.sounds.map((sound, idx) => {
              const isActive = activeSoundId === sound.sound_id && isPlaying;
              const hasKeybind = idx < 9;

              return (
                <div
                  key={sound.id}
                  className={`group relative rounded-2xl p-4 transition-all duration-200 cursor-pointer flex flex-col justify-between select-none ${
                    isActive
                      ? 'bg-gradient-to-b from-indigo-600/30 via-indigo-900/40 to-[#12141b] border-2 border-indigo-400 shadow-xl shadow-indigo-500/20 scale-[1.02]'
                      : 'bg-[#14161d] hover:bg-[#1a1d26] border border-white/10 hover:border-indigo-500/50 shadow-md hover:shadow-lg'
                  }`}
                  onClick={() =>
                    onPlaySound({
                      sound_id: sound.sound_id,
                      sound_name: sound.name,
                      file_path: sound.file_path,
                      volume: sound.volume,
                    })
                  }
                >
                  {/* Top Bar on Pad: Keybind badge + Delete button */}
                  <div className="flex items-center justify-between w-full mb-3">
                    {hasKeybind ? (
                      <span className="w-5 h-5 rounded-md bg-white/10 text-zinc-300 font-mono text-[10px] font-bold flex items-center justify-center border border-white/10 group-hover:bg-indigo-500/30 group-hover:text-indigo-200 transition-colors">
                        {idx + 1}
                      </span>
                    ) : (
                      <span className="w-5 h-5" />
                    )}

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSound(sound.id, sound.name);
                      }}
                      title="Delete from soundboard"
                      className="opacity-0 group-hover:opacity-100 p-1 rounded-lg text-zinc-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* Center Emoji / Animated wave */}
                  <div className="my-2 flex flex-col items-center justify-center">
                    <div className="relative text-3xl mb-2 group-hover:scale-110 transition-transform">
                      {sound.emoji || '🎵'}
                      {isActive && (
                        <span className="absolute -inset-2 rounded-full bg-indigo-500/30 animate-ping -z-10" />
                      )}
                    </div>

                    <h3 className="font-bold text-xs sm:text-sm text-white text-center truncate max-w-full capitalize tracking-tight">
                      {sound.name}
                    </h3>
                  </div>

                  {/* Bottom Stats: Volume + Sound wave animation if active */}
                  <div className="mt-3 pt-2 border-t border-white/5 flex items-center justify-between text-[10px] text-zinc-400">
                    <span className="flex items-center gap-1">
                      <Sliders className="w-3 h-3 text-zinc-500" />
                      {Math.round(sound.volume * 100)}%
                    </span>

                    {isActive ? (
                      <div className="flex items-end gap-0.5 h-3">
                        <span className="w-0.5 bg-cyan-400 rounded-full animate-soundwave-1" />
                        <span className="w-0.5 bg-indigo-400 rounded-full animate-soundwave-2" />
                        <span className="w-0.5 bg-purple-400 rounded-full animate-soundwave-3" />
                        <span className="w-0.5 bg-cyan-400 rounded-full animate-soundwave-4" />
                      </div>
                    ) : (
                      <span className="font-mono text-zinc-500">{sound.duration}s</span>
                    )}
                  </div>
                </div>
              );
            })}

            {/* Quick Add Placeholder Card if slots available */}
            {availableSlots > 0 && (
              <button
                onClick={onOpenCatalog}
                className="rounded-2xl p-4 border border-dashed border-white/10 hover:border-indigo-500/50 bg-white/[0.02] hover:bg-indigo-500/5 transition-all flex flex-col items-center justify-center text-center group min-h-[140px]"
              >
                <div className="w-9 h-9 rounded-xl bg-white/5 group-hover:bg-indigo-600/20 text-zinc-400 group-hover:text-indigo-400 flex items-center justify-center mb-2 transition-all">
                  <Plus className="w-5 h-5" />
                </div>
                <span className="text-xs font-semibold text-zinc-300 group-hover:text-white">
                  Add Sound
                </span>
                <span className="text-[10px] text-zinc-500 mt-0.5">
                  {availableSlots} slots free
                </span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

"use client";

import React from "react";
import Link from "next/link";
import { X, Sparkles, Check, Lock, Zap, ShieldAlert } from "lucide-react";

interface PaywallModalProps {
  isOpen: boolean;
  onClose: () => void;
  featureName?: string;
  featureDescription?: string;
}

export default function PaywallModal({
  isOpen,
  onClose,
  featureName = "Dissound Pro Feature",
  featureDescription = "This premium capability is exclusive to Dissound Pro and Server Pass subscribers.",
}: PaywallModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-lg rounded-2xl bg-[#141721] border border-amber-500/30 p-6 sm:p-8 shadow-2xl shadow-amber-500/10">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Badge */}
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 text-amber-300 font-semibold text-xs mb-4">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          Paywalled Premium Capability
        </div>

        {/* Title & Desc */}
        <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
          <Lock className="w-6 h-6 text-amber-400" />
          {featureName}
        </h2>
        <p className="text-sm text-gray-300 leading-relaxed mb-6">
          {featureDescription}
        </p>

        {/* What you get */}
        <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-2.5 mb-6 text-sm">
          <div className="font-semibold text-xs text-amber-300 uppercase tracking-wider mb-1">
            Unlock with Dissound Pro:
          </div>
          <div className="flex items-center gap-2.5 text-gray-200">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>AI Voice & Text-to-Sound Effect Generator</span>
          </div>
          <div className="flex items-center gap-2.5 text-gray-200">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Voice Channel Live Web Remote Soundboard</span>
          </div>
          <div className="flex items-center gap-2.5 text-gray-200">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Automated Soundboard Sync across all your servers</span>
          </div>
          <div className="flex items-center gap-2.5 text-gray-200">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>AI Vocal Stem Separation & Noise Cleaner</span>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Link
            href="/pricing"
            onClick={onClose}
            className="flex-1 py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-black font-bold text-sm text-center shadow-lg shadow-amber-500/25 transition"
          >
            Explore Pro Plans ($4.99/mo)
          </Link>
          <button
            onClick={onClose}
            className="py-3 px-4 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 font-medium text-sm transition"
          >
            Maybe Later
          </button>
        </div>
      </div>
    </div>
  );
}

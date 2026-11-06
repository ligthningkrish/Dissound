"use client";

import React, { useState, useEffect, useRef, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import { Mail, ShieldCheck, ArrowRight, RefreshCw, KeyRound, CheckCircle, AlertCircle, Sparkles } from "lucide-react";

function VerifyOtpContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const userId = searchParams.get("userId") || "";
  const rawEmail = searchParams.get("email") || "your registered email";
  const isDemo = searchParams.get("demo") === "true";

  const [digits, setDigits] = useState(["", "", "", "", "", ""]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resending, setResending] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(60);
  const [devCode, setDevCode] = useState<string | null>(null);

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Mask email for display: k***@example.com
  const maskedEmail = (() => {
    try {
      if (!rawEmail.includes("@")) return rawEmail;
      const [name, domain] = rawEmail.split("@");
      if (name.length <= 2) return `${name}***@${domain}`;
      return `${name.slice(0, 2)}***${name.slice(-1)}@${domain}`;
    } catch {
      return rawEmail;
    }
  })();

  // Resend countdown timer
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = setInterval(() => setResendCooldown((prev) => prev - 1), 1000);
    return () => clearInterval(timer);
  }, [resendCooldown]);

  // Fetch dev simulated OTP for frictionless local testing
  useEffect(() => {
    fetch("/api/auth/dev-preview")
      .then((r) => r.json())
      .then((res) => {
        if (res.available && res.data?.code) {
          setDevCode(res.data.code);
        }
      })
      .catch(() => {});
  }, []);

  const handleDigitChange = (index: number, value: string) => {
    // Only accept numeric digit
    const cleaned = value.replace(/\D/g, "");
    if (!cleaned) {
      const next = [...digits];
      next[index] = "";
      setDigits(next);
      return;
    }

    // Handle copy-paste of full 6-digit code
    if (cleaned.length === 6) {
      const splitDigits = cleaned.split("").slice(0, 6);
      setDigits(splitDigits);
      submitCode(cleaned);
      return;
    }

    const next = [...digits];
    next[index] = cleaned[cleaned.length - 1];
    setDigits(next);

    // Auto-advance to next box
    if (index < 5 && cleaned) {
      inputRefs.current[index + 1]?.focus();
    }

    // If all digits filled, auto-submit
    const fullCode = next.join("");
    if (fullCode.length === 6) {
      submitCode(fullCode);
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const submitCode = async (code: string) => {
    setError(null);
    setLoading(true);

    try {
      const res = await fetch("/api/auth/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId, code }),
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        setError(data.error || "Incorrect verification code. Please check your email.");
        setLoading(false);
        return;
      }

      // Successful verification
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to verify code.");
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (resendCooldown > 0 || resending) return;
    setResending(true);
    setError(null);

    try {
      const res = await fetch("/api/auth/resend-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setResendCooldown(60);
        // Refresh dev preview code
        const previewRes = await fetch("/api/auth/dev-preview").then((r) => r.json());
        if (previewRes.available) setDevCode(previewRes.data.code);
      } else {
        setError(data.error || "Failed to resend code.");
      }
    } catch {
      setError("Failed to resend code.");
    } finally {
      setResending(false);
    }
  };

  const fillDevCode = () => {
    if (devCode) {
      setDigits(devCode.split(""));
      submitCode(devCode);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 bg-[#0B0D13]">
      <div className="w-full max-w-md rounded-3xl bg-[#141721] border border-white/10 p-8 shadow-2xl relative overflow-hidden">
        {/* Glow backdrop accent */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-discord-blurple/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-purple-600/20 rounded-full blur-3xl pointer-events-none" />

        {/* Header Icon */}
        <div className="relative text-center mb-6">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-tr from-discord-blurple to-purple-600 p-0.5 shadow-xl shadow-discord-blurple/25 mb-4">
            <div className="w-full h-full bg-[#141721] rounded-[14px] flex items-center justify-center">
              <Mail className="w-7 h-7 text-discord-blurple animate-bounce" />
            </div>
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Check Your Inbox</h1>
          <p className="text-sm text-gray-400 mt-2 leading-relaxed">
            We sent a 6-digit verification code to your Discord-registered email address:
          </p>
          <div className="inline-block mt-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-cyan-300">
            {maskedEmail}
          </div>
        </div>

        {/* Dev / Testing Helper Alert */}
        {devCode && (
          <div className="mb-6 p-3.5 rounded-xl bg-discord-blurple/10 border border-discord-blurple/30 flex items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2 text-discord-blurple">
              <Sparkles className="w-4 h-4 shrink-0" />
              <span>
                <strong>Dev OTP Code:</strong> <code className="bg-black/30 px-1.5 py-0.5 rounded text-white font-mono">{devCode}</code>
              </span>
            </div>
            <button
              onClick={fillDevCode}
              type="button"
              className="px-2.5 py-1 rounded bg-discord-blurple hover:bg-discord-blurple/90 text-white font-semibold transition"
            >
              Auto-Fill
            </button>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="mb-6 p-3 rounded-xl bg-red-500/15 border border-red-500/30 text-red-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* 6 Digit Inputs */}
        <div className="flex justify-between gap-2 sm:gap-3 mb-6">
          {digits.map((digit, index) => (
            <input
              key={index}
              ref={(el) => {
                inputRefs.current[index] = el;
              }}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              onChange={(e) => handleDigitChange(index, e.target.value)}
              onKeyDown={(e) => handleKeyDown(index, e)}
              className="w-12 h-14 sm:w-13 sm:h-16 text-center text-2xl font-extrabold font-mono rounded-xl bg-white/5 border border-white/15 text-white focus:border-discord-blurple focus:ring-2 focus:ring-discord-blurple/40 focus:outline-none transition"
              autoFocus={index === 0}
            />
          ))}
        </div>

        {/* Submit Button */}
        <button
          onClick={() => submitCode(digits.join(""))}
          disabled={loading || digits.join("").length !== 6}
          className="w-full py-3.5 rounded-xl bg-discord-blurple hover:bg-discord-blurple/90 disabled:opacity-50 text-white font-bold text-sm flex items-center justify-center gap-2 shadow-lg shadow-discord-blurple/25 transition active:scale-98"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Verifying Security Code...</span>
            </>
          ) : (
            <>
              <span>Verify & Continue to Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>

        {/* Resend Code Action */}
        <div className="text-center mt-6 text-xs text-gray-400">
          Didn't receive the email?{" "}
          <button
            onClick={handleResend}
            disabled={resendCooldown > 0 || resending}
            className="text-discord-blurple hover:underline font-semibold disabled:text-gray-500 disabled:no-underline ml-1"
          >
            {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : resending ? "Resending..." : "Resend Code"}
          </button>
        </div>

        <div className="mt-8 pt-4 border-t border-white/5 flex items-center justify-center gap-1.5 text-[11px] text-gray-500">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Secured with Discord Two-Factor Authentication</span>
        </div>
      </div>
    </div>
  );
}

export default function VerifyOtpPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 bg-[#0B0D13]">
          <div className="text-gray-400 text-sm flex items-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-discord-blurple" />
            <span>Loading verification screen...</span>
          </div>
        </div>
      }
    >
      <VerifyOtpContent />
    </Suspense>
  );
}

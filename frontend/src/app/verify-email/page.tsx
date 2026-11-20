"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Activity, ShieldCheck } from "lucide-react";

export default function VerifyEmailPage() {
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const username = searchParams.get("username");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const res = await fetch("https://omnipulse-1ds1.onrender.com/api/verify-email/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, code }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Verification failed.");
      }

      router.push("/login");
    } catch (err: any) {
      setError(err.message || "Connection failed.");
    } finally {
      setIsLoading(false);
    }
  };

  if (!username) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-white">
        <p>Invalid request. Please register again.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-zinc-950">
      <div className="hidden lg:flex w-1/2 bg-gradient-to-tr from-zinc-900 via-zinc-950 to-emerald-950/30 relative overflow-hidden items-center justify-center p-12">
        <div className="relative z-10 max-w-md">
          <ShieldCheck className="w-16 h-16 text-emerald-500 mb-8" />
          <h1 className="text-4xl font-bold text-white mb-4 tracking-tight">Verify your email</h1>
          <p className="text-lg text-zinc-400 leading-relaxed">
            We've sent a 6-digit code to your email. Enter it to activate your account.
          </p>
        </div>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-10 justify-center">
            <Activity className="w-8 h-8 text-emerald-500" />
            <h1 className="text-2xl font-bold text-white">OmniPulse</h1>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-white">Enter verification code</h2>
            <p className="text-zinc-400 text-sm mt-2">We sent a code to your email address.</p>
          </div>

          {error && (
            <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-sm text-center">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">Verification Code</label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                maxLength={6}
                className="w-full text-center tracking-[1em] text-2xl py-3 bg-zinc-900 border border-zinc-800 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all text-white placeholder-zinc-600"
                placeholder="000000"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center"
            >
              {isLoading ? "Verifying..." : "Verify Email"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

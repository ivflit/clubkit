"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { getApiBase } from "@/lib/api";
import { useBrandKit } from "@/hooks/useBrandKit";

export default function ForgotPasswordPage() {
  const { brandKit, subdomain } = useBrandKit();

  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!subdomain) return;
    setError("");
    setLoading(true);
    try {
      const base = getApiBase(subdomain);
      const res = await fetch(`${base}/api/auth/password-reset/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) throw new Error("Request failed");
      setSubmitted(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";

  if (submitted) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm text-center">
          <h1 className="text-2xl font-bold mb-4" style={{ color: primaryColour }}>
            Check your email
          </h1>
          <p className="text-zinc-600 dark:text-zinc-400 mb-6">
            If an account with that email exists, we&apos;ve sent a password reset link.
          </p>
          <Link href="/login" className="text-sm font-medium hover:underline" style={{ color: primaryColour }}>
            Back to login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-12">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold text-center mb-8" style={{ color: primaryColour }}>
          Reset password
        </h1>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-800 dark:border-zinc-600 dark:text-white"
              style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            style={{ backgroundColor: primaryColour }}
          >
            {loading ? "Sending..." : "Send reset link"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-zinc-600 dark:text-zinc-400">
          <Link href="/login" className="font-medium hover:underline" style={{ color: primaryColour }}>
            Back to login
          </Link>
        </p>
      </div>
    </div>
  );
}

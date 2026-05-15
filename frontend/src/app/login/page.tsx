"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { login, AuthError } from "@/lib/auth";
import { useBrandKit } from "@/hooks/useBrandKit";
import { getSubdomain } from "@/lib/tenant";

export default function LoginPage() {
  const router = useRouter();
  const { brandKit, subdomain } = useBrandKit();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [btnHover, setBtnHover] = useState(false);

  async function quickLogin(quickEmail: string, quickPassword: string) {
    const sub = subdomain ?? getSubdomain(window.location.hostname);
    if (!sub) { setError("Could not detect club subdomain."); return; }
    setError("");
    setLoading(true);
    try {
      const tokens = await login(sub, quickEmail, quickPassword);
      console.log("[login] success, tokens:", tokens);
      router.push("/dashboard");
    } catch (err) {
      console.error("[login] error:", err);
      setError("Quick login failed. Check console.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    // Read subdomain synchronously at click time as a fallback
    const sub = subdomain ?? getSubdomain(window.location.hostname);
    if (!sub) {
      setError("Could not detect club subdomain. Check the URL.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await login(sub, email, password);
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof AuthError) {
        setError(
          typeof err.data.detail === "string"
            ? err.data.detail
            : "Invalid email or password.",
        );
      } else if (err instanceof TypeError && (err as TypeError).message.includes("fetch")) {
        setError("Cannot reach the server. Is the backend running on port 8000?");
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";
  const btnBg = btnHover ? `${primaryColour}cc` : primaryColour;

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-12">
      <div className="w-full max-w-sm">
        {brandKit?.logo && (
          <img
            src={brandKit.logo}
            alt="Club logo"
            className="h-16 w-auto mx-auto mb-6"
          />
        )}
        <h1 className="text-2xl font-bold text-center mb-8" style={{ color: primaryColour }}>
          Log in
        </h1>

        {/* Dev quick-login buttons */}
        <div className="mb-6 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-xs font-medium text-amber-700 mb-2">Dev shortcuts</p>
          <div className="flex gap-2 flex-wrap">
            {[
              { label: "Admin", email: "admin@demo.com", password: "Admin123!" },
              { label: "Alice (member)", email: "alice@demo.com", password: "Member123!" },
              { label: "Carol (guest)", email: "carol@demo.com", password: "Member123!" },
            ].map(({ label, email: e, password: p }) => (
              <button
                key={e}
                type="button"
                disabled={loading}
                onClick={() => quickLogin(e, p)}
                className="px-3 py-1 text-xs rounded border border-amber-300 bg-white text-amber-800 hover:bg-amber-100 cursor-pointer disabled:opacity-50"
              >
                {label}
              </button>
            ))}
          </div>
        </div>

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

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-800 dark:border-zinc-600 dark:text-white"
              style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            onMouseEnter={() => setBtnHover(true)}
            onMouseLeave={() => setBtnHover(false)}
            className="w-full rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50 transition-opacity cursor-pointer"
            style={{ backgroundColor: btnBg }}
          >
            {loading ? "Logging in..." : "Log in"}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-zinc-600 dark:text-zinc-400 space-y-2">
          <p>
            Don&apos;t have an account?{" "}
            <Link href="/register" className="font-medium hover:underline" style={{ color: primaryColour }}>
              Register
            </Link>
          </p>
          <p>
            <Link href="/forgot-password" className="font-medium hover:underline" style={{ color: primaryColour }}>
              Forgot password?
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

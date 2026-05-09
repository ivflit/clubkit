"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { login, AuthError } from "@/lib/auth";
import { useBrandKit } from "@/hooks/useBrandKit";

export default function LoginPage() {
  const router = useRouter();
  const { brandKit, subdomain } = useBrandKit();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!subdomain) return;
    setError("");
    setLoading(true);
    try {
      await login(subdomain, email, password);
      router.push("/");
    } catch (err) {
      if (err instanceof AuthError) {
        setError(
          typeof err.data.detail === "string"
            ? err.data.detail
            : "Invalid email or password.",
        );
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";

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
            className="w-full rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            style={{ backgroundColor: primaryColour }}
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

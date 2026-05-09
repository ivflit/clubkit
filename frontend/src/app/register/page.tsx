"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { register, login, AuthError } from "@/lib/auth";
import { useBrandKit } from "@/hooks/useBrandKit";

export default function RegisterPage() {
  const router = useRouter();
  const { brandKit, subdomain } = useBrandKit();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    first_name: "",
    last_name: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function update(field: string, value: string) {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!subdomain) return;

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setError("");
    setLoading(true);
    try {
      await register(subdomain, {
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name,
      });
      // Auto-login after registration
      await login(subdomain, formData.email, formData.password);
      router.push("/");
    } catch (err) {
      if (err instanceof AuthError) {
        const data = err.data;
        // Flatten field errors
        const messages: string[] = [];
        for (const val of Object.values(data)) {
          if (Array.isArray(val)) messages.push(...val.map(String));
          else if (typeof val === "string") messages.push(val);
        }
        setError(messages.join(" ") || "Registration failed.");
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
          Create an account
        </h1>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="first_name" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                First name
              </label>
              <input
                id="first_name"
                type="text"
                value={formData.first_name}
                onChange={(e) => update("first_name", e.target.value)}
                className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-800 dark:border-zinc-600 dark:text-white"
                style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
              />
            </div>
            <div>
              <label htmlFor="last_name" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Last name
              </label>
              <input
                id="last_name"
                type="text"
                value={formData.last_name}
                onChange={(e) => update("last_name", e.target.value)}
                className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-800 dark:border-zinc-600 dark:text-white"
                style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
              />
            </div>
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={formData.email}
              onChange={(e) => update("email", e.target.value)}
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
              minLength={8}
              value={formData.password}
              onChange={(e) => update("password", e.target.value)}
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-800 dark:border-zinc-600 dark:text-white"
              style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
            />
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Confirm password
            </label>
            <input
              id="confirmPassword"
              type="password"
              required
              minLength={8}
              value={formData.confirmPassword}
              onChange={(e) => update("confirmPassword", e.target.value)}
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
            {loading ? "Creating account..." : "Register"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-zinc-600 dark:text-zinc-400">
          Already have an account?{" "}
          <Link href="/login" className="font-medium hover:underline" style={{ color: primaryColour }}>
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}

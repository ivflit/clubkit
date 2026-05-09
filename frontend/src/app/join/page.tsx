"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useBrandKit } from "@/hooks/useBrandKit";
import { apiGet } from "@/lib/api";

interface PublicMembershipType {
  id: number;
  name: string;
  description: string;
  price: string;
  billing_frequency: "monthly" | "annual";
  renewal_mode: "rolling" | "one_off";
}

export default function JoinPage() {
  const { brandKit, subdomain } = useBrandKit();
  const [types, setTypes] = useState<PublicMembershipType[]>([]);
  const [loading, setLoading] = useState(true);

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";
  const accentColour = brandKit?.accent_colour ?? "#ff6d00";

  useEffect(() => {
    if (!subdomain) return;
    apiGet("/api/membership-types/public/", subdomain)
      .then(setTypes)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [subdomain]);

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-zinc-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col px-6 py-12 max-w-4xl mx-auto w-full">
      {brandKit?.logo && (
        <img
          src={brandKit.logo}
          alt="Club logo"
          className="h-16 w-auto mx-auto mb-6"
        />
      )}

      <h1 className="text-3xl font-bold text-center mb-2" style={{ color: primaryColour }}>
        Join Our Club
      </h1>
      <p className="text-center text-zinc-600 dark:text-zinc-400 mb-8">
        Choose a membership that suits you.
      </p>

      {types.length === 0 ? (
        <div className="text-center py-12 text-zinc-500">
          <p>No membership options are available at the moment.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {types.map((mt) => (
            <div
              key={mt.id}
              className="border border-zinc-200 dark:border-zinc-700 rounded-lg p-6 flex flex-col bg-white dark:bg-zinc-800"
            >
              <h2 className="text-xl font-semibold mb-2 text-zinc-900 dark:text-zinc-100">
                {mt.name}
              </h2>
              {mt.description && (
                <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-4 flex-1">
                  {mt.description}
                </p>
              )}
              <div className="mb-4">
                <span className="text-2xl font-bold" style={{ color: primaryColour }}>
                  &pound;{mt.price}
                </span>
                <span className="text-sm text-zinc-500 ml-1">
                  / {mt.billing_frequency === "monthly" ? "month" : "year"}
                </span>
              </div>
              <p className="text-xs text-zinc-500 mb-4">
                {mt.renewal_mode === "rolling" ? "Auto-renews" : "One-off payment"}
              </p>
              <Link
                href="/register"
                className="block text-center rounded-lg px-4 py-2 text-sm font-medium text-white"
                style={{ backgroundColor: primaryColour }}
              >
                Sign up
              </Link>
            </div>
          ))}
        </div>
      )}

      <div className="mt-8 text-center text-sm text-zinc-600 dark:text-zinc-400">
        Already a member?{" "}
        <Link href="/login" className="font-medium hover:underline" style={{ color: primaryColour }}>
          Log in
        </Link>
      </div>
    </div>
  );
}

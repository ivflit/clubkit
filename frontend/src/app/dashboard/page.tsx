"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useBrandKit } from "@/hooks/useBrandKit";
import { apiAuthGet, ApiError } from "@/lib/api";
import { getStoredTokens } from "@/lib/auth";

interface ActiveMembership {
  id: number;
  membership_type: number;
  membership_type_name: string;
  status: string;
  start_date: string;
  end_date: string | null;
}

interface UpcomingEvent {
  id: number;
  title: string;
  date_time: string;
  location: string;
}

interface DashboardData {
  active_memberships: ActiveMembership[];
  upcoming_events: UpcomingEvent[];
}

function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function DashboardPage() {
  const router = useRouter();
  const { brandKit, subdomain } = useBrandKit();

  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";

  useEffect(() => {
    if (!subdomain) return;
    const tokens = getStoredTokens();
    if (!tokens?.access) {
      router.push("/login");
      return;
    }
    apiAuthGet("/api/auth/dashboard/", tokens.access, subdomain)
      .then((d: DashboardData) => setData(d))
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          router.push("/login");
        } else {
          setError("Failed to load dashboard.");
        }
      })
      .finally(() => setLoading(false));
  }, [subdomain, router]);

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-zinc-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col px-6 py-8 max-w-4xl mx-auto w-full">
      <h1 className="text-2xl font-bold mb-8" style={{ color: primaryColour }}>
        Dashboard
      </h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6 text-sm">
          {error}
        </div>
      )}

      {/* Quick links */}
      <div className="flex gap-3 mb-8 flex-wrap">
        {[
          { href: "/my-memberships", label: "My Memberships" },
          { href: "/events", label: "Events" },
          { href: "/profile", label: "Profile" },
        ].map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className="px-4 py-2 rounded-lg text-sm font-medium text-white"
            style={{ backgroundColor: primaryColour }}
          >
            {label}
          </Link>
        ))}
      </div>

      {/* Active Memberships */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3 text-zinc-800 dark:text-zinc-200">
          Active Memberships
        </h2>

        {data?.active_memberships.length === 0 ? (
          <div className="border border-dashed border-zinc-300 dark:border-zinc-600 rounded-lg p-6 text-center text-zinc-500">
            <p className="mb-3">No active memberships.</p>
            <Link
              href="/join"
              className="text-sm font-medium underline"
              style={{ color: primaryColour }}
            >
              Browse membership options
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {data?.active_memberships.map((m) => (
              <div
                key={m.id}
                className="border border-zinc-200 dark:border-zinc-700 rounded-lg p-4 bg-white dark:bg-zinc-800 flex items-center justify-between"
              >
                <div>
                  <p className="font-medium text-zinc-900 dark:text-zinc-100">
                    {m.membership_type_name}
                  </p>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-0.5">
                    Renews {m.end_date ?? "—"}
                  </p>
                </div>
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                  Active
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Upcoming Registered Events */}
      <section>
        <h2 className="text-lg font-semibold mb-3 text-zinc-800 dark:text-zinc-200">
          Upcoming Events
        </h2>

        {data?.upcoming_events.length === 0 ? (
          <div className="border border-dashed border-zinc-300 dark:border-zinc-600 rounded-lg p-6 text-center text-zinc-500">
            <p className="mb-3">No upcoming events registered.</p>
            <Link
              href="/events"
              className="text-sm font-medium underline"
              style={{ color: primaryColour }}
            >
              Browse events
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {data?.upcoming_events.map((ev) => (
              <Link
                key={ev.id}
                href={`/events/${ev.id}`}
                className="block border border-zinc-200 dark:border-zinc-700 rounded-lg p-4 bg-white dark:bg-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-500 transition-colors"
              >
                <p className="font-medium text-zinc-900 dark:text-zinc-100">
                  {ev.title}
                </p>
                <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-0.5">
                  {formatDateTime(ev.date_time)}
                </p>
                {ev.location && (
                  <p className="text-sm text-zinc-400 dark:text-zinc-500">
                    {ev.location}
                  </p>
                )}
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useBrandKit } from "@/hooks/useBrandKit";
import { apiAuthGet, apiAuthPost, ApiError } from "@/lib/api";
import { getStoredTokens } from "@/lib/auth";

interface Registration {
  id: number;
  event: number;
  event_title: string;
  event_date_time: string;
  event_location: string;
  registered_at: string;
}

export default function MyEventsPage() {
  const router = useRouter();
  const { brandKit, subdomain } = useBrandKit();

  const [registrations, setRegistrations] = useState<Registration[]>([]);
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
    apiAuthGet("/api/events/my-registrations/", tokens.access, subdomain)
      .then((data) => setRegistrations(data))
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          router.push("/login");
        } else {
          setError("Failed to load registrations.");
        }
      })
      .finally(() => setLoading(false));
  }, [subdomain, router]);

  async function handleCancel(eventId: number) {
    const tokens = getStoredTokens();
    if (!tokens?.access || !subdomain) return;
    try {
      await apiAuthPost(`/api/events/${eventId}/unregister/`, {}, tokens.access, subdomain);
      setRegistrations((prev) => prev.filter((r) => r.event !== eventId));
    } catch {
      setError("Failed to cancel registration.");
    }
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

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-zinc-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col px-6 py-8 max-w-4xl mx-auto w-full">
      <h1 className="text-2xl font-bold mb-6" style={{ color: primaryColour }}>
        My Registered Events
      </h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded mb-4 text-sm">
          {error}
        </div>
      )}

      {registrations.length === 0 ? (
        <div className="text-center py-12 text-zinc-500">
          <p className="text-lg mb-2">No registrations</p>
          <p className="text-sm">
            Browse{" "}
            <button onClick={() => router.push("/events")} className="underline" style={{ color: primaryColour }}>
              events
            </button>{" "}
            and register for one.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {registrations.map((reg) => (
            <div
              key={reg.id}
              className="border border-zinc-200 dark:border-zinc-700 rounded-lg p-4 bg-white dark:bg-zinc-800 flex items-center justify-between"
            >
              <div
                className="cursor-pointer flex-1"
                onClick={() => router.push(`/events/${reg.event}`)}
              >
                <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">
                  {reg.event_title}
                </h3>
                <p className="text-sm text-zinc-600 dark:text-zinc-400">
                  {formatDateTime(reg.event_date_time)}
                </p>
                {reg.event_location && (
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">
                    {reg.event_location}
                  </p>
                )}
              </div>
              <button
                onClick={() => handleCancel(reg.event)}
                className="ml-4 px-3 py-1.5 text-sm rounded border border-red-300 text-red-700 hover:bg-red-50"
              >
                Cancel
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useBrandKit } from "@/hooks/useBrandKit";
import { apiAuthGet, ApiError } from "@/lib/api";
import { getStoredTokens } from "@/lib/auth";
import EventCalendarList, { type CalendarEvent } from "@/components/EventCalendarList";

export default function MemberEventsPage() {
  const router = useRouter();
  const { brandKit, subdomain } = useBrandKit();

  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";
  const accentColour = brandKit?.accent_colour ?? "#ff6d00";

  useEffect(() => {
    if (!subdomain) return;
    const tokens = getStoredTokens();
    if (!tokens?.access) {
      router.push("/login");
      return;
    }
    apiAuthGet("/api/events/mine/", tokens.access, subdomain)
      .then((data) => setEvents(data))
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          router.push("/login");
        } else {
          setError("Failed to load events.");
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
    <div className="flex flex-1 flex-col px-6 py-8 max-w-5xl mx-auto w-full">
      <h1 className="text-2xl font-bold mb-8" style={{ color: primaryColour }}>
        Events
      </h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6 text-sm">
          {error}
        </div>
      )}

      <EventCalendarList
        events={events}
        primaryColour={primaryColour}
        accentColour={accentColour}
      />
    </div>
  );
}

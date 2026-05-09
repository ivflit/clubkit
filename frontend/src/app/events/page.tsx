"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useBrandKit } from "@/hooks/useBrandKit";
import { apiGet } from "@/lib/api";

interface PublicEvent {
  id: number;
  title: string;
  description: string;
  date_time: string;
  location: string;
  visibility: string;
  capacity: number | null;
  status: string;
}

export default function EventsPage() {
  const router = useRouter();
  const { brandKit, subdomain } = useBrandKit();

  const [events, setEvents] = useState<PublicEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";

  useEffect(() => {
    if (!subdomain) return;
    apiGet("/api/events/public/", subdomain)
      .then((data) => setEvents(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [subdomain]);

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
        Events
      </h1>

      {events.length === 0 ? (
        <div className="text-center py-12 text-zinc-500">
          <p className="text-lg mb-2">No upcoming events</p>
          <p className="text-sm">Check back soon for new events.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {events.map((ev) => (
            <div
              key={ev.id}
              onClick={() => router.push(`/events/${ev.id}`)}
              className="border border-zinc-200 dark:border-zinc-700 rounded-lg p-5 hover:shadow-md transition-shadow cursor-pointer bg-white dark:bg-zinc-800"
            >
              <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 mb-2">{ev.title}</h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-1">{formatDateTime(ev.date_time)}</p>
              {ev.location && (
                <p className="text-sm text-zinc-500 dark:text-zinc-400">{ev.location}</p>
              )}
              {ev.capacity && (
                <p className="text-xs text-zinc-400 mt-2">Capacity: {ev.capacity}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

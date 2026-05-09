"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useBrandKit } from "@/hooks/useBrandKit";
import { apiGet, apiAuthGet, ApiError } from "@/lib/api";
import { getStoredTokens } from "@/lib/auth";

interface EventDetail {
  id: number;
  title: string;
  description: string;
  date_time: string;
  location: string;
  visibility: string;
  capacity: number | null;
  status: string;
}

export default function EventDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const { brandKit, subdomain } = useBrandKit();

  const [event, setEvent] = useState<EventDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";

  useEffect(() => {
    if (!subdomain || !id) return;

    async function loadEvent() {
      try {
        const tokens = getStoredTokens();
        let data: EventDetail;
        if (tokens?.access) {
          data = await apiAuthGet(`/api/events/detail/${id}/`, tokens.access, subdomain!);
        } else {
          data = await apiGet(`/api/events/detail/${id}/`, subdomain!);
        }
        setEvent(data);
      } catch (err) {
        if (err instanceof ApiError) {
          if (err.status === 403) {
            setError("This event is for members only. Please log in with an active membership to view it.");
          } else if (err.status === 404) {
            setError("Event not found.");
          } else {
            setError("Failed to load event.");
          }
        } else {
          setError("Failed to load event.");
        }
      } finally {
        setLoading(false);
      }
    }

    loadEvent();
  }, [subdomain, id]);

  function formatDateTime(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleDateString("en-GB", {
      weekday: "long",
      day: "numeric",
      month: "long",
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

  if (error) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-12">
        <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg text-sm max-w-md text-center">
          {error}
        </div>
      </div>
    );
  }

  if (!event) return null;

  return (
    <div className="flex flex-1 flex-col px-6 py-8 max-w-3xl mx-auto w-full">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2" style={{ color: primaryColour }}>
          {event.title}
        </h1>

        <div className="flex flex-wrap gap-4 text-sm text-zinc-600 dark:text-zinc-400 mb-4">
          <span>{formatDateTime(event.date_time)}</span>
          {event.location && <span>{event.location}</span>}
          {event.capacity && <span>Capacity: {event.capacity}</span>}
        </div>

        {event.status === "cancelled" && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded mb-4 text-sm font-medium">
            This event has been cancelled.
          </div>
        )}

        {event.visibility === "members_only" && (
          <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 mb-4">
            Members Only
          </span>
        )}
      </div>

      {event.description && (
        <div
          className="prose prose-zinc dark:prose-invert max-w-none"
          dangerouslySetInnerHTML={{ __html: event.description }}
        />
      )}
    </div>
  );
}

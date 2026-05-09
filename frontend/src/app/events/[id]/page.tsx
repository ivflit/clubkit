"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useBrandKit } from "@/hooks/useBrandKit";
import { apiGet, apiAuthGet, apiAuthPost, ApiError } from "@/lib/api";
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
  spots_remaining: number | null;
  is_registered: boolean;
  registration_count: number;
}

export default function EventDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const { brandKit, subdomain } = useBrandKit();

  const [event, setEvent] = useState<EventDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState("");

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";
  const tokens = getStoredTokens();
  const isLoggedIn = !!tokens?.access;

  useEffect(() => {
    if (!subdomain || !id) return;

    async function loadEvent() {
      try {
        const tkns = getStoredTokens();
        let data: EventDetail;
        if (tkns?.access) {
          data = await apiAuthGet(`/api/events/detail/${id}/`, tkns.access, subdomain!);
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

  async function handleRegister() {
    if (!tokens?.access || !subdomain) return;
    setActionLoading(true);
    setActionMsg("");
    try {
      await apiAuthPost(`/api/events/${id}/register/`, {}, tokens.access, subdomain);
      // Reload event to get updated registration state
      const data = await apiAuthGet(`/api/events/detail/${id}/`, tokens.access, subdomain);
      setEvent(data);
      setActionMsg("Registered successfully!");
    } catch (err) {
      if (err instanceof ApiError) {
        const detail = (err.data as { detail?: string })?.detail ?? "Registration failed.";
        setActionMsg(detail);
      } else {
        setActionMsg("Registration failed.");
      }
    } finally {
      setActionLoading(false);
    }
  }

  async function handleUnregister() {
    if (!tokens?.access || !subdomain) return;
    setActionLoading(true);
    setActionMsg("");
    try {
      await apiAuthPost(`/api/events/${id}/unregister/`, {}, tokens.access, subdomain);
      const data = await apiAuthGet(`/api/events/detail/${id}/`, tokens.access, subdomain);
      setEvent(data);
      setActionMsg("Registration cancelled.");
    } catch (err) {
      if (err instanceof ApiError) {
        const detail = (err.data as { detail?: string })?.detail ?? "Cancellation failed.";
        setActionMsg(detail);
      } else {
        setActionMsg("Cancellation failed.");
      }
    } finally {
      setActionLoading(false);
    }
  }

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

  const canRegister = isLoggedIn && event.status === "upcoming" && !event.is_registered &&
    (event.spots_remaining === null || event.spots_remaining > 0);

  return (
    <div className="flex flex-1 flex-col px-6 py-8 max-w-3xl mx-auto w-full">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2" style={{ color: primaryColour }}>
          {event.title}
        </h1>

        <div className="flex flex-wrap gap-4 text-sm text-zinc-600 dark:text-zinc-400 mb-4">
          <span>{formatDateTime(event.date_time)}</span>
          {event.location && <span>{event.location}</span>}
          {event.capacity !== null && (
            <span>
              {event.spots_remaining !== null
                ? `${event.spots_remaining} / ${event.capacity} spots remaining`
                : `Capacity: ${event.capacity}`}
            </span>
          )}
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

        {/* Registration section */}
        {event.status === "upcoming" && (
          <div className="border border-zinc-200 dark:border-zinc-700 rounded-lg p-4 mb-4 bg-white dark:bg-zinc-800">
            {event.is_registered ? (
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-green-700 dark:text-green-400">
                  You are registered for this event
                </span>
                <button
                  onClick={handleUnregister}
                  disabled={actionLoading}
                  className="px-4 py-2 text-sm rounded-lg border border-red-300 text-red-700 hover:bg-red-50 disabled:opacity-50"
                >
                  {actionLoading ? "Cancelling..." : "Cancel Registration"}
                </button>
              </div>
            ) : canRegister ? (
              <div className="flex items-center justify-between">
                <span className="text-sm text-zinc-600 dark:text-zinc-400">
                  {event.spots_remaining !== null && event.spots_remaining === 0
                    ? "This event is full."
                    : "Register to attend this event."}
                </span>
                <button
                  onClick={handleRegister}
                  disabled={actionLoading}
                  className="px-4 py-2 text-sm rounded-lg text-white disabled:opacity-50"
                  style={{ backgroundColor: primaryColour }}
                >
                  {actionLoading ? "Registering..." : "Register"}
                </button>
              </div>
            ) : event.spots_remaining !== null && event.spots_remaining === 0 ? (
              <span className="text-sm text-zinc-500">This event is full.</span>
            ) : !isLoggedIn ? (
              <span className="text-sm text-zinc-500">Log in to register for this event.</span>
            ) : null}

            {actionMsg && (
              <p className="text-sm mt-2 text-zinc-600 dark:text-zinc-400">{actionMsg}</p>
            )}
          </div>
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

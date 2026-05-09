"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useBrandKit } from "@/hooks/useBrandKit";
import { getStoredTokens, fetchMe } from "@/lib/auth";
import { apiAuthGet, apiAuthPost, apiAuthPatch, ApiError } from "@/lib/api";

interface Event {
  id: number;
  title: string;
  description: string;
  date_time: string;
  location: string;
  visibility: "public" | "members_only";
  capacity: number | null;
  status: "upcoming" | "past" | "cancelled";
  created_by: number | null;
  created_by_email: string;
  created_at: string;
  updated_at: string;
}

type EventFormData = {
  title: string;
  description: string;
  date_time: string;
  location: string;
  visibility: "public" | "members_only";
  capacity: string;
};

const EMPTY_FORM: EventFormData = {
  title: "",
  description: "",
  date_time: "",
  location: "",
  visibility: "public",
  capacity: "",
};

const STATUS_STYLES: Record<string, string> = {
  upcoming: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  past: "bg-zinc-100 text-zinc-500 dark:bg-zinc-700 dark:text-zinc-400",
  cancelled: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
};

export default function AdminEventsPage() {
  const router = useRouter();
  const { brandKit, subdomain } = useBrandKit();

  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<EventFormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";

  function getToken(): string | null {
    const tokens = getStoredTokens();
    return tokens?.access ?? null;
  }

  async function loadEvents() {
    const token = getToken();
    if (!token || !subdomain) return;
    try {
      const data = await apiAuthGet("/api/events/", token, subdomain);
      setEvents(data);
    } catch {
      setError("Failed to load events.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!subdomain) return;
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }
    fetchMe(subdomain)
      .then((user) => {
        if (user.role !== "admin") {
          router.push("/");
          return;
        }
        loadEvents();
      })
      .catch(() => router.push("/login"));
  }, [subdomain]);

  function openCreate() {
    setForm(EMPTY_FORM);
    setEditingId(null);
    setFormError("");
    setShowForm(true);
  }

  function openEdit(ev: Event) {
    setForm({
      title: ev.title,
      description: ev.description,
      date_time: ev.date_time.slice(0, 16),
      location: ev.location,
      visibility: ev.visibility,
      capacity: ev.capacity?.toString() ?? "",
    });
    setEditingId(ev.id);
    setFormError("");
    setShowForm(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token || !subdomain) return;
    setSaving(true);
    setFormError("");

    const payload: Record<string, unknown> = {
      title: form.title,
      description: form.description,
      date_time: form.date_time,
      location: form.location,
      visibility: form.visibility,
      capacity: form.capacity ? parseInt(form.capacity, 10) : null,
    };

    try {
      if (editingId) {
        await apiAuthPatch(`/api/events/${editingId}/`, payload, token, subdomain);
      } else {
        await apiAuthPost("/api/events/", payload, token, subdomain);
      }
      setShowForm(false);
      setForm(EMPTY_FORM);
      setEditingId(null);
      await loadEvents();
    } catch (err) {
      if (err instanceof ApiError) {
        const messages = Object.values(err.data).flat().join(" ");
        setFormError(messages || "Failed to save.");
      } else {
        setFormError("Something went wrong.");
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleCancel(id: number) {
    const token = getToken();
    if (!token || !subdomain) return;
    try {
      await apiAuthPost(`/api/events/${id}/cancel/`, {}, token, subdomain);
      await loadEvents();
    } catch {
      setError("Failed to cancel event.");
    }
  }

  function formatDateTime(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleDateString("en-GB", {
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
    <div className="flex flex-1 flex-col px-6 py-8 max-w-5xl mx-auto w-full">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold" style={{ color: primaryColour }}>
          Events
        </h1>
        <button
          onClick={openCreate}
          className="rounded-lg px-4 py-2 text-sm font-medium text-white"
          style={{ backgroundColor: primaryColour }}
        >
          + New Event
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4 text-sm">
          {error}
        </div>
      )}

      {showForm && (
        <div className="border border-zinc-300 dark:border-zinc-600 rounded-lg p-6 mb-6 bg-white dark:bg-zinc-800">
          <h2 className="text-lg font-semibold mb-4" style={{ color: primaryColour }}>
            {editingId ? "Edit Event" : "Create Event"}
          </h2>

          {formError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4 text-sm">
              {formError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Title</label>
              <input
                required
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-900 dark:border-zinc-600 dark:text-white"
                style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Description (supports HTML for rich content)
              </label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={6}
                className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 font-mono dark:bg-zinc-900 dark:border-zinc-600 dark:text-white"
                style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
                placeholder="<h2>Schedule</h2><p>Details about the event...</p>"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Date &amp; Time</label>
                <input
                  type="datetime-local"
                  required
                  value={form.date_time}
                  onChange={(e) => setForm({ ...form, date_time: e.target.value })}
                  className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-900 dark:border-zinc-600 dark:text-white"
                  style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Location</label>
                <input
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                  className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-900 dark:border-zinc-600 dark:text-white"
                  style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
                  placeholder="e.g. Main Pitch"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Visibility</label>
                <select
                  value={form.visibility}
                  onChange={(e) => setForm({ ...form, visibility: e.target.value as "public" | "members_only" })}
                  className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-900 dark:border-zinc-600 dark:text-white"
                  style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
                >
                  <option value="public">Public</option>
                  <option value="members_only">Members Only</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Capacity (optional)</label>
                <input
                  type="number"
                  min="1"
                  value={form.capacity}
                  onChange={(e) => setForm({ ...form, capacity: e.target.value })}
                  className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-900 dark:border-zinc-600 dark:text-white"
                  style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
                  placeholder="Leave blank for unlimited"
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={saving}
                className="rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                style={{ backgroundColor: primaryColour }}
              >
                {saving ? "Saving..." : editingId ? "Update" : "Create"}
              </button>
              <button
                type="button"
                onClick={() => { setShowForm(false); setEditingId(null); }}
                className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-600 border border-zinc-300 hover:bg-zinc-50 dark:text-zinc-300 dark:border-zinc-600 dark:hover:bg-zinc-700"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {events.length === 0 ? (
        <div className="text-center py-12 text-zinc-500">
          <p className="text-lg mb-2">No events yet</p>
          <p className="text-sm">Create your first event to let members know what&apos;s happening.</p>
        </div>
      ) : (
        <div className="border border-zinc-200 dark:border-zinc-700 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-zinc-50 dark:bg-zinc-800 text-left">
              <tr>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Title</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Date</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Location</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Visibility</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Capacity</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Status</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
              {events.map((ev) => (
                <tr key={ev.id} className={ev.status === "cancelled" ? "opacity-50" : ""}>
                  <td className="px-4 py-3 text-zinc-900 dark:text-zinc-100 font-medium">{ev.title}</td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">{formatDateTime(ev.date_time)}</td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">{ev.location || "—"}</td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">
                    {ev.visibility === "public" ? "Public" : "Members only"}
                  </td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">{ev.capacity ?? "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${STATUS_STYLES[ev.status] ?? ""}`}>
                      {ev.status.charAt(0).toUpperCase() + ev.status.slice(1)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => openEdit(ev)}
                        className="text-sm font-medium hover:underline"
                        style={{ color: primaryColour }}
                      >
                        Edit
                      </button>
                      {ev.status === "upcoming" && (
                        <button
                          onClick={() => handleCancel(ev.id)}
                          className="text-sm font-medium text-red-600 hover:underline"
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

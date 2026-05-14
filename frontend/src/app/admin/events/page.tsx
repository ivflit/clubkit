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
  series_id: number | null;
  series_title: string | null;
  created_by: number | null;
  created_by_email: string;
  created_at: string;
  updated_at: string;
  registration_count: number;
}

interface Series {
  id: number;
  title: string;
  recurrence_pattern: string;
  occurrence_count: number;
}

type EventFormData = {
  title: string;
  description: string;
  date_time: string;
  location: string;
  visibility: "public" | "members_only";
  capacity: string;
};

type RecurringFormData = {
  title: string;
  description: string;
  location: string;
  visibility: "public" | "members_only";
  capacity: string;
  recurrence_pattern: "weekly" | "fortnightly";
  start_date: string;
  end_date: string;
  time: string;
};

const EMPTY_FORM: EventFormData = {
  title: "",
  description: "",
  date_time: "",
  location: "",
  visibility: "public",
  capacity: "",
};

const EMPTY_RECURRING_FORM: RecurringFormData = {
  title: "",
  description: "",
  location: "",
  visibility: "public",
  capacity: "",
  recurrence_pattern: "weekly",
  start_date: "",
  end_date: "",
  time: "18:00",
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
  const [series, setSeries] = useState<Series[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");

  const [formMode, setFormMode] = useState<"none" | "single" | "recurring">("none");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<EventFormData>(EMPTY_FORM);
  const [recurringForm, setRecurringForm] = useState<RecurringFormData>(EMPTY_RECURRING_FORM);
  const [saving, setSaving] = useState(false);

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";

  function getToken(): string | null {
    const tokens = getStoredTokens();
    return tokens?.access ?? null;
  }

  async function loadData() {
    const token = getToken();
    if (!token || !subdomain) return;
    try {
      const [eventsData, seriesData] = await Promise.all([
        apiAuthGet("/api/events/", token, subdomain),
        apiAuthGet("/api/events/series/", token, subdomain),
      ]);
      setEvents(eventsData);
      setSeries(seriesData);
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
        loadData();
      })
      .catch(() => router.push("/login"));
  }, [subdomain]);

  function openCreate() {
    setForm(EMPTY_FORM);
    setEditingId(null);
    setFormError("");
    setFormMode("single");
  }

  function openRecurring() {
    setRecurringForm(EMPTY_RECURRING_FORM);
    setFormError("");
    setFormMode("recurring");
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
    setFormMode("single");
  }

  function closeForm() {
    setFormMode("none");
    setEditingId(null);
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
      closeForm();
      await loadData();
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

  async function handleRecurringSubmit(e: FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token || !subdomain) return;
    setSaving(true);
    setFormError("");

    const payload: Record<string, unknown> = {
      title: recurringForm.title,
      description: recurringForm.description,
      location: recurringForm.location,
      visibility: recurringForm.visibility,
      capacity: recurringForm.capacity ? parseInt(recurringForm.capacity, 10) : null,
      recurrence_pattern: recurringForm.recurrence_pattern,
      start_date: recurringForm.start_date,
      end_date: recurringForm.end_date,
      time: recurringForm.time,
    };

    try {
      await apiAuthPost("/api/events/series/", payload, token, subdomain);
      closeForm();
      await loadData();
    } catch (err) {
      if (err instanceof ApiError) {
        const messages = Object.values(err.data).flat().join(" ");
        setFormError(messages || "Failed to create recurring events.");
      } else {
        setFormError("Something went wrong.");
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleCancelEvent(id: number) {
    const token = getToken();
    if (!token || !subdomain) return;
    try {
      await apiAuthPost(`/api/events/${id}/cancel/`, {}, token, subdomain);
      await loadData();
    } catch {
      setError("Failed to cancel event.");
    }
  }

  async function handleCancelSeries(seriesId: number) {
    const token = getToken();
    if (!token || !subdomain) return;
    if (!confirm("Cancel all future occurrences of this series?")) return;
    try {
      await apiAuthPost(`/api/events/series/${seriesId}/cancel/`, {}, token, subdomain);
      await loadData();
    } catch {
      setError("Failed to cancel series.");
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

  const inputCls = "w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-900 dark:border-zinc-600 dark:text-white";

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
        <div className="flex gap-2">
          <button
            onClick={openCreate}
            className="rounded-lg px-4 py-2 text-sm font-medium text-white"
            style={{ backgroundColor: primaryColour }}
          >
            + New Event
          </button>
          <button
            onClick={openRecurring}
            className="rounded-lg px-4 py-2 text-sm font-medium border"
            style={{ color: primaryColour, borderColor: primaryColour }}
          >
            + Recurring
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4 text-sm">
          {error}
        </div>
      )}

      {/* Single event form */}
      {formMode === "single" && (
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
              <input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className={inputCls} />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Description (HTML)</label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={5}
                className={`${inputCls} font-mono`}
                placeholder="<p>Details...</p>"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Date &amp; Time</label>
                <input type="datetime-local" required value={form.date_time} onChange={(e) => setForm({ ...form, date_time: e.target.value })} className={inputCls} />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Location</label>
                <input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} className={inputCls} placeholder="e.g. Main Pitch" />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Visibility</label>
                <select value={form.visibility} onChange={(e) => setForm({ ...form, visibility: e.target.value as "public" | "members_only" })} className={inputCls}>
                  <option value="public">Public</option>
                  <option value="members_only">Members Only</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Capacity (optional)</label>
                <input type="number" min="1" value={form.capacity} onChange={(e) => setForm({ ...form, capacity: e.target.value })} className={inputCls} placeholder="Unlimited" />
              </div>
            </div>
            <div className="flex gap-3">
              <button type="submit" disabled={saving} className="rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50" style={{ backgroundColor: primaryColour }}>
                {saving ? "Saving..." : editingId ? "Update" : "Create"}
              </button>
              <button type="button" onClick={closeForm} className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-600 border border-zinc-300 hover:bg-zinc-50 dark:text-zinc-300 dark:border-zinc-600">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Recurring event form */}
      {formMode === "recurring" && (
        <div className="border border-zinc-300 dark:border-zinc-600 rounded-lg p-6 mb-6 bg-white dark:bg-zinc-800">
          <h2 className="text-lg font-semibold mb-4" style={{ color: primaryColour }}>
            Create Recurring Events
          </h2>
          {formError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4 text-sm">
              {formError}
            </div>
          )}
          <form onSubmit={handleRecurringSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Series Title</label>
              <input required value={recurringForm.title} onChange={(e) => setRecurringForm({ ...recurringForm, title: e.target.value })} className={inputCls} placeholder="e.g. Tuesday Training" />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Description (HTML, optional)</label>
              <textarea
                value={recurringForm.description}
                onChange={(e) => setRecurringForm({ ...recurringForm, description: e.target.value })}
                rows={3}
                className={`${inputCls} font-mono`}
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Location</label>
                <input value={recurringForm.location} onChange={(e) => setRecurringForm({ ...recurringForm, location: e.target.value })} className={inputCls} placeholder="e.g. Main Pitch" />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Time</label>
                <input type="time" required value={recurringForm.time} onChange={(e) => setRecurringForm({ ...recurringForm, time: e.target.value })} className={inputCls} />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Recurrence</label>
                <select value={recurringForm.recurrence_pattern} onChange={(e) => setRecurringForm({ ...recurringForm, recurrence_pattern: e.target.value as "weekly" | "fortnightly" })} className={inputCls}>
                  <option value="weekly">Weekly</option>
                  <option value="fortnightly">Fortnightly</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Start Date</label>
                <input type="date" required value={recurringForm.start_date} onChange={(e) => setRecurringForm({ ...recurringForm, start_date: e.target.value })} className={inputCls} />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">End Date</label>
                <input type="date" required value={recurringForm.end_date} onChange={(e) => setRecurringForm({ ...recurringForm, end_date: e.target.value })} className={inputCls} />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Visibility</label>
                <select value={recurringForm.visibility} onChange={(e) => setRecurringForm({ ...recurringForm, visibility: e.target.value as "public" | "members_only" })} className={inputCls}>
                  <option value="public">Public</option>
                  <option value="members_only">Members Only</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Capacity (optional)</label>
                <input type="number" min="1" value={recurringForm.capacity} onChange={(e) => setRecurringForm({ ...recurringForm, capacity: e.target.value })} className={inputCls} placeholder="Unlimited" />
              </div>
            </div>
            <div className="flex gap-3">
              <button type="submit" disabled={saving} className="rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50" style={{ backgroundColor: primaryColour }}>
                {saving ? "Creating..." : "Create Series"}
              </button>
              <button type="button" onClick={closeForm} className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-600 border border-zinc-300 hover:bg-zinc-50 dark:text-zinc-300 dark:border-zinc-600">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Series summary */}
      {series.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-zinc-500 uppercase tracking-wide mb-2">Recurring Series</h2>
          <div className="flex flex-wrap gap-2">
            {series.map((s) => (
              <div key={s.id} className="flex items-center gap-2 border border-zinc-200 dark:border-zinc-700 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-zinc-800">
                <span className="font-medium text-zinc-800 dark:text-zinc-200">{s.title}</span>
                <span className="text-zinc-400">·</span>
                <span className="text-zinc-500 capitalize">{s.recurrence_pattern}</span>
                <span className="text-zinc-400">·</span>
                <span className="text-zinc-500">{s.occurrence_count} events</span>
                <button
                  onClick={() => handleCancelSeries(s.id)}
                  className="ml-1 text-xs text-red-500 hover:underline"
                >
                  Cancel all future
                </button>
              </div>
            ))}
          </div>
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
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Registered</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Status</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
              {events.map((ev) => (
                <tr key={ev.id} className={ev.status === "cancelled" ? "opacity-50" : ""}>
                  <td className="px-4 py-3">
                    <p className="font-medium text-zinc-900 dark:text-zinc-100">{ev.title}</p>
                    {ev.series_title && (
                      <p className="text-xs text-zinc-400 mt-0.5">Part of: {ev.series_title}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">{formatDateTime(ev.date_time)}</td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">{ev.location || "—"}</td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">
                    {ev.visibility === "public" ? "Public" : "Members only"}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => router.push(`/admin/events/${ev.id}/registrations`)}
                      className="text-sm hover:underline"
                      style={{ color: primaryColour }}
                    >
                      {ev.registration_count}
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${STATUS_STYLES[ev.status] ?? ""}`}>
                      {ev.status.charAt(0).toUpperCase() + ev.status.slice(1)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button onClick={() => openEdit(ev)} className="text-sm font-medium hover:underline" style={{ color: primaryColour }}>
                        Edit
                      </button>
                      {ev.status === "upcoming" && (
                        <button onClick={() => handleCancelEvent(ev.id)} className="text-sm font-medium text-red-600 hover:underline">
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

"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useBrandKit } from "@/hooks/useBrandKit";
import { getStoredTokens, fetchMe } from "@/lib/auth";
import { apiAuthGet, apiAuthPost, apiAuthPatch, ApiError } from "@/lib/api";

interface MembershipType {
  id: number;
  name: string;
  description: string;
  price: string;
  billing_frequency: "monthly" | "annual";
  renewal_mode: "rolling" | "one_off";
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

type FormData = {
  name: string;
  description: string;
  price: string;
  billing_frequency: "monthly" | "annual";
  renewal_mode: "rolling" | "one_off";
};

const EMPTY_FORM: FormData = {
  name: "",
  description: "",
  price: "",
  billing_frequency: "monthly",
  renewal_mode: "rolling",
};

export default function AdminMembershipTypesPage() {
  const router = useRouter();
  const { brandKit, subdomain } = useBrandKit();

  const [types, setTypes] = useState<MembershipType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";

  function getToken(): string | null {
    const tokens = getStoredTokens();
    return tokens?.access ?? null;
  }

  async function loadTypes() {
    const token = getToken();
    if (!token || !subdomain) return;
    try {
      const data = await apiAuthGet("/api/membership-types/", token, subdomain);
      setTypes(data);
    } catch {
      setError("Failed to load membership types.");
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
        loadTypes();
      })
      .catch(() => router.push("/login"));
  }, [subdomain]);

  function openCreate() {
    setForm(EMPTY_FORM);
    setEditingId(null);
    setFormError("");
    setShowForm(true);
  }

  function openEdit(mt: MembershipType) {
    setForm({
      name: mt.name,
      description: mt.description,
      price: mt.price,
      billing_frequency: mt.billing_frequency,
      renewal_mode: mt.renewal_mode,
    });
    setEditingId(mt.id);
    setFormError("");
    setShowForm(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token || !subdomain) return;
    setSaving(true);
    setFormError("");

    try {
      if (editingId) {
        await apiAuthPatch(`/api/membership-types/${editingId}/`, form as unknown as Record<string, unknown>, token, subdomain);
      } else {
        await apiAuthPost("/api/membership-types/", form as unknown as Record<string, unknown>, token, subdomain);
      }
      setShowForm(false);
      setForm(EMPTY_FORM);
      setEditingId(null);
      await loadTypes();
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

  async function handleDeactivate(id: number) {
    const token = getToken();
    if (!token || !subdomain) return;
    try {
      await apiAuthPost(`/api/membership-types/${id}/deactivate/`, {}, token, subdomain);
      await loadTypes();
    } catch {
      setError("Failed to deactivate membership type.");
    }
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
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold" style={{ color: primaryColour }}>
          Membership Types
        </h1>
        <button
          onClick={openCreate}
          className="rounded-lg px-4 py-2 text-sm font-medium text-white"
          style={{ backgroundColor: primaryColour }}
        >
          + New Type
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4 text-sm">
          {error}
        </div>
      )}

      {/* Form modal */}
      {showForm && (
        <div className="border border-zinc-300 dark:border-zinc-600 rounded-lg p-6 mb-6 bg-white dark:bg-zinc-800">
          <h2 className="text-lg font-semibold mb-4" style={{ color: primaryColour }}>
            {editingId ? "Edit Membership Type" : "Create Membership Type"}
          </h2>

          {formError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4 text-sm">
              {formError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Name</label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-900 dark:border-zinc-600 dark:text-white"
                style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Description</label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={3}
                className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-900 dark:border-zinc-600 dark:text-white"
                style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Price</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={form.price}
                  onChange={(e) => setForm({ ...form, price: e.target.value })}
                  className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-900 dark:border-zinc-600 dark:text-white"
                  style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Billing Frequency</label>
                <select
                  value={form.billing_frequency}
                  onChange={(e) => setForm({ ...form, billing_frequency: e.target.value as "monthly" | "annual" })}
                  className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-900 dark:border-zinc-600 dark:text-white"
                  style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
                >
                  <option value="monthly">Monthly</option>
                  <option value="annual">Annual</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Renewal Mode</label>
                <select
                  value={form.renewal_mode}
                  onChange={(e) => setForm({ ...form, renewal_mode: e.target.value as "rolling" | "one_off" })}
                  className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-900 dark:border-zinc-600 dark:text-white"
                  style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
                >
                  <option value="rolling">Rolling (auto-renew)</option>
                  <option value="one_off">One-off (expires)</option>
                </select>
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

      {/* Table */}
      {types.length === 0 ? (
        <div className="text-center py-12 text-zinc-500">
          <p className="text-lg mb-2">No membership types yet</p>
          <p className="text-sm">Create your first membership type to start accepting members.</p>
        </div>
      ) : (
        <div className="border border-zinc-200 dark:border-zinc-700 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-zinc-50 dark:bg-zinc-800 text-left">
              <tr>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Name</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Price</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Billing</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Renewal</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Status</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
              {types.map((mt) => (
                <tr key={mt.id} className={!mt.is_active ? "opacity-50" : ""}>
                  <td className="px-4 py-3 text-zinc-900 dark:text-zinc-100 font-medium">{mt.name}</td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">&pound;{mt.price}</td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300 capitalize">{mt.billing_frequency}</td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">
                    {mt.renewal_mode === "rolling" ? "Rolling" : "One-off"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                        mt.is_active
                          ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                          : "bg-zinc-100 text-zinc-500 dark:bg-zinc-700 dark:text-zinc-400"
                      }`}
                    >
                      {mt.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => openEdit(mt)}
                        className="text-sm font-medium hover:underline"
                        style={{ color: primaryColour }}
                      >
                        Edit
                      </button>
                      {mt.is_active && (
                        <button
                          onClick={() => handleDeactivate(mt.id)}
                          className="text-sm font-medium text-red-600 hover:underline"
                        >
                          Deactivate
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

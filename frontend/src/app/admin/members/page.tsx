"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useBrandKit } from "@/hooks/useBrandKit";
import { getStoredTokens, fetchMe } from "@/lib/auth";
import { apiAuthGet, apiAuthPost, ApiError } from "@/lib/api";

interface Membership {
  id: number;
  owner: number;
  owner_email: string;
  membership_type: number;
  membership_type_name: string;
  status: "active" | "lapsed" | "cancelled";
  start_date: string;
  end_date: string | null;
  created_at: string;
  updated_at: string;
}

const STATUS_STYLES: Record<string, string> = {
  active: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  lapsed: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  cancelled: "bg-zinc-100 text-zinc-500 dark:bg-zinc-700 dark:text-zinc-400",
};

const STATUS_OPTIONS = ["all", "active", "lapsed", "cancelled"] as const;

export default function AdminMembersPage() {
  const router = useRouter();
  const { brandKit, subdomain } = useBrandKit();

  const [memberships, setMemberships] = useState<Membership[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";

  function getToken(): string | null {
    const tokens = getStoredTokens();
    return tokens?.access ?? null;
  }

  async function loadMemberships(filter: string) {
    const token = getToken();
    if (!token || !subdomain) return;
    const query = filter !== "all" ? `?status=${filter}` : "";
    try {
      const data = await apiAuthGet(
        `/api/membership-types/memberships/admin/${query}`,
        token,
        subdomain
      );
      setMemberships(data);
    } catch {
      setError("Failed to load memberships.");
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
        loadMemberships(statusFilter);
      })
      .catch(() => router.push("/login"));
  }, [subdomain]);

  useEffect(() => {
    if (!subdomain || loading) return;
    setLoading(true);
    loadMemberships(statusFilter);
  }, [statusFilter]);

  async function handleTransition(id: number, newStatus: string) {
    const token = getToken();
    if (!token || !subdomain) return;
    try {
      await apiAuthPost(
        `/api/membership-types/memberships/${id}/transition/`,
        { status: newStatus },
        token,
        subdomain
      );
      await loadMemberships(statusFilter);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.data?.detail as string || "Failed to update membership.");
      } else {
        setError("Something went wrong.");
      }
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
    <div className="flex flex-1 flex-col px-6 py-8 max-w-5xl mx-auto w-full">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold" style={{ color: primaryColour }}>
          Members
        </h1>
        <div className="flex items-center gap-2">
          <label className="text-sm text-zinc-600 dark:text-zinc-400">Filter:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 dark:bg-zinc-900 dark:border-zinc-600 dark:text-white"
            style={{ "--tw-ring-color": primaryColour } as React.CSSProperties}
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4 text-sm">
          {error}
        </div>
      )}

      {memberships.length === 0 ? (
        <div className="text-center py-12 text-zinc-500">
          <p className="text-lg mb-2">No memberships found</p>
          <p className="text-sm">
            {statusFilter !== "all"
              ? `No ${statusFilter} memberships. Try a different filter.`
              : "No one has purchased a membership yet."}
          </p>
        </div>
      ) : (
        <div className="border border-zinc-200 dark:border-zinc-700 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-zinc-50 dark:bg-zinc-800 text-left">
              <tr>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Member</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Type</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Status</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Start</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">End/Renewal</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
              {memberships.map((m) => (
                <tr key={m.id}>
                  <td className="px-4 py-3 text-zinc-900 dark:text-zinc-100">{m.owner_email}</td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">{m.membership_type_name}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${STATUS_STYLES[m.status]}`}>
                      {m.status.charAt(0).toUpperCase() + m.status.slice(1)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">{m.start_date}</td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">{m.end_date ?? "—"}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      {m.status === "lapsed" && (
                        <button
                          onClick={() => handleTransition(m.id, "active")}
                          className="text-sm font-medium hover:underline"
                          style={{ color: primaryColour }}
                        >
                          Reactivate
                        </button>
                      )}
                      {m.status === "active" && (
                        <button
                          onClick={() => handleTransition(m.id, "lapsed")}
                          className="text-sm font-medium text-yellow-600 hover:underline"
                        >
                          Mark Lapsed
                        </button>
                      )}
                      {(m.status === "active" || m.status === "lapsed") && (
                        <button
                          onClick={() => handleTransition(m.id, "cancelled")}
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

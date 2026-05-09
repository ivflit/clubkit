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

export default function MyMembershipsPage() {
  const router = useRouter();
  const { brandKit, subdomain } = useBrandKit();

  const [memberships, setMemberships] = useState<Membership[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";

  function getToken(): string | null {
    const tokens = getStoredTokens();
    return tokens?.access ?? null;
  }

  async function loadMemberships() {
    const token = getToken();
    if (!token || !subdomain) return;
    try {
      const data = await apiAuthGet("/api/membership-types/memberships/mine/", token, subdomain);
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
      .then(() => loadMemberships())
      .catch(() => router.push("/login"));
  }, [subdomain]);

  async function handleCancel(id: number) {
    const token = getToken();
    if (!token || !subdomain) return;
    if (!confirm("Are you sure you want to cancel this membership?")) return;
    try {
      await apiAuthPost(`/api/membership-types/memberships/${id}/cancel/`, {}, token, subdomain);
      await loadMemberships();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.data?.detail as string || "Failed to cancel membership.");
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
    <div className="flex flex-1 flex-col px-6 py-8 max-w-4xl mx-auto w-full">
      <h1 className="text-2xl font-bold mb-6" style={{ color: primaryColour }}>
        My Memberships
      </h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4 text-sm">
          {error}
        </div>
      )}

      {memberships.length === 0 ? (
        <div className="text-center py-12 text-zinc-500">
          <p className="text-lg mb-2">No memberships yet</p>
          <p className="text-sm mb-4">Browse available membership options and join the club.</p>
          <button
            onClick={() => router.push("/join")}
            className="rounded-lg px-4 py-2 text-sm font-medium text-white"
            style={{ backgroundColor: primaryColour }}
          >
            View Membership Options
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {memberships.map((m) => (
            <div
              key={m.id}
              className="border border-zinc-200 dark:border-zinc-700 rounded-lg p-5 bg-white dark:bg-zinc-800"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                    {m.membership_type_name}
                  </h3>
                  <span
                    className={`inline-block mt-1 px-2 py-0.5 rounded text-xs font-medium ${STATUS_STYLES[m.status]}`}
                  >
                    {m.status.charAt(0).toUpperCase() + m.status.slice(1)}
                  </span>
                </div>
                {m.status === "active" && (
                  <button
                    onClick={() => handleCancel(m.id)}
                    className="text-sm font-medium text-red-600 hover:underline"
                  >
                    Cancel
                  </button>
                )}
              </div>
              <div className="mt-3 grid grid-cols-2 gap-4 text-sm text-zinc-600 dark:text-zinc-400">
                <div>
                  <span className="font-medium text-zinc-700 dark:text-zinc-300">Start date:</span>{" "}
                  {m.start_date}
                </div>
                <div>
                  <span className="font-medium text-zinc-700 dark:text-zinc-300">
                    {m.status === "active" ? "Renewal date:" : "End date:"}
                  </span>{" "}
                  {m.end_date ?? "—"}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

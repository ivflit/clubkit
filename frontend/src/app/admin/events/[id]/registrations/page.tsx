"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useBrandKit } from "@/hooks/useBrandKit";
import { getStoredTokens, fetchMe } from "@/lib/auth";
import { apiAuthGet } from "@/lib/api";

interface Registration {
  id: number;
  user_email: string;
  user_first_name: string;
  user_last_name: string;
  registered_at: string;
}

export default function AdminEventRegistrationsPage() {
  const params = useParams();
  const id = params.id as string;
  const router = useRouter();
  const { brandKit, subdomain } = useBrandKit();

  const [registrations, setRegistrations] = useState<Registration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";

  useEffect(() => {
    if (!subdomain || !id) return;
    const tokens = getStoredTokens();
    if (!tokens?.access) {
      router.push("/login");
      return;
    }
    fetchMe(subdomain)
      .then((user) => {
        if (user.role !== "admin") {
          router.push("/");
          return;
        }
        return apiAuthGet(`/api/events/${id}/registrations/`, tokens.access, subdomain);
      })
      .then((data) => {
        if (data) setRegistrations(data);
      })
      .catch(() => setError("Failed to load registrations."))
      .finally(() => setLoading(false));
  }, [subdomain, id, router]);

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
    <div className="flex flex-1 flex-col px-6 py-8 max-w-4xl mx-auto w-full">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold" style={{ color: primaryColour }}>
          Event Registrations
        </h1>
        <button
          onClick={() => router.push("/admin/events")}
          className="text-sm font-medium hover:underline"
          style={{ color: primaryColour }}
        >
          Back to Events
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded mb-4 text-sm">
          {error}
        </div>
      )}

      {registrations.length === 0 ? (
        <div className="text-center py-12 text-zinc-500">
          <p>No registrations for this event.</p>
        </div>
      ) : (
        <div className="border border-zinc-200 dark:border-zinc-700 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-zinc-50 dark:bg-zinc-800 text-left">
              <tr>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Name</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Email</th>
                <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Registered At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
              {registrations.map((reg) => (
                <tr key={reg.id}>
                  <td className="px-4 py-3 text-zinc-900 dark:text-zinc-100">
                    {reg.user_first_name} {reg.user_last_name}
                  </td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">{reg.user_email}</td>
                  <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">{formatDateTime(reg.registered_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="px-4 py-3 bg-zinc-50 dark:bg-zinc-800 text-sm text-zinc-600 dark:text-zinc-400">
            Total: {registrations.length} registered
          </div>
        </div>
      )}
    </div>
  );
}

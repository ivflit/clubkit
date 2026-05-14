"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getStoredPlatformAdminToken, clearPlatformAdminToken } from "@/lib/platform-admin-auth";
import { getApiBase } from "@/lib/api";

interface Stats {
  total_tenants: number;
  total_users: number;
  total_active_memberships: number;
}

interface TenantRow {
  id: number;
  name: string;
  slug: string;
  status: string;
  plan: string;
  created_at: string;
}

async function platformAdminGet(path: string, token: string) {
  const base = getApiBase();
  const res = await fetch(`${base}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 403 || res.status === 401) throw new Error("unauthorized");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

const PLAN_BADGE: Record<string, string> = {
  free: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300",
  pro: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-200",
};

const STATUS_BADGE: Record<string, string> = {
  active: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200",
  suspended: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200",
};

export default function PlatformAdminDashboard() {
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [tenants, setTenants] = useState<TenantRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getStoredPlatformAdminToken();
    if (!token) {
      router.push("/platform-admin/login");
      return;
    }

    Promise.all([
      platformAdminGet("/api/platform-admin/stats/", token),
      platformAdminGet("/api/platform-admin/tenants/", token),
    ])
      .then(([s, t]) => {
        setStats(s);
        setTenants(t);
      })
      .catch((err) => {
        if (err.message === "unauthorized") {
          clearPlatformAdminToken();
          router.push("/platform-admin/login");
        } else {
          setError("Failed to load dashboard data.");
        }
      })
      .finally(() => setLoading(false));
  }, [router]);

  function handleLogout() {
    clearPlatformAdminToken();
    router.push("/platform-admin/login");
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-zinc-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* Header */}
      <header className="bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-700 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold text-sm">
              CK
            </div>
            <span className="font-semibold text-zinc-900 dark:text-zinc-100">
              Platform Admin
            </span>
          </div>
          <button
            onClick={handleLogout}
            className="text-sm text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
          >
            Log out
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6 text-sm">
            {error}
          </div>
        )}

        {/* Aggregate stats */}
        {stats && (
          <section className="mb-8">
            <h2 className="text-lg font-semibold text-zinc-800 dark:text-zinc-200 mb-4">
              Platform Overview
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <StatCard label="Total Clubs" value={stats.total_tenants} />
              <StatCard label="Total Users" value={stats.total_users} />
              <StatCard label="Active Memberships" value={stats.total_active_memberships} />
            </div>
          </section>
        )}

        {/* Tenant list */}
        <section>
          <h2 className="text-lg font-semibold text-zinc-800 dark:text-zinc-200 mb-4">
            All Clubs ({tenants.length})
          </h2>

          {tenants.length === 0 ? (
            <div className="text-center py-12 text-zinc-500 bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-700">
              <p>No clubs onboarded yet.</p>
            </div>
          ) : (
            <div className="bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-700 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-zinc-50 dark:bg-zinc-800 text-left">
                  <tr>
                    <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Club</th>
                    <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Subdomain</th>
                    <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Status</th>
                    <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Plan</th>
                    <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300">Created</th>
                    <th className="px-4 py-3 font-medium text-zinc-600 dark:text-zinc-300"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
                  {tenants.map((t) => (
                    <tr key={t.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
                      <td className="px-4 py-3 font-medium text-zinc-900 dark:text-zinc-100">
                        {t.name}
                      </td>
                      <td className="px-4 py-3 text-zinc-500 font-mono text-xs">
                        {t.slug}.lvh.me
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${STATUS_BADGE[t.status] ?? ""}`}>
                          {t.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${PLAN_BADGE[t.plan] ?? ""}`}>
                          {t.plan}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-zinc-500">
                        {new Date(t.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3">
                        <Link
                          href={`/platform-admin/tenants/${t.id}`}
                          className="text-indigo-600 hover:text-indigo-800 text-xs font-medium"
                        >
                          View →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-700 px-6 py-5">
      <p className="text-sm text-zinc-500 dark:text-zinc-400">{label}</p>
      <p className="text-3xl font-bold text-zinc-900 dark:text-zinc-100 mt-1">{value}</p>
    </div>
  );
}

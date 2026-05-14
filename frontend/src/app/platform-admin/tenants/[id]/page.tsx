"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, useParams } from "next/navigation";
import { getStoredPlatformAdminToken, clearPlatformAdminToken } from "@/lib/platform-admin-auth";
import { getApiBase } from "@/lib/api";

interface TenantDetail {
  id: number;
  name: string;
  slug: string;
  status: string;
  plan: string;
  created_at: string;
  member_count: number;
  active_memberships: number;
  stripe_connected: boolean;
}

async function platformAdminGet(path: string, token: string) {
  const base = getApiBase();
  const res = await fetch(`${base}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 403 || res.status === 401) throw new Error("unauthorized");
  if (res.status === 404) throw new Error("not_found");
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

export default function TenantDetailPage() {
  const router = useRouter();
  const params = useParams();
  const tenantId = params.id as string;

  const [tenant, setTenant] = useState<TenantDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getStoredPlatformAdminToken();
    if (!token) {
      router.push("/platform-admin/login");
      return;
    }

    platformAdminGet(`/api/platform-admin/tenants/${tenantId}/`, token)
      .then(setTenant)
      .catch((err) => {
        if (err.message === "unauthorized") {
          clearPlatformAdminToken();
          router.push("/platform-admin/login");
        } else if (err.message === "not_found") {
          setError("Club not found.");
        } else {
          setError("Failed to load club details.");
        }
      })
      .finally(() => setLoading(false));
  }, [router, tenantId]);

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
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold text-sm">
            CK
          </div>
          <nav className="flex items-center gap-2 text-sm text-zinc-500">
            <Link href="/platform-admin" className="hover:text-zinc-700 dark:hover:text-zinc-300">
              Platform Admin
            </Link>
            <span>/</span>
            <span className="text-zinc-900 dark:text-zinc-100 font-medium">
              {tenant?.name ?? "Club"}
            </span>
          </nav>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6 text-sm">
            {error}
          </div>
        )}

        {tenant && (
          <>
            {/* Club header */}
            <div className="flex items-start justify-between mb-6">
              <div>
                <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
                  {tenant.name}
                </h1>
                <p className="text-sm text-zinc-500 font-mono mt-1">
                  {tenant.slug}.lvh.me
                </p>
              </div>
              <div className="flex gap-2">
                <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${STATUS_BADGE[tenant.status] ?? ""}`}>
                  {tenant.status}
                </span>
                <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${PLAN_BADGE[tenant.plan] ?? ""}`}>
                  {tenant.plan}
                </span>
              </div>
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
              <StatCard label="Members" value={tenant.member_count} />
              <StatCard label="Active Memberships" value={tenant.active_memberships} />
              <div className="bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-700 px-6 py-5">
                <p className="text-sm text-zinc-500 dark:text-zinc-400">Stripe</p>
                <p className="text-lg font-semibold mt-1">
                  {tenant.stripe_connected ? (
                    <span className="text-green-600">Connected</span>
                  ) : (
                    <span className="text-zinc-400">Not connected</span>
                  )}
                </p>
              </div>
            </div>

            {/* Metadata */}
            <div className="bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-700 px-6 py-5">
              <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-3">
                Details
              </h2>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-zinc-500">Created</dt>
                  <dd className="text-zinc-800 dark:text-zinc-200">
                    {new Date(tenant.created_at).toLocaleDateString("en-GB", {
                      day: "numeric",
                      month: "long",
                      year: "numeric",
                    })}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-zinc-500">ID</dt>
                  <dd className="text-zinc-800 dark:text-zinc-200 font-mono">{tenant.id}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-zinc-500">Plan</dt>
                  <dd className="text-zinc-800 dark:text-zinc-200 capitalize">{tenant.plan}</dd>
                </div>
              </dl>
            </div>
          </>
        )}
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

import Link from "next/link";
import { headers } from "next/headers";
import type { Metadata } from "next";
import { fetchBrandKit } from "@/lib/brand-kit";
import { apiGet } from "@/lib/api";
import PublicHeader from "@/components/PublicHeader";

interface PublicMembershipType {
  id: number;
  name: string;
  description: string;
  price: string;
  billing_frequency: "monthly" | "annual";
  renewal_mode: "rolling" | "one_off";
}

export async function generateMetadata(): Promise<Metadata> {
  const headersList = await headers();
  const subdomain = headersList.get("x-subdomain");
  if (!subdomain) return { title: "Join | ClubKit" };

  const brandKit = await fetchBrandKit(subdomain);
  const clubName = brandKit?.club_name ?? subdomain;
  return {
    title: `Join | ${clubName}`,
    description: `Membership options at ${clubName}`,
  };
}

export default async function JoinPage() {
  const headersList = await headers();
  const subdomain = headersList.get("x-subdomain");

  const [brandKit, types] = await Promise.all([
    subdomain ? fetchBrandKit(subdomain) : null,
    subdomain
      ? apiGet("/api/membership-types/public/", subdomain).catch(
          () => [] as PublicMembershipType[]
        )
      : ([] as PublicMembershipType[]),
  ]);

  return (
    <div className="flex flex-1 flex-col">
      <PublicHeader brandKit={brandKit} />

      <main className="max-w-6xl mx-auto w-full px-6 py-12">
        {brandKit?.logo && (
          <img
            src={brandKit.logo}
            alt={`${brandKit.club_name ?? "Club"} logo`}
            className="h-16 w-auto mx-auto mb-6"
          />
        )}

        <h1
          className="text-3xl font-bold text-center mb-2"
          style={{ color: "var(--brand-primary)" }}
        >
          Join Our Club
        </h1>
        <p className="text-center text-zinc-600 dark:text-zinc-400 mb-10">
          Choose a membership that suits you.
        </p>

        {(types as PublicMembershipType[]).length === 0 ? (
          <div className="text-center py-12 text-zinc-500 bg-zinc-50 dark:bg-zinc-900 rounded-xl">
            <p>No membership options are available at the moment.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {(types as PublicMembershipType[]).map((mt) => (
              <div
                key={mt.id}
                className="border border-zinc-200 dark:border-zinc-700 rounded-xl p-6 flex flex-col bg-white dark:bg-zinc-800"
              >
                <h2 className="text-xl font-semibold mb-2 text-zinc-900 dark:text-zinc-100">
                  {mt.name}
                </h2>
                {mt.description && (
                  <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-4 flex-1">
                    {mt.description}
                  </p>
                )}
                <div className="mb-1">
                  <span
                    className="text-2xl font-bold"
                    style={{ color: "var(--brand-primary)" }}
                  >
                    &pound;{mt.price}
                  </span>
                  <span className="text-sm text-zinc-500 ml-1">
                    / {mt.billing_frequency === "monthly" ? "month" : "year"}
                  </span>
                </div>
                <p className="text-xs text-zinc-500 mb-5">
                  {mt.renewal_mode === "rolling"
                    ? "Auto-renews"
                    : "One-off payment"}
                </p>
                <Link
                  href="/register"
                  className="block text-center rounded-lg px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90"
                  style={{ backgroundColor: "var(--brand-primary)" }}
                >
                  Sign up
                </Link>
              </div>
            ))}
          </div>
        )}

        <div className="mt-10 text-center text-sm text-zinc-600 dark:text-zinc-400">
          Already a member?{" "}
          <Link
            href="/login"
            className="font-medium hover:underline"
            style={{ color: "var(--brand-primary)" }}
          >
            Log in
          </Link>
        </div>
      </main>
    </div>
  );
}

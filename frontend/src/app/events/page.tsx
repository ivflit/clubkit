import Link from "next/link";
import { headers } from "next/headers";
import type { Metadata } from "next";
import { fetchBrandKit } from "@/lib/brand-kit";
import { apiGet } from "@/lib/api";
import PublicHeader from "@/components/PublicHeader";

interface PublicEvent {
  id: number;
  title: string;
  date_time: string;
  location: string;
  capacity: number | null;
  status: string;
}

export async function generateMetadata(): Promise<Metadata> {
  const headersList = await headers();
  const subdomain = headersList.get("x-subdomain");
  if (!subdomain) return { title: "Events | ClubKit" };

  const brandKit = await fetchBrandKit(subdomain);
  const clubName = brandKit?.club_name ?? subdomain;
  return {
    title: `Events | ${clubName}`,
    description: `Upcoming events at ${clubName}`,
  };
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default async function EventsPage() {
  const headersList = await headers();
  const subdomain = headersList.get("x-subdomain");

  const [brandKit, events] = await Promise.all([
    subdomain ? fetchBrandKit(subdomain) : null,
    subdomain
      ? apiGet("/api/events/public/", subdomain).catch(() => [] as PublicEvent[])
      : ([] as PublicEvent[]),
  ]);

  return (
    <div className="flex flex-1 flex-col">
      <PublicHeader brandKit={brandKit} />

      <main className="max-w-6xl mx-auto w-full px-6 py-10">
        <h1
          className="text-2xl font-bold mb-8"
          style={{ color: "var(--brand-primary)" }}
        >
          Events
        </h1>

        {(events as PublicEvent[]).length === 0 ? (
          <div className="text-center py-16 text-zinc-500 bg-zinc-50 dark:bg-zinc-900 rounded-xl">
            <p className="text-lg mb-2">No upcoming events</p>
            <p className="text-sm">Check back soon for new events.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {(events as PublicEvent[]).map((ev) => (
              <Link
                key={ev.id}
                href={`/events/${ev.id}`}
                className="border border-zinc-200 dark:border-zinc-700 rounded-xl p-5 hover:shadow-md transition-shadow bg-white dark:bg-zinc-800 block"
              >
                <p
                  className="text-xs font-semibold uppercase tracking-wide mb-2"
                  style={{ color: "var(--brand-accent)" }}
                >
                  {formatDateTime(ev.date_time)}
                </p>
                <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 mb-1">
                  {ev.title}
                </h3>
                {ev.location && (
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">
                    {ev.location}
                  </p>
                )}
                {ev.capacity !== null && (
                  <p className="text-xs text-zinc-400 mt-2">
                    Capacity: {ev.capacity}
                  </p>
                )}
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

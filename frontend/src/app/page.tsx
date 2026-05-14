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
}

async function fetchUpcomingEvents(subdomain: string): Promise<PublicEvent[]> {
  try {
    return await apiGet("/api/events/public/", subdomain);
  } catch {
    return [];
  }
}

export async function generateMetadata(): Promise<Metadata> {
  const headersList = await headers();
  const subdomain = headersList.get("x-subdomain");
  if (!subdomain) return { title: "ClubKit" };

  const brandKit = await fetchBrandKit(subdomain);
  const clubName = brandKit?.club_name ?? subdomain;
  return {
    title: clubName,
    description: brandKit?.description || `Welcome to ${clubName}`,
  };
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default async function Home() {
  const headersList = await headers();
  const subdomain = headersList.get("x-subdomain");

  // Platform root — show landing page
  if (!subdomain) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center bg-zinc-50 dark:bg-zinc-950">
        <main className="max-w-lg text-center px-6">
          <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-white mb-4">
            ClubKit
          </h1>
          <p className="text-lg text-zinc-600 dark:text-zinc-400 mb-8">
            The all-in-one platform for local sports clubs. Memberships, events,
            and a branded website — ready in minutes.
          </p>
          <Link
            href="/onboarding"
            className="inline-flex rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white hover:bg-blue-700"
          >
            Set up your club
          </Link>
        </main>
      </div>
    );
  }

  const [brandKit, events] = await Promise.all([
    fetchBrandKit(subdomain),
    fetchUpcomingEvents(subdomain),
  ]);

  if (!brandKit) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center">
        <p className="text-zinc-500">Club not found.</p>
      </div>
    );
  }

  const upcomingEvents = events.slice(0, 3);

  return (
    <div className="flex flex-1 flex-col">
      <PublicHeader brandKit={brandKit} />

      {/* Hero section */}
      <section
        className="relative flex items-center justify-center py-24 px-6 text-white"
        style={{ backgroundColor: "var(--brand-primary)" }}
      >
        {brandKit.hero_image && (
          <div
            className="absolute inset-0 bg-cover bg-center opacity-30"
            style={{ backgroundImage: `url(${brandKit.hero_image})` }}
          />
        )}
        <div className="relative z-10 text-center max-w-2xl">
          {brandKit.logo && (
            <img
              src={brandKit.logo}
              alt={`${brandKit.club_name} logo`}
              className="h-20 w-auto mx-auto mb-6"
            />
          )}
          <h1 className="text-4xl font-bold tracking-tight mb-4">
            {brandKit.club_name || "Welcome"}
          </h1>
          {brandKit.description && (
            <p className="text-lg opacity-90 mb-8">{brandKit.description}</p>
          )}
          <div className="flex gap-4 justify-center flex-wrap">
            <Link
              href="/join"
              className="rounded-lg px-6 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
              style={{ backgroundColor: "var(--brand-accent)" }}
            >
              Join the club
            </Link>
            <Link
              href="/events"
              className="rounded-lg px-6 py-2.5 text-sm font-semibold bg-white/20 hover:bg-white/30 transition-colors text-white"
            >
              View events
            </Link>
          </div>
        </div>
      </section>

      {/* Upcoming events */}
      <section className="max-w-6xl mx-auto w-full px-6 py-14">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-bold" style={{ color: "var(--brand-primary)" }}>
            Upcoming Events
          </h2>
          <Link
            href="/events"
            className="text-sm font-medium hover:underline"
            style={{ color: "var(--brand-primary)" }}
          >
            View all →
          </Link>
        </div>

        {upcomingEvents.length === 0 ? (
          <div className="text-center py-12 text-zinc-500 bg-zinc-50 dark:bg-zinc-900 rounded-xl">
            <p className="text-lg mb-1">No upcoming events</p>
            <p className="text-sm">Check back soon for new events.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {upcomingEvents.map((ev) => (
              <Link
                key={ev.id}
                href={`/events/${ev.id}`}
                className="border border-zinc-200 dark:border-zinc-700 rounded-xl p-5 hover:shadow-md transition-shadow bg-white dark:bg-zinc-800 block"
              >
                <p
                  className="text-xs font-semibold uppercase tracking-wide mb-2"
                  style={{ color: "var(--brand-accent)" }}
                >
                  {formatDate(ev.date_time)}
                </p>
                <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 mb-1">
                  {ev.title}
                </h3>
                {ev.location && (
                  <p className="text-sm text-zinc-500">{ev.location}</p>
                )}
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Contact info */}
      {(brandKit.contact_email ||
        brandKit.contact_phone ||
        brandKit.contact_address) && (
        <section
          className="border-t border-zinc-100 dark:border-zinc-800 py-12 px-6"
          style={{ backgroundColor: "var(--brand-primary)", opacity: 0.97 }}
        >
          <div className="max-w-6xl mx-auto text-white">
            <h2 className="text-xl font-bold mb-4">Get in Touch</h2>
            <div className="flex flex-wrap gap-6 text-sm text-white/80">
              {brandKit.contact_email && (
                <a
                  href={`mailto:${brandKit.contact_email}`}
                  className="hover:text-white transition-colors"
                >
                  {brandKit.contact_email}
                </a>
              )}
              {brandKit.contact_phone && <span>{brandKit.contact_phone}</span>}
              {brandKit.contact_address && (
                <span>{brandKit.contact_address}</span>
              )}
            </div>
            {(brandKit.social_facebook ||
              brandKit.social_twitter ||
              brandKit.social_instagram) && (
              <div className="flex gap-4 mt-4">
                {brandKit.social_facebook && (
                  <a
                    href={brandKit.social_facebook}
                    className="text-sm text-white/80 hover:text-white transition-colors"
                  >
                    Facebook
                  </a>
                )}
                {brandKit.social_twitter && (
                  <a
                    href={brandKit.social_twitter}
                    className="text-sm text-white/80 hover:text-white transition-colors"
                  >
                    Twitter
                  </a>
                )}
                {brandKit.social_instagram && (
                  <a
                    href={brandKit.social_instagram}
                    className="text-sm text-white/80 hover:text-white transition-colors"
                  >
                    Instagram
                  </a>
                )}
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}

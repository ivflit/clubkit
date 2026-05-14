import { headers } from "next/headers";
import type { Metadata } from "next";
import { fetchBrandKit } from "@/lib/brand-kit";
import { apiGet } from "@/lib/api";
import PublicHeader from "@/components/PublicHeader";
import EventCalendarList, { type CalendarEvent } from "@/components/EventCalendarList";

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

export default async function EventsPage() {
  const headersList = await headers();
  const subdomain = headersList.get("x-subdomain");

  const [brandKit, events] = await Promise.all([
    subdomain ? fetchBrandKit(subdomain) : null,
    subdomain
      ? apiGet("/api/events/public/", subdomain).catch(() => [] as CalendarEvent[])
      : ([] as CalendarEvent[]),
  ]);

  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";
  const accentColour = brandKit?.accent_colour ?? "#ff6d00";

  return (
    <div className="flex flex-1 flex-col">
      <PublicHeader brandKit={brandKit} />

      <main className="max-w-5xl mx-auto w-full px-6 py-10">
        <h1 className="text-2xl font-bold mb-8" style={{ color: "var(--brand-primary)" }}>
          Events
        </h1>

        <EventCalendarList
          events={events as CalendarEvent[]}
          primaryColour={primaryColour}
          accentColour={accentColour}
        />
      </main>
    </div>
  );
}

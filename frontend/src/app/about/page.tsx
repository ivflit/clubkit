import { headers } from "next/headers";
import type { Metadata } from "next";
import { fetchBrandKit } from "@/lib/brand-kit";
import PublicHeader from "@/components/PublicHeader";

export async function generateMetadata(): Promise<Metadata> {
  const headersList = await headers();
  const subdomain = headersList.get("x-subdomain");
  if (!subdomain) return { title: "About | ClubKit" };

  const brandKit = await fetchBrandKit(subdomain);
  const clubName = brandKit?.club_name ?? subdomain;
  return {
    title: `About | ${clubName}`,
    description: brandKit?.description || `Learn more about ${clubName}`,
  };
}

export default async function AboutPage() {
  const headersList = await headers();
  const subdomain = headersList.get("x-subdomain");

  if (!subdomain) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-zinc-500">Not found.</p>
      </div>
    );
  }

  const brandKit = await fetchBrandKit(subdomain);

  if (!brandKit) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-zinc-500">Club not found.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col">
      <PublicHeader brandKit={brandKit} />

      {/* Page header */}
      <section
        className="py-12 px-6 text-white"
        style={{ backgroundColor: "var(--brand-primary)" }}
      >
        <div className="max-w-3xl mx-auto">
          <h1 className="text-3xl font-bold">About {brandKit.club_name}</h1>
        </div>
      </section>

      <main className="max-w-3xl mx-auto w-full px-6 py-12 space-y-12">
        {/* Club description */}
        {brandKit.description && (
          <section>
            <h2
              className="text-xl font-bold mb-4"
              style={{ color: "var(--brand-primary)" }}
            >
              About Us
            </h2>
            <p className="text-zinc-700 dark:text-zinc-300 leading-relaxed whitespace-pre-line">
              {brandKit.description}
            </p>
          </section>
        )}

        {/* Contact info */}
        {(brandKit.contact_email ||
          brandKit.contact_phone ||
          brandKit.contact_address) && (
          <section>
            <h2
              className="text-xl font-bold mb-4"
              style={{ color: "var(--brand-primary)" }}
            >
              Contact
            </h2>
            <ul className="space-y-2 text-zinc-700 dark:text-zinc-300 text-sm">
              {brandKit.contact_email && (
                <li>
                  <span className="font-medium text-zinc-500 dark:text-zinc-400 mr-2">
                    Email
                  </span>
                  <a
                    href={`mailto:${brandKit.contact_email}`}
                    className="hover:underline"
                    style={{ color: "var(--brand-primary)" }}
                  >
                    {brandKit.contact_email}
                  </a>
                </li>
              )}
              {brandKit.contact_phone && (
                <li>
                  <span className="font-medium text-zinc-500 dark:text-zinc-400 mr-2">
                    Phone
                  </span>
                  {brandKit.contact_phone}
                </li>
              )}
              {brandKit.contact_address && (
                <li>
                  <span className="font-medium text-zinc-500 dark:text-zinc-400 mr-2">
                    Address
                  </span>
                  {brandKit.contact_address}
                </li>
              )}
            </ul>
          </section>
        )}

        {/* Social media links */}
        {(brandKit.social_facebook ||
          brandKit.social_twitter ||
          brandKit.social_instagram) && (
          <section>
            <h2
              className="text-xl font-bold mb-4"
              style={{ color: "var(--brand-primary)" }}
            >
              Follow Us
            </h2>
            <div className="flex gap-4">
              {brandKit.social_facebook && (
                <a
                  href={brandKit.social_facebook}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-lg border px-4 py-2 text-sm font-medium hover:opacity-80 transition-opacity text-white"
                  style={{ backgroundColor: "var(--brand-primary)" }}
                >
                  Facebook
                </a>
              )}
              {brandKit.social_twitter && (
                <a
                  href={brandKit.social_twitter}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-lg border px-4 py-2 text-sm font-medium hover:opacity-80 transition-opacity text-white"
                  style={{ backgroundColor: "var(--brand-primary)" }}
                >
                  Twitter
                </a>
              )}
              {brandKit.social_instagram && (
                <a
                  href={brandKit.social_instagram}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-lg border px-4 py-2 text-sm font-medium hover:opacity-80 transition-opacity text-white"
                  style={{ backgroundColor: "var(--brand-primary)" }}
                >
                  Instagram
                </a>
              )}
            </div>
          </section>
        )}

        {/* Empty state */}
        {!brandKit.description &&
          !brandKit.contact_email &&
          !brandKit.contact_phone &&
          !brandKit.contact_address && (
            <div className="text-center py-12 text-zinc-500">
              <p>No club information has been set up yet.</p>
            </div>
          )}
      </main>
    </div>
  );
}

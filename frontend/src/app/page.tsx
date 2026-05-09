import Link from "next/link";
import { headers } from "next/headers";
import { fetchBrandKit } from "@/lib/brand-kit";

export default async function Home() {
  const headersList = await headers();
  const subdomain = headersList.get("x-subdomain");

  // If on a tenant subdomain, show the club's branded landing page
  if (subdomain) {
    const brandKit = await fetchBrandKit(subdomain);

    if (!brandKit) {
      return (
        <div className="flex flex-1 flex-col items-center justify-center">
          <p className="text-zinc-500">Club not found.</p>
        </div>
      );
    }

    return (
      <div className="flex flex-1 flex-col">
        {/* Hero section with Brand Kit theming */}
        <nav className="absolute top-0 right-0 z-20 flex gap-4 p-4">
          <Link
            href="/login"
            className="text-sm font-medium text-white/90 hover:text-white"
          >
            Log in
          </Link>
          <Link
            href="/register"
            className="rounded-lg px-4 py-1.5 text-sm font-medium text-white"
            style={{ backgroundColor: brandKit.accent_colour }}
          >
            Register
          </Link>
        </nav>
        <header
          className="relative flex items-center justify-center py-20 px-6 text-white"
          style={{ backgroundColor: brandKit.primary_colour }}
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
                alt="Club logo"
                className="h-20 w-auto mx-auto mb-6"
              />
            )}
            <h1 className="text-4xl font-bold tracking-tight mb-4">
              Welcome
            </h1>
            {brandKit.description && (
              <p className="text-lg opacity-90">{brandKit.description}</p>
            )}
          </div>
        </header>

        {/* Contact info section */}
        {(brandKit.contact_email || brandKit.contact_phone || brandKit.contact_address) && (
          <section className="max-w-2xl mx-auto py-12 px-6">
            <h2
              className="text-2xl font-bold mb-6"
              style={{ color: brandKit.primary_colour }}
            >
              Contact
            </h2>
            <div className="space-y-2 text-zinc-700 dark:text-zinc-300">
              {brandKit.contact_email && <p>Email: {brandKit.contact_email}</p>}
              {brandKit.contact_phone && <p>Phone: {brandKit.contact_phone}</p>}
              {brandKit.contact_address && <p>Address: {brandKit.contact_address}</p>}
            </div>

            {/* Social links */}
            {(brandKit.social_facebook || brandKit.social_twitter || brandKit.social_instagram) && (
              <div className="flex gap-4 mt-4">
                {brandKit.social_facebook && (
                  <a
                    href={brandKit.social_facebook}
                    className="text-sm hover:underline"
                    style={{ color: brandKit.accent_colour }}
                  >
                    Facebook
                  </a>
                )}
                {brandKit.social_twitter && (
                  <a
                    href={brandKit.social_twitter}
                    className="text-sm hover:underline"
                    style={{ color: brandKit.accent_colour }}
                  >
                    Twitter
                  </a>
                )}
                {brandKit.social_instagram && (
                  <a
                    href={brandKit.social_instagram}
                    className="text-sm hover:underline"
                    style={{ color: brandKit.accent_colour }}
                  >
                    Instagram
                  </a>
                )}
              </div>
            )}
          </section>
        )}
      </div>
    );
  }

  // Platform root — show landing page
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

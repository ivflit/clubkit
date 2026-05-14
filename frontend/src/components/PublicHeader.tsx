import Link from "next/link";
import { BrandKit } from "@/lib/brand-kit";

interface PublicHeaderProps {
  brandKit: BrandKit | null;
}

/**
 * Server Component: shared branded header for all public-facing pages.
 * Uses CSS custom properties (--brand-primary, --brand-accent) set by the root layout.
 */
export default function PublicHeader({ brandKit }: PublicHeaderProps) {
  return (
    <header
      className="sticky top-0 z-30 shadow-sm"
      style={{ backgroundColor: "var(--brand-primary)" }}
    >
      <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
        {/* Logo + club name */}
        <Link href="/" className="flex items-center gap-3 shrink-0">
          {brandKit?.logo ? (
            <img
              src={brandKit.logo}
              alt={`${brandKit.club_name ?? "Club"} logo`}
              className="h-9 w-auto"
            />
          ) : (
            <span className="text-white font-bold text-lg">
              {brandKit?.club_name ?? "ClubKit"}
            </span>
          )}
        </Link>

        {/* Nav links */}
        <nav className="flex items-center gap-5 text-sm font-medium">
          <Link href="/" className="text-white/80 hover:text-white transition-colors">
            Home
          </Link>
          <Link href="/about" className="text-white/80 hover:text-white transition-colors">
            About
          </Link>
          <Link href="/events" className="text-white/80 hover:text-white transition-colors">
            Events
          </Link>
          <Link href="/join" className="text-white/80 hover:text-white transition-colors">
            Join
          </Link>
          <Link
            href="/login"
            className="rounded-lg px-4 py-1.5 text-white text-sm font-medium transition-opacity hover:opacity-90"
            style={{ backgroundColor: "var(--brand-accent)" }}
          >
            Log in
          </Link>
        </nav>
      </div>
    </header>
  );
}

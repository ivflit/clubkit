/**
 * Extracts the subdomain from a hostname.
 * e.g. "riverside-fc.lvh.me" → "riverside-fc"
 *      "lvh.me" → null (platform root)
 *      "localhost" → null
 */
export function getSubdomain(hostname: string): string | null {
  // Strip port if present
  const host = hostname.split(":")[0];

  // Known platform root domains
  const platformDomains = ["lvh.me", "localhost", "127.0.0.1"];

  for (const domain of platformDomains) {
    if (host === domain) return null;
    if (host.endsWith(`.${domain}`)) {
      const sub = host.slice(0, -(domain.length + 1));
      return sub || null;
    }
  }

  // For production: assume first segment is subdomain (e.g. riverside-fc.clubkit.com)
  const parts = host.split(".");
  if (parts.length >= 3) {
    return parts[0];
  }

  return null;
}

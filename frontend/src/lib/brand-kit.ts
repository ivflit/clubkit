import { apiGet, ApiError } from "./api";

export interface BrandKit {
  club_name: string;
  logo: string;
  primary_colour: string;
  accent_colour: string;
  hero_image: string;
  description: string;
  contact_email: string;
  contact_phone: string;
  contact_address: string;
  social_facebook: string;
  social_twitter: string;
  social_instagram: string;
}

/**
 * Fetches the Brand Kit for a given tenant subdomain.
 * Returns null if the tenant doesn't exist (404).
 */
export async function fetchBrandKit(subdomain: string): Promise<BrandKit | null> {
  try {
    return await apiGet("/api/brand-kit/", subdomain);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return null;
    }
    throw err;
  }
}

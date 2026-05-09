"use client";

import { useState, useEffect } from "react";
import { getSubdomain } from "@/lib/tenant";
import { BrandKit, fetchBrandKit } from "@/lib/brand-kit";

export function useBrandKit() {
  const [brandKit, setBrandKit] = useState<BrandKit | null>(null);
  const [subdomain, setSubdomain] = useState<string | null>(null);

  useEffect(() => {
    const sub = getSubdomain(window.location.hostname);
    setSubdomain(sub);
    if (sub) {
      fetchBrandKit(sub).then(setBrandKit).catch(() => {});
    }
  }, []);

  return { brandKit, subdomain };
}

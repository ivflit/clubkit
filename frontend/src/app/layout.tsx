import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { headers } from "next/headers";
import "./globals.css";
import { fetchBrandKit } from "@/lib/brand-kit";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ClubKit",
  description: "The all-in-one platform for local sports clubs",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const headersList = await headers();
  const subdomain = headersList.get("x-subdomain");

  const brandKit = subdomain ? await fetchBrandKit(subdomain) : null;
  const primaryColour = brandKit?.primary_colour ?? "#1a73e8";
  const accentColour = brandKit?.accent_colour ?? "#ff6d00";

  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      style={
        {
          "--brand-primary": primaryColour,
          "--brand-accent": accentColour,
        } as React.CSSProperties
      }
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}

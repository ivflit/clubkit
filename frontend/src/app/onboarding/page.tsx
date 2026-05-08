"use client";

import { useState } from "react";
import { apiPost, ApiError } from "@/lib/api";

type Step = "club" | "brand" | "contact" | "done";

interface FormState {
  club_name: string;
  subdomain: string;
  primary_colour: string;
  accent_colour: string;
  description: string;
  contact_email: string;
  contact_phone: string;
  contact_address: string;
  social_facebook: string;
  social_twitter: string;
  social_instagram: string;
  logo: File | null;
  hero_image: File | null;
}

const initial: FormState = {
  club_name: "",
  subdomain: "",
  primary_colour: "#1a73e8",
  accent_colour: "#ff6d00",
  description: "",
  contact_email: "",
  contact_phone: "",
  contact_address: "",
  social_facebook: "",
  social_twitter: "",
  social_instagram: "",
  logo: null,
  hero_image: null,
};

export default function OnboardingPage() {
  const [step, setStep] = useState<Step>("club");
  const [form, setForm] = useState<FormState>(initial);
  const [errors, setErrors] = useState<Record<string, string[]>>({});
  const [submitting, setSubmitting] = useState(false);
  const [tenantSlug, setTenantSlug] = useState("");

  function set<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }

  function autoSlug(name: string) {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "")
      .slice(0, 63);
  }

  async function handleSubmit() {
    setSubmitting(true);
    setErrors({});
    try {
      const fd = new FormData();
      fd.append("club_name", form.club_name);
      fd.append("subdomain", form.subdomain);
      fd.append("primary_colour", form.primary_colour);
      fd.append("accent_colour", form.accent_colour);
      if (form.description) fd.append("description", form.description);
      if (form.contact_email) fd.append("contact_email", form.contact_email);
      if (form.contact_phone) fd.append("contact_phone", form.contact_phone);
      if (form.contact_address)
        fd.append("contact_address", form.contact_address);
      if (form.social_facebook)
        fd.append("social_facebook", form.social_facebook);
      if (form.social_twitter)
        fd.append("social_twitter", form.social_twitter);
      if (form.social_instagram)
        fd.append("social_instagram", form.social_instagram);
      if (form.logo) fd.append("logo", form.logo);
      if (form.hero_image) fd.append("hero_image", form.hero_image);

      const data = await apiPost("/api/onboarding/", fd);
      setTenantSlug(data.slug);
      setStep("done");
    } catch (err) {
      if (err instanceof ApiError) {
        setErrors(err.data as Record<string, string[]>);
      }
    } finally {
      setSubmitting(false);
    }
  }

  const fieldError = (field: string) =>
    errors[field] ? (
      <p className="text-sm text-red-600 mt-1">{errors[field].join(", ")}</p>
    ) : null;

  const inputClass =
    "w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-white";
  const labelClass = "block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1";
  const btnPrimary =
    "rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50";
  const btnSecondary =
    "rounded-lg border border-zinc-300 px-6 py-2.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-300 dark:hover:bg-zinc-800";

  if (step === "done") {
    const clubUrl = `http://${tenantSlug}.lvh.me:8000`;
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
        <div className="mx-auto max-w-md rounded-xl bg-white p-8 shadow-lg dark:bg-zinc-900 text-center">
          <div className="text-4xl mb-4">&#10003;</div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-2">
            Your club is live!
          </h1>
          <p className="text-zinc-600 dark:text-zinc-400 mb-6">
            Your club site is ready at{" "}
            <a
              href={clubUrl}
              className="font-medium text-blue-600 hover:underline"
            >
              {tenantSlug}.lvh.me
            </a>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white p-8 shadow-lg dark:bg-zinc-900">
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-1">
          Set up your club
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-6">
          {step === "club" && "Step 1 of 3 — Club details"}
          {step === "brand" && "Step 2 of 3 — Branding"}
          {step === "contact" && "Step 3 of 3 — Contact info"}
        </p>

        {/* Non-field errors */}
        {errors.non_field_errors && (
          <p className="text-sm text-red-600 mb-4">
            {(errors.non_field_errors as string[]).join(", ")}
          </p>
        )}

        {step === "club" && (
          <div className="space-y-4">
            <div>
              <label className={labelClass}>Club name *</label>
              <input
                className={inputClass}
                value={form.club_name}
                onChange={(e) => {
                  set("club_name", e.target.value);
                  if (!form.subdomain || form.subdomain === autoSlug(form.club_name)) {
                    set("subdomain", autoSlug(e.target.value));
                  }
                }}
                placeholder="Riverside FC"
              />
              {fieldError("club_name")}
            </div>
            <div>
              <label className={labelClass}>Subdomain *</label>
              <div className="flex items-center gap-1">
                <input
                  className={inputClass}
                  value={form.subdomain}
                  onChange={(e) => set("subdomain", e.target.value.toLowerCase())}
                  placeholder="riverside-fc"
                />
                <span className="text-sm text-zinc-500 whitespace-nowrap">
                  .clubkit.com
                </span>
              </div>
              {fieldError("subdomain")}
            </div>
            <div>
              <label className={labelClass}>Club description</label>
              <textarea
                className={inputClass + " h-24 resize-none"}
                value={form.description}
                onChange={(e) => set("description", e.target.value)}
                placeholder="Tell people about your club..."
              />
              {fieldError("description")}
            </div>
            <div className="flex justify-end">
              <button
                className={btnPrimary}
                onClick={() => setStep("brand")}
                disabled={!form.club_name || !form.subdomain}
              >
                Next
              </button>
            </div>
          </div>
        )}

        {step === "brand" && (
          <div className="space-y-4">
            <div>
              <label className={labelClass}>Logo</label>
              <input
                type="file"
                accept="image/*"
                className={inputClass}
                onChange={(e) => set("logo", e.target.files?.[0] ?? null)}
              />
              {fieldError("logo")}
            </div>
            <div>
              <label className={labelClass}>Hero image</label>
              <input
                type="file"
                accept="image/*"
                className={inputClass}
                onChange={(e) => set("hero_image", e.target.files?.[0] ?? null)}
              />
              {fieldError("hero_image")}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Primary colour</label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={form.primary_colour}
                    onChange={(e) => set("primary_colour", e.target.value)}
                    className="h-10 w-10 cursor-pointer rounded border-0"
                  />
                  <input
                    className={inputClass}
                    value={form.primary_colour}
                    onChange={(e) => set("primary_colour", e.target.value)}
                  />
                </div>
                {fieldError("primary_colour")}
              </div>
              <div>
                <label className={labelClass}>Accent colour</label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={form.accent_colour}
                    onChange={(e) => set("accent_colour", e.target.value)}
                    className="h-10 w-10 cursor-pointer rounded border-0"
                  />
                  <input
                    className={inputClass}
                    value={form.accent_colour}
                    onChange={(e) => set("accent_colour", e.target.value)}
                  />
                </div>
                {fieldError("accent_colour")}
              </div>
            </div>
            <div className="flex justify-between">
              <button className={btnSecondary} onClick={() => setStep("club")}>
                Back
              </button>
              <button className={btnPrimary} onClick={() => setStep("contact")}>
                Next
              </button>
            </div>
          </div>
        )}

        {step === "contact" && (
          <div className="space-y-4">
            <div>
              <label className={labelClass}>Contact email</label>
              <input
                type="email"
                className={inputClass}
                value={form.contact_email}
                onChange={(e) => set("contact_email", e.target.value)}
                placeholder="info@riverside-fc.com"
              />
              {fieldError("contact_email")}
            </div>
            <div>
              <label className={labelClass}>Contact phone</label>
              <input
                className={inputClass}
                value={form.contact_phone}
                onChange={(e) => set("contact_phone", e.target.value)}
                placeholder="+44 1234 567890"
              />
              {fieldError("contact_phone")}
            </div>
            <div>
              <label className={labelClass}>Address</label>
              <textarea
                className={inputClass + " h-20 resize-none"}
                value={form.contact_address}
                onChange={(e) => set("contact_address", e.target.value)}
                placeholder="123 Sports Ground, City, Postcode"
              />
              {fieldError("contact_address")}
            </div>
            <div>
              <label className={labelClass}>Facebook URL</label>
              <input
                type="url"
                className={inputClass}
                value={form.social_facebook}
                onChange={(e) => set("social_facebook", e.target.value)}
              />
              {fieldError("social_facebook")}
            </div>
            <div>
              <label className={labelClass}>Twitter / X URL</label>
              <input
                type="url"
                className={inputClass}
                value={form.social_twitter}
                onChange={(e) => set("social_twitter", e.target.value)}
              />
              {fieldError("social_twitter")}
            </div>
            <div>
              <label className={labelClass}>Instagram URL</label>
              <input
                type="url"
                className={inputClass}
                value={form.social_instagram}
                onChange={(e) => set("social_instagram", e.target.value)}
              />
              {fieldError("social_instagram")}
            </div>
            <div className="flex justify-between">
              <button className={btnSecondary} onClick={() => setStep("brand")}>
                Back
              </button>
              <button
                className={btnPrimary}
                onClick={handleSubmit}
                disabled={submitting}
              >
                {submitting ? "Creating..." : "Create my club"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

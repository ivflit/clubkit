import Link from "next/link";

export default function Home() {
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

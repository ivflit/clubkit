import Link from "next/link";

export default function ClubNotFoundPage() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center bg-zinc-50 dark:bg-zinc-950">
      <main className="max-w-md text-center px-6">
        <h1 className="text-6xl font-bold text-zinc-300 dark:text-zinc-700 mb-4">
          404
        </h1>
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-white mb-2">
          Club not found
        </h2>
        <p className="text-zinc-600 dark:text-zinc-400 mb-8">
          We couldn&apos;t find a club at this address. It may not exist yet, or
          the URL might be incorrect.
        </p>
        <Link
          href="http://lvh.me:3000/onboarding"
          className="inline-flex rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white hover:bg-blue-700"
        >
          Set up a new club
        </Link>
      </main>
    </div>
  );
}

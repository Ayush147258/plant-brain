import Link from "next/link";

export default function NotFound() {
  return (
    <section className="mx-auto flex min-h-[60vh] w-full max-w-3xl flex-col items-center justify-center px-6 text-center">
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-primary">404</p>
      <h1 className="mt-3 text-3xl font-bold text-text-primary md:text-4xl">Page not found</h1>
      <p className="mt-4 max-w-xl text-base text-text-secondary">
        This PlantBrain page is not available. Return to the demo or the homepage to keep exploring the system.
      </p>
      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        <Link href="/demo" className="rounded-lg bg-primary px-5 py-3 text-sm font-semibold text-white transition hover:bg-primary-dark">
          Open demo
        </Link>
        <Link href="/" className="rounded-lg border border-border px-5 py-3 text-sm font-semibold text-text-primary transition hover:bg-surface">
          Go home
        </Link>
      </div>
    </section>
  );
}
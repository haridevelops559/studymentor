import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "StudyMentor — Personal Learning & Retention Coach",
  description:
    "Turn your notes into retrieval practice, spaced reviews, and Feynman-style explanations.",
};

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/subjects", label: "Subjects" },
  { href: "/review", label: "Review" },
  { href: "/practice", label: "Practice" },
  { href: "/feynman", label: "Feynman" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen">
          <header className="border-b border-slate-200 bg-white">
            <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
              <Link href="/dashboard" className="flex items-center gap-2">
                <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-sm font-bold text-white">
                  S
                </span>
                <span className="text-lg font-semibold tracking-tight">
                  StudyMentor
                </span>
              </Link>
              <nav className="flex items-center gap-1">
                {NAV_LINKS.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"
                  >
                    {link.label}
                  </Link>
                ))}
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-5xl px-6 py-8">{children}</main>
        </div>
      </body>
    </html>
  );
}

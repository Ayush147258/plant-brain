import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

const appUrl = process.env.NEXT_PUBLIC_APP_URL || "https://plant-brain-sooty.vercel.app";

export const metadata: Metadata = {
  metadataBase: new URL(appUrl),
  title: "PlantBrain - Industrial Knowledge Intelligence",
  description: "Instant, source-cited answers from all your plant's maintenance records, safety procedures, and compliance documents.",
  openGraph: {
    title: "PlantBrain - Industrial Knowledge Intelligence",
    description: "Your plant's memory, finally answerable. Instant answers from all your procedures and records.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "PlantBrain Preview",
      },
    ],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen flex flex-col bg-background text-text-primary">
        <Navbar />
        <main className="flex-1 flex flex-col">
          {children}
        </main>
      </body>
    </html>
  );
}
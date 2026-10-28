import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aviation Flight Planner — 3D Global Dispatch Platform",
  description: "Global aviation flight planning platform with 3D interactive Earth, OurAirports database, route routing engine, and OFP briefing generation.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased bg-[#0B0F19] text-[#F3F4F6]">{children}</body>
    </html>
  );
}

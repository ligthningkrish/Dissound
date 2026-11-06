import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "Dissound — Discord Soundboard Bot & Web Dashboard",
  description: "Discover, manage, auto-trim, and upload meme sounds directly into your Discord Server Soundboards with one click.",
  icons: {
    icon: "/logo.jpg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0B0D13] text-gray-100 min-h-screen flex flex-col selection:bg-discord-blurple selection:text-white">
        <Navbar />
        <main className="flex-1 pt-16">
          {children}
        </main>
        <footer className="border-t border-white/5 py-8 text-center text-xs text-gray-500 bg-[#07090E]">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p>&copy; {new Date().getFullYear()} Dissound. Built for gaming communities & voice channel fun.</p>
            <div className="flex items-center gap-6">
              <a href="https://discord.com" target="_blank" rel="noreferrer" className="hover:text-discord-blurple transition">Discord API</a>
              <a href="/pricing" className="hover:text-amber-300 transition">Premium Features</a>
              <a href="https://github.com/ligthningkrish/Dissound" target="_blank" rel="noreferrer" className="hover:text-white transition">GitHub</a>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}

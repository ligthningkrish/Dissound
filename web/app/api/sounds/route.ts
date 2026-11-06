import { NextRequest, NextResponse } from "next/server";

export interface SoundItem {
  id: string;
  name: string;
  category: string;
  duration: number;
  fileSize: number;
  url: string;
  tags: string[];
  isPremium?: boolean;
}

const DEFAULT_SOUNDS: SoundItem[] = [
  {
    id: "vine_boom",
    name: "Vine Boom",
    category: "Meme Sounds",
    duration: 1.5,
    fileSize: 25120,
    url: "/sounds/vine_boom.mp3",
    tags: ["vine", "boom", "bass", "thud", "dramatic"],
  },
  {
    id: "metal_pipe",
    name: "Metal Pipe Falling",
    category: "Random & Funny",
    duration: 1.8,
    fileSize: 29718,
    url: "/sounds/metal_pipe.mp3",
    tags: ["metal", "pipe", "falling", "clang", "loud"],
  },
  {
    id: "windows_error",
    name: "Windows XP Error",
    category: "Classic Internet",
    duration: 1.2,
    fileSize: 20105,
    url: "/sounds/windows_error.mp3",
    tags: ["windows", "xp", "error", "classic", "microsoft"],
  },
  {
    id: "airhorn",
    name: "MLG Airhorn",
    category: "Random & Funny",
    duration: 1.2,
    fileSize: 20105,
    url: "/sounds/airhorn.mp3",
    tags: ["airhorn", "mlg", "horn", "hype"],
  },
  {
    id: "roblox_oof",
    name: "Roblox Oof",
    category: "Gaming",
    duration: 0.9,
    fileSize: 15507,
    url: "/sounds/roblox_oof.mp3",
    tags: ["roblox", "oof", "gaming", "death"],
  },
  {
    id: "bruh",
    name: "Bruh Sound Effect #2",
    category: "Meme Sounds",
    duration: 1.2,
    fileSize: 20105,
    url: "/sounds/bruh.mp3",
    tags: ["bruh", "reaction", "disappointment"],
  },
  {
    id: "bonk",
    name: "Bonk (Doge Mallet)",
    category: "Reactions",
    duration: 0.8,
    fileSize: 13835,
    url: "/sounds/bonk.mp3",
    tags: ["bonk", "hammer", "doge", "cartoon"],
  },
  {
    id: "among_us",
    name: "Among Us Impostor Kill",
    category: "Gaming",
    duration: 1.4,
    fileSize: 23448,
    url: "/sounds/among_us.mp3",
    tags: ["among us", "sus", "impostor", "gaming"],
  },
  {
    id: "anime_wow",
    name: "Anime Wow",
    category: "Reactions",
    duration: 1.0,
    fileSize: 17179,
    url: "/sounds/anime_wow.mp3",
    tags: ["anime", "wow", "cute", "reaction"],
  },
  {
    id: "tada",
    name: "Tada Fanfare",
    category: "Reactions",
    duration: 1.5,
    fileSize: 25120,
    url: "/sounds/tada.mp3",
    tags: ["tada", "fanfare", "success", "winner"],
  },
  // Paywalled / Premium Sounds showcase
  {
    id: "ai_voice_morgan",
    name: "AI Narrator 'It Was At This Moment'",
    category: "AI Generated (PRO)",
    duration: 3.2,
    fileSize: 45000,
    url: "/sounds/vine_boom.mp3",
    tags: ["ai", "narrator", "pro", "meme"],
    isPremium: true,
  },
  {
    id: "ultra_bass_8k",
    name: "Ultra-Sub Spatial 8D Boom",
    category: "HD Audio (PRO)",
    duration: 4.8,
    fileSize: 85000,
    url: "/sounds/vine_boom.mp3",
    tags: ["8d", "spatial", "hd", "pro"],
    isPremium: true,
  },
];

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const q = searchParams.get("q")?.toLowerCase();
  const cat = searchParams.get("category");

  let filtered = DEFAULT_SOUNDS;
  if (cat && cat !== "All") {
    filtered = filtered.filter((s) => s.category.toLowerCase() === cat.toLowerCase());
  }

  if (q) {
    filtered = filtered.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.tags.some((t) => t.toLowerCase().includes(q)) ||
        s.category.toLowerCase().includes(q)
    );
  }

  return NextResponse.json({
    sounds: filtered,
    categories: ["All", "Meme Sounds", "Gaming", "Reactions", "Classic Internet", "Random & Funny", "AI Generated (PRO)", "HD Audio (PRO)"],
  });
}
